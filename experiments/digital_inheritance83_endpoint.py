"""Offspring accounting on fully literal-verified INHERITANCE83 data.

No producer imports, target generation, policy changes or selection acceptance.
The 64 served-decision flag is a diagnostic, not scientific admission.
"""
from experiments.digital_inheritance83_referee import audit, digest
from experiments.digital_memory80_endpoint import paid_viable_children


def evaluate(state, **configuration):
    # Never trust a caller-supplied verified flag or a detached endpoint proof.
    physics = audit(state, **configuration)
    births = paid_viable_children(state)
    rows = []
    for birth in births:
        identity = birth['child']
        events = [e for e in state['events'] if e['actor'] == identity]
        attempts = [e for e in events if 'attempt' in e]
        own_children = [b for b in births if b['parent'] == identity]
        deaths = [e for e in events if 'death' in e]
        living = state['entities'].get(str(identity))
        if living is None:
            living = state['entities'].get(identity)
        captured = sum(e.get('captured', 0) for e in events)
        startup_transferred = sum(e['birth']['startup_energy'] for e in events if 'birth' in e)
        terminal_energy = 0 if living is None else living['energy']
        # Includes dissipated energy on death; transfers to children are separated.
        outflow = 112 + captured - startup_transferred - terminal_energy
        assert outflow >= 0
        rows.append(dict(
            **birth, dispatches=len(events), served_decisions=len(attempts),
            absent_decisions=sum(e.get('decoded', [None])[0] == 6 and 'attempt' not in e for e in events),
            successes=sum(e['attempt']['success'] for e in attempts),
            experienced_cues=sorted({e['attempt']['cue'] for e in attempts}),
            captured=captured, terminal_energy=terminal_energy,
            startup_transferred=startup_transferred,
            operating_and_death_outflow=outflow,
            copy_instructions=sum(e.get('decoded', [None])[0] == 10 for e in events),
            copied_words=sum(len(e.get('writes', [])) for e in events),
            sampler_draws=sum('draw' in e for e in events),
            sampler_aborts=sum(e.get('sampler_finished', {}).get('abort', 0) for e in events),
            paid_children=len(own_children),
            own_resource_children=sum(b['own_resource_viable'] for b in own_children),
            completed_64_served_decisions=len(attempts) >= 64,
            paid_replacement_with_own_acquisition=any(b['own_resource_viable'] for b in own_children),
            death=None if not deaths else deaths[0]['death']['cause'],
            right_censored=living is not None,
        ))
    assert len(rows) == state['births']
    return dict(version='INHERITANCE83-ENDPOINT-v1',
                physics=physics, history_sha256=digest(state), offspring=rows,
                scientific_admission=False, selection_demonstrated=False,
                scientific_worlds=0, stage_credit=False)
