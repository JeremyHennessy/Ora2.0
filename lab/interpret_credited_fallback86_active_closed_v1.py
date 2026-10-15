"""Independent stdlib closed-data SOFTWARE census; no producer/literal imports."""
import hashlib
import json
from pathlib import Path
ROOT=Path('D:/OraLab')
path=ROOT/'reports/credited-fallback86-active-software-v1.json'
report=json.loads(path.read_bytes())
assert report['verified'] and report['archive_exact'] and report['native_calls']==52
enc=lambda value:json.dumps(value,sort_keys=True,separators=(',',':')).encode()
ARMS=('model_erased','model_misbound','fallback_misbound','history_disabled')
CASES=[[q,r] for q in (2,4,8) for r in ('fallback0','model','fallback1')]
rows=[];inputs=[];opportunities={};warm_hashes={}
for seed in range(2100080,2100084):
    for arm in ARMS:
        spec=report['completed_roles'][f'original:{seed}:{arm}:generate']
        raw=Path(spec['path']).read_bytes()
        assert len(raw)==spec['extent'] and hashlib.sha256(raw).hexdigest()==spec['sha256']
        body=json.loads(raw);assert raw==enc(body)
        assert body['seed']==seed and body['arm']==arm and body['error'] is None
        assert [r['descriptor'] for r in body['records']]==CASES
        inputs.append(spec)
        for row in body['records']:
            state=row['state'];events=state['events'];ledger=row['ledger'];descriptor=row['descriptor']
            summary=next(x for x in report['summary'][f'{seed}:{arm}']['summaries'] if x['descriptor']==descriptor)
            assert len(events)==len(ledger)==summary['paid_cpu']
            actions=[e for e in events if e['decoded'][0]==6]
            actual=[e for e in actions if 'attempt' in e]
            captured=sum(e.get('captured',0) for e in events)
            penalty=sum(e.get('penalty',0) for e in events)
            success=sum(e['attempt']['success'] for e in actual)
            capheat=20*success-captured;failedheat=20*(len(actual)-success)
            formation=3*len(row['programme'])+descriptor[0]+8
            fees=sum(e.get('release_energy',0) for e in events)
            deathheat=sum(e.get('death',{}).get('dissipated',0) for e in events)
            living=sum(e['energy'] for e in state['entities'].values())
            assert state['births']==state['writes']==0
            assert state['heat']==formation+len(events)+penalty+capheat+failedheat+fees+deathheat
            assert living==112+captured-len(events)-penalty-deathheat
            assert state['heat']+living+state['constructor_remaining']+20*len(state['food'])==1536+20*state['admitted']
            assert state['offered']==state['admitted']+state['rejected']
            physical={k:v for k,v in state.items() if k!='events'}
            assert hashlib.sha256(enc(physical)).hexdigest()==summary['proof']['final_state_sha256']
            completed=sum(item['completion'] is not None for item in ledger)
            assert completed==summary['completed']
            assert len(actions)-completed in (0,1)
            active=[(e,item) for e,item in zip(events,ledger) if item['completed_before']>=48]
            late=[e['attempt'] for e,item in active if 'attempt' in e]
            assert late==summary['late_served']
            key=(seed,*descriptor)
            opportunities.setdefault(key,{})[arm]={(a['packet'],a['cue']) for a in late}
            warm=[e for e,item in zip(events,ledger) if item['completed_before']<48]
            warm_hashes.setdefault(key,set()).add(hashlib.sha256(enc(warm)).hexdigest())
            rows.append(dict(seed=seed,arm=arm,descriptor=descriptor,instructions=len(events),
                decisions=len(actions),served=len(actual),absence=len(actions)-len(actual),
                acquisitions=success,captured=captured,penalty=penalty,cap_heat=capheat,
                failed_packet_heat=failedheat,formation=formation,world_fees=fees,heat=state['heat'],
                living_energy=living,constructor_remaining=state['constructor_remaining'],food=len(state['food']),
                offered=state['offered'],admitted=state['admitted'],rejected=state['rejected'],
                births=0,mutations=0,deaths=state['deaths'],completed=completed,
                complete60=int(completed==60),never_active=summary['never_active'],cut=summary['cut'],
                late_served=len(late),late_correct=sum(a['success'] for a in late),
                operating_surplus=captured-len(events)-penalty,
                model_store_instructions=sum(e['decoded'][0]==20 for e in events),
                active_model_reads=sum(item['read'] is not None for e,item in active),
                active_entry_changes=sum(item['entry'] is not None and item['entry']['actual_entry']!=item['entry']['projected_entry'] for e,item in active)))
assert len(rows)==144 and len(opportunities)==36
assert all(len(v)==1 for v in warm_hashes.values())
common=[dict(seed=key[0],descriptor=list(key[1:]),count=len(set.intersection(*arms.values())),
             packet_cues=sorted(set.intersection(*arms.values()))) for key,arms in opportunities.items()]
numeric=[k for k,v in rows[0].items() if type(v) is int and k!='seed']
summary={str(q):dict(cases=48,complete60=sum(r['complete60'] for r in rows if r['descriptor'][0]==q),
    deaths=sum(r['deaths'] for r in rows if r['descriptor'][0]==q),
    never_active=sum(r['never_active'] for r in rows if r['descriptor'][0]==q),
    minimum_earned_cut_energy=min(r['cut']['earned_energy'] for r in rows if r['descriptor'][0]==q and r['cut']),
    common_active=sum(c['count'] for c in common if c['descriptor'][0]==q)) for q in (2,4,8)}
value=dict(scope='All144 CLOSED original SOFTWARE histories; no intact60/fixed/unseen scientific comparison',
    worlds=0,targets=0,producer_imported=False,referee_imported=False,stage_credit=False,
    full_acceptance_or_learning_claim=False,closed_archive=report['archive_sha256'],
    inputs=inputs,rows=rows,totals={k:sum(r[k] for r in rows) for k in numeric},by_capacity=summary,
    all36_independently_earned_warm_prefixes_physically_equal_across_four_arms=True,
    common_active_opportunities=common)
out=json.dumps(value,indent=2).encode()+b'\n';assert len(out)<256*1024
(ROOT/'reports/credited-fallback86-active-closed-census-v1.json').write_bytes(out)
print(json.dumps(dict(totals=value['totals'],by_capacity=summary),sort_keys=True))
