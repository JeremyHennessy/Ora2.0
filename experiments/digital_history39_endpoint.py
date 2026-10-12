"""Complete-census summary adapter; full VM/custody proof is a precondition.

Prepared inputs are reachability fixtures, never measured organism improvement.
The frozen History33 per-cell bill/predicate is reused without rescoring it.
"""
from .digital_history33_endpoint import compare, MODES, REFERENCES
from .digital_source37_coverage import manifest

VERSION = 'DIGITAL-HISTORY-39-ENDPOINT-v1'
SEEDS = tuple(range(38200, 38208))
RESERVED = tuple(range(38300, 38308))


def identities():
    return tuple(x['path_id'] for x in manifest()['candidates'])


def contract():
    return dict(version=VERSION, candidates=list(identities()),
                fresh_seeds=list(SEEDS), reserved_unopened=list(RESERVED),
                references=list(REFERENCES), controls=list(MODES),
                candidate_cells=896, candidate_histories=2688,
                reference_histories=264, total_histories=2952, horizon=512,
                all_eight_cells_required_per_genotype=True,
                performance_selection=False, world_histories_executed=0,
                learning=False, stage_credit=False)


def census(cells, references, predicate=compare):
    """All 112 sparse ancestry IDs, eight seeds and every arm; no winners inserted.

Keys and values must already have independently authenticated ancestry,
complete paid VM histories and strict before-completion origin extraction.
This adapter does not authenticate a trace or establish learning by itself.
"""
    ids = identities()
    expected = {(i, s) for i in ids for s in SEEDS}
    if (any(type(i) is not int or type(s) is not int for i, s in cells)
            or set(cells) != expected or set(references) != set(SEEDS)
            or any(type(s) is not int for s in references)):
        raise ValueError('complete unselected fresh census required')
    results = {(i, s): predicate(cells[i, s], references[s]) for i, s in sorted(expected)}
    return dict(cells=[dict(path_id=i, seed=s, **results[i, s]) for i, s in sorted(expected)],
                qualified_cells=sum(x['qualified'] for x in results.values()),
                all_eight_qualified=sum(all(results[i, s]['qualified'] for s in SEEDS) for i in ids),
                denominator_genotypes=len(ids), denominator_cells=len(expected),
                learning=False, stage_credit=False)
