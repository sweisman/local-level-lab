"""Observed method report keeps numerical and physical outcomes separate."""

import numpy as np
import pytest
from types import SimpleNamespace

from lll import ilvis0_observed_method_report as report
from lll.ilvis0_observed_method_pilot import tasks


def _layouts():
    from lll.ilvis0_observed_method_pilot import SEGMENTS
    return [dict(segment_id=segment,receiver_epochs=243,
                 training_epochs=162,native_packets=49000)
            for segment in SEGMENTS]


def _cases():
    return [dict(identity=task['identity'],**task['payload'],
                 converged=True,training_cost=20.,
                 prediction_horizontal_rms_m=1.,
                 prediction_vertical_rms_m=2.,
                 training_epochs=81 if task['payload']['origin']=='inner' else 162,
                 prediction_epochs=81,
                 forecast=np.zeros((162 if task['payload']['origin']=='inner'
                                    else 243,3)).tolist())
            for task in tasks(_layouts())]


def test_six_cuts_report_method_agreement_without_detections():
    value=report.summarize(_cases(),_layouts())
    assert value['cuts']==6
    assert value['numerical_stops']==24
    assert value['method_agreement_within_diagnostic_scale']==6
    assert value['scientific_decision']=='abstain'


def test_missing_or_disagreeing_method_is_visible():
    cases=_cases()
    cases[0]['forecast']=(np.asarray(cases[0]['forecast'])+[0,0,.11]).tolist()
    value=report.summarize(cases,_layouts())
    assert value['method_agreement_within_diagnostic_scale']==5
    assert cases[0]['identity'] in value['cut_rows'][0]['largest_path_pair']
    with pytest.raises(ValueError,match='exact observed method identities'):
        report.summarize(cases[:-1],_layouts())


def test_calibration_and_separate_axis_errors_reach_detail_csv():
    cases=_cases()
    cases[0].update(parameters={'gyro_bias_z':.01},active_bounds=['gyro_bias_z'],
                    prediction_north_rms_m=.8,prediction_east_rms_m=.6)
    value=report.summarize(cases,_layouts())
    text=report.csv_bytes(value).decode()
    assert 'calibration_gyro_bias_z' in text.splitlines()[0]
    assert 'prediction_north_rms_m' in text.splitlines()[0]
    assert 'termination' in text.splitlines()[0]
    assert 'probe_reason' in text.splitlines()[0]
    assert 'probe_actual_cost_change' in text.splitlines()[0]
    assert 'gyro_bias_z' in text.splitlines()[1]


def test_nonstopping_reason_is_separate_from_method_agreement():
    cases=_cases()
    cases[0]['converged']=False
    cases[0]['probe_reason']='fresh_position_probe_not_stable'
    value=report.summarize(cases,_layouts())
    assert value['numerical_stops']==23
    assert value['nonstopping_reasons']=={'fresh_position_probe_not_stable':1}
    assert value['method_agreement_within_diagnostic_scale']==6


def test_recovery_selects_completed_fits_once_and_ignores_interruption():
    expected={name:{'payload':{'model':'sphere_rotating'}}
              for name in ('saved','lost')}
    parent=SimpleNamespace(tasks=expected,
        rows={'saved':{'status':'complete'},'lost':{'status':'interrupted'}})
    stage=SimpleNamespace(tasks={'lost':expected['lost']},
        rows={'lost':{'status':'complete'}})
    assert report.select_completed([parent,stage],expected)=={
        'saved':parent,'lost':stage}
    with pytest.raises(ValueError,match='duplicate completed'):
        report.select_completed([parent,stage,stage],expected)
    with pytest.raises(ValueError,match='all observed'):
        report.select_completed([parent],expected)
