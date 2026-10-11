"""Exhaustive, performance-blind affine source; prepared software inputs only."""
import base64, hashlib, json, zlib

VERSION = 'DIGITAL-AFFINE-SOURCE-18-v1'
BOOT = [[4,1,1],[6,0,0],[5,0,1],[6,0,0],[3,1,0]]

def compile_program(identity):
    assert type(identity) is int and 0 <= identity < 8
    feedback, previous, constant = identity >> 2, (identity >> 1) & 1, identity & 1
    # Every identity costs the same eight instructions per recurring action.
    # Disabled terms are paid NOP/CONST instructions, not free evaluation.
    return [r[:] for r in BOOT] + [
        [2,0,1] if previous else [4,0,0],
        [1,1,0] if feedback else [18,0,0],
        [5,0,1] if feedback else [18,0,0],
        [4,1,constant], [5,0,1], [3,1,0], [6,0,0], [7,0,5]]

def probe(code, feedback, previous):
    assert type(feedback) is int and feedback in (0,1)
    assert type(previous) is int and previous in (0,1)
    memory = [0,previous]+[0]*6; registers = [0,0]; pc = 5; trace = []
    for _ in range(8):
        before = pc; op,a,b = code[pc]; pc = (pc+1) % len(code)
        if op == 1: registers[a%2] = feedback
        elif op == 2: registers[a%2] = memory[b%8]
        elif op == 3: memory[a%8] = registers[b%2]
        elif op == 4: registers[a%2] = b%16
        elif op == 5: registers[a%2] ^= registers[b%2]
        elif op == 7: pc = b%len(code)
        else: assert op in (6,18)
        trace.append(dict(pc=before,instruction=code[before],registers=registers[:],memory=memory[:],next_pc=pc))
        if op == 6: return dict(port=registers[a%2]%2,instructions=len(trace),trace=trace)
    raise AssertionError('No prepared output within the registered fixture horizon')

def manifest():
    bank = []
    for identity in range(8):
        code = compile_program(identity)
        rows = [dict(inputs=[f,p],**probe(code,f,p)) for f in (0,1) for p in (0,1)]
        bank.append(dict(identity=identity,program=code,program_sha256=hashlib.sha256(json.dumps(code,separators=(',',':')).encode()).hexdigest(),probes=rows))
    return dict(contract=VERSION,software_only=True,world_histories=0,bank=bank)

if __name__ == '__main__':
    print(base64.b64encode(zlib.compress(json.dumps(manifest(),sort_keys=True,separators=(',',':')).encode())).decode())
