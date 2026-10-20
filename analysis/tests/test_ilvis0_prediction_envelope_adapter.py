# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import ilvis0_prediction_envelope_adapter as adapter
from lll.ilvis0_bounded_prediction import known_scale
from lll.ilvis0_error_model import Spec


def fixture(p=4,two=False):
    train=np.arange(12,dtype=float);future=np.arange(12,16,dtype=float)
    spec=Spec(white=np.eye(3),components=((3.,np.eye(3)*.2),),drift=np.eye(3)*.1,drift_origin_s=0.,drift_span_s=16.)
    keys=('a','b') if two else ('a',)
    frame=adapter.Frame(origin=[1.,2.,3.],matrix=np.diag([2.,3.,4.]),source_id='fixed-software-chart')
    family=adapter.Family(train,future,{k:spec for k in keys},
        {k:known_scale(.2,source_id='shared-reference',covariance_id=k) for k in keys},
        frame=frame,parameter_names=tuple(f'p{i}' for i in range(p)),assessment_id='one-shared-assessment')
    rng=np.random.default_rng(20261019);jac=rng.normal(size=(48,p))
    if p==27:jac[:36,-3:]=0.
    base=rng.normal(size=48);center=np.full(p,.3);truth=np.full(p,-.2)
    prediction=(base+jac@center).reshape(-1,3);observed=(base+jac@truth).reshape(-1,3)
    inputs=dict(candidate_id='sphere_rotating',training_observations=observed[:12],
        center_parameters=center,training_prediction=prediction[:12],future_prediction=prediction[12:],
        training_jacobian=jac[:36],future_jacobian=jac[36:],lower=np.full(p,-1.),upper=np.full(p,1.))
    bound=adapter.Remainder(candidate_id='sphere_rotating',configuration=family.configuration,
        center=center,lower=inputs['lower'],upper=inputs['upper'],training_radii={k:0. for k in keys},
        future_bounds=np.zeros(12),source_id='analytic-exact-affine-mean',scope='global_parameter_box')
    return family,inputs,bound,observed[12:]


@pytest.mark.parametrize('p',[4,27])
@pytest.mark.parametrize('two',[False,True])
def test_nonzero_center_and_all_parameter_columns_predict_known_truth(p,two):
    family,inputs,bound,truth=fixture(p,two)
    result=family.envelope(**inputs,remainder=bound)
    target=family.frame.positions(truth).ravel()
    assert result['supported'] and result['parameter_count']==p
    assert np.all(result['lower']<=target) and np.all(result['upper']>=target)
    assert result['scientific_decision']=='abstain'
    assert result['observational_coverage_calibrated'] is False
    assert result['global_bound_validity_established'] is False


def test_missing_global_remainder_abstains_and_local_samples_are_rejected():
    family,inputs,bound,_=fixture()
    assert not family.envelope(**inputs)['supported']
    with pytest.raises(ValueError,match='global'):
        adapter.Remainder(candidate_id=bound.candidate_id,configuration=bound.configuration,center=bound.center,
            lower=bound.lower,upper=bound.upper,training_radii=bound.training_radii,future_bounds=bound.future_bounds,
            source_id='saved-axis-probes',scope='sampled_local_probes')


def test_missing_one_covariance_alternative_is_not_dropped():
    family,inputs,bound,_=fixture(two=True)
    missing=adapter.Remainder(candidate_id=bound.candidate_id,configuration=bound.configuration,center=bound.center,
        lower=bound.lower,upper=bound.upper,training_radii={'a':0.},future_bounds=bound.future_bounds,
        source_id='incomplete-declaration',scope='global_parameter_box')
    result=family.envelope(**inputs,remainder=missing)
    assert not result['supported'] and result['unsupported_ids']==['b']


@pytest.mark.parametrize('kind',['candidate','center','bounds','configuration'])
def test_global_bound_cannot_be_reused_for_another_problem(kind):
    family,inputs,bound,_=fixture()
    if kind=='candidate':inputs['candidate_id']='flat_still'
    elif kind=='center':inputs['center_parameters']=np.zeros(4)
    elif kind=='bounds':inputs['upper']=np.full(4,.9)
    else:
        bound=adapter.Remainder(candidate_id=bound.candidate_id,configuration='another-family',center=bound.center,
            lower=bound.lower,upper=bound.upper,training_radii=bound.training_radii,future_bounds=bound.future_bounds,
            source_id='wrong-configuration',scope='global_parameter_box')
    with pytest.raises(ValueError):family.envelope(**inputs,remainder=bound)


