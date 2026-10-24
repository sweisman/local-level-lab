# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('structured,diagnostic_target',[(False,None),(True,None),
    (True,'physical_position'),(True,'receiver_measurement')])
def test_generated_prediction_initializes_from_noisy_rows_and_scores_after_saved_forecast(profile,structured,diagnostic_target):
    import copy
    import numpy as np
    from lll.generated_prediction import calculate
    from lll.airquantumgrav_noisy_inputs import construct,noise_settings
    from lll.airquantumgrav_height_training import recipe
    from lll.airquantumgrav_truth import A
    spec=dict(model='sphere_rotating',latitude_deg=55.,profile=profile,start=0,policy_id='reported-short-v1')
    r=dict(recipe(),duration_s=40.,queries=39,noise=noise_settings())
    material=construct(spec,r,reserve=lambda **kwargs:None);before=copy.deepcopy(material['training_rows'])
    count=len(material['times']);active=[f'p{i}' for i in range(26+int(profile))]
    coordinates=np.zeros((count,3));saved={};events=[];received=[];truth_calls=[]
    def save(name,value):saved[name]=copy.deepcopy(value);events.append(name)
    def kernel_factory(anchor):
        assert anchor==before[0]['height_m']
        return None,None,dict(anchor=anchor)
    error_provider=object()
    def fit(**kwargs):
        assert 'truth' not in kwargs and kwargs['training_rows']==before
        if structured:
            assert kwargs['training_error_factory'] is error_provider
            for _ in range(7):kwargs['reserve'](native_calls=1,packet_visits=10)
        else:assert 'training_error_factory' not in kwargs
        assert len(kwargs['training_rows'])==material['training_epochs']
        received.append(kwargs['training_rows'])
        kwargs['save']('fit.json',dict(fixed=True))
        kwargs['save']('forecast.json',dict(coordinates=coordinates.tolist()))
        result=dict(fit=dict(converged=True,evaluations=1,residual_sum_squares=4.,active_parameters=active),
            forecast=dict(coordinates=coordinates,jacobian=np.zeros((count*3,len(active))),active_parameters=active),
            all_columns_retained=True,true_initial_state_supplied=False,true_calibration_supplied=False)
        if diagnostic_target:
            assert kwargs['forecast_error_diagnostic'] is error_provider
            result['forecast_error_diagnostic']=dict(prediction_target=diagnostic_target,
                fixed_parameters=dict(mean=coordinates[material['training_epochs']:]),
                linear_calibration=dict(status='active_bounds_unsupported'))
            kwargs['save']('forecast-error-diagnostic.json',{'preserved':True})
        return result
    def truth(times):
        truth_calls.append(True)
        assert 'forecast.json' in saved
        return dict(coordinates=coordinates,position_world_m=np.tile([A,0.,0.],(count,1)),
            body_axes_world=np.tile(np.eye(3),(count,1,1)),attitude_body_to_local=np.tile(np.eye(3),(count,1,1)))
    def run():return calculate(spec,r,material=material,train_and_forecast=fit,kernel_factory=kernel_factory,
        reserve=lambda **kwargs:None,reserve_construction=lambda **kwargs:None,save=save,truth=truth,
        check_continue=lambda:None,**(dict(training_error_factory=error_provider) if structured else {}),
        **(dict(forecast_error_diagnostic=error_provider) if diagnostic_target else {}))
    if diagnostic_target=='receiver_measurement':
        with pytest.raises(ValueError,match='physical-position'):run()
        assert not truth_calls
        return
    result=run()
    assert result['passed'] and result['accuracy_all_sections'] and result['all_columns_retained']
    assert result['score_reference']=='generated noiseless physical truth' and not result['confidence_calibrated']
    assert events.index('forecast.json')<events.index('scoring-observations.json')<events.index('scores.json')
    assert material['training_rows']==before
    assert received==[before] and saved['input-binding.json']['noise']['gravity_anchor_height_m']==before[0]['height_m']
    assert result['native_calls']==(7 if structured else 2)
    if diagnostic_target:
        assert events.index('forecast-error-diagnostic.json')<events.index('scoring-observations.json')
        assert result['conditional_prediction']['accuracy']['passed'] is True
        assert result['linear_calibration_status']=='active_bounds_unsupported'


def test_generated_prediction_rejects_a_provider_that_does_not_save_forecast_before_scoring():
    from lll.generated_prediction import calculate
    from lll.airquantumgrav_noisy_inputs import construct,noise_settings
    from lll.airquantumgrav_height_training import recipe
    spec=dict(model='sphere_rotating',latitude_deg=55.,profile=False,start=0,policy_id='reported-short-v1')
    r=dict(recipe(),duration_s=40.,queries=39,noise=noise_settings())
    material=construct(spec,r,reserve=lambda **kwargs:None)
    def forbidden_truth(times):raise AssertionError('later truth opened prematurely')
    with pytest.raises(ValueError,match='saved forecast'):
        calculate(spec,r,material=material,train_and_forecast=lambda **kwargs:{},
            kernel_factory=lambda anchor:(None,None,{}),reserve=lambda **kwargs:None,
            reserve_construction=lambda **kwargs:None,save=lambda *args:None,truth=forbidden_truth,check_continue=lambda:None)
