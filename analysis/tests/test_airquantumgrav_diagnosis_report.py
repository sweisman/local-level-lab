# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import unittest


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_diagnosis_report') is not None,'saved diagnosis reporter missing'
    return importlib.import_module('lll.airquantumgrav_diagnosis_report')


def result():
    return dict(passed=True,settings=12,available_settings=0,native_calls=0,observed_starts=0,new_propagations=0,
        original_reads=0,protected_reads=0,forecasts_changed=False,causation_established=False,
        gravity_reference=dict(gravity_measured=False,scale_is_forecast=False,scale_is_error_bound=False,causation_established=False))


class TestMetadata(unittest.TestCase):
    def test_reference_sensitivity_cannot_be_promoted_to_measurement_or_cause(self):
        value=result();library().check_scope(value)
        for key in ('gravity_measured','scale_is_forecast','scale_is_error_bound','causation_established'):
            value=result();value['gravity_reference'][key]=True
            with self.assertRaises(ValueError):library().check_scope(value)

    def test_recomputed_predictions_or_original_reads_cannot_be_readonly_diagnosis(self):
        for key in ('native_calls','observed_starts','new_propagations','original_reads','protected_reads','forecasts_changed'):
            value=result();value[key]=1
            with self.assertRaises(ValueError):library().check_scope(value)

    def test_open_diagnosis_cannot_be_published(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaisesRegex(ValueError,'closed study required'):library().inspect(Path(name))
