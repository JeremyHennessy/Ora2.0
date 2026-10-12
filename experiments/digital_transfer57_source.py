"""Paid-source inventory and identity-only enrollment; no producer or fitness input."""
from experiments.digital_informative_exposure23_interpret import h

DOMAIN='DIGITAL-TRANSFER-57-neutral-v1'


def identity(record):
    assert type(record['seed']) is int and record['seed'] in range(55000,55032)
    assert record['mode']=='mutating'
    assert type(record['child']) is int and record['child']>0
    return record['seed'],record['child']


def enroll(records,count=8):
    assert type(count) is int and count==8 and len(records)>=count
    seen=set();ranked=[]
    for record in records:
        key=identity(record);assert key not in seen;seen.add(key)
        score=h([DOMAIN,*key]);ranked.append((score,key,record))
    return [dict(record,neutral_rank=index+1,neutral_score=score)
            for index,(score,key,record) in enumerate(sorted(ranked,key=lambda v:(v[0],v[1]))[:count])]


def sources(row,proof):
    """Only called after full generic VM/Mobile55 audit; synthetic tests are joins only."""
    assert row['mode']=='mutating' and type(row['seed']) is int and row['seed'] in range(55000,55032)
    certificates={};records=[];parents={0:0}
    for event in row['final']['events']:
        for write in event.get('writes',[]):
            assert write['write_id'] not in certificates
            certificates[write['write_id']]=(event['actor'],write)
        if 'birth' not in event:continue
        birth=event['birth'];child=birth['child'];parent=event['actor']
        assert child['id'] not in parents and parent in parents and child['parent']==parent
        assert child['generation']==parents[parent]+1;parents[child['id']]=child['generation']
        assert type(birth['startup_energy']) is int and birth['startup_energy']==child['energy']==12
        assert len(child['code'])==len(birth['write_ids'])==27 and len(set(birth['write_ids']))==27
        joins=[]
        for index,(identifier,cell) in enumerate(zip(birth['write_ids'],child['code'])):
            assert identifier in certificates;owner,write=certificates[identifier]
            assert owner==parent and write['tick']<event['tick'] and write['index']==index
            assert type(cell[0]) is int and 0<=cell[0]<32 and type(cell[1]) is int and cell[1]>=0
            assert [write['value'],write['unit']]==cell
            joins.append(dict(write,owner=owner))
        values=[v[0] for v in child['code']]
        record=dict(seed=row['seed'],mode=row['mode'],child=child['id'],parent=parent,
                    generation=child['generation'],birth_tick=event['tick'],birth_position=child['pos'],
                    birth_body_hash=h(child),program_hash=h(values),program=[values[i:i+3] for i in range(0,27,3)],
                    paid_words=joins,source_row_hash=row['hash'],
                    assistance='Natural paid source birth; future assay installation is researcher assistance, charged43 formation, position0 and empty startup state')
        identity(record);records.append(record)
    assert len(records)==proof['summary']['births']
    return records
