# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import sys
import tempfile
import unittest


class TestReport(unittest.TestCase):
    def test_observed_height_report_rejects_open_before_numerical_imports(self):
        module=importlib.import_module('lll.airquantumgrav_observed_height_report')
        before='numpy' in sys.modules
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises((ValueError,FileNotFoundError)):
                module.inspect(root,'data/not-complete')
        self.assertEqual('numpy' in sys.modules,before)

    def test_observed_height_gravity_binding_rejects_mismatched_anchor_or_mode(self):
        module=importlib.import_module('lll.airquantumgrav_observed_height_report')
        binding=dict(gravity_model='inverse-square-height-v1',gravity_anchor_height_m=1500.,
            gravity_anchor_source='first_training_receiver_height',predicted_midpoint_height=True,
            extra_parameters=0,later_receiver_heights_used=False)
        meta=dict(gravity_model='inverse-square-height-v1',gravity_anchor_height_m=1500.)
        module.verify_gravity(binding,dict(value=meta,tangent=meta),anchor=1500.)
        for changed in (dict(binding,gravity_anchor_height_m=1501.),dict(binding,later_receiver_heights_used=True),
                dict(binding,extra_parameters=1),dict(binding,gravity_model='constant')):
            with self.assertRaises(ValueError):module.verify_gravity(changed,dict(value=meta,tangent=meta),anchor=1500.)
        with self.assertRaises(ValueError):
            module.verify_gravity(binding,dict(value=meta,tangent=dict(meta,gravity_anchor_height_m=1501.)),anchor=1500.)

    def test_height_comparison_keeps_missing_and_failed_baseline_starts(self):
        module=importlib.import_module('lll.airquantumgrav_observed_height_report')
        old=dict(identity='a',complete=False,passed=False)
        new=dict(identity='a',complete=True,passed=True,prediction=dict(horizontal_rms_m=1.,vertical_rms_m=2.,total_rms_m=3.))
        rows=module.matched_changes(dict(rows=[new]),dict(rows=[old]))
        self.assertEqual(rows[0]['baseline_complete'],False)
        self.assertEqual(rows[0]['revised_complete'],True)
        self.assertIsNone(rows[0]['baseline_prediction_total_rms_m'])
        self.assertEqual(rows[0]['revised_prediction_total_rms_m'],3.)
        with self.assertRaises(ValueError):module.matched_changes(dict(rows=[]),dict(rows=[old]))
