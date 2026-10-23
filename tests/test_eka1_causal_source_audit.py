import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('audit', ROOT/'tools/eka1_causal_source_audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class SourceAuditTests(unittest.TestCase):
    def test_pinned_real_source_is_not_a_causal_pass(self):
        result = audit.audit(ROOT)
        self.assertEqual(result['source_audit'], 'PASS')
        self.assertFalse(result['causal_assay_qualified'])
        self.assertEqual(result['worlds_authorized'], 0)

    def test_restore_without_replay_is_distinguished(self):
        raw = b'class World:\n def step(self): pass\n def restore(cls,state): return state\n'
        r = audit.inspect_source(raw)
        self.assertFalse(r['restore_replays_steps'])
        self.assertFalse(r['restore_requires_exact_history'])

    def test_exact_equality_without_replay_is_not_replay(self):
        raw = b'class World:\n def step(self): pass\n def restore(cls,state):\n  assert h(world.snapshot()) == h(state)\n'
        r = audit.inspect_source(raw)
        self.assertTrue(r['restore_requires_exact_history'])
        self.assertFalse(r['restore_replays_steps'])

    def test_comment_cannot_fabricate_channel(self):
        r = audit.inspect_source(b'class World:\n def step(self):\n  # e["memory"]\n  pass\n')
        self.assertNotIn('memory', r['channels'])

    def test_pressure_restore_also_requires_exact_replay(self):
        r = audit.audit(ROOT)['source_findings']['digital_pressure71_population.py']
        self.assertTrue(r['restore_defined_here'])
        self.assertTrue(r['restore_replays_steps'])
        self.assertTrue(r['restore_requires_exact_history'])

    def test_read_and_write_contexts_are_distinct(self):
        r = audit.inspect_source(b'class World:\n def step(self):\n  e["feedback"]=0\n  x=e["feedback"]\n')
        self.assertEqual(r['channels']['feedback'], ['Load', 'Store'])


if __name__ == '__main__':
    unittest.main()
