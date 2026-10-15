"""Emit a standalone literal with explicit reviewed hooks; no World execution."""
import hashlib
from pathlib import Path

ROOT = Path('D:/OraLab/src/Ora2.0-recording82/experiments')
base = (ROOT/'digital_memory80_referee.py').read_bytes()
assert hashlib.sha256(base).hexdigest() == '9da82afd0394721b11af205826775c86cf75c44f2b605c17bb86a23ed770c061'
text = base.decode().replace('\r\n', '\n')
text = text.replace('Literal population replay of software-only MEMORY80 receipts. No producer imports.',
    'Literal MEMORY80 replay with independent credited-fallback86 control hooks.')
text = text.replace('software_assistance=None):', 'software_assistance=None, control=None, ledger=None):', 1)
helpers = '''
def boundary_before(entity, pending, completed, initial_entry, control):
    if pending is None:
        return None
    previous, actual = pending
    assert entity['pc'] == actual
    assert (previous, actual) in ((4,6),(5,1),(11,6),(15,1),(15,16),(19,6),(20,16))
    active = int(completed >= 48)
    projected = actual
    if active and control == 'history_disabled':
        projected = initial_entry
    elif active and control == 'fallback_misbound' and actual in (1,16):
        projected = 16 if actual == 1 else 1
    entity['pc'] = projected
    return dict(previous_pc=previous, actual_entry=actual, projected_entry=projected,
                completed=completed, active=active)


def model_value(entity, pc, completed, control):
    assert pc in (7,12)
    memory = entity['memory']
    index = entity['registers'][1]
    address = index % len(memory)
    origin = address
    active = int(completed >= 48)
    if active and control in ('model_erased','history_disabled'):
        origin = None
    elif active and control == 'model_misbound':
        origin = (address + len(memory)//2) % len(memory)
    value = 0 if origin is None else memory[origin]
    return dict(pc=pc,index=index,address=address,source_address=origin,
                truthful_cell=memory[address],value=value,active=active)


def boundary_after(pc, event, completed):
    after = event.get('after')
    if after is None or (pc, after['pc']) not in ((4,6),(5,1),(11,6),(15,1),(15,16),(19,6),(20,16)):
        return completed, None, None
    completed += 1
    return completed, (pc,after['pc']), dict(completed=completed,previous_pc=pc,
        entry=after['pc'],energy=after['energy'])


'''
text = text.replace('\ndef audit(', '\n'+helpers+'def audit(', 1)
text = text.replace('    typed(state)\n', '''    typed(state)
    assert control is None or type(control) is str and control in (
        'intact','model_erased','model_misbound','fallback_misbound','history_disabled')
    completed=0; pending_boundary=None
    if control is None:
        assert ledger is None
    else:
        assert mode=='no_variation' and max_population==1 and expansion_tick==0
        assert software_assistance is None and horizon==1024
        q=program[0][1]; initial_entry=program[0][2]
        assert initial_entry in (1,6,16)
        assert program==[
            [7,q,initial_entry],[4,0,0],[6,0,0],[1,0,0],[8,0,6],[7,0,1],
            [0,1,0],[19,0,1],[6,0,0],[1,0,0],[8,0,12],[7,0,6],
            [19,0,1],[21,0,0],[20,1,0],[8,0,1],
            [4,0,1],[6,0,0],[1,0,0],[8,0,6],[7,0,16]]
        assert type(ledger) is list and len(ledger)==len(state['events'])
        typed(ledger)
''', 1)
old = "        e=s['entities'][str(actor)]; s['tick']+=1; e['turns']+=1"
new = '''        e=s['entities'][str(actor)]
        if control is not None:
            assert completed<60
            completed_before=completed
            entry=boundary_before(e,pending_boundary,completed,initial_entry,control)
            pending_boundary=None
            pc_before=e['pc']
            observed_read=model_value(e,pc_before,completed,control) if pc_before in (7,12) else None
        s['tick']+=1; e['turns']+=1'''
assert old in text
text = text.replace(old,new,1)
old = "            elif op==19: r[a%2]=e['memory'][r[b%2]%q]"
new = '''            elif op==19:
                r[a%2]=e['memory'][r[b%2]%q] if control is None else observed_read['value']'''
assert old in text
text = text.replace(old,new,1)
old = '        assert event==receipt, \'Literal transition mismatch at dispatch \'+'
assert old in text
text = text.replace(old,'''        if control is not None:
            completed,pending_boundary,completion=boundary_after(pc_before,event,completed)
            expected_ledger=dict(tick=event['tick'],dispatch_pc=pc_before,
                completed_before=completed_before,entry=entry,read=observed_read,completion=completion)
            assert ledger[s['tick']-1]==expected_ledger, 'Control ledger mismatch'
        assert event==receipt, 'Literal transition mismatch at dispatch '+''',1)
text = text.replace("assert s['tick']==horizon or not s['entities'], 'Premature trace truncation'",
    "assert s['tick']==horizon or not s['entities'] or (control is not None and completed==60), 'Premature trace truncation'",1)
# A separate module is emitted; the pinned old referee is never overwritten.
out = ROOT/'digital_credited_fallback86_control_referee.py'
assert not out.exists()
out.write_text(text, encoding='utf-8', newline='\n')
print('Emitted independent literal with explicit hooks over pinned old referee')
