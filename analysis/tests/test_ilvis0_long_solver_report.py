"""Long-horizon confirmation keeps numerical and physical gates distinct."""

import numpy as np
import pytest

from lll import ilvis0_long_solver_report as report
from lll.ilvis0_long_solver_study import tasks


def _cases():
    return [dict(identity=task['identity'],**task['payload'],
                 converged=True,physical_accuracy_passed=True,
                 training_cost=94.,prediction_horizontal_rms_m=.7,
                 prediction_vertical_rms_m=2.,
                 forecast=np.zeros((119,3)).tolist()) for task in tasks()]


def test_exact_six_four_fit_gates_and_holdout_metadata():
    value=report.summarize(_cases())
    assert value['passing_fixtures']==6
    assert value['numerical_stops']==24
    assert value['maximum_later_horizontal_rms_m']==.7
    assert value['scientific_decision']=='abstain'
    with pytest.raises(ValueError):
        report.summarize(_cases()[:-1])


def test_cost_and_path_agreement_fail_independently_of_physical_screen():
    cases=_cases()
    cases[0]['training_cost']+=.02
    cases[1]['forecast']=(np.zeros((119,3))+[0.,0.,.11]).tolist()
    cases[2]['physical_accuracy_passed']=False
    value=report.summarize(cases)
    assert value['passing_fixtures']==5
    assert value['physical_accuracy_passes']==23
    assert value['fixture_rows'][0]['maximum_training_cost_range']>.01
    assert value['fixture_rows'][0]['maximum_later_path_spread_m']>.1
    assert '79 earlier' in report.render(value)
