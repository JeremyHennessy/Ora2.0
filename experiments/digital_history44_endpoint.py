"""Complete-census summary adapter; full VM/custody proof is a precondition.

Prepared inputs are reachability fixtures, never measured organism improvement.
The frozen History33 per-cell bill/predicate is reused without rescoring it.
"""
from .digital_history33_endpoint import compare, MODES, REFERENCES

VERSION = 'DIGITAL-HISTORY-44-ENDPOINT-v1'
SEEDS = tuple(range(44200, 44208))
RESERVED = tuple(range(44300, 44308))


def identities():
    return tuple(range(256))


def contract():
    return dict(version=VERSION, candidates=list(identities()),
                fresh_seeds=list(SEEDS), reserved_unopened=list(RESERVED),
                references=list(REFERENCES), controls=list(MODES),
                candidate_cells=2048, candidate_histories=6144,
                reference_histories=264, total_histories=6408, horizon=512,
                all_eight_cells_required_per_genotype=True,
                performance_selection=False, world_histories_executed=0,
                learning=False, stage_credit=False)


def census(cells, references, predicate=compare):
    """All 256 frozen sample IDs, eight seeds and every arm; no winners inserted.

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
    return dict(cells=[dict(sample_id=i, seed=s, **results[i, s]) for i, s in sorted(expected)],
                qualified_cells=sum(x['qualified'] for x in results.values()),
                all_eight_qualified=sum(all(results[i, s]['qualified'] for s in SEEDS) for i in ids),
                denominator_genotypes=len(ids), denominator_cells=len(expected),
                learning=False, stage_credit=False)
