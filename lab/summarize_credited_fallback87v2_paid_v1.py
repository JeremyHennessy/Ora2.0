"""Small audit-receipt aggregation; NOT an independent raw-physics interpreter."""
import hashlib,json
from pathlib import Path
LAB=Path('D:/OraLab');path=LAB/'reports/credited-fallback87v2-paid-software-v1.json'
raw=path.read_bytes();report=json.loads(raw)
assert report['verified'] and report['archive_exact'] and report['native_calls']==22
rows=[];by_descriptor={}
for group,batch in report['summary'].items():
    for row in batch['summaries']:
        item=dict(row,group=group)
        if group!='references':by_descriptor.setdefault(tuple(row['descriptor']),{})[group]=row
        rows.append(item)
assert len(rows)==51 and len(by_descriptor)==9
fields=('paid_cpu','acts','served','absence','acquisitions','captured','penalties','deaths','births','writes')
totals={k:sum(row[k] for row in rows) for k in fields}
totals.update(complete60=sum(row['completed']==60 for row in rows),
    heat=sum(row['proof']['heat'] for row in rows),living_energy=sum(row['proof']['living_energy'] for row in rows),
    offered=sum(row['proof']['offered'] for row in rows),admitted=sum(row['proof']['admitted'] for row in rows),
    rejected=sum(row['proof']['rejected'] for row in rows))
common=[]
for descriptor,arms in by_descriptor.items():
    assert len(arms)==5
    keys=set.intersection(*[{(a['packet'],a['cue']) for a in row['late_served']} for row in arms.values()])
    common.append(dict(descriptor=list(descriptor),count=len(keys),packet_cues=sorted(keys)))
value=dict(scope='Aggregation of all51 producer-free literal audit receipts; NOT separate raw interpretation or scientific acceptance',
    source_report_sha256=hashlib.sha256(raw).hexdigest(),archive=report['archive_sha256'],
    original_histories=51,blank_replays=51,software_geneses=102,native_roles=22,
    scientific_worlds=0,scientific_targets=0,stage_credit=False,totals=totals,
    common_active_packet_cues=common,
    all_descriptors=[dict(group=r['group'],descriptor=r['descriptor'],completed=r['completed'],deaths=r['deaths'],cut=r['cut']) for r in rows])
out=LAB/'reports/credited-fallback87v2-paid-closure-summary-v1.json';assert not out.exists()
out.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(totals=totals,common=common),sort_keys=True))
