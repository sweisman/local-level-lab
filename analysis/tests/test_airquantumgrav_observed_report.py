# SPDX-License-Identifier: AGPL-3.0-or-later
"""Report-decision checks without numerical-library imports or observed data."""
import importlib
import unittest


MODELS=['sphere_rotating','sphere_still','flat_still']


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_observed_report') is not None,'observed ESA saved-result audit missing'
    return importlib.import_module('lll.airquantumgrav_observed_report')


def row(model,start=0,*,cost=1.,future=1.,converged=True,adequate=True):
    return dict(identity=f'{model}-{start}',model=model,profile=False,policy_id='short',start=start,
        complete=True,passed=converged,converged=converged,training_cost=cost,
        prediction=dict(total_rms_m=future,accuracy=dict(passed=adequate)),
        training=dict(accuracy=dict(passed=adequate)),accuracy_all_sections=adequate)


def recipe():return dict(models=MODELS,profiles=[False],policies=['short'],starts=2)


class TestObservedSelection(unittest.TestCase):
    def test_start_selection_uses_training_cost_even_when_prediction_is_worse(self):
        rows=[row(MODELS[0],cost=1.,future=100.),row(MODELS[0],1,cost=2.,future=.1)]
        report=library().summarize_starts(rows,recipe())
        self.assertEqual(report['primaries'][0]['primary']['start'],0)

    def test_exact_ties_retain_first_declared_start(self):
        rows=[row(MODELS[0],1,cost=1.),row(MODELS[0],0,cost=1.)]
        report=library().summarize_starts(rows,recipe())
        self.assertEqual(report['primaries'][0]['primary']['start'],0)

    def test_failed_fit_cannot_become_primary_through_good_prediction(self):
        rows=[row(MODELS[0],cost=0.,future=0.,converged=False),row(MODELS[0],1,cost=10.,future=10.)]
        report=library().summarize_starts(rows,recipe())
        self.assertEqual(report['primaries'][0]['primary']['start'],1)

    def test_best_training_fit_with_failed_forecast_cannot_be_replaced(self):
        failed=row(MODELS[0],cost=.5,future=0.,converged=False)
        failed.update(complete=False,training_fit_converged=True)
        rows=[failed,row(MODELS[0],1,cost=1.,future=.1)]
        report=library().summarize_starts(rows,recipe());group=report['primaries'][0]
        self.assertIsNone(group['primary'])
        self.assertEqual(group['selected_training_start'],0)
        self.assertFalse(report['comparisons'][0]['complete'])

    def test_missing_model_withholds_both_shape_and_field(self):
        report=library().summarize_starts([row(MODELS[0]),row(MODELS[1])],recipe())
        case=report['comparisons'][0]
        self.assertFalse(case['complete']);self.assertIsNone(case['shape_lower_error_family'])
        self.assertIsNone(case['field_lower_error_model'])

    def test_inaccurate_globe_can_have_lower_error_without_positive_field_result(self):
        rows=[row(MODELS[0],future=10.,adequate=False),row(MODELS[1],future=20.,adequate=False),row(MODELS[2],future=30.)]
        case=library().summarize_starts(rows,recipe())['comparisons'][0]
        self.assertTrue(case['complete']);self.assertEqual(case['shape_lower_error_family'],'globe')
        self.assertFalse(case['preferred_accuracy']);self.assertIsNone(case['field_lower_error_model'])

    def test_adequate_disc_preference_does_not_trigger_field_comparison(self):
        rows=[row(MODELS[0],future=10.),row(MODELS[1],future=20.),row(MODELS[2],future=1.)]
        case=library().summarize_starts(rows,recipe())['comparisons'][0]
        self.assertEqual(case['shape_lower_error_family'],'disc');self.assertIsNone(case['field_lower_error_model'])

    def test_field_comparison_follows_complete_adequate_globe_result(self):
        rows=[row(MODELS[0],future=1.),row(MODELS[1],future=2.),row(MODELS[2],future=30.)]
        case=library().summarize_starts(rows,recipe())['comparisons'][0]
        self.assertEqual(case['shape_lower_error_family'],'globe');self.assertTrue(case['preferred_accuracy'])
        self.assertEqual(case['field_lower_error_model'],'specified_field')

    def test_shape_stage_profiles_both_globe_candidates(self):
        rows=[row(MODELS[0],future=30.),row(MODELS[1],future=1.),row(MODELS[2],future=2.)]
        case=library().summarize_starts(rows,recipe())['comparisons'][0]
        self.assertEqual(case['shape_lower_error_family'],'globe');self.assertEqual(case['field_lower_error_model'],'zero_field')

    def test_unknown_or_duplicate_start_is_rejected(self):
        value=row(MODELS[0])
        with self.assertRaises(ValueError):library().summarize_starts([value,value],recipe())
        with self.assertRaises(ValueError):library().summarize_starts([dict(value,start=2)],recipe())

    def test_open_study_cannot_be_audited_or_import_numerical_engines(self):
        import sys
        import tempfile
        from pathlib import Path
        before=set(sys.modules)
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaisesRegex(ValueError,'closed study required'):
                library().inspect(Path(name),'data/unfinished')
        self.assertFalse(any(name=='numpy' or name.startswith('numpy.') for name in set(sys.modules)-before))

    def test_audit_rejects_changed_python_or_numerical_packages(self):
        qualified=dict(python='3.14.0',packages=dict(numpy='2.3.0',scipy='1.16.0'))
        for changed in [dict(qualified,python='3.14.1'),dict(qualified,packages=dict(numpy='2.3.1',scipy='1.16.0'))]:
            with self.assertRaises(ValueError):library().verify_audit_environment(qualified,changed)
        library().verify_audit_environment(qualified,dict(qualified,platform='another recorded platform'))
