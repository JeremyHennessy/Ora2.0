"""Independent subset-graph interpreter; imports no closure producer."""
import itertools
import json
import sys


def reachable(routes, initial):
    seen, pending = {initial}, [initial]
    while pending:
        state = pending.pop()
        for role in range(3):
            if state & (1 << role):
                continue
            required = {bit for bit in range(3) if routes[role] & (1 << bit)}
            present = {bit for bit in range(3) if state & (1 << bit)}
            if required <= present:
                target = state + (1 << role)
                if target not in seen:
                    seen.add(target)
                    pending.append(target)
    return seen


def audit(payload):
    if (set(payload) != {"schema", "cases", "costs", "energy_admission",
                         "natural_worlds"} or
            payload["schema"] != "formation-closure01-v1" or
            payload["costs"] != "UNKNOWN" or
            payload["energy_admission"] is not False or
            type(payload["natural_worlds"]) is not int or
            payload["natural_worlds"] != 0):
        raise ValueError("Structural reachability is not energy admission")
    rows = payload["cases"]
    if len(rows) != 4096:
        raise ValueError("Incomplete catalogue")
    raw_complete = assisted = graph_states = 0
    for index, (routes, initial) in enumerate(itertools.product(
            itertools.product(range(8), repeat=3), range(8))):
        row = rows[index]
        states = reachable(routes, initial)
        union = 0
        for state in states:
            union |= state
        expected = dict(routes=list(routes), initial=initial,
                        closure=union, all_roles=7 in states)
        # Canonical JSON comparison distinguishes booleans from integers.
        if json.dumps(row, sort_keys=True) != json.dumps(expected, sort_keys=True):
            raise ValueError(f"Case{index} differs from independent graph")
        if initial == 0:
            raw_complete += int(7 in states)
        else:
            assisted += int(7 in states)
        graph_states += len(states)
    return dict(cases=len(rows), catalogues=512,
                raw_start_all_roles=raw_complete,
                raw_start_blocked=512-raw_complete,
                supplied_role_complete_cases=assisted,
                subset_graph_states=graph_states,
                energy_admission=False, costs="UNKNOWN", natural_worlds=0)


if __name__ == "__main__":
    try:
        result = audit(json.load(sys.stdin))
    except (ValueError, TypeError, KeyError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
    print(json.dumps(result, sort_keys=True))
