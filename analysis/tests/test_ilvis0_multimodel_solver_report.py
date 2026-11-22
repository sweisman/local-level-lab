"""Six-fixture accounting retains every generated fit and failure."""

import numpy as np
import pytest

from lll import ilvis0_multimodel_solver_report as report
from lll.ilvis0_multimodel_solver_study import tasks


def _cases():
    return [dict(identity=task['identity'],**task['payload'],
                 converged=True,physical_accuracy_passed=True,
                 training_cost=1.,prediction_horizontal_rms_m=.5,
                 prediction_vertical_rms_m=2.,
                 forecast=np.zeros((59,3)).tolist()) for task in tasks()]


def test_six_fixture_gate_requires_all_twenty_four_solved_paths():
    cases=_cases()
    result=report.summarize(cases)
    assert result['tasks']==24
    assert result['passing_fixtures']==6
    assert result['numerical_stops']==24
    assert result['scientific_decision']=='abstain'
    with pytest.raises(ValueError):
        report.summarize(cases[:-1])


def test_one_solver_disagreement_fails_only_its_fixture():
    cases=_cases()
    cases[0]['forecast']=(np.zeros((59,3))+[0.,0.,.11]).tolist()
    result=report.summarize(cases)
    assert result['passing_fixtures']==5
    assert not result['passed']
    cases[0]['technical_error']='saved failure'
    result=report.summarize(cases)
    assert result['technical_failures']==1
    assert result['fixture_rows'][0]['maximum_later_path_spread_m'] is None


def test_report_shows_truth_errors_separately_from_solver_agreement():
    value=report.summarize(_cases())
    assert value['maximum_later_horizontal_rms_m']==.5
    assert value['maximum_later_height_rms_m']==2.
    text=report.render(value)
    assert '0.5 m horizontal' in text
    assert '2 m in height' in text
