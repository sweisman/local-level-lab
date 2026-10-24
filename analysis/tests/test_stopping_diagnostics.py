# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib
import sys
import tempfile
import unittest


class TestStoppingDiagnostics(unittest.TestCase):
    def test_stopping_audit_requires_closed_study_before_importing_numerical_libraries(self):
        module=importlib.import_module('lll.stopping_diagnostics');before='numpy' in sys.modules
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises((ValueError,FileNotFoundError)):module.audit(root,'data/not-closed')
        self.assertEqual('numpy' in sys.modules,before)

    def material(self):
        policy=dict(relative_cost_tolerance=1e-8,stationarity_tolerance=1e-4,
            position_rms_tolerance_m=.001,position_max_tolerance_m=.01)
        fit=dict(converged=False,evaluations=22,maximum_evaluations=200,termination='unresolved',
            stationarity_tolerance=1e-4,near_zero_probe=None,stability_probe=dict(passed=False,
                actual_cost_change=4.45e-8,fresh_stationarity=2.4e-7,
                position_rms_neu_m=[2.6e-8,4.3e-8,1.9e-8],position_max_abs_neu_m=[7.5e-8,1.6e-7,5.7e-8],
                position_rms_tolerance_m=.001,position_max_tolerance_m=.01))
        return fit,policy

    def test_stopping_diagnostic_identifies_only_the_failed_cost_gate(self):
        module=importlib.import_module('lll.stopping_diagnostics');fit,policy=self.material();before=copy.deepcopy(fit)
        result=module.components(fit,policy)
        self.assertEqual(result['failed_components'],['relative_cost_change'])
        self.assertFalse(result['saved_converged']);self.assertFalse(result['reclassified'])
        self.assertEqual(fit,before)

    def test_stopping_diagnostic_preserves_original_label_even_if_components_pass(self):
        module=importlib.import_module('lll.stopping_diagnostics');fit,policy=self.material()
        fit['stability_probe'].update(passed=True,actual_cost_change=1e-9)
        result=module.components(fit,policy)
        self.assertEqual(result['failed_components'],[]);self.assertFalse(result['saved_converged'])
        self.assertTrue(result['all_components_satisfied']);self.assertEqual(result['scientific_decision'],'abstain')

    def test_stopping_diagnostic_checks_every_axis_and_stationarity(self):
        module=importlib.import_module('lll.stopping_diagnostics');fit,policy=self.material()
        fit['stability_probe'].update(actual_cost_change=0.,fresh_stationarity=.01,
            position_rms_neu_m=[0.,.002,0.],position_max_abs_neu_m=[0.,0.,.02])
        self.assertEqual(module.components(fit,policy)['failed_components'],
            ['fresh_stationarity','position_rms','position_maximum'])

    def test_stopping_diagnostic_rejects_nonfinite_and_inconsistent_saved_probes(self):
        module=importlib.import_module('lll.stopping_diagnostics');fit,policy=self.material()
        for change in (dict(actual_cost_change=float('nan')),dict(position_rms_neu_m=[0.,0.]),
                dict(passed=True),dict(position_rms_tolerance_m=.1),dict(position_max_abs_neu_m=[0.,-1.,0.])):
            changed=copy.deepcopy(fit);changed['stability_probe'].update(change)
            with self.subTest(change=change):
                with self.assertRaises(ValueError):module.components(changed,policy)

    def test_stopping_diagnostic_leaves_other_stopping_rules_unclassified(self):
        module=importlib.import_module('lll.stopping_diagnostics');fit,policy=self.material()
        fit['near_zero_probe']=dict(passed=True,reason='near_zero_repeat_verified')
        result=module.components(fit,policy)
        self.assertFalse(result['available']);self.assertFalse(result['saved_converged'])

    def test_stopping_policy_is_read_from_literal_frozen_source_not_imported(self):
        module=importlib.import_module('lll.stopping_diagnostics')
        refinement=b"raise RuntimeError('must not execute')\nPOLICY=dict(relative_cost_tolerance=1e-8,stationarity_tolerance=1e-4)\n"
        position=b"POLICY=dict(other.POLICY,position_rms_tolerance_m=.001,position_max_tolerance_m=.01)\n"
        _,expected=self.material();self.assertEqual(module.frozen_policy(refinement,position),expected)
        for bad in (b'POLICY=calculate()',b'POLICY=dict(relative_cost_tolerance=unknown,stationarity_tolerance=1e-4)',
                b'POLICY=dict(relative_cost_tolerance=0.,stationarity_tolerance=1e-4)'):
            with self.assertRaises(ValueError):module.frozen_policy(bad,position)
