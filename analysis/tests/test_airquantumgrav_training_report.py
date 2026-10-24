# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only training report controls; no numerical imports or propagation."""
import copy
import importlib.util
import math

import pytest


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_training_report') is not None, 'saved-only training auditor is missing'
    return __import__('lll.airquantumgrav_training_report',fromlist=['case_gate'])


@pytest.mark.parametrize('model',['sphere_rotating','sphere_still','flat_still'])
def test_saved_position_errors_use_generating_cartesian_geometry_and_neu_sign(model):
    a=6378137.;r=6371000.;e2=(1/298.257223563)*(2-1/298.257223563)
    if model=='flat_still':
        point=[r*math.pi/2+1.,-2.,100.];axes=[[-1.,0.,0.],[0.,1.,0.],[0.,0.,-1.]];rotation=[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]
    else:
        point=[a+100.,-2.,-1.];axes=[[0.,0.,-1.],[1.,0.,0.],[0.,-1.,0.]];rotation=[[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]]
    answer=dict(position_world_m=[point],body_axes_world=[axes],attitude_body_to_local=[rotation])
    error=library().saved_position_errors([[0.,0.,103.]],answer,model=model,constants=dict(A=a,E2=e2,DISC_RADIUS=r))
    assert error==[[1.,2.,3.]]


def fixture():
    names=[n+'_'+a for n in ('attitude','velocity','position','gyro_bias','accel_bias','gyro_gain','accel_gain','lever') for a in 'xyz']
    names+=['gravity_delta','time_offset']
    training=dict(rms_neu_m=[.01,.02,.03],horizontal_rms_m=math.sqrt(.0005),vertical_rms_m=.03,
        total_rms_m=math.sqrt(.0014),maximum_3d_m=math.sqrt(.0014))
    prediction=dict(rms_neu_m=[.04,.05,.06],horizontal_rms_m=math.sqrt(.0041),vertical_rms_m=.06,
        total_rms_m=math.sqrt(.0077),maximum_3d_m=math.sqrt(.0077))
    accuracy={name:dict(horizontal_rms_m=True,vertical_rms_m=True,maximum_3d_m=True) for name in ('training','prediction')}
    result=dict(passed=True,profile=False,converged=True,evaluations=12,training_cost=.03,
        training_epochs=2,prediction_epochs=1,training=training,prediction=prediction,accuracy=accuracy,
        all_columns_retained=True,true_initial_state_supplied=False,true_calibration_supplied=False,
        forecast_saved_before_scoring=True)
    fit=dict(converged=True,evaluations=12,residual_sum_squares=.03,active_parameters=names,normalized_parameters=[0.]*26)
    forecast=dict(coordinates=[[0.,0.,100.]]*3,active_parameters=names,training_epochs=2,prediction_epochs=1,
        continuous_propagation_without_gps_reset=True,prediction_receiver_positions_used=False)
    scores=dict(training=training,prediction=prediction,errors_neu_m=[[.01,.02,.03],[.01,.02,.03],[.04,.05,.06]],
        training_positions_reproduced_for_scoring=True)
    recipe=dict(queries=3,maximum_evaluations=200,accuracy=dict(horizontal_rms_m=.1,vertical_rms_m=.1,maximum_3d_m=.5))
    return result,fit,forecast,scores,recipe


def test_saved_training_audit_reconciles_fit_labels_and_both_error_sections():
    assert library().case_gate(*fixture())['passed']


def test_small_prediction_error_does_not_relabel_an_unconverged_fit():
    result,fit,forecast,scores,recipe=fixture()
    result['converged']=False;fit['converged']=False;result['passed']=False
    assert not library().case_gate(result,fit,forecast,scores,recipe)['passed']


@pytest.mark.parametrize('fault',['cost','columns','error','count','gate','supplied_truth','reused_positions'])
def test_saved_training_audit_rejects_changed_binding_or_qualification_labels(fault):
    result,fit,forecast,scores,recipe=copy.deepcopy(fixture())
    if fault=='cost':fit['residual_sum_squares']=.02
    elif fault=='columns':forecast['active_parameters'].pop()
    elif fault=='error':scores['errors_neu_m'][0][0]=100.
    elif fault=='count':result['evaluations']=13
    elif fault=='gate':result['accuracy']['prediction']['horizontal_rms_m']=False
    elif fault=='supplied_truth':result['true_initial_state_supplied']=True
    else:scores['training_positions_reproduced_for_scoring']=False
    with pytest.raises(ValueError):library().case_gate(result,fit,forecast,scores,recipe)
