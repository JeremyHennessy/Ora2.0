"""Author-fabricated measurement fixtures only; zero histories or Worlds run."""
import copy
import unittest
from experiments import digital_pressure71_measure as measure
from experiments import digital_pressure71_census as census
from tests.test_digital_pressure71_census import panel

PROVENANCE = dict(source_sha256='a' * 64, configuration_sha256='b' * 64)


def fixture():
    row, summary = panel()
    summary.update(seed=74000, dose=1, horizon=4096, software_only=False)
    row.update(seed=74000, dose=1)
    context = dict(seed=74000, dose=1, horizon=4096, software_only=False,
                   natural_history_hash=row['hash'], birth_edges=copy.deepcopy(summary['birth_edges']))
    proofs = []
    for kind, edge in zip(('parent', 'child'), measure.roster(context)):
        for role in ('sham', 'ancestor_value_control' if kind == 'parent' else 'inherited_source_control'):
            s = copy.deepcopy(summary); r = copy.deepcopy(row)
            if role == 'ancestor_value_control':
                # Fixed prepared branch: one fewer lineage g4 birth; keep world denominators.
                s['birth_edges'][-1]['parent'] = 5
                r['final']['events'][-1]['actor'] = 5
                r['final']['events'][-1]['birth']['child']['parent'] = 5
                r['hash'] = census.digest(r['final'])
            target = dict(censored=False, births=2 if role == 'sham' else 1,
                          food=3 if role == 'sham' else 2,
                          signatures=[['ACT', 0 if role == 'sham' else 1, 0]])
            proof = dict(verified=True, scientific_admission=False, stage_credit=False,
                         slot_kind=kind, role=role, provenance=copy.deepcopy(PROVENANCE),
                         seed=74000, natural_history_hash=context['natural_history_hash'],
                         branch_hash=r['hash'], null=False, summary=s, target=target,
                         transition_mask=[0], slot=dict(target=edge['child'], parent=edge['parent'],
                                                       generation=edge['generation'], tick=edge['tick']))
            if kind == 'parent': proof['census'] = census.census_from_replayed(r, s, edge['child'])
            proofs.append(proof)
    return proofs, context


class MeasurementTests(unittest.TestCase):
    def compare(self, proofs, context):
        return measure.family_comparison(*proofs, PROVENANCE, context)

    def test_prepared_positive_exact_growth_no_science(self):
        proofs, context = fixture(); result = self.compare(proofs, context)
        self.assertTrue(result['conditional_functional_contribution'])
        self.assertTrue(result['conditional_selection'])
        self.assertEqual(result['sham_growth'], [1, 6])
        self.assertEqual(result['control_growth'], [-1, 6])
        self.assertFalse(result['scientific_acceptance']); self.assertFalse(result['stage_credit'])

    def test_doses_not_interchangeable(self):
        proofs, context = fixture(); context['dose'] = 8
        with self.assertRaises(AssertionError): self.compare(proofs, context)

    def test_actual_first_child_and_full_slot_binding(self):
        for key, value in (('parent', 4), ('generation', 2), ('tick', 4096), ('target', 99)):
            proofs, context = fixture(); proofs[2]['slot'][key] = proofs[3]['slot'][key] = value
            with self.assertRaises(AssertionError): self.compare(proofs, context)

    def test_censored_and_empty_mask_retained_as_negative(self):
        for defect in ('censored', 'mask', 'action'):
            proofs, context = fixture()
            if defect == 'censored': proofs[2]['target']['censored'] = True
            elif defect == 'mask': proofs[2]['transition_mask'] = proofs[3]['transition_mask'] = []
            else: proofs[2]['target']['signatures'] = proofs[3]['target']['signatures']
            result = self.compare(proofs, context)
            self.assertFalse(result['conditional_functional_contribution'])
            self.assertFalse(result['conditional_selection'])

    def test_census_hash_counts_and_exact_fraction_bound(self):
        for defect in ('history_hash', 'frame', 'growth', 'lineage_birth_ids', 'death_records'):
            proofs, context = fixture(); c = proofs[0]['census']
            if defect == 'history_hash': c[defect] = 'f' * 64
            elif defect == 'frame': c[defect]['early_total'] += 1
            elif defect == 'growth': c[defect] = [0, 1]
            elif defect == 'lineage_birth_ids': c[defect] = []
            else: c[defect] = [dict(actor=6, tick=10)]
            with self.assertRaises(AssertionError): self.compare(proofs, context)

    def test_missing_child_retained_without_summary_or_dose_flag(self):
        proofs, context = fixture()
        context['birth_edges'] = context['birth_edges'][:3]
        for proof in proofs[2:]:
            proof.update(null=True, slot=None, target=None, branch_hash=None, transition_mask=None)
            proof.pop('summary')
        result = self.compare(proofs, context)
        self.assertTrue(result['child']['null'])
        self.assertFalse(result['conditional_functional_contribution'])
        context['birth_edges'].append(dict(parent=3, child=6, generation=3, tick=6))
        with self.assertRaises(AssertionError): self.compare(proofs, context)

    def test_provenance_natural_identity_and_short_scope_refused(self):
        for defect in ('provenance', 'natural_history_hash', 'software_only', 'horizon'):
            proofs, context = fixture()
            if defect == 'provenance': proofs[3][defect]['source_sha256'] = 'f' * 64
            elif defect == 'natural_history_hash': proofs[3][defect] = 'f' * 64
            elif defect == 'software_only': context[defect] = True
            else: context[defect] = 512
            with self.assertRaises(AssertionError): self.compare(proofs, context)

    def test_unsorted_mask_and_boolean_integer_refused(self):
        proofs, context = fixture(); proofs[0]['transition_mask'] = proofs[1]['transition_mask'] = [1, 0]
        with self.assertRaises(AssertionError): self.compare(proofs, context)

    def test_panel_keeps_all_denominators_doses_and_banks(self):
        families, populations = [], []
        for seed in measure.SEEDS:
            for dose in (1, 8):
                families.append(dict(seed=seed, dose=dose, provenance=PROVENANCE,
                    natural_history_hash='c' * 64, scientific_acceptance=False, stage_credit=False,
                    conditional_functional_contribution=dose == 1, conditional_selection=dose == 1))
                populations.append(dict(verified=True, provenance=PROVENANCE, stage_credit=False,
                    natural_history_hash='c' * 64, summary=dict(seed=seed, dose=dose, verified=True,
                    software_only=False, horizon=4096, mode='mutating', inheritance_mode='parent_copy',
                    births=2 if dose == 1 else 1, renewed_food=3 if dose == 1 else 2)))
        result = measure.panel(families, populations, PROVENANCE)
        self.assertTrue(result['pressure_alleviation'])
        self.assertEqual(result['replicated_selection'], {1: True, 8: False})
        self.assertEqual(result['banks']['unseen']['doses'][8]['denominator'], 4)
        self.assertFalse(result['scientific_acceptance'])
        for fs, ps in ((families[:-1], populations), (families + [families[0]], populations),
                       (families, populations[:-1])):
            with self.assertRaises(AssertionError): measure.panel(fs, ps, PROVENANCE)
        populations[0]['natural_history_hash'] = 'd' * 64
        with self.assertRaises(AssertionError): measure.panel(families, populations, PROVENANCE)
        proofs, context = fixture(); context['dose'] = True
        with self.assertRaises(AssertionError): self.compare(proofs, context)


if __name__ == '__main__': unittest.main()
