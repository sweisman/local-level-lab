"""Nominal-clock publication distinguishes solver and physical gates."""

import numpy as np
import pytest

from lll import ilvis0_nominal_solver_report as report
from lll.ilvis0_nominal_solver_study import tasks


def _cases():
    return [dict(identity=task['identity'],**task['payload'],
                 converged=True,physical_accuracy_passed=True,
                 training_cost=1.,prediction_horizontal_rms_m=.4,
                 prediction_vertical_rms_m=1.2,
                 forecast=np.zeros((59,3)).tolist()) for task in tasks()]


def test_exact_twenty_four_results_and_six_agreement_gates():
    value=report.summarize(_cases())
    assert value['passing_fixtures']==6
    assert value['numerical_stops']==24
    assert value['scientific_decision']=='abstain'
    assert value['maximum_later_horizontal_rms_m']==.4
    with pytest.raises(ValueError):
        report.summarize(_cases()[:-1])


def test_agreement_and_physical_accuracy_are_separate():
    cases=_cases()
    cases[0]['physical_accuracy_passed']=False
    cases[0]['forecast']=(np.zeros((59,3))+[0.,0.,.11]).tolist()
    value=report.summarize(cases)
    assert value['physical_accuracy_passes']==23
    assert value['passing_fixtures']==5
    text=report.render(value)
    assert 'exact 200 Hz' in text
    assert 'distinct noise seeds' in text
    assert 'irregular packet' in text
