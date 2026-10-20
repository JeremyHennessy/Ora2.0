"""Prospective software qualification only; no primary experiment entry point.

Reuses the sealed resource engine. Does not alter Context90 laws or samples.
Requests, observations and controls are versioned apparatus, not learned policy.
"""
import types
from experiments import digital_context90_crossed_engine_v1 as engine

VERSION = "BUDGETED-FIRST-RESPONSE-SOFTWARE-v1"
SOFTWARE_ONLY = "NEW-INTERFACE-FIXTURES-ONLY"
MODES = ("intact", "memory_disabled", "history_disrupted")
# No clock/energy sensor, copying, division, code writes or hidden task access.
OPS = frozenset((0, 1, 2, 3, 4, 5, 6, 7, 8, 19, 20, 24, 25))

def validate(code, mask, order, mode, budget):
    engine.validate(code)
    if any(t[0] not in OPS for t in code):
        raise ValueError("unregistered actor channel")
    if type(mask) is not int or not 0 <= mask < 16:
        raise ValueError("four-bit hidden map")
    if (type(order) is not tuple or len(order) != 8 or
        any(type(x) is not int for x in order) or
        sorted(order[:4]) != list(range(4)) or
        sorted(order[4:]) != list(range(4, 8))):
        raise ValueError("one request per cue, acquisition before transfer")
    if mode not in MODES or type(budget) is not int or not 0 <= budget <= 328:
        raise ValueError("control or ceiling")

