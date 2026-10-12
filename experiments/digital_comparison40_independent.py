"""Literal pairwise referee; no producer/scorer/World import."""
import json
IDS=(19, 243, 597, 1092, 1295, 1456, 1749, 1849, 2271, 2716, 3225, 3260, 3421, 3825, 4004, 4396, 5033, 5034, 5106, 5510, 5603, 5829, 6208, 6367, 6934, 7101, 7429, 7479, 7962, 7967, 8610, 8820, 9142, 9460, 9714, 9901, 10350, 10424, 10966, 11070, 11499, 11631, 11891, 12194, 12421, 12770, 13347, 13405, 13836, 13988, 14420, 14557, 15036, 15106, 15186, 15678, 15973, 16237, 16379, 16412, 16905, 17328, 17875, 17905, 18147, 18282, 18547, 18853, 19332, 19336, 20030, 20060, 20394, 20648, 21113, 21217, 21578, 21635, 22183, 22307, 22679, 22724, 22980, 23218, 23570, 24009, 24105, 24427, 25144, 25198, 25204, 25534, 25996, 26082, 26516, 26870, 26911, 27006, 27459, 27909, 28129, 28191, 28968, 29119, 29454, 29636, 29842, 29904, 30354, 30357, 30862, 31155)
SEEDS=tuple(range(38200,38208))
MODES=('intact','retained_disabled','own_disrupted')
REFS=tuple('affine'+str(i) for i in range(8))+('alternating','fixed0','fixed1')

def validate(m):
    """Refuse inconsistent/bool-valued bills; absence is never zero-cost success."""
    for k in ('formation', 'food', 'fresh', 'own_origins', 'terminal_tick'):
        if type(m[k]) is not int:
            raise ValueError(k)
    if not (19 <= m['formation'] <= 112 and (m['formation']-16) % 3 == 0
            and 0 <= m['fresh'] <= 16 and m['fresh'] <= m['food'] <= 32
            and 0 <= m['own_origins'] <= 512 and 1 <= m['terminal_tick'] <= 512):
        raise ValueError('range')
    for k in ('completed', 'survived64', 'delivered_own', 'both_own_outcomes'):
        if type(m[k]) is not bool:
            raise ValueError(k)
    if m['completed']:
        t = m['completion_tick']
        if (type(t) is not int or not 64 <= t <= m['terminal_tick']
                or type(m['paid_work']) is not int
                or m['paid_work'] != m['formation'] + t
                or m['food'] != 32 or m['fresh'] != 16 or not m['survived64']):
            raise ValueError('complete bill')
    elif m['completion_tick'] is not None or m['paid_work'] is not None or m['food'] == 32:
        raise ValueError('incomplete bill')
    if not m['delivered_own'] and m['both_own_outcomes']:
        # Native availability in disrupted controls is a separate input channel.
        raise ValueError('native availability presented as delivered own history')


def diagnose(bank):
    rows=bank['rows'];mapped={}
    for r in rows:
        key=(r['role'],r['seed'],r['control'])
        if type(r['seed']) is not int or key in mapped:raise ValueError('identity')
        validate(r['metric']);mapped[key]=r['metric']
    wanted=set()
    for s in SEEDS:
        for c in MODES:
            for role in ['candidate'+str(i) for i in IDS]+list(REFS):wanted.add((role,s,c))
    if set(mapped)!=wanted:raise ValueError('whole census')
    cells=[]
    for i in IDS:
        for s in SEEDS:
            a=[mapped['candidate'+str(i),s,c] for c in MODES];x=a[0]
            if a[2]['delivered_own']:raise ValueError('unrelated labelled own')
            if any(m['formation']!=x['formation'] for m in a):raise ValueError('formation')
            refs=[mapped[r,s,'intact'] for r in REFS]
            if not refs[3]['completed'] or not refs[8]['completed']:raise ValueError('ordinary')
            complete=not any(not m['completed'] for m in a)
            personal=x['delivered_own'] and x['both_own_outcomes'] and x['own_origins']>=16
            gaps={}
            control=complete
            for c,m in zip(MODES[1:],a[1:]):
                if x['completed'] and m['completed']:
                    dt=x['completion_tick']-m['completion_tick'];dw=x['paid_work']-m['paid_work'];gaps[c]=[dt,dw]
                    if dt>=0 or dw>=0:control=False
                else:gaps[c]=None
            done=[(r,m) for r,m in zip(REFS,refs) if m['completed']]
            fastest=[];cheapest=[];bt=513;bw=10000;fixed=x['completed']
            for r,m in done:
                t=m['completion_tick'];w=m['paid_work']
                if t<bt:bt=t;fastest=[r]
                elif t==bt:fastest.append(r)
                if w<bw:bw=w;cheapest=[r]
                elif w==bw:cheapest.append(r)
                if x['completed'] and (x['completion_tick']>=t or x['paid_work']>=w):fixed=False
            cells.append(dict(path_id=i,seed=s,complete_all=complete,personal=personal,control_gaps=gaps,
                fixed_gaps=[x['completion_tick']-bt,x['paid_work']-bw] if x['completed'] else None,
                best_latency_roles=fastest,best_work_roles=cheapest,strict_control_benefit=control,strict_fixed_benefit=fixed))
    counts=dict(cells=0,complete_all=0,personal_complete=0,strict_control_benefit=0,personal_control_benefit=0,personal_complete_fixed_benefit=0,personal_control_benefit_without_fixed=0)
    for c in cells:
        counts['cells']+=1
        if c['complete_all']:counts['complete_all']+=1
        if c['complete_all'] and c['personal']:counts['personal_complete']+=1
        if c['strict_control_benefit']:counts['strict_control_benefit']+=1
        if c['personal'] and c['strict_control_benefit']:
            counts['personal_control_benefit']+=1
            if not c['strict_fixed_benefit']:counts['personal_control_benefit_without_fixed']+=1
        if c['complete_all'] and c['personal'] and c['strict_fixed_benefit']:counts['personal_complete_fixed_benefit']+=1
    return dict(cells=cells,summary=counts,classification='descriptive_paired_bills_no_rescore',learning=False,stage_credit=False)

if __name__=='__main__':
    import sys
    print(json.dumps(diagnose(json.load(open(sys.argv[1]))),sort_keys=True,separators=(',',':')))
