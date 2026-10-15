"""Source/data/control checks only; no World, target or VM execution."""
import ast
import unittest
from pathlib import Path
from experiments import digital_credited_fallback86_source as source


def path(code, entry, feedback, bit):
    pc = entry
    registers = [7, 11]
    memory = [15*bit]*code[0][1]
    trace, actions, writes = [], [], []
    for _ in range(10):
        op, a, b = code[pc]
        trace.append(pc)
        pc += 1
        if op == 0:
            registers[a] = 7  # invented symbol; never an environment query
        elif op == 1:
            registers[a] = feedback
        elif op == 4:
            registers[a] = b
        elif op == 6:
            actions.append(registers[a] % 2)
        elif op == 7:
            pc = b
        elif op == 8 and registers[a] == 0:
            pc = b
        elif op == 19:
            registers[a] = memory[registers[b] % len(memory)]
        elif op == 20:
            memory[registers[a] % len(memory)] = registers[b]
            writes.append(registers[b])
        elif op == 21:
            registers[a] ^= 15
        if pc in (1, 6, 16):
            return trace, pc, actions, writes
    raise AssertionError('No complete boundary')


class CreditedFallbackSource(unittest.TestCase):
    def test_neutral_complete_sources_and_formation(self):
        m = source.manifest()
        self.assertEqual(len(m['descriptors']), 9)
        self.assertEqual(len({r['programme_sha256'] for r in m['descriptors']}), 9)
        base = source.programme(2, 'fallback0')
        for row in m['descriptors']:
            code = row['programme']
            self.assertEqual(len(code), 21)
            self.assertTrue(all(t[0] in source.OPS for t in code))
            self.assertTrue(all(len(t) == 3 and all(type(v) is int and 0 <= v < 32 for v in t) for t in code))
            self.assertLessEqual({(i,j) for i in range(21) for j in range(3) if code[i][j] != base[i][j]}, {(0,1),(0,2)})
            self.assertEqual(row['formation'], 3*len(code)+row['capacity']+8)
            self.assertEqual(row['blank_models'], [0]*row['capacity'])
            self.assertEqual(256-112-row['formation']-16, {2:55,4:53,8:49}[row['capacity']])
        for args in ((True,'model'),(3,'model'),(8,1),(8,'oracle')):
            with self.assertRaises(AssertionError):
                source.programme(*args)

    def test_all_synthetic_paths_credit_only_sensed_error(self):
        count = 0
        for descriptor in source.DESCRIPTORS:
            code = source.programme(*descriptor)
            for entry in (1,6,16):
                for feedback in (0,1,2):
                    for bit in (0,1):
                        trace, nxt, actions, writes = path(code,entry,feedback,bit)
                        model, error = entry == 6, feedback == 0
                        self.assertEqual(len(trace), (9 if error else 6) if model else (4 if error else 5))
                        self.assertEqual(actions, [bit if model else int(entry == 16)])
                        self.assertEqual(writes, [15*(1-bit)] if model and error else [])
                        self.assertEqual(nxt, (1 if bit else 16) if model and error else (6 if error else entry))
                        self.assertIn((trace[-1],nxt),source.BOUNDARIES)
                        count += 1
        self.assertEqual(count,162)

    def test_only_complete_boundaries_preserve_microflow(self):
        for prev in range(21):
            for nxt in (1,6,16):
                if (prev,nxt) not in source.BOUNDARIES:
                    with self.assertRaises(AssertionError):
                        source.entry_after_completed_decision(prev,nxt,'model','intact',False)
                    continue
                for initial in source.ENTRIES:
                    for control in source.CONTROLS:
                        self.assertEqual(source.entry_after_completed_decision(prev,nxt,initial,control,False),nxt)
                        expected = source.ENTRIES[initial] if control == 'history_disabled' else (17-nxt if control == 'fallback_misbound' and nxt != 6 else nxt)
                        self.assertEqual(source.entry_after_completed_decision(prev,nxt,initial,control,True),expected)
        for args in ((True,6,'model','intact',True),(15,16,'oracle','intact',True),
                     (15,16,'model','intact',1),(15,16,'model','unknown',True)):
            with self.assertRaises(AssertionError):
                source.entry_after_completed_decision(*args)

    def test_both_read_channels_binding_erasure_and_nonmutation(self):
        for q in source.CAPACITIES:
            cells = list(range(q))
            for pc in (7,12):
                for i in range(16):
                    for c in source.CONTROLS:
                        self.assertEqual(source.model_read(pc,cells,i,c,False),cells[i%q])
                        expected = 0 if c in ('model_erased','history_disabled') else cells[(i+(q//2 if c=='model_misbound' else 0))%q]
                        self.assertEqual(source.model_read(pc,cells,i,c,True),expected)
                        self.assertEqual(cells,list(range(q)))
                    for equal in (0,15):
                        self.assertEqual(source.model_read(pc,[equal]*q,i,'model_misbound',True),equal)
                self.assertEqual({source.model_read(pc,cells,i,'model_misbound',True) for i in range(q)},set(cells))
        for args in ((True,[0,0],0,'intact',True),(7,[0,True],0,'intact',True),
                     (12,[0,0],True,'intact',True),(7,[0,0],16,'intact',True),
                     (7,[0,0],0,'intact',1),(7,[0,0],0,'unknown',True),(9,[0,0],0,'intact',True)):
            with self.assertRaises(AssertionError):
                source.model_read(*args)

    def test_no_world_or_target_dependency_and_no_control_installation(self):
        tree = ast.parse(Path(source.__file__).read_bytes())
        imports = [n for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
        self.assertTrue(all(isinstance(n,ast.Import) for n in imports))
        self.assertEqual({a.name for n in imports for a in n.names},{'hashlib','json'})
        m = source.manifest()
        self.assertFalse(m['controls_installed'])
        self.assertFalse(m['scientific_admission'])
        self.assertEqual((m['worlds'],m['targets_queried']),(0,0))


if __name__ == '__main__':
    unittest.main()
