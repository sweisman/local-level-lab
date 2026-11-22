"""Independent-method report must preserve disagreements and failures."""

import numpy as np

from lll import ilvis0_independent_solver_report as report
from lll.ilvis0_independent_solver_study import tasks


def _cases():
    return [dict(identity=task['identity'],**task['payload'],
                 converged=True,physical_accuracy_passed=True,
                 training_cost=20.,prediction_horizontal_rms_m=.5,
                 prediction_vertical_rms_m=1.,
                 forecast=np.zeros((59,3)).tolist()) for task in tasks()]


def test_independent_method_matrix_reports_six_fixture_gates():
    value=report.summarize(_cases())
    assert value['passing_fixtures']==6
    assert value['numerical_stops']==24
    assert value['scientific_decision']=='abstain'
    assert 'different bounded optimizer' in report.render(value)


def test_one_method_disagreement_fails_its_fixture():
    cases=_cases()
    cases[0]['forecast']=(np.zeros((59,3))+[0.,0.,.11]).tolist()
    value=report.summarize(cases)
    assert value['passing_fixtures']==5
    assert value['fixture_rows'][0]['maximum_later_path_spread_m']>.1
