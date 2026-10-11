"""Read-only diagnosis of frozen failed19 admission; never executes a World."""
import json
from .digital_release07_audit import audit as interpret
from .digital_affine_admission19_audit import endpoint

def panel_admitted(metrics):
    try:
        expected={(s,r) for s in (26590,26591) for r in ('affine3','alternating','fixed0','fixed1')}
        assert len(metrics)==8 and all(type(m['seed']) is int for m in metrics)
        assert {(m['seed'],m['route']) for m in metrics}==expected
        return all(endpoint(m['personal_opportunities'])==(m['route'] in ('affine3','alternating')) for m in metrics)
    except (AssertionError,KeyError,TypeError): return False

def diagnose(record):
    assert record['contract']=='DIGITAL-AFFINE-ADMISSION-19-v1'
    row=record['history'];assert row['seed']==26590 and type(row['seed']) is int and row['route']=='affine3'
    m=interpret(row);ev=row['final']['events'];acts=[e for e in ev if e['decoded'][0]==6]
    cold=[dict(tick=e['tick'],port=e['attempt']['port']) for e in acts if e['tick']<=5]
    assert cold==[dict(tick=2,port=0),dict(tick=4,port=1)]
    bytick={e['tick']:e for e in ev};fresh=[e['tick'] for e in ev if e.get('attempt',{}).get('success') and 16<=e['attempt']['packet']<32]
    energy=12;cap=0
    for e in ev:
        energy-=1
        if e.get('attempt',{}).get('success'):cap+=max(0,energy+20-64)
        energy=e['after']['energy'] if 'after' in e else 0
    f=row['final'];assert bytick[5]['after']['energy']==27 and bytick[60]['after']['energy']==52
    assert fresh==list(range(244,485,16)) and m['successful_food']==32 and m['deaths']==m['births']==0
    assert f['tick']==512 and m['live_energy']==36 and f['heat']==687 and cap==104 and f['constructor_remaining']==57
    assert 36+687+57+20*len(f['food'])==1420 and len(f['free'])==457
    assert [e['tick'] for e in acts if e['tick']>5]==list(range(12,513,8))
    return dict(verified=True,classification='FROZEN_COLD_ACT_TIMING_PREDICTION_MISMATCH',
        actual_cold_attempts=cold,frozen_predicted_ticks=[2,5],mismatch='Second ACT is instruction4; instruction5 writes memory1.',
        full_history_independently_interpreted=True,seed=26590,route='affine3',ticks=512,successful_food=32,
        fresh_packets=16,actions=len(acts),actual_attempts=sum('attempt' in e for e in acts),
        empty_actions=sum('attempt' not in e for e in acts),feedback_reads=0,births=0,deaths=0,
        first_fresh_tick=244,last_fresh_tick=484,formation=55,release=16,cap_waste=104,
        live_energy=36,heat=687,constructor=57,unused_food_energy=640,free_material=457,
        other_phase_predictions_verified=True,planned_histories=8,executed_histories=1,unexecuted_histories=7,
        combined_admission=False,learning=False,evolution=False,repair=False,stage_credit=False,
        new_world_histories=0,whole_work=None,fresh_work=None,damage=None,
        next_dependency='Register a separately prospective correction of cold ACT timing2/4 after this failed admission is closed; preserve this source/protocol/raw/failure and all seven unexecuted planned histories. No learner/other family identity, price, horizon or old gate tuning.')

if __name__=='__main__':
    import sys
    with open(sys.argv[1],encoding='utf-8') as f: print(json.dumps(diagnose(json.load(f)),sort_keys=True))
