# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import tempfile
import unittest
from pathlib import Path


class TestReport(unittest.TestCase):
    def test_height_report_rejects_open_study_before_numerical_imports(self):
        import sys
        module=importlib.import_module('lll.airquantumgrav_height_report');before=set(sys.modules)
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaisesRegex(ValueError,'closed study'):module.inspect(Path(name),'data/open')
        self.assertFalse(any(n=='numpy' or n.startswith('numpy.') for n in set(sys.modules)-before))

    def test_height_report_keeps_generated_scope_and_earlier_anchor_explicit(self):
        from lll.airquantumgrav_height_report import require_scope
        value=dict(original_reads=0,protected_reads=0,observed_starts=0,true_initial_state_supplied=False,
            true_calibration_supplied=False,confidence_calibrated=False,raw_arrays_retained=False,
            gravity_anchor_source='first_training_receiver_height',scientific_decision='abstain')
        require_scope(value)
        for key,other in [('original_reads',1),('true_initial_state_supplied',True),
                ('true_calibration_supplied',True),('gravity_anchor_source','true_height'),('confidence_calibrated',True)]:
            with self.assertRaises(ValueError):require_scope(dict(value,**{key:other}))
