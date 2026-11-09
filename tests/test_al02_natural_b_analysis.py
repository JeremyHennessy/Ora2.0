import json
from pathlib import Path
import unittest
from tools.al02_natural_b_analysis import analyze_pair, contexts, lineage, summarize


class PanelAnalysisTests(unittest.TestCase):
    def test_frozen_contexts(self):
        path = Path('D:/OraLab/reports/ora-al02-natural-b-panel-20261109/contexts.json')
        self.assertEqual(json.loads(path.read_bytes()), contexts())
        self.assertEqual(len({row['seed'] for row in contexts()}), 128)
        self.assertNotIn(8195177122164069225, {row['seed'] for row in contexts()})

    def test_actual_zero_uptake_and_bad_pin(self):
        path = Path('D:/OraLab/reports/al02-first-depletion-successor-20261109/attempt-v3/raw.bin')
        payload = json.loads(path.read_bytes())
        raw = payload['checkpoint'].encode()
        result = analyze_pair(8195177122164069225, raw, payload['checkpoint_sha256'], payload['branches'])
        self.assertEqual(result['result']['contrast'], 0)
        for branch in result['branches'].values():
            self.assertEqual((branch['origins'], branch['attempts'], branch['meals']), ([], [], 0))
            self.assertEqual(len(branch['actors']), 10)
        with self.assertRaisesRegex(ValueError, 'pin mismatch'):
            analyze_pair(8195177122164069225, raw, '0'*64, payload['branches'])

    def test_incomplete_denominator(self):
        rows = [dict(index=i, status='accepted', result={'contrast': 0}) for i in range(128)]
        self.assertEqual(summarize(rows)['all_context_mean'], 0)
        rows[0] = dict(index=0, status='failed')
        result = summarize(rows)
        self.assertIsNone(result['all_context_mean'])
        self.assertEqual(result['counts']['failed'], 1)
        with self.assertRaisesRegex(ValueError, 'Every committed'):
            summarize(rows[:-1])

    def test_copy_origin_survives_faithful_inheritance(self):
        # Structural lineage fixture only. Scientific input goes through verify_pair.
        def event(kind, event_id, **fields):
            return dict(kind=kind, event_id=event_id, tick=event_id, **fields)
        rows = [event('GENESIS',0,organism_id=0,tape_ops=[0]),
                event('COPY_WRITE',1,parent_id=0,written_op=1,mutated=True,nursery_index=0),
                event('BIRTH',2,parent_id=0,child_id=1,child_genome_ops=[1],copy_event_ids=[1]),
                event('COPY_WRITE',3,parent_id=1,written_op=1,mutated=False,source_index=0),
                event('BIRTH',4,parent_id=1,child_id=2,child_genome_ops=[1],copy_event_ids=[3]),
                event('EXEC',5,organism_id=2,opcode=1,outcome='ate_b',food_b=1,
                      energy_before=4,energy_after=23)]
        result = lineage(rows)
        self.assertEqual(result['actors'][2]['slots'], {0:1})
        self.assertEqual(result['actors'][1]['same_program_children'], [2])
        self.assertEqual(result['meals'], 1)
        rows[0]['tape_ops'] = [1]
        with self.assertRaisesRegex(ValueError, 'Engineered founder'):
            lineage(rows)
