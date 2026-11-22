"""The longer independent-method report preserves disagreements and failures."""

import numpy as np
import pytest
from types import SimpleNamespace

from lll import ilvis0_long_independent_solver_report as report
from lll.ilvis0_long_independent_solver_study import tasks


def _cases():
    return [dict(identity=task['identity'],**task['payload'],
                 converged=True,physical_accuracy_passed=True,
                 training_cost=20.,prediction_horizontal_rms_m=.5,
                 prediction_vertical_rms_m=1.,
                 forecast=np.zeros((119,3)).tolist()) for task in tasks()]


def test_long_independent_method_matrix_reports_six_fixture_gates():
    value=report.summarize(_cases())
    assert value['passing_fixtures']==6
    assert value['numerical_stops']==24
    assert value['scientific_decision']=='abstain'
    assert 'SciPy TRF' in report.render(value)


def test_one_long_method_disagreement_fails_its_fixture():
    cases=_cases()
    cases[0]['forecast']=(np.zeros((119,3))+[0.,0.,.11]).tolist()
    value=report.summarize(cases)
    assert value['passing_fixtures']==5
    assert value['fixture_rows'][0]['maximum_later_path_spread_m']>.1


def test_recovery_uses_completed_tasks_once_and_ignores_interrupted_charges():
    expected={name:{'payload':{'model':'globe'}} for name in ('saved','lost')}
    original=SimpleNamespace(tasks=expected,
        rows={'saved':{'status':'complete'},'lost':{'status':'interrupted'}})
    recovery=SimpleNamespace(tasks={'lost':expected['lost']},
        rows={'lost':{'status':'complete'}})
    selected=report.select_completed([original,recovery],expected)
    assert selected=={'saved':original,'lost':recovery}
    with pytest.raises(ValueError,match='duplicate completed'):
        report.select_completed([original,recovery,recovery],expected)
    with pytest.raises(ValueError,match='all original'):
        report.select_completed([original],expected)
