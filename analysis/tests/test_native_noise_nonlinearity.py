# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite two-second qualification of matched nonlinear noise controls."""
import pytest
from test_native_structured_training import training_kernels,native_training_case

ADDITIONAL=['analysis/lll/noise_nonlinearity.py','analysis/tests/test_noise_nonlinearity.py',
    'analysis/tests/test_native_noise_nonlinearity.py','docs/noisy-prediction-benchmark/NONLINEAR_PLAN.md',
    'analysis/lll/generated_noise_benchmark.py','analysis/lll/ilvis0_precision_value.py',
    'analysis/tests/test_generated_noise_benchmark.py','analysis/tests/test_prediction_error_benchmark.py']
DEFINITION=dict(additional_sources=ADDITIONAL,maximum_wall_s=180.,allowances={
    'builds':dict(builds=2),'scalar-build':dict(builds=1),
    **{f'{law}:0:0:1':dict(native_calls=700,packet_steps=10000,packet_query_visits=40000,
        generated_samples=610,constructed_intervals=600,noise_normal_variates=20000) for law in ('increment','point')}})


def scalar_library(shared,*,anchor):
    if 'scalar_kernel' in shared:return shared['scalar_kernel']
    import gzip
    from lll.ilvis0_precision_value import load
    from lll.studies.allowances import PrepaidCase
    from lll.studies.artifacts import atomic,encoded,digest
    with PrepaidCase(shared['journal'],'scalar-build',require_exact=True) as budget:
        budget.reserve(builds=1)
        kernel,meta=load(shared['directory'],precision='long_double',gravity_anchor_height_m=anchor,
            expected_source_sha256=shared['hashes']['analysis/lll/ilvis0_tangent.cpp'])
    shared['outcomes'].append(budget.snapshot());shared['scalar_kernel']=kernel
    for kind,suffix,key in [('source','.cpp','derived_source_sha256'),('binary','.so','binary_sha256')]:
        raw=(shared['directory']/('precision-value-'+meta['derived_source_sha256']+suffix)).read_bytes()
        assert digest(raw)==meta[key]
        atomic(shared['path'].with_name(shared['path'].stem+'.scalar.'+kind+'.gz'),gzip.compress(raw,mtime=0))
    atomic(shared['path'].with_suffix('.scalar.json'),encoded(meta))
    return kernel


@pytest.mark.parametrize('training_kernels',[DEFINITION],indirect=True)
@pytest.mark.parametrize('law',['increment','point'])
@pytest.mark.parametrize('model',[0])
@pytest.mark.parametrize('profile',[False])
@pytest.mark.parametrize('height',[True])
def test_native_nonlinear_noise_wrapper_and_antithetic_response(native_training_case,training_kernels,law,model,profile,height):
    import numpy as np
    from lll.generated_noise_benchmark import material,build_operator
    from lll.noise_nonlinearity import draw,propagate,conditional_error,summarize_pair
    from lll.ilvis0_wide_tangent import load,evaluate
    from lll.ilvis0_shape import TangentProblem
    from lll.ilvis0_estimator import Bounds
    from lll.airquantumgrav_training_controls import parameter_limits
    k=native_training_case
    data=material(duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2,reserve=k['reserve'])
    op,mean,descriptor=build_operator(data,law=law,kernel=k['kernel'],reserve=k['reserve'])
    scalar=scalar_library(training_kernels,anchor=data['anchor_height_m'])
    nominal=propagate(data,theta=data['raw_theta'],dv=data['raw_dv'],operator=op,kernel=scalar,reserve=k['reserve'])
    np.testing.assert_allclose((nominal-mean)*data['nominal_metric'],0,rtol=0,atol=1e-5)
    initial=dict(zip(('latitude_rad','longitude_rad','height_m'),data['initial']['coordinates']))
    initial.update(velocity_ned_mps=data['initial']['velocity'],attitude_body_to_ned=data['initial']['rotation'])
    tangent,_=load(k['directory'],expected_source_sha256=k['hashes']['analysis/lll/ilvis0_tangent.cpp'],
        gravity_anchor_height_m=data['anchor_height_m'])
    base=TangentProblem(data['raw_theta'],data['raw_dv'],data['dt'],data['times'],np.zeros((9,3)),np.eye(27),
        initial,Bounds(parameter_limits()),tangent_kernel=tangent,fit_earth_removal=False,clock_hypothesis='header_elapsed',
        processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.007,
        gravity_mps2=data['gravity_mps2'],disc_radius_m=data['radius_m'])
    point=np.array([data['sensor_correction'].get(name,0)/base.bounds.limits[name] for name in base.bounds.active])
    k['reserve'](native_calls=1,packet_steps=600,packet_query_visits=5400)
    reference=evaluate(base,point,'sphere_rotating',kernel=tangent)[0]
    np.testing.assert_allclose((nominal-reference)*data['nominal_metric'],0,rtol=0,atol=1e-5)
    realization=draw(data,law=law,seed=26102500,reserve=k['reserve'])
    cut=data['training_epochs'];metric=data['nominal_metric'][cut:]
    _,state=op.apply_block(np.zeros(3*cut),first_epoch=0)
    cov=op.conditional_marginals(state=state)['covariance']
    sigma=np.sqrt(np.diagonal(cov,axis1=1,axis2=2))*metric
    errors=[]
    for amplitude in (1.,-1.,.5,-.5):
        perturbed=propagate(data,theta=data['raw_theta']+amplitude*realization['theta_error'],
            dv=data['raw_dv']+amplitude*realization['dv_error'],operator=op,kernel=scalar,reserve=k['reserve'])
        errors.append(conditional_error(op,nominal,perturbed,amplitude*realization['receiver_error'],
            training_epochs=cut,metric=metric))
    summary=summarize_pair(*errors,standard_deviation=sigma,absolute_limit_m=.001,relative_limit=.01)
    assert summary['passed'] and summary['confidence_calibrated'] is False
    assert descriptor['prediction_target']=='physical_position'
    k['results'].append(dict(law=law,summary=summary,seed=26102500,
        scalar_reference_maximum_difference_m=float(np.max(abs((nominal-reference)*data['nominal_metric']))),
        generated_array_hashes=realization['array_sha256'],global_remainder_bound_established=False,
        original_reads=0,protected_reads=0,optimizer_starts=0))
