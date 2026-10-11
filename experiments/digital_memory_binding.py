"""Versioned inert-program measurement binding; never an organism controller."""
import json
from experiments.digital_memory_task import Task, digest

VERSION = 'DIGITAL-MEMORY-BINDING-01'
CONSTRUCTOR_FUEL = 128
MATERIAL = 512


def measure(program, orientation):
    assert isinstance(program, list) and 1 <= len(program) <= 32
    assert all(isinstance(i, list) and len(i) == 3 and
               all(type(v) is int and 0 <= v < 32 for v in i) for i in program)
    original = [i[:] for i in program]
    code = [v for i in program for v in i]
    # Code, memory, registers, PC and cue/feedback latches are all paid cells.
    values = code + [0] * 13
    formation = [dict(unit=i, value=v, energy=1, assistance='researcher assembly')
                 for i, v in enumerate(values)]
    task = Task(orientation)
    registers = [0, 0]; pc = 0; cue = 0; feedback = 0; events = []
    while True:
        opcode, a, b = code[3*pc:3*pc+3]
        if opcode == 0: op, arg = 'sense', None
        elif opcode == 2: op, arg = 'read', b % 8
        elif opcode == 3: op, arg = 'write', [a % 8, registers[b % 2]]
        elif opcode == 6: op, arg = 'act', registers[a % 2] % 2
        else: op, arg = 'read', 7  # Explicit paid kernel cycle; result discarded.
        count = len(task.events)
        out = task.step(op, arg)
        if len(task.events) == count:
            stop = dict(op=op, arg=arg); break
        next_pc = (pc + 1) % len(program); changed = None
        if opcode == 0: cue = out; registers[a % 2] = out
        elif opcode == 1: registers[a % 2] = feedback
        elif opcode == 2: registers[a % 2] = out
        elif opcode == 4: registers[a % 2] = b % 16
        elif opcode == 5: registers[a % 2] ^= registers[b % 2]
        elif opcode == 6: feedback = out
        elif opcode == 7: next_pc = b % len(program)
        elif opcode == 8 and registers[a % 2] == 0: next_pc = b % len(program)
        elif opcode == 9:
            unit = b % len(code); code[unit] = registers[a % 2]
            changed = dict(unit=unit, value=code[unit])
        pc = next_pc
        state = dict(program_hash=digest(code), memory_hash=digest(task.memory),
                     registers=registers[:], pc=pc, cue=cue, feedback=feedback)
        events.append(dict(tick=count, decoded=[opcode,a,b], task_tick=count,
                           code_write=changed, state=state))
    final = dict(code=code, memory=task.memory[:], registers=registers[:], pc=pc,
                 cue=cue, feedback=feedback, constructor_remaining=128-len(values),
                 constructor_heat=len(values), assigned=list(range(len(values))),
                 free=list(range(len(values),512)))
    return dict(version=VERSION, program=original, formation=formation,
                events=events, task=task.record(), stop=stop, final=final,
                state_hash=digest(final), assistance='Authored fixture program and paid assembly; no organism')


if __name__ == '__main__':
    import sys
    config = json.load(open(sys.argv[1], encoding='utf-8'))
    print(json.dumps([measure(p['program'], o) | {'label': p['label']}
                      for p in config['programs'] for o in (0,1)], sort_keys=True))
