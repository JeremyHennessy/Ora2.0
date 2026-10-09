"""Separate LIGATE-01 interpreter. No producer import; replay registered attempts."""
import argparse, hashlib, json, math
from pathlib import Path

def pack(x): return json.dumps(x, sort_keys=True, separators=(',', ':')).encode()
def kind(ids): return ''.join('0' if i < 16 else '1' for i in ids)

def initial(seed, arm):
    return {'seed':seed,'arm':arm,'rng':seed,'step':0,'photons':256,'heat':0,'removed':0,
            'objects':[{'id':i,'atoms':[i],'alive':True,'active':False,'charge':None,
                        'parents':[],'born':0,'route':'genesis'} for i in range(32)],
            'productive':[],'opportunity':False,'observation':None,
            'stats':dict(activation=0,basal=0,catalytic=0,ligation=0,cleavage=0,cross=0,reused=0,post_withdrawal=0),
            'depleted_at':None}

def interpret(w, t, numbers):
    if t == 1024:
        species = sorted(set(kind(o['atoms']) for o in w['objects'] if o['alive'] and o['id'] in w['productive']))
        w['observation'] = {'live_productive_sequences':species,'cross':w['stats']['cross']}
        w['opportunity'] = len(species) > 1 and w['stats']['cross'] > 3
    if t == 1536:
        w['removed'] = w['photons']; w['photons'] = 0
    ids = [i for i, x in enumerate(w['objects']) if x['alive']]
    first, second, catalyst = [ids[numbers[i] % len(ids)] for i in (1,2,3)]
    x = w['objects'][first]; y = w['objects'][second]; z = w['objects'][catalyst]
    chance = numbers[4] & 255; reaction = numbers[0] % 3; action = None
    if reaction == 0:
        sequence = kind(z['atoms'])
        selectivity = hashlib.sha256(('LIGATE-01|'+sequence).encode('ascii')).digest()[0] & 1
        available = first != catalyst and len(sequence) > 1
        cat = available and selectivity == (0 if x['atoms'][0] < 16 else 1)
        if w['arm'] == 'shuffled': cat = available and selectivity != (0 if x['atoms'][0] < 16 else 1)
        if w['arm'] == 'inert': cat = False
        limit = 64 if cat or w['arm'] == 'constitutive' else 8
        if len(x['atoms']) == 1 and not x['active'] and w['photons'] > 2 and chance < limit:
            credited = catalyst if cat and chance > 7 and w['arm'] != 'constitutive' else None
            x.update(active=True,charge={'donor':credited,'step':t})
            w['photons'] -= 3; w['heat'] += 1; w['stats']['activation'] += 1
            w['stats']['basal' if credited is None else 'catalytic'] += 1
            action = ['activate',first,credited]
    elif reaction == 1:
        if first != second and x['active'] != y['active'] and len(x['atoms'])+len(y['atoms']) < 5 and chance < 128:
            charged, recipient = (x,y) if x['active'] else (y,x)
            chain = (charged['atoms']+recipient['atoms']) if not numbers[5]&1 else (recipient['atoms']+charged['atoms'])
            identity = len(w['objects']); provenance = dict(charged['charge'])
            w['objects'].append({'id':identity,'atoms':chain,'alive':True,'active':False,'charge':None,
                'parents':[charged['id'],recipient['id']],'born':t,'route':'ligation','funding':provenance})
            x['alive'] = False; y['alive'] = False; w['heat'] += 1; w['stats']['ligation'] += 1
            w['stats']['post_withdrawal'] += int(t >= 1536)
            w['stats']['reused'] += int(charged['route']=='cleavage' or recipient['route']=='cleavage')
            source = provenance['donor']
            if source is not None and kind(w['objects'][source]['atoms']) != kind(chain):
                w['stats']['cross'] += 1
                w['productive'] = sorted(set(w['productive']) | {source})
            action = ['ligate',identity,charged['id'],recipient['id'],source]
    else:
        if len(x['atoms']) > 1 and not x['active'] and chance < 8:
            split = numbers[5] % (len(x['atoms'])-1)+1; new_ids = []
            for fragment in (x['atoms'][:split],x['atoms'][split:]):
                identity = len(w['objects']); new_ids.append(identity)
                w['objects'].append({'id':identity,'atoms':fragment,'alive':True,'active':False,'charge':None,
                                      'parents':[first],'born':t,'route':'cleavage'})
            x['alive'] = False; w['heat'] += 1; w['stats']['cleavage'] += 1
            action = ['cleave',first,*new_ids,split]
    if w['depleted_at'] is None and w['photons'] < 3: w['depleted_at'] = t
    w['step'] = t
    living = [o for o in w['objects'] if o['alive']]
    if sorted(a for o in living for a in o['atoms']) != list(range(32)): raise ValueError('Matter')
    energy = w['heat']+w['removed']+w['photons']+sum(len(o['atoms'])-1+2*o['active'] for o in living)
    if energy != 256 or min(w['heat'],w['removed'],w['photons']) < 0: raise ValueError('Energy')
    return action

