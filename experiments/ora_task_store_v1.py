"""Bounded local task/observation service. No model, shell or network execution.

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
    def __init__(self, directory):
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
        if kind not in ('remember', 'recall', 'forget'):
            raise ValueError('Only remember, recall and forget are supported')
        text(key, MAX_KEY)
        if kind == 'remember':
            text(value, MAX_TEXT)
        elif value != '':
            raise ValueError('This task has no value')
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
        with self.db:
            row = self.db.execute('SELECT id,kind,key,value,state FROM tasks WHERE id=?', (ident,)).fetchone()
            if row != (*task, 'running'):
                raise ValueError('Task is not the current claimed task')
            if kind == 'remember':
                self.db.execute('INSERT OR REPLACE INTO memories VALUES(?,?,?)', (key, value, ident))
                # Deterministic oldest-update eviction. No ever-growing history.
                self.db.execute('DELETE FROM memories WHERE key IN (SELECT key FROM memories ORDER BY task DESC LIMIT -1 OFFSET ?)', (MAX_MEMORIES,))
                result = 'remembered'
            elif kind == 'forget':
                self.db.execute('DELETE FROM memories WHERE key=?', (key,))
                result = 'forgotten'
            else:
                found = self.db.execute('SELECT value FROM memories WHERE key=?', (key,)).fetchone()
                result = found[0] if found else None
            self.db.execute("UPDATE tasks SET state='done',result=? WHERE id=?", (result, ident))
            self.db.execute("DELETE FROM tasks WHERE id IN (SELECT id FROM tasks WHERE state='done' ORDER BY id DESC LIMIT -1 OFFSET ?)", (MAX_RECEIPTS,))
        return result

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
    with Store(args.directory) as store:
        result = serve(store, args.directory / 'STOP', args.seconds, args.max_tasks,
                       args.directory / 'inbox.json')
        print(json.dumps(dict(run=result, store=store.status()), sort_keys=True))


if __name__ == '__main__':
    main()
