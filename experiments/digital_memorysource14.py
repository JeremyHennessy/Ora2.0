"""Performance-blind truth-table compiler; counterfactual software fixtures only."""
import base64,hashlib,json,zlib
BOOT=[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[3,1,0]]

def compile_program(table):
    assert type(table) is int and 0<=table<256
    code=[r[:] for r in BOOT]+[[2,1,0],[1,0,0],[3,0,0]]
    leaves=[]
    def emit(op,a=0,b=0):code.append([op,a,b]);return len(code)-1
    def tree(depth,values):
        if depth==3:
            # Last leaf falls into the first shared terminal; all other leaves
            # jump to a shared CONST. No successful table is selected here.
            if len(leaves)<7:
                leaves.append((emit(7),values))
            else:leaves.append((None,values))
            return
        if depth==2:emit(2,0,1)
        branch=emit(8,1 if depth==1 else 0)
        tree(depth+1,values+[1]);code[branch][2]=len(code)
        tree(depth+1,values+[0])
    tree(0,[])
    zero_output=table&1;first=len(code);emit(4,0,zero_output);jump=emit(7)
    second=len(code);emit(4,0,1-zero_output);common=len(code);code[jump][2]=common
    emit(3,1,0);emit(6,0,0);emit(7,0,5)
    for location,bits in leaves:
        current,older,previous=bits;index=4*older+2*current+previous
        output=(table>>index)&1
        if location is not None:code[location][2]=first if output==zero_output else second
        else:assert index==0 and output==zero_output
    assert len(code)==32 and all(type(v) is int and 0<=v<32 for r in code for v in r)
    return code

def probe(code,older,current,previous):
    # Prepared values are software measurement assistance, not organism history.
    memory=[older,previous]+[0]*6;regs=[0,0];pc=5;trace=[]
    for _ in range(32):
        before=pc;op,a,b=code[pc];pc=(pc+1)%len(code)
        if op==1:regs[a%2]=current
        elif op==2:regs[a%2]=memory[b%8]
        elif op==3:memory[a%8]=regs[b%2]
        elif op==4:regs[a%2]=b%16
        elif op==7:pc=b%len(code)
        elif op==8:
            if regs[a%2]==0:pc=b%len(code)
        elif op!=6:raise AssertionError('Unspecified fixture opcode')
        trace.append(dict(pc=before,instruction=code[before],registers=regs[:],memory=memory[:],next_pc=pc))
        if op==6:return dict(port=regs[a%2]%2,instructions=len(trace),trace=trace)
    raise AssertionError('No output reached within fixed fixture horizon')

def manifest():
    bank=[]
    for table in range(256):
        code=compile_program(table);rows=[]
        for older in (0,1):
            for current in (0,1):
                for previous in (0,1):
                    rows.append(dict(inputs=[older,current,previous],**probe(code,older,current,previous)))
        bank.append(dict(table=table,program=code,program_sha256=hashlib.sha256(json.dumps(code,separators=(',',':')).encode()).hexdigest(),probes=rows))
    return dict(contract='DIGITAL-MEMORYSOURCE-14-v1',bank=bank,software_only=True,world_histories=0)

if __name__=='__main__':
    print(base64.b64encode(zlib.compress(json.dumps(manifest(),sort_keys=True,separators=(',',':')).encode())).decode())