def test_future_observations_are_not_an_input():
    family,inputs,bound,truth=fixture()
    with pytest.raises(TypeError):family.envelope(**inputs,remainder=bound,future_observations=truth)


def test_frame_is_fixed_affine_and_jacobian_uses_the_same_transform():
    frame=adapter.Frame(origin=[1.,2.,3.],matrix=[[2.,.1,0.],[0.,3.,0.],[0.,0.,4.]],source_id='configured')
    x=np.arange(6.).reshape(2,3);j=np.arange(24.).reshape(6,4)
    np.testing.assert_array_equal(frame.positions(x),(x-[1.,2.,3.])@frame.matrix.T)
    expected=np.vstack([frame.matrix@j[3*i:3*i+3] for i in range(2)])
    np.testing.assert_array_equal(frame.jacobian(j),expected)
    with pytest.raises(ValueError):frame.matrix[0,0]=100.


def test_candidate_jacobian_always_uses_full_training_noise_dimension():
    family,inputs,bound,_=fixture()
    result=family.envelope(**inputs,remainder=bound)
    assert result['noise_degrees_of_freedom_by_covariance']=={'a':36}


def test_shared_scale_sources_cannot_be_candidate_specific():
    f,_,_,_=fixture(two=True)
    with pytest.raises(ValueError,match='shared'):
        adapter.Family(f.training_times,f.future_times,f.specifications,
            {'a':known_scale(.2,source_id='candidate-a',covariance_id='a'),
             'b':known_scale(.2,source_id='candidate-b',covariance_id='b')},
            frame=f.frame,parameter_names=f.parameter_names,assessment_id='invalid')


def test_global_nonlinear_remainder_is_propagated_in_training_and_future():
    family,inputs,_,truth=fixture()
    q=.1*np.sin(np.arange(48)*.17);center=inputs['center_parameters'][0];true_parameter=-.2
    inputs['training_prediction']=inputs['training_prediction']+q[:36].reshape(-1,3)*center**2
    inputs['future_prediction']=inputs['future_prediction']+q[36:].reshape(-1,3)*center**2
    inputs['training_observations']=inputs['training_observations']+q[:36].reshape(-1,3)*true_parameter**2
    inputs['training_jacobian'][:,0]+=2*center*q[:36]
    inputs['future_jacobian'][:,0]+=2*center*q[36:]
    transformed=family.frame.jacobian(q[:,None]).ravel()
    maximum_delta_squared=max(abs(-1-center),abs(1-center))**2
    radius=maximum_delta_squared*np.linalg.norm(family._operators['a'].whiten(transformed[:36]))
    bound=adapter.Remainder(candidate_id=inputs['candidate_id'],configuration=family.configuration,
        center=inputs['center_parameters'],lower=inputs['lower'],upper=inputs['upper'],training_radii={'a':radius},
        future_bounds=maximum_delta_squared*abs(transformed[36:]),source_id='analytic-quadratic-remainder',scope='global_parameter_box')
    result=family.envelope(**inputs,remainder=bound)
    target=family.frame.positions(truth+q[36:].reshape(-1,3)*true_parameter**2).ravel()
    assert result['supported']
    assert np.all(result['lower']<=target) and np.all(result['upper']>=target)


def test_native_candidate_cannot_inflate_the_shared_scale_from_bad_residuals():
    family,inputs,bound,_=fixture();scale=family.scales['a']
    inputs['training_prediction']+=1000.
    family.envelope(**inputs,remainder=bound)
    assert family.scales['a'] is scale and scale.upper==.2


def test_numeric_configuration_and_parameter_order_are_bound_to_remainder():
    family,inputs,bound,_=fixture()
    changed=adapter.Family(family.training_times,family.future_times,family.specifications,family.scales,
        frame=family.frame,parameter_names=tuple(reversed(family.parameter_names)),assessment_id=family.assessment_id)
    assert changed.configuration!=family.configuration
    with pytest.raises(ValueError):changed.envelope(**inputs,remainder=bound)
