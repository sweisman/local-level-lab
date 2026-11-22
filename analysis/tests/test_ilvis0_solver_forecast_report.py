"""The generated forecast report accounts for every frozen fit."""

import pytest
import numpy as np

from lll import ilvis0_solver_forecast_report as report
from lll.ilvis0_solver_forecast_study import tasks


def _cases():
    return [dict(identity=task['identity'],**task['payload'],
                 converged=True,training_cost=.01,known_cost=.01,
                 later_truth_maximum_error_m=.02,
                 metric=[6371000.,6371000.,1.],
                 later_path=[[0.,0.,0.]]*8) for task in tasks()]


def test_six_fixture_gate_requires_all_twenty_four_fits():
    cases=_cases()
    value=report.summarize(cases)
    assert value['tasks']==24
    assert value['passing_fixtures']==6
    assert value['passed']
    cases[0]['converged']=False
    assert not report.summarize(cases)['passed']
    with pytest.raises(ValueError):
        report.summarize(cases[:-1])


def test_path_disagreement_fails_its_fixture_without_hiding_other_five():
    cases=_cases()
    cases[0]['later_path']=[[0.,0.,.11]]*8
    value=report.summarize(cases)
    assert value['passing_fixtures']==5
    assert value['scientific_decision']=='abstain'


def test_public_result_does_not_round_small_path_spreads_to_zero():
    cases=_cases()
    cases[0]['later_path']=[[0.,0.,2e-7]]*8
    text=report.render(report.summarize(cases))
    assert '2e-07 m' in text
    assert '0.0000 m' not in text


def test_report_checks_saved_later_error_against_generated_truth():
    fixture=dict(gps=np.zeros((24,3)),metric=np.array([2.,3.,1.]))
    case=dict(later_path=[[0.,0.,.02]]*8,metric=[2.,3.,1.],
              later_truth_maximum_error_m=.02)
    report.verify_saved_truth(case,fixture)
    case['later_truth_maximum_error_m']=.03
    with pytest.raises(ValueError,match='later truth score'):
        report.verify_saved_truth(case,fixture)
