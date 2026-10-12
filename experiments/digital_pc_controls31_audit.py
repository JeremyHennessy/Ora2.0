"""Independent literal transition and epoch-shadow reconstruction; no producer import."""
import hashlib,json

def copy(x):return json.loads(json.dumps(x))
def move(program,state,feedback,zero):
    result=copy(state);op,a,b=program[state['pc']];result['pc']=(state['pc']+1)%len(program)
    if op==1:result['r'][a%2]=0 if zero else state['feedback']
    if op==2:result['r'][a%2]=state['m'][b%8]
    if op==3:result['m'][a%8]=state['r'][b%2]
    if op==4:result['r'][a%2]=b%16
    if op==5:result['r'][a%2]=state['r'][a%2]^state['r'][b%2]
    if op==6:result['feedback']=feedback
    if op==7 or op==8 and state['r'][a%2]==0:result['pc']=b%len(program)
    return result

def audit(data):
    programs={'branch':[[1,0,0],[8,0,4],[4,1,7],[7,0,5],[4,1,2],[6,1,0],[7,0,0]],'memory':[[1,0,0],[3,2,0],[4,0,0],[6,0,0],[7,0,0]],'no_feedback':[[4,0,0],[8,0,3],[4,1,7],[6,0,0],[4,0,1],[8,0,0],[7,0,0]]}
    assert data['contract']=='DIGITAL-PC-CONTROLS-31-v1' and len(data['fixtures'])==data['prepared_fixture_count']==18
    index=0;pc_rewrites=memory_rewrites=substitutions=0;no_feedback={}
    for role in programs:
        for mode in ('intact','retained_disabled','own_disrupted'):
            for fb in (0,1):
                row=data['fixtures'][index];index+=1;program=programs[role]
                assert row['role']==role and row['mode']==mode and row['seed']==31000 and row['program']==program
                state=dict(r=[0,0],m=[0]*8,pc=0,feedback=fb);shadow=copy(state);assert row['genesis']==state
                reads=epoch=0;assert len(row['events'])==32
                for tick,observed in enumerate(row['events'],1):
                    op,a,b=program[state['pc']];assert observed['before']==state and observed['decoded']==[op,a,b] and observed['tick']==tick and observed['prepared_feedback']==tick%2
                    native=move(program,state,tick%2,False);shadow=move(program,shadow,0,True);result=copy(native);sub=None;rewrites=[]
                    if op==1:
                        reads+=1
                        if mode=='own_disrupted':
                            text=json.dumps([31000//2,'own-disrupt31',reads],sort_keys=True,separators=(',',':')).encode();value=int(hashlib.sha256(text).hexdigest()[:8],16)%2
                            sub=dict(read_index=reads,register=a%2,original=result['r'][a%2],value=value);result['r'][a%2]=value;substitutions+=1
                    saved=copy(shadow) if op==6 else None
                    if op==6:
                        if mode=='retained_disabled':
                            for key in ('r','m','pc'):
                                if result[key]!=shadow[key]:rewrites.append(dict(channel=key,original=copy(result[key]),value=copy(shadow[key])))
                                result[key]=copy(shadow[key])
                        epoch+=1;shadow=copy(result)
                    annotation=dict(mode=mode,epoch=epoch,read_count=reads,substitution=sub,rewrites=rewrites,shadow_at_action=saved,shadow=copy(shadow))
                    assert observed['native_after']==native and observed['after']==result and observed['control']==annotation
                    assert result['feedback']==native['feedback'];pc_rewrites+=sum(x['channel']=='pc' for x in rewrites);memory_rewrites+=sum(x['channel']=='m' for x in rewrites);state=result
                assert row['final']==state and row['world'] is row['resource_accounting'] is row['learning'] is False
                if role=='no_feedback':no_feedback[(mode,fb)]=[x['after'] for x in row['events']]
    for fb in (0,1):assert no_feedback[('intact',fb)]==no_feedback[('retained_disabled',fb)]==no_feedback[('own_disrupted',fb)]
    assert pc_rewrites>0 and memory_rewrites>0 and substitutions>0
    assert data['world_histories']==data['actions']==data['births']==data['deaths']==data['candidate_genomes_executed']==0 and data['learning'] is data['stage_credit'] is False
    return dict(verified=True,prepared_fixture_count=18,prepared_instruction_transitions=576,pc_rewrites=pc_rewrites,memory_rewrites=memory_rewrites,unrelated_substitutions=substitutions,no_feedback_physical_invariance=True,latest_latch_preserved=True,world_histories=0,candidate_viability=False,learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f:result=audit(json.load(f))
    print(json.dumps(result,sort_keys=True))
