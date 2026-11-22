"""Saved four-task numerical and physical accounting."""

import numpy as np
import pytest

from lll import ilvis0_fullcal_solver_report as report


def _cases():
    return [dict(identity=f'{solver}-{start}',solver=solver,start=start,
                 converged=True,physical_accuracy_passed=False,
                 training_cost=.1,prediction_horizontal_rms_m=.32,
                 prediction_vertical_rms_m=1.31,
                 forecast=np.zeros((59,3)).tolist())
            for solver in ('near_zero','trust_v2') for start in (0,1)]


def test_report_keeps_technical_numerical_and_physical_status_separate():
    value=report.compare(_cases())
    assert value['tasks']==4
    assert value['numerical_stops']==4
    assert value['physical_accuracy_passes']==0
    assert value['maximum_later_path_spread_m']==0.
    assert value['scientific_decision']=='abstain'


def test_missing_fit_or_task_cannot_be_reported_as_agreement():
    cases=_cases()
    with pytest.raises(ValueError):
        report.compare(cases[:3])
    cases[0]['technical_error']='saved failure'
    value=report.compare(cases)
    assert value['technical_failures']==1
    assert value['maximum_later_path_spread_m'] is None


def test_later_path_spread_is_in_metres():
    cases=_cases()
    cases[-1]['forecast']=(np.zeros((59,3))+np.array([0.,0.,2.])).tolist()
    assert report.compare(cases)['maximum_later_path_spread_m']==2.


def test_report_separates_solver_spread_from_later_truth_error():
    text=report.render(report.compare(_cases()))
    assert '0.32 m' in text
    assert '1.31 m' in text
    assert 'solver agreement is not aircraft accuracy' in text
