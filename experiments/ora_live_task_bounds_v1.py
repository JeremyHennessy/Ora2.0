"""Read-only task bounds from the existing Store contract, no runtime changes."""
MAX_DONE=128
MAX_UNFINISHED=128


def task_bounds(db):
    counts=dict(db.execute('SELECT state,count(*) FROM tasks GROUP BY state').fetchall())
    if set(counts)-{'pending','running','done'}:
        raise ValueError('Unknown task state')
    done=counts.get('done',0)
    pending=counts.get('pending',0)
    running=counts.get('running',0)
    if not all(type(n) is int and n>=0 for n in counts.values()):
        raise ValueError('Invalid task count')
    if done>MAX_DONE or pending+running>MAX_UNFINISHED:
        raise ValueError('Existing completed/unfinished task limit exceeded')
    return dict(done=done,pending=pending,running=running,total=done+pending+running,
                completed_limit=MAX_DONE,unfinished_limit=MAX_UNFINISHED)
