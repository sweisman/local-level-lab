# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import inspect
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestDefinition(unittest.TestCase):
    def test_resolution_matrix_has_24_fixed_points_and_separate_finite_allowance(self):
        m=importlib.import_module('lll.airquantumgrav_resolution');r=m.recipe();tasks=m.tasks()
        self.assertEqual(len(tasks),24);self.assertEqual(len({v['identity'] for v in tasks}),24)
        self.assertEqual(sum(v['limits']['native_calls'] for v in tasks),240)
        self.assertEqual(sum(v['limits']['packet_visits'] for v in tasks),46054464000)
        self.assertEqual((r['workers'],r['threads'],r['maximum_wall_s']),(4,1,3600.))
        self.assertEqual(r['optimizer_starts'],0)

    def test_resolution_prepare_requires_tests_before_any_inputs(self):
        m=importlib.import_module('lll.airquantumgrav_resolution')
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError,'qualification'):m.prepare(root,qualification=None)
            self.assertFalse((Path(root)/'data').exists())

    def test_resolution_prepare_rejects_unguarded_environment_before_source_reads(self):
        m=importlib.import_module('lll.airquantumgrav_resolution')
        with tempfile.TemporaryDirectory() as root,patch.object(m,'environment',return_value=dict(numerical_environment={})):
            with self.assertRaisesRegex(ValueError,'thread environment'):m.prepare(root,qualification='missing')
            self.assertFalse((Path(root)/'data').exists())

    def test_resolution_interface_has_no_later_position_or_forecast_callback(self):
        m=importlib.import_module('lll.airquantumgrav_resolution')
        self.assertFalse({'scoring','scoring_rows','later_rows','open_scoring','forecast'}&set(inspect.signature(m.calculate).parameters))
        self.assertEqual(m.MEASUREMENT_KEYS,('interval','training','layout','working-errors'))
