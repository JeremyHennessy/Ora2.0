"""Independent response/billing checks; not full VM replay qualification."""
def verify(code, mask, order, rows, result):
    cost = 3*len(code) + code[0][1] + 8
    completed = 0
    packets = set()
    for tick, row in enumerate(rows, 1):
        assert row["tick"] == tick and row["request"] == completed
        assert row["cue"] == order[completed]
        op = code[row["pc"]][0]
        response = row["response"]
        penalty = 0
        if response is not None:
            assert op == 6 and response["request"] == completed
            assert response["cue"] == order[completed]
            assert type(response["action"]) is int and response["action"] in (0, 1)
            assert response["packet"] not in packets
            packets.add(response["packet"])
            cue = order[completed]
            target = ((mask // (2**(cue % 4))) % 2 + cue//4) % 2
            assert type(response["correct"]) is bool
            assert response["correct"] == (response["action"] == target)
            penalty = 0 if response["correct"] else 4
            completed += 1
        # A partial terminal penalty may be lower when energy is exhausted.
        # Such rows require full independent energy replay, never auto-pass.
        assert row["charged"] == 1 + penalty + (16 if tick == 64 else 0)
        cost += row["charged"]
        assert row["cost"] == cost <= 328
    assert result["cost"] == cost and result["completed"] == completed
    assert result["ticks"] == len(rows) and len(result["planned"]) == 8
    responses = [row["response"] for row in rows if row["response"] is not None]
    for i, planned in enumerate(result["planned"]):
        assert planned["request"] == i and planned["cue"] == order[i]
        if i < completed:
            assert planned == responses[i]
        else:
            assert planned["delivered"] is False and planned["correct"] is None
    assert result["transfer_correct"] == sum(x["correct"] for x in responses if x["request"] >= 4)
    if completed == 8:
        assert rows[-1]["response"] is not None and result["stop"] == "responses"
    return True
