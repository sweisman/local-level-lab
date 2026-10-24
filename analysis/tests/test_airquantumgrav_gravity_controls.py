# SPDX-License-Identifier: AGPL-3.0-or-later
"""Definition checks require no numerical libraries."""
import importlib
import tempfile
import unittest
from pathlib import Path


def library():return importlib.import_module('lll.airquantumgrav_gravity_controls')


class TestDefinition(unittest.TestCase):
    def test_gravity_matrix_has_separate_finite_48_case_allowance(self):
        module=library();r=module.recipe();tasks=module.tasks()
        self.assertEqual(len(tasks),48);self.assertEqual(len({v['identity'] for v in tasks}),48)
        self.assertEqual((r['workers'],r['threads'],r['maximum_wall_s']),(4,1,3600.))
        self.assertEqual(sum(t['limits']['native_calls'] for t in tasks),144)
        self.assertEqual(sum(t['limits']['packet_visits'] for t in tasks),2695680000)
        self.assertTrue(all(t['native_kind']=='mixed' and t['limits']['bound_calls']==0 for t in tasks))
        self.assertEqual(module.construction_limits(r),dict(constructed_intervals=1080000,generated_samples=1080041))
        self.assertEqual(len({tuple(v['payload'].values()) for v in tasks}),48)
        for key in ('observed_starts','original_reads','protected_reads','retries'):self.assertEqual(r[key],0)

    def test_gravity_study_requires_qualification_before_any_files(self):
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaisesRegex(ValueError,'qualification'):library().prepare(Path(name),qualification=None)
            self.assertFalse((Path(name)/'data').exists())

    def test_gravity_comparison_cannot_pass_missing_accuracy_or_columns(self):
        module=library();r=module.recipe()
        phases=[dict(horizontal_rms_m=.01,vertical_rms_m=.02,maximum_3d_m=.04),
                dict(horizontal_rms_m=.001,vertical_rms_m=.002,maximum_3d_m=.004)]
        self.assertTrue(module.checks(phases,value_disagreement_m=0.,all_columns_retained=True,r=r)['passed'])
        for pair,disagree,columns in (([dict(phases[0],vertical_rms_m=2.),phases[1]],0.,True),
                (phases,.01,True),(phases,0.,False)):
            self.assertFalse(module.checks(pair,value_disagreement_m=disagree,all_columns_retained=columns,r=r)['passed'])
