import json
import unittest
from experiments.digital_memory80_recording import FIELDS, terminal_view


class TerminalRecordingTests(unittest.TestCase):
    def fixture(self):
        raw = dict.fromkeys(FIELDS, 0)
        raw.update(food={2: 1, 10: 0}, leases={10: 2},
                   entities={2: {'memory': [0, 15]}, 10: {'memory': [15, 0]}},
                   free=[4, 8], events=[{'feedback': 0, 'text': '\u03bb\n"'}])
        return raw

    def test_canonical_bytes_equal_json_clone_with_numeric_table_order(self):
        raw = self.fixture()
        old = json.loads(json.dumps(raw))
        encode = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
        self.assertEqual(encode(terminal_view(raw)), encode(old))
        self.assertEqual(list(raw['entities']), [2, 10])

    def test_history_storage_not_duplicated(self):
        raw = self.fixture()
        raw['events'] *= 10000
        view = terminal_view(raw)
        self.assertIs(view['events'], raw['events'])
        self.assertIs(view['entities']['2'], raw['entities'][2])

    def test_already_recorded_tables_preserve_exact_content(self):
        raw = json.loads(json.dumps(self.fixture()))
        self.assertEqual(terminal_view(raw), raw)

    def test_collision_cannot_silently_replace_an_entity(self):
        raw = self.fixture()
        raw['entities']['2'] = {'memory': [7, 7]}
        with self.assertRaises(ValueError):
            terminal_view(raw)

    def test_schema_and_noncanonical_keys_refused(self):
        for key in (True, -1, '02', 1.5):
            raw = self.fixture()
            raw['food'] = {key: 0}
            with self.assertRaises(ValueError):
                terminal_view(raw)
        raw = self.fixture()
        raw['hidden'] = 1
        with self.assertRaises(ValueError):
            terminal_view(raw)


if __name__ == '__main__':
    unittest.main()