class _Labels:
    def __init__(self, task):
        self.task = task
    def __getitem__(self, index):
        t = self.task
        if index != 0 or t.completed >= 8:
            raise ValueError("target outside current ACT")
        cue = t.order[t.completed]
        target = ((t.mask >> (cue % 4)) & 1) ^ (cue // 4)
        return 255 if target else 0

class Fixture:
    """Bounded authored software fixture. Never accepts a primary-mode token."""
    def __init__(self, code, mask=0, order=(0,1,2,3,4,5,6,7),
                 mode="intact", budget=328, admission=None):
        if admission != SOFTWARE_ONLY:
            raise ValueError("software-only admission required; primary unavailable")
        validate(code, mask, order, mode, budget)
        self.mask, self.order, self.mode, self.budget = mask, order, mode, budget
        self.completed = 0
        self.cost = 3 * len(code) + code[0][1] + 8
        if self.cost > budget:
            raise ValueError("formation exceeds ceiling")
        self.world = engine.World(2100790, code[0][1], "no_variation", 1, 0,
                                  code, "CONTEXT90-CROSSED-SOFTWARE-v1")
        namespace = dict(engine.World.step.__globals__)
        namespace["MASKS"] = _Labels(self)
        self._transition = types.FunctionType(engine.World.step.__code__, namespace)
        self.rows = []

    def snapshot(self):
        payload = dict(version=VERSION, mask=self.mask, order=list(self.order),
                       mode=self.mode, budget=self.budget, completed=self.completed,
                       cost=self.cost, rows=engine.clone(self.rows),
                       budget_refused=getattr(self, "_budget_refused", False),
                       world=self.world.snapshot())
        return dict(payload=payload, sha256=engine.h(payload))

    @classmethod
    def restore(cls, sealed, admission=None):
        if (type(sealed) is not dict or set(sealed) != {"payload", "sha256"} or
            engine.h(sealed["payload"]) != sealed["sha256"]):
            raise ValueError("snapshot integrity")
        p = engine.clone(sealed["payload"])
        if p["version"] != VERSION:
            raise ValueError("snapshot version")
        w = p["world"]
        body = w["entities"].get("0")
        if body is None:
            raise ValueError("only live software checkpoint restore is qualified")
        code = [[v[0] for v in body["code"][i:i+3]]
                for i in range(0, len(body["code"]), 3)]
        t = cls(code, p["mask"], tuple(p["order"]), p["mode"], p["budget"], admission)
        w["entities"] = {int(k):v for k,v in w["entities"].items()}
        w["food"] = {int(k):v for k,v in w["food"].items()}
        w["leases"] = {int(k):v for k,v in w["leases"].items()}
        t.world.__dict__.clear()
        t.world.__dict__.update(w)
        t.completed, t.cost, t.rows = p["completed"], p["cost"], p["rows"]
        t._budget_refused = p["budget_refused"]
        t.world.check()
        if not 0 <= t.completed <= 8 or not 0 <= t.cost <= t.budget:
            raise ValueError("task checkpoint bounds")
        if len(t.rows) != t.world.tick:
            raise ValueError("checkpoint tick mismatch")
        return t

    def reason(self):
        if self.completed == 8:
            return "responses"
        if not self.world.entities:
            return "death"
        if self.world.tick >= 2048:
            return "horizon"
        if self.cost >= self.budget:
            return "budget"
        return None

    def step(self):
        if self.reason() is not None:
            return False
        w = self.world
        e = w.entities[0]
        pc = e["pc"]
        op, a, b = [x[0] for x in e["code"][3*pc:3*pc+3]]
        # Exact known mandatory cost: this subset has only unit-price ops.
        # Wrong ACT penalty is possible even though label is private: reserve4
        # for every ACT, never use hidden target to decide whether to execute.
        required = 1 + (4 if op == 6 else 0) + (16 if w.tick+1 == 64 else 0)
        if self.cost + required > self.budget:
            self._budget_refused = True
            return False
        request, cue = self.completed, self.order[self.completed]
        before = engine.clone(e)
        packet = w.packet(e)
        if not self._transition(w):
            raise AssertionError("ordinary transition refused unexpectedly")
        event = w.events[-1]
        charged = 1 + event.get("penalty", 0) + event.get("release_energy", 0)
        self.cost += charged
        after = w.entities.get(0)
        intervention = None
        if op == 0 and after is not None:
            # Public request token is acquired through the paid SENSE only.
            after["cue"] = cue
            after["registers"][a % 2] = cue
            event["sense"]["request_cue"] = cue
        if self.mode == "history_disrupted" and op == 1 and after is not None:
            # Explicit masked-feedback apparatus. Physical ACT consequences are
            # unchanged. Transcript is constant0, independent of hidden maps.
            real = event["read_feedback"]
            after["registers"][a % 2] = 0
            intervention = dict(channel="OBS", physical=real, delivered=0)
        if self.mode == "memory_disabled" and after is not None:
            if op in (2, 19):
                after["registers"][a % 2] = 0
            if op in (3, 20):
                after["memory"] = before["memory"]
            if op in (2, 3, 19, 20):
                intervention = dict(channel="memory", persistence=False)
        response = None
        if op == 6 and "attempt" in event:
            attempt = event["attempt"]
            assert attempt["packet"] == packet
            response = dict(request=request, cue=cue, packet=packet,
                            action=attempt["port"], correct=bool(attempt["success"]),
                            phase="acquisition" if request < 4 else "transfer")
            self.completed += 1
        if after is not None:
            event["after"] = engine.clone(after)
        event["state_hash"] = engine.h(w.snapshot(False))
        self.rows.append(dict(tick=w.tick, pc=pc, request=request, cue=cue,
                              response=response, charged=charged, cost=self.cost,
                              intervention=intervention))
        w.check()
        return True

    def run_fixture(self):
        while self.step():
            pass
        reason = "budget" if getattr(self, "_budget_refused", False) else self.reason()
        responses = [x["response"] for x in self.rows if x["response"] is not None]
        planned = [next((x for x in responses if x["request"] == i),
                        dict(request=i, cue=self.order[i], delivered=False,
                             correct=None, reason=reason)) for i in range(8)]
        return dict(version=VERSION, software_only=True, completed=self.completed,
                    cost=self.cost, unused=self.budget-self.cost, stop=reason,
                    planned=planned, ticks=self.world.tick,
                    transfer_correct=sum(x.get("correct") is True for x in planned[4:]))
