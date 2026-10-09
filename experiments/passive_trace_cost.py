"""TRACE-01 authored passive component only; no action selection/controller."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil

ARMS=('candidate','fixed-reactive','memory-disabled','shuffled-history')
HORIZONS=(0,16,64,128,224,256)
FILES=('experiments/passive_trace_cost.py','experiments/passive_trace_cost_audit.py','docs/TRACE-01-COST-CONTRACT.md')
ROOT=Path(__file__).resolve().parents[1]

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'))

def schedule(horizon):return [('write',i) for i in range(0,16,2)]+[('clock',None)]*horizon+[('read',i) for i in range(16)]+[('erase',i) for i in (0,4,8,12)]+[('read',i) for i in range(16)]+[('write',i) for i in (0,4,8,12)]


class Cell:
    def __init__(self,arm):
        if arm not in ARMS:raise ValueError('Registered passive arm')
        self.arm=arm;self.fuel=list(range(256));self.operator=list(range(64));self.atoms=list(range(64));self.heat=0
        self.active={};self.traces={};self.next_trace=0;self.clocks=0
        self.rng=random.Random(91004);self.fixed=[self.rng.getrandbits(1) for _ in range(16)]

    def state(self):return dict(arm=self.arm,fuel=self.fuel,operator=self.operator,atoms=self.atoms,heat=self.heat,active=self.active,traces=self.traces,next_trace=self.next_trace,clocks=self.clocks,fixed=self.fixed)

    def step(self,request,t):
        op,site=request
        if op not in ('write','read','erase','clock') or (op!='clock' and (type(site) is not int or site not in range(16))) or (op=='clock' and site is not None):raise ValueError('Fixed component request')
        if op=='write':
            price=2 if self.arm=='shuffled-history' else 1
            if len(self.fuel)<2 or len(self.operator)<price:return dict(kind='unaffordable',operation=op)
            paid=self.fuel[:2];pulse=self.operator[:price];del self.fuel[:2];del self.operator[:price];self.heat+=price
            target=(site+1)%16 if self.arm=='shuffled-history' else site;made=None
            if self.arm in ('candidate','shuffled-history') and target not in self.active:
                made=self.next_trace;self.next_trace+=1
                self.traces[made]=dict(site=target,born=t,parents=dict(fuel=paid,pulse=pulse),atoms=list(range(4*target,4*target+4)));self.active[target]=made;self.heat+=1
            else:self.heat+=2
            return dict(kind='write',site=site,target=target,fuel=paid,pulse=pulse,trace=made)
        if op=='read':
            if not self.fuel:return dict(kind='unaffordable',operation=op,output=None)
            paid=self.fuel.pop(0);self.heat+=1
            value=self.fixed[site] if self.arm=='fixed-reactive' else 0 if self.arm=='memory-disabled' else int(site in self.active)
            return dict(kind='read',site=site,fuel=paid,output=value)
        if op=='erase':
            erased=self.active.pop(site,None);self.heat+=int(erased is not None);return dict(kind='erase',site=site,trace=erased)
        self.clocks+=1
        if self.fuel:
            paid=self.fuel.pop(0);self.heat+=1;return dict(kind='clock',fuel=paid)
        lost=sorted(self.active.values());self.heat+=len(lost);self.active={};return dict(kind='unaffordable',operation='clock',lost=lost)


def panel(output,revision):
    output=Path(output).resolve()
    if output.drive.upper()!='D:' or output.exists() or len(revision)!=40 or any(c not in '0123456789abcdef' for c in revision) or shutil.disk_usage(output.parent).free<5*1024**3:raise ValueError('Fresh bounded D: source/floor')
    output.mkdir();manifest=dict(schema='trace01-cost-v1',revision=revision,arms=list(ARMS),horizons=list(HORIZONS),source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES},traces=[])
    for horizon in HORIZONS:
        for arm in ARMS:
            model=Cell(arm);events=[];initial=json.loads(canonical(model.state()));rng=model.rng.getstate()
            for t,r in enumerate(schedule(horizon)):events.append(dict(t=t,request=list(r),event=model.step(r,t),state=json.loads(canonical(model.state()))))
            name=f'{horizon}-{arm}.json';value=dict(horizon=horizon,arm=arm,initial=initial,initial_rng=rng,events=events,final=model.state(),final_rng=model.rng.getstate())
            (output/name).write_text(canonical(value)+'\n',encoding='utf-8',newline='\n');manifest['traces'].append(name)
    if sum(p.stat().st_size for p in output.iterdir())>16*1024**2:raise ValueError('Fixed evidence ceiling')
    manifest['files_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()};(output/'manifest.json').write_text(canonical(manifest)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);p.add_argument('--source-revision',required=True);a=p.parse_args();panel(a.output_dir,a.source_revision)
