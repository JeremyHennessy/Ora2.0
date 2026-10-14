"""Prospectively neutral integer-data genomes; never query a task target."""
import hashlib,json
VERSION='DIGITAL-EXPERIENCE75-SOURCE-v1'
OPS=(0,1,2,3,4,5,6,7,8,18,19,20)
PREFIX=[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[18,0,0]]
REFERENCES=('fixed0','fixed1','context_identity','context_inverse','fixed_exploration','latest_response')
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def digest(x):return hashlib.sha256(enc(x)).hexdigest()
def candidate(sample):
    assert type(sample) is int and 0<=sample<16
    code=[row[:] for row in PREFIX];draws=[]
    for slot in range(9):
        words=[]
        for field in range(3):
            certificate=digest(['experience75-source',75,sample,slot,field]);draw=int(certificate[:16],16)
            value=OPS[draw%12] if field==0 else draw%32
            words.append(value);draws.append(dict(slot=slot,field=field,sha256=certificate,low64_decimal=str(draw),value=value))
        code.append(words)
    return dict(sample_id=sample,program=code,program_sha256=digest(code),draws=draws,parent=None,founder='researcher supplied neutral grammar',performance_selection=False,resampling=False)
def pad(tail):
    code=[row[:] for row in PREFIX]+tail
    assert len(code)<=14
    return code+[[18,0,0] for _ in range(14-len(code))]
def references():
    return dict(fixed0=pad([[4,0,0],[6,0,0],[7,0,5]]),fixed1=pad([[4,0,1],[6,0,0],[7,0,5]]),
        context_identity=pad([[0,0,0],[6,0,0],[7,0,5]]),context_inverse=pad([[0,0,0],[4,1,1],[5,0,1],[6,0,0],[7,0,5]]),
        fixed_exploration=pad([[6,0,0],[5,0,1],[7,0,5]]),
        latest_response=pad([[6,0,0],[1,1,0],[8,1,10],[7,0,5],[18,0,0],[4,1,1],[5,0,1],[7,0,5]]))
def manifest():
    return dict(version=VERSION,candidates=[candidate(i) for i in range(16)],references=references(),assembly_words=58,performance_selection=False,targets_queried=0,worlds=0,stage_credit=False)
def programmes():
    return {**{f'candidate{i}':candidate(i)['program'] for i in range(16)},**references()}
