import ast
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from experiments import digital_tail43_world as new
from experiments import digital_admission38_world as old


class TailAdmissionScopeTests(unittest.TestCase):
    def test_all_frozen_identities_and_bytes(self):
        raw=(Path(new.__file__).resolve().parents[1]/'data/digital-neutral-tail42-manifest.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),new.SOURCE_SHA256)
        m=new.manifest()
        self.assertEqual(m['candidates'],json.loads(raw)['candidates'])
        self.assertEqual([x['sample_id'] for x in m['candidates']],list(range(256)))
        self.assertEqual(m['total_histories'],1602)
        self.assertFalse(m['primary'])

    def test_corrupt_source_refused_before_construction(self):
        with patch.object(Path,'read_bytes',return_value=b'{}'),patch.object(new.law.World,'__init__',side_effect=AssertionError('No World fixture')):
            with self.assertRaisesRegex(ValueError,'byte identity'):new.manifest()

    def test_exact_world_install_local_history_body(self):
        def bodies(module):
            tree=ast.parse(Path(module.__file__).read_text(encoding='utf-8'))
            return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        a,b=bodies(new),bodies(old)
        for name in ('install','local','World','history'):self.assertEqual(a[name],b[name])

    def test_literal_referee_only_namespace_changed(self):
        root=Path(new.__file__).parent
        oldtext=(root/'digital_admission38_interpret.py').read_text(encoding='utf-8')
        self.assertEqual((root/'digital_tail43_interpret.py').read_text(encoding='utf-8'),oldtext.replace('DIGITAL-ADMISSION-38-PAID-v1','DIGITAL-TAIL-43-ADMISSION-v1').replace('(38100,38101)','(43100,43101)'))

    def test_chunks_keep_every_identity_and_reference(self):
        chunks=new.chunks();roles=sum(chunks,[])
        self.assertEqual(len(chunks),34)
        self.assertEqual(roles,list(new.programmes()))
        self.assertEqual(len(set(roles)),267)
        self.assertEqual([len(c) for c in chunks],[8]*33+[3])
        self.assertTrue(all(x.startswith('candidate') for x in roles[:256]))

    def test_refuses_invalid_scope_before_world(self):
        with patch.object(new.law.World,'__init__',side_effect=AssertionError('No World fixture')):
            for seed,arm,chunk in [(True,'intact',0),(38100,'intact',0),(38200,'intact',0),(38300,'intact',0),(33200,'intact',0),(43200,'intact',0),(43100,'bad',0),(43100,'intact',True),(43100,'intact',34),(-1,'intact',0)]:
                with self.assertRaises(ValueError):new.batch(seed,arm,chunk)

    def test_old_namespace_stays_closed(self):
        with self.assertRaises(ValueError):old.batch(43100,'intact',0)
        self.assertEqual(old.SEEDS,(38100,38101))

    def test_fixed_formation_and_permitted_immutable_ops(self):
        m=new.manifest()
        for x in m['candidates']:
            self.assertEqual(3*len(x['program'])+16,55)
            self.assertEqual(x['constructor_after_formation'],73)
            self.assertFalse(x['viability_verified'])
            self.assertFalse(x['natural_birth'])
            self.assertTrue(all(t[0] in (1,2,3,4,5,6,7,8,18) for t in x['program']))


if __name__=='__main__':unittest.main()
