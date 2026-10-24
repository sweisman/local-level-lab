# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import tempfile
import unittest
from pathlib import Path


class TestDefinition(unittest.TestCase):
    def test_observed_height_binds_selector_to_published_baseline_report(self):
        module=importlib.import_module('lll.airquantumgrav_observed_height')
        completion=dict(manifest_sha256='m',summary_sha256='s')
        report=dict(verified=True,total=24,manifest_sha256='m',summary_sha256='s',
            primary_selector_source_sha256='published-selector',numerically_converged=15)
        module.verify_baseline(report,completion,selector_sha256='published-selector')
        with self.assertRaises(ValueError):module.verify_baseline(report,completion,selector_sha256='changed')
        with self.assertRaises(ValueError):module.verify_baseline(dict(report,verified=False),completion,selector_sha256='published-selector')

    def test_observed_height_changes_only_declared_gravity_variant(self):
        module=importlib.import_module('lll.airquantumgrav_observed_height')
        from lll.airquantumgrav_observed import recipe,tasks
        old=recipe();new=module.recipe()
        self.assertEqual({k:v for k,v in new.items() if k not in ('gravity_model','gravity_anchor_source','version')},
            {k:v for k,v in old.items() if k!='version'})
        layout=dict(native_packets=360028,training_prefix_packets=239867,training_epochs=800,receiver_epochs=1200)
        self.assertEqual(module.tasks(layout),tasks(layout))
        self.assertEqual(sum(v['limits']['native_calls'] for v in module.tasks(layout)),4824)
        self.assertEqual(sum(v['limits']['packet_visits'] for v in module.tasks(layout)),931458086400)

    def test_observed_height_requires_qualification_before_reading_inputs(self):
        module=importlib.import_module('lll.airquantumgrav_observed_height')
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaisesRegex(ValueError,'qualification'):module.prepare(Path(name),qualification=None)
            self.assertFalse((Path(name)/'data').exists())

    def test_observed_height_rejects_verified_but_unqualified_parent(self):
        module=importlib.import_module('lll.airquantumgrav_observed_height')
        good=dict(verified=True,qualified=True,total=24,passed=24)
        module.require_qualification(good)
        for change in (dict(qualified=False),dict(passed=23),dict(total=25),dict(verified=False)):
            with self.assertRaises(ValueError):module.require_qualification(dict(good,**change))
