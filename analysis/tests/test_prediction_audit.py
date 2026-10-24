# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cheap corruption controls for shared saved-fit evidence checks."""
import copy

import pytest


def fit():
    return dict(active_parameters=['a','b'],normalized_parameters=[0.,1.],evaluations=4,
        residual_sum_squares=2.,converged=False,message='Budget exhausted')


def test_saved_training_fit_retains_nonconvergence_and_every_column():
    from lll.prediction_audit import training_fit
    original=fit();saved=copy.deepcopy(original)
    row=training_fit(original,active=['a','b'],maximum_evaluations=8)
    assert original==saved
    assert not row['training_fit_converged']
    assert row['last_training_cost']==2. and row['stop_reason']=='Budget exhausted'
    assert row['normalized_parameters']==dict(a=0.,b=1.)


@pytest.mark.parametrize('change',[
    dict(active_parameters=['b','a']),dict(normalized_parameters=[0.]),
    dict(normalized_parameters=[0.,1.00001]),dict(normalized_parameters=[0.,float('nan')]),
    dict(evaluations=True),dict(evaluations=9),dict(residual_sum_squares=-1.),
    dict(residual_sum_squares=float('nan')),dict(converged='true')])
def test_saved_training_fit_rejects_corrupted_bounds_columns_cost_or_status(change):
    from lll.prediction_audit import training_fit
    with pytest.raises(ValueError):training_fit(dict(fit(),**change),active=['a','b'],maximum_evaluations=8)


def evidence():
    spec=dict(model='flat_still',profile=False,policy_id='test',start=0)
    current=dict(fit(),converged=True)
    result=dict(spec,passed=True,converged=True,evaluations=4,native_calls=5,training_cost=2.,
        all_columns_retained=True,training_epochs=2,prediction_epochs=1,forecast_saved_before_scoring=True,
        weight_configuration={'name':'test'},group_id='dev',original_reads=0,protected_reads=0)
    forecast=dict(active_parameters=['a','b'],times_s=[1.,2.,3.],training_epochs=2,prediction_epochs=1,
        continuous_propagation_without_gps_reset=True,prediction_receiver_positions_used=False)
    earlier=dict(times_s=[1.,2.],coordinates=[[0.,0.,0.],[0.,0.,0.]],training_epochs=2,prediction_epochs=1,
        native_prefix_packets=3,training_prefix_sha256={'theta':'x'},weight_configuration={'name':'test'},
        weight_descriptor={'kind':'test'},weight_source_sha256='weight',time_origin_gps_sow_s=0.,
        prediction_receiver_positions_used=False,true_initial_state_supplied=False,true_calibration_supplied=False)
    binding=dict(group_id='dev',layout={'test':1},input_sha256={'interval':'input'},original_reads=0,protected_reads=0)
    expected=dict(active=['a','b'],maximum_evaluations=8,times=[1.,2.,3.],cut=2,
        training_coordinates=earlier['coordinates'],prefix_packets=3,prefix_sha256={'theta':'x'},
        configuration={'name':'test'},descriptor={'kind':'test'},weight_sha256='weight',time_origin_s=0.,
        group='dev',layout={'test':1},input_sha256={'interval':'input'},packet_visits=4*3*2+5*3)
    return dict(spec=spec,result=result,fit=current,forecast=forecast,earlier=earlier,binding=binding,
        operations=dict(value=0,tangent=5,packet_visits=39),expected=expected)


def test_saved_prediction_checks_complete_independence_and_exact_native_accounting():
    from lll.prediction_audit import complete_prediction
    data=evidence();original=copy.deepcopy(data)
    checked=complete_prediction(**data)
    assert checked['training_fit_converged'] and data==original


@pytest.mark.parametrize('key,field,value',[
    ('operations','tangent',4),('operations','packet_visits',38),
    ('result','passed',False),('result','training_cost',3.),
    ('earlier','true_initial_state_supplied',True),('earlier','prediction_receiver_positions_used',True),
    ('earlier','times_s',[1.,2.1]),('earlier','weight_source_sha256','changed'),
    ('forecast','continuous_propagation_without_gps_reset',False),
    ('forecast','prediction_receiver_positions_used',True),('forecast','active_parameters',['a']),
    ('binding','input_sha256',{'interval':'changed'}),('result','protected_reads',1)])
def test_saved_prediction_rejects_leakage_mismatched_calls_and_changed_evidence(key,field,value):
    from lll.prediction_audit import complete_prediction
    data=evidence();data[key][field]=value
    with pytest.raises(ValueError):complete_prediction(**data)


def test_saved_start_sensitivity_is_descriptive_and_retains_failed_starts():
    from lll.prediction_audit import start_sensitivity
    rows=[dict(identity=str(i),model='flat_still',profile=False,policy_id='test',start=i,converged=i==0) for i in (0,1)]
    errors={'0':[[0.,0.,0.],[1.,2.,3.]],'1':[[3.,4.,0.],[4.,6.,3.]]}
    original=copy.deepcopy((rows,errors))
    report=start_sensitivity(rows,errors)
    assert report[0]['available'] and not report[0]['both_numerically_converged']
    assert report[0]['rms_neu_m']==[3.,4.,0.]
    assert not report[0]['calibrated_confidence_interval']
    assert (rows,errors)==original


def test_saved_start_sensitivity_keeps_incomplete_pairs_unavailable():
    from lll.prediction_audit import start_sensitivity
    rows=[dict(identity='0',model='flat_still',profile=False,policy_id='test',start=0,converged=True)]
    assert not start_sensitivity(rows,{'0':[[0.,0.,0.]]})[0]['available']


def test_saved_start_sensitivity_rejects_mismatched_queries_instead_of_truncating():
    from lll.prediction_audit import start_sensitivity
    rows=[dict(identity=str(i),model='flat_still',profile=False,policy_id='test',start=i,converged=True) for i in (0,1)]
    with pytest.raises(ValueError):start_sensitivity(rows,{'0':[[0.,0.,0.]],'1':[[0.,0.,0.],[0.,0.,0.]]})
