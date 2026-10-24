# SPDX-License-Identifier: AGPL-3.0-or-later
"""Complete short native noisy protocol; no observed or protected inputs."""
import pytest
from test_native_structured_training import training_kernels,native_training_case,sources


def definition():
    limits={'builds':dict(builds=2)}
    for law in ('increment','point'):
        for model in (0,1,2):
            for profile in (False,True):
                limits[f'{law}:{model}:{int(profile)}:1']=dict(native_calls=1000,packet_steps=10000,
                    packet_query_visits=30000,constructed_intervals=600,generated_samples=616,
                    noise_normal_variates=10848 if law=='increment' else 7254)
    return dict(allowances=limits,maximum_wall_s=300,additional_sources=[
        'analysis/tests/test_noisy_native_protocol.py','analysis/tests/test_physical_prediction_target.py',
        'analysis/tests/test_native_error_extension.py','analysis/tests/test_source_specific_noisy_inputs.py',
        'analysis/tests/test_linear_rate_noise_inputs.py','analysis/tests/test_generated_prediction.py',
        'analysis/tests/test_joint_state_space_covariance.py','analysis/tests/test_receiver_noise_states.py',
        'analysis/lll/generated_prediction.py','analysis/lll/airquantumgrav_noisy_inputs.py',
        'analysis/lll/structured_noisy_training.py','analysis/lll/structured_noisy_report.py',
        'docs/integrated-noise-covariance/NONLINEAR_PLAN.md',
        'docs/integrated-noise-covariance/NATIVE_PROTOCOL_PLAN.md'])


@pytest.mark.parametrize('training_kernels',[pytest.param(definition(),id='short-noisy-v1')],indirect=True)
@pytest.mark.parametrize('law',['increment','point'])
@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('height',[True])
def test_complete_short_native_noisy_protocol(native_training_case,law,model,profile,height):
    import numpy as np
    from lll.structured_noisy_training import recipe,calculate
    from lll.structured_noisy_report import check_case
    from lll.ilvis0_exploratory import MODELS
    from lll.ilvis0_wide_tangent import load
    k=native_training_case
    r=dict(recipe(),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2,
        maximum_evaluations=8)
    spec=dict(law=law,model=MODELS[model],latitude_deg=55.,profile=profile,start=0,policy_id='reported-short-v1')
    cut=6;saved={};events=[];native_work=[]
    def save(name,value):saved[name]=value;events.append(name)
    def factory(height):
        tangent,meta=load(k['directory'],gravity_anchor_height_m=height,
            expected_source_sha256=k['hashes']['analysis/lll/ilvis0_tangent.cpp'])
        return None,tangent,dict(tangent=meta)
    def charge(**work):
        assert work['native_calls']==1
        visits=work['packet_visits']
        if visits==1:steps=1
        elif visits==600*9:steps=600
        elif visits==saved['input-binding.json']['training_prefix_packets']*cut:
            steps=saved['input-binding.json']['training_prefix_packets']
        else:raise ValueError('undeclared native protocol work shape')
        k['reserve'](native_calls=1,packet_steps=steps,packet_query_visits=visits)
        native_work.append(work)
    result=calculate(spec,r,kernel_factory=factory,noise_kernel=k['kernel'],
        reserve=charge,reserve_construction=k['reserve'],save=save,check_continue=lambda:None)
    checked=check_case(spec,result,saved,r=r)
    assert checked['native_calls']==result['native_calls']
    import copy
    for field in ('target','counts','normalization'):
        altered=copy.deepcopy(saved)
        if field=='target':altered['forecast-error-diagnostic.json']['prediction_target']='receiver_measurement'
        elif field=='counts':altered['native-operation-summary.json']['bridge_calls']+=1
        else:altered['fit.json']['gaussian_training_score']['log_determinant']+=1.
        with pytest.raises(ValueError):check_case(spec,result,altered,r=r)
    assert result['native_calls']==len(native_work)<=1000
    assert result['evaluations']<=8 and len(saved['fit.json']['active_parameters'])==26+int(profile)
    assert saved['fit.json']['gaussian_training_score']['row_count']==3*cut
    assert events.index('forecast.json')<events.index('forecast-error-diagnostic.json')<events.index('scoring-observations.json')
    errors=saved['forecast-error-diagnostic.json']
    assert errors['prediction_target']=='physical_position' and errors['later_observations_used'] is False
    assert errors['error_operator']['later_receiver_fields_used'] is False
    assert errors['error_operator']['receiver_observation_epochs']==cut
    assert errors['confidence_calibrated'] is False
    assert errors['linear_calibration']['status'] in ('estimable','unidentifiable',
        'active_bounds_unsupported','linear_step_outside_bounds')
    assert saved['conditional-scores.json']['primary_raw_forecast_unchanged'] is True
    assert result['true_initial_state_supplied'] is False and result['true_calibration_supplied'] is False
    assert result['original_reads']==result['protected_reads']==result['observed_starts']==0
    k['results'].append(dict(kind='short_native_protocol',law=law,model=MODELS[model],profile=profile,
        columns=26+int(profile),evaluations=result['evaluations'],native_calls=result['native_calls'],
        converged=result['converged'],raw_accuracy=result['accuracy_all_sections'],
        raw_prediction=result['prediction'],conditional_prediction=result['conditional_prediction'],
        linear_status=result['linear_calibration_status'],prediction_target='physical_position',
        software_checks_passed=True,scientific_decision='abstain'))
