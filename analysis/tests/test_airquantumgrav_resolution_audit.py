# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import sys
import tempfile
import unittest


class TestReportingRevision(unittest.TestCase):
    def test_resolution_reporting_revision_rejects_open_before_any_override(self):
        m=importlib.import_module('lll.airquantumgrav_resolution_audit');before='numpy' in sys.modules
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises((ValueError,FileNotFoundError)):
                m.inspect(root,'data/not-closed',qualification=None)
        self.assertEqual('numpy' in sys.modules,before)
