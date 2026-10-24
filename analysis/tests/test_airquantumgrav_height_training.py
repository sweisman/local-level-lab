# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import tempfile
import unittest
from pathlib import Path


class TestDefinition(unittest.TestCase):
    def test_height_training_freezes_separate_24_case_fit_allowance(self):
        m=importlib.import_module('lll.airquantumgrav_height_training');r=m.recipe();tasks=m.tasks()
        self.assertEqual(len(tasks),24);self.assertEqual(len({v['identity'] for v in tasks}),24)
        self.assertEqual(sum(t['limits']['native_calls'] for t in tasks),4824)
        self.assertEqual(sum(t['limits']['packet_visits'] for t in tasks),931411200000)
        self.assertEqual(m.prefix_limit(r),239855)
        self.assertEqual((r['workers'],r['threads'],r['maximum_wall_s']),(4,1,28800.))
        self.assertEqual({t['payload']['profile'] for t in tasks},{False,True})
        self.assertEqual({t['payload']['start'] for t in tasks},{0,1})
        self.assertEqual(len({t['payload']['policy_id'] for t in tasks}),2)
        self.assertEqual(m.construction_limits(r),dict(constructed_intervals=360000,generated_samples=362001))
        from lll.airquantumgrav_training_controls import recipe as original
        self.assertEqual(r['accuracy'],original()['accuracy'])

    def test_height_training_requires_qualification_before_any_files(self):
        m=importlib.import_module('lll.airquantumgrav_height_training')
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaisesRegex(ValueError,'qualification'):m.prepare(Path(name),qualification=None)
            self.assertFalse((Path(name)/'data').exists())
