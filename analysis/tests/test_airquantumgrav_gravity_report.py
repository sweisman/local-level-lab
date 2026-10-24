# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import tempfile
import unittest
from pathlib import Path


class TestReport(unittest.TestCase):
    def test_gravity_reporting_rejects_open_study_before_numerical_imports(self):
        import sys
        module=importlib.import_module('lll.airquantumgrav_gravity_report');before=set(sys.modules)
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaisesRegex(ValueError,'closed study'):module.inspect(Path(name),'data/open')
        self.assertFalse(any(n=='numpy' or n.startswith('numpy.') for n in set(sys.modules)-before))

    def test_known_correction_controls_cannot_claim_observed_or_training_qualification(self):
        from lll.airquantumgrav_gravity_report import require_scope
        base=dict(known_corrections_supplied_not_estimated=True,original_reads=0,protected_reads=0,
            observed_starts=0,confidence_calibrated=False,scientific_decision='abstain')
        require_scope(base)
        for key,value in [('known_corrections_supplied_not_estimated',False),('original_reads',1),
                ('protected_reads',1),('observed_starts',1),('confidence_calibrated',True),('scientific_decision','support')]:
            with self.assertRaises(ValueError):require_scope(dict(base,**{key:value}))
