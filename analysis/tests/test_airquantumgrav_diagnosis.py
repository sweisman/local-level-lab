# SPDX-License-Identifier: AGPL-3.0-or-later
"""Definition tests import no numerical engine; numerical checks wait for capacity."""
import importlib
import unittest


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_diagnosis') is not None,'saved-data diagnosis adapter missing'
    return importlib.import_module('lll.airquantumgrav_diagnosis')


class TestDefinition(unittest.TestCase):
    def test_diagnosis_has_finite_read_only_scope(self):
        r=library().recipe();tasks=library().tasks()
        self.assertEqual((r['workers'],r['threads'],r['maximum_wall_s']),(1,1,600.))
        self.assertEqual(len(tasks),1)
        self.assertTrue(all(value==0 for value in tasks[0]['limits'].values()))
        for key in ('native_calls','observed_starts','new_propagations','original_reads','protected_reads'):
            self.assertEqual(r[key],0)
        self.assertEqual(r['maximum_settings'],12)
        self.assertEqual(r['maximum_saved_error_epochs'],28800)

    def test_diagnosis_requires_qualification_before_reading_inputs(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaisesRegex(ValueError,'qualification'):library().prepare(Path(name),qualification=None)
            self.assertFalse((Path(name)/'data').exists())

    def test_diagnosis_rejects_open_parent_before_numerical_imports(self):
        import sys
        import tempfile
        from pathlib import Path
        before=set(sys.modules)
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaisesRegex(ValueError,'closed study required'):library().closed_parent(Path(name))
        self.assertFalse(any(name=='numpy' or name.startswith('numpy.') for name in set(sys.modules)-before))

    def test_preparation_rejects_unguarded_threads_before_reading_inputs(self):
        import os
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from lll.compute_budget import THREAD_KEYS
        with tempfile.TemporaryDirectory() as name,patch.dict(os.environ):
            for key in (*THREAD_KEYS,'OMP_THREAD_LIMIT','OMP_MAX_ACTIVE_LEVELS'):os.environ.pop(key,None)
            with self.assertRaisesRegex(ValueError,'thread environment'):
                library().prepare(Path(name),qualification='missing-request.json')
            self.assertFalse((Path(name)/'data').exists())
