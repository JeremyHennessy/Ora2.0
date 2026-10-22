"""Bounded local task/observation service. No shell or generated-code execution.

New service apparatus, not PILOT74 qualification or an evolved learning policy.
One owner holds an OS lock; SQLite commits task completion and memory together.
Sequential submission IDs make retries safe even after old receipts are pruned.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time

MAX_TEXT = 4096
MAX_KEY = 128
MAX_PENDING = 128
MAX_MEMORIES = 256
MAX_RECEIPTS = 128
MAX_PAGES = 1024  # 4 MiB, rollback journal is transient and separately bounded.


def text(value, limit):
    if type(value) is not str or not value or len(value.encode('utf8')) > limit:
        raise ValueError('Nonempty bounded UTF-8 text required')
    return value


class Store:
    def __init__(self, directory, generator=None, feedback_key=None):
        self.generator=generator
        self.feedback_key=feedback_key
        if generator is not None and (type(feedback_key) is not bytes or len(feedback_key)!=32):
            raise ValueError('Model mode requires separate operator feedback key')
        self.db = None
        self.lock = None
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        if root.is_symlink() or getattr(root.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('Store directory must be a plain directory')
        for name in ('owner.lock', 'memory.sqlite3', 'memory.sqlite3-journal'):
            p = root / name
            if p.exists() and (p.is_symlink() or p.stat().st_nlink != 1 or
                              getattr(p.lstat(), 'st_file_attributes', 0) & 0x400):
                raise ValueError('Store files must be plain unshared files')
        self.lock = (root / 'owner.lock').open('a+b')
        try:
            self.lock.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.db = sqlite3.connect(root / 'memory.sqlite3', timeout=1)
            self.db.execute('PRAGMA page_size=4096')
            self.db.execute('PRAGMA journal_mode=DELETE')
            self.db.execute('PRAGMA synchronous=FULL')
            self.db.execute(f'PRAGMA max_page_count={MAX_PAGES}')
            self.db.execute('PRAGMA busy_timeout=1000')
            if self.db.execute('PRAGMA user_version').fetchone()[0] not in (0, 1):
                raise ValueError('Unsupported memory schema; migration required')
            if self.db.execute('PRAGMA page_count').fetchone()[0] > MAX_PAGES:
                raise ValueError('Existing store exceeds configured capacity')
            if self.db.execute('PRAGMA quick_check').fetchone() != ('ok',):
                raise ValueError('Memory integrity check failed')
            self.db.executescript('''
                CREATE TABLE IF NOT EXISTS meta(id INTEGER PRIMARY KEY CHECK(id=1), submitted INTEGER NOT NULL);
                INSERT OR IGNORE INTO meta VALUES(1,0);
                CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, kind TEXT NOT NULL,
                    key TEXT NOT NULL, value TEXT NOT NULL, state TEXT NOT NULL,
                    result TEXT, CHECK(state IN ('pending','running','done')));
                CREATE TABLE IF NOT EXISTS memories(key TEXT PRIMARY KEY, value TEXT NOT NULL,
                    task INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS proposals(key TEXT PRIMARY KEY, value TEXT NOT NULL,
                    task INTEGER NOT NULL, sha256 TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS memory_provenance(key TEXT PRIMARY KEY, task INTEGER NOT NULL,
                    issuer TEXT NOT NULL);
                PRAGMA user_version=1;
            ''')
            with self.db:
                # OS lock proves previous owner is gone. Reclaim unfinished work.
                self.db.execute("UPDATE tasks SET state='pending' WHERE state='running'")
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None
        if self.lock is not None:
            self.lock.close()
            self.lock = None

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()

    def submit(self, sequence, kind, key, value=''):
        if type(sequence) is not int or not 0 < sequence < 2**63:
            raise ValueError('Positive signed 64-bit sequence required')
        allowed=('recall','ask','ask-isolated','approve') if self.generator is not None else ('remember','recall','forget')
        if kind not in allowed:
            raise ValueError('Task kind is not enabled in this trust mode')
        text(key, MAX_KEY)
        if kind in ('remember','ask','ask-isolated','approve'):
            text(value, MAX_TEXT)
        elif value != '':
            raise ValueError('This task has no value')
        if kind=='approve':
            from experiments.ora_ollama_feedback_v1 import verify
            verify(self.feedback_key,sequence,key,value)
        with self.db:
            last = self.db.execute('SELECT submitted FROM meta').fetchone()[0]
            if sequence <= last:
                old = self.db.execute('SELECT kind,key,value FROM tasks WHERE id=?', (sequence,)).fetchone()
                if old is not None and old != (kind, key, value):
                    raise ValueError('Submission ID reused with different content')
                # Pruned IDs cannot be replayed or silently accepted as new tasks.
                return 'already-submitted' if old else 'expired-receipt'
            if sequence != last + 1:
                raise ValueError('Submission IDs must be consecutive')
            count = self.db.execute("SELECT count(*) FROM tasks WHERE state!='done'").fetchone()[0]
            if count >= MAX_PENDING:
                raise ValueError('Queue full; producer must wait')
            self.db.execute('INSERT INTO tasks VALUES(?,?,?,?,?,NULL)',
                            (sequence, kind, key, value, 'pending'))
            self.db.execute('UPDATE meta SET submitted=?', (sequence,))
        return 'submitted'

    def claim(self):
        with self.db:
            row = self.db.execute("SELECT id,kind,key,value FROM tasks WHERE state='pending' ORDER BY id LIMIT 1").fetchone()
            if row:
                self.db.execute("UPDATE tasks SET state='running' WHERE id=?", (row[0],))
            return row

    def complete(self, task):
        ident, kind, key, value = task
        if self.generator is not None and kind in ('remember','forget'):
            raise ValueError('Unsigned mutation pending from another trust mode; operator migration required')
        with self.db:
            row = self.db.execute('SELECT id,kind,key,value,state FROM tasks WHERE id=?', (ident,)).fetchone()
            if row != (*task, 'running'):
                raise ValueError('Task is not the current claimed task')
            if kind in ('ask','ask-isolated'):
                if self.generator is None: raise ValueError('Pending model task requires model trust mode')
                # Reuse only previously trusted memory; a key hit avoids generation.
                remembered=self.db.execute('SELECT value FROM memories WHERE key=?',(key,)).fetchone() if kind=='ask' else None
                if remembered:
                    result=remembered[0]
                else:
                    from experiments.ora_memory_context_v1 import context
                    prompt,retrieved=context(self.db,value) if kind=='ask' else (value,[])
                    answer=self.generator(prompt); text(answer,MAX_TEXT)
                    digest=hashlib.sha256(answer.encode('utf8')).hexdigest()
                    self.db.execute('INSERT OR REPLACE INTO proposals VALUES(?,?,?,?)',(key,answer,ident,digest))
                    self.db.execute('DELETE FROM proposals WHERE key IN (SELECT key FROM proposals ORDER BY task DESC LIMIT -1 OFFSET 16)')
                    result=json.dumps(dict(trusted=False,proposal_sha256=digest,answer=answer,retrieved_memories=retrieved),separators=(',',':'))
            elif kind=='approve':
                from experiments.ora_ollama_feedback_v1 import verify
                if self.generator is None: raise ValueError('Signed feedback mode required')
                feedback=verify(self.feedback_key,ident,key,value)
                proposal=self.db.execute('SELECT sha256 FROM proposals WHERE key=?',(key,)).fetchone()
                if proposal!=(feedback['proposal_sha256'],): raise ValueError('Proposal is absent, replaced or expired')
                self.db.execute('INSERT OR REPLACE INTO memories VALUES(?,?,?)',(key,feedback['value'],ident))
                self.db.execute('INSERT OR REPLACE INTO memory_provenance VALUES(?,?,?)',(key,ident,feedback['issuer']))
                self.db.execute('DELETE FROM proposals WHERE key=?',(key,))
                result='operator-confirmed' if feedback['issuer']=='operator' else 'program-confirmed'
            elif kind == 'remember':
                self.db.execute('INSERT OR REPLACE INTO memories VALUES(?,?,?)', (key, value, ident))
                self.db.execute('INSERT OR REPLACE INTO memory_provenance VALUES(?,?,?)',(key,ident,'local-operator'))
                # Deterministic oldest-update eviction. No ever-growing history.
                self.db.execute('DELETE FROM memories WHERE key IN (SELECT key FROM memories ORDER BY task DESC LIMIT -1 OFFSET ?)', (MAX_MEMORIES,))
                result = 'remembered'
            elif kind == 'forget':
                self.db.execute('DELETE FROM memories WHERE key=?', (key,))
                result = 'forgotten'
            elif kind=='recall':
                found = self.db.execute('SELECT value FROM memories WHERE key=?', (key,)).fetchone()
                result = found[0] if found else None
            else:
                raise ValueError('Pending task is incompatible with current trust mode')
            self.db.execute('DELETE FROM memories WHERE key IN (SELECT key FROM memories ORDER BY task DESC LIMIT -1 OFFSET ?)', (MAX_MEMORIES,))
            self.db.execute('DELETE FROM memory_provenance WHERE key NOT IN (SELECT key FROM memories)')
            self.db.execute("UPDATE tasks SET state='done',result=? WHERE id=?", (result, ident))
            self.db.execute("DELETE FROM tasks WHERE id IN (SELECT id FROM tasks WHERE state='done' ORDER BY id DESC LIMIT -1 OFFSET ?)", (MAX_RECEIPTS,))
        return result

    def backup(self, directory):
        """Two bounded SQLite snapshots. Never silently roll back trusted state."""
        root=Path(directory); root.mkdir(exist_ok=True)
        for name in ('snapshot.next','snapshot-0.sqlite3','snapshot-1.sqlite3'):
            p=root/name
            if p.exists() and (p.is_symlink() or p.stat().st_nlink!=1 or
                              getattr(p.lstat(),'st_file_attributes',0)&0x400):
                raise ValueError('Backup targets must be plain local files')
        if root.is_symlink() or getattr(root.lstat(),'st_file_attributes',0)&0x400:
            raise ValueError('Backup directory must be plain')
        temporary=root/'snapshot.next'
        if temporary.exists():
            # Owned fixed temporary only, never an unknown snapshot or directory.
            temporary.unlink()
        destination=sqlite3.connect(temporary)
        try:
            self.db.backup(destination,pages=64)
            if destination.execute('PRAGMA integrity_check').fetchone()!=('ok',):
                raise ValueError('Backup integrity check failed')
        finally:
            destination.close()
        if temporary.stat().st_size>MAX_PAGES*4096:
            raise ValueError('Snapshot exceeds database cap')
        with temporary.open('r+b') as stream: stream.flush(); os.fsync(stream.fileno())
        # A complete current snapshot survives a failed replacement of its older sibling.
        slot=root/'snapshot-0.sqlite3'; previous=root/'snapshot-1.sqlite3'
        if slot.exists(): os.replace(slot,previous)
        os.replace(temporary,slot)
        return dict(bytes=slot.stat().st_size,sha256=hashlib.sha256(slot.read_bytes()).hexdigest(),
                    automatic_restore=False)

    def status(self):
        return dict(submitted=self.db.execute('SELECT submitted FROM meta').fetchone()[0],
                    pending=self.db.execute("SELECT count(*) FROM tasks WHERE state!='done'").fetchone()[0],
                    memories=self.db.execute('SELECT count(*) FROM memories').fetchone()[0],
                    receipts=self.db.execute("SELECT count(*) FROM tasks WHERE state='done'").fetchone()[0],
                    database_bytes=self.db.execute('PRAGMA page_count').fetchone()[0] * 4096,
                    database_limit_bytes=MAX_PAGES * 4096)


def serve(store, stop_path, seconds=60, max_tasks=1000, inbox=None):
    """Finite supervised slice; durable queue continues in the next slice.

    Producer integration is explicit through submit(), not arbitrary file scans.
    Stop checks happen between bounded local transactions, including when idle.
    """
    if not 0 < seconds <= 3600 or type(max_tasks) is not int or not 0 < max_tasks <= 10000:
        raise ValueError('Invalid supervised slice bounds')
    deadline = time.monotonic() + seconds
    done = 0
    seen = None
    while time.monotonic() < deadline and done < max_tasks:
        if Path(stop_path).exists():
            return dict(reason='operator-stop', completed=done)
        if inbox is not None and Path(inbox).exists():
            # A single atomically replaced bounded mailbox; never execute its text.
            with Path(inbox).open('rb') as stream:
                raw = stream.read(65537)
            if len(raw) > 65536:
                raise ValueError('Inbox exceeds 64 KiB')
            digest = hashlib.sha256(raw).digest()
            if digest != seen:
                batch = json.loads(raw)
                if type(batch) is not list or not 0 < len(batch) <= 16:
                    raise ValueError('Inbox must contain 1..16 tasks')
                for item in batch:
                    if type(item) is not dict or set(item) != {'sequence', 'kind', 'key', 'value'}:
                        raise ValueError('Invalid inbox task')
                    store.submit(**item)
                seen = digest
        task = store.claim()
        if task is None:
            time.sleep(min(.1, max(0, deadline - time.monotonic())))
        else:
            store.complete(task)
            done += 1
    return dict(reason='slice-bound', completed=done)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--seconds', type=float, default=60)
    parser.add_argument('--max-tasks', type=int, default=1000)
    args = parser.parse_args()
    from experiments.ora_ollama_feedback_v1 import configuration
    generator,key=configuration(args.directory)
    with Store(args.directory,generator=generator,feedback_key=key) as store:
        result = serve(store, args.directory / 'STOP', args.seconds, args.max_tasks,
                       args.directory / 'inbox.json')
        print(json.dumps(dict(run=result, store=store.status()), sort_keys=True))


if __name__ == '__main__':
    main()
