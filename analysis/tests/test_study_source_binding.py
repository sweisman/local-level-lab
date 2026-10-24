# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import tempfile
import unittest
from pathlib import Path


class TestSourceBinding(unittest.TestCase):
    def test_source_binding_accepts_only_unchanged_qualified_subset_and_shared_engine(self):
        m=importlib.import_module('lll.studies.source_binding')
        from lll.studies.artifacts import digest
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);files={'analysis/lll/experiment.py':b'x=1\n',
                'analysis/lll/studies/streams.py':b'x=2\n','analysis/tests/ilvis0_control_shards.py':b'x=3\n'}
            hashes={}
            for name,raw in files.items():
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);hashes[name]=digest(raw)
            declared={'analysis/lll/experiment.py':hashes['analysis/lll/experiment.py']}
            proof=m.verify(root,declared=declared,manifest=hashes)
            self.assertEqual((proof['qualified_count'],proof['manifest_count'],proof['engine_extension_count']),(1,3,2))
            changed=dict(declared);changed['analysis/lll/experiment.py']='wrong'
            with self.assertRaises(ValueError):m.verify(root,declared=changed,manifest=hashes)
            with self.assertRaises(ValueError):m.verify(root,declared=declared,manifest={})
            (root/'analysis/lll/experiment.py').write_bytes(b'changed')
            with self.assertRaises(ValueError):m.verify(root,declared=declared,manifest=hashes)

    def test_source_binding_rejects_unqualified_science_and_nested_engine_paths(self):
        m=importlib.import_module('lll.studies.source_binding')
        from lll.studies.artifacts import digest
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);p=root/'analysis/lll/experiment.py';p.parent.mkdir(parents=True);p.write_bytes(b'x=1')
            declared={'analysis/lll/experiment.py':digest(p.read_bytes())}
            for name in ('analysis/lll/other_science.py','analysis/lll/studies/nested/other.py','docs/other.md'):
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'x=2')
                with self.subTest(name=name):
                    with self.assertRaises(ValueError):m.verify(root,declared=declared,manifest=dict(declared,**{name:digest(path.read_bytes())}))

    def test_source_binding_scope_restores_enumerator_on_failure(self):
        m=importlib.import_module('lll.studies.source_binding')
        from types import SimpleNamespace
        original=lambda root:['a'];adapter=SimpleNamespace(qualification_sources=original)
        with self.assertRaisesRegex(RuntimeError,'test'):
            with m.enumeration(adapter,['a','b']):
                self.assertEqual(adapter.qualification_sources(None),['a','b'])
                raise RuntimeError('test')
        self.assertIs(adapter.qualification_sources,original)