def audit_file(path, revision):
    with path.open() as stream:
        header = json.loads(next(stream)); seed,arm = header['seed'],header['arm']
        if header != dict(schema='ligate01',revision=revision,seed=seed,arm=arm): raise ValueError('Header')
        if seed not in range(75000,75032) or arm not in ('candidate','inert','shuffled','constitutive'): raise ValueError('Sample')
        w = initial(seed,arm); seen = 0
        for t,line in enumerate(stream,1):
            row = json.loads(line); numbers=[]
            for _ in range(6):
                state=w['rng']; state=(state^(state<<13))&0xffffffff
                state^=state>>17; state=(state^(state<<5))&0xffffffff
                w['rng']=state; numbers.append(state)
            if row['step'] != t or row['draws'] != numbers: raise ValueError('Draw continuity')
            action=interpret(w,t,numbers)
            if row['event'] != action or row['state'] != hashlib.sha256(pack(w)).hexdigest(): raise ValueError('Transition')
            seen=t
        if seen != 2048: raise ValueError('Horizon')
    final=path.with_name(path.stem+'-final.json')
    if pack(json.loads(final.read_bytes())) != pack(w): raise ValueError('Final state/provenance')
    return dict(seed=seed,arm=arm,opportunity=w['opportunity'],observation=w['observation'],stats=w['stats'],
                depleted_at=w['depleted_at'],photons_removed=w['removed'],active_final=sum(o['alive'] and o['active'] for o in w['objects']),
                lengths=[len(o['atoms']) for o in w['objects'] if o['alive']])

def decision(records):
    if len(records) != 128 or len({(r['seed'],r['arm']) for r in records}) != 128: raise ValueError('Complete panel')
    by={(r['seed'],r['arm']):r for r in records}; tests=[]
    for null in ('inert','shuffled'):
        wins=losses=0
        for seed in range(75000,75032):
            a,b=by[seed,'candidate']['opportunity'],by[seed,null]['opportunity']
            wins+=a and not b; losses+=b and not a
        n=wins+losses; p=sum(math.comb(n,k) for k in range(wins,n+1))/2**n
        tests.append(dict(null=null,wins=wins,losses=losses,p=p))
    ordered=sorted(tests,key=lambda x:x['p']); passed=ordered[0]['p']<=.025 and ordered[1]['p']<=.05
    counts={a:sum(r['opportunity'] for r in records if r['arm']==a) for a in ('candidate','inert','shuffled','constitutive')}
    return dict(worlds=128,transitions=262144,opportunity_counts=counts,paired=tests,
                gate_pass=counts['candidate']>=16 and passed,maintenance_demonstrated=False)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--revision',required=True)
    args=p.parse_args()
    try:
        records=[audit_file(x,args.revision) for x in sorted(Path(args.input).glob('*.jsonl'))]
        print(json.dumps(dict(verified=True,records=records,decision=decision(records)),sort_keys=True))
    except (ValueError,KeyError,IndexError,StopIteration,json.JSONDecodeError) as e:
        print(json.dumps(dict(verified=False,error=str(e)))); raise SystemExit(2)

if __name__=='__main__': main()
