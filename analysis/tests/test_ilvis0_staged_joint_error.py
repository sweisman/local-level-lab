# SPDX-License-Identifier: AGPL-3.0-or-later
"""One small complete API path; not aircraft or recording-length qualification."""
from fractions import Fraction as F

import numpy as np
import pytest


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_staged_regions_and_future_measurement_keep_one_joint_error_budget(tmp_path,model,profile):
    from test_ilvis0_native_box_bounds import configuration
    from test_ilvis0_regrouped_history import native
    from lll import ilvis0_direct_native as candidate
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_batched_transport import configure_backend
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel
    from lll.ilvis0_source_point_derivatives import load_kernel as load_point
    from lll.ilvis0_staged_native import predict
    from lll.ilvis0_bounded_prediction import known_scale
    from lll.ilvis0_gaussian_allowances import allowances
    from lll.ilvis0_error_model import Spec,factor
    from lll.ilvis0_inertial_error import joint_covariance
    from lll.ilvis0_joint_variance_bounds import marginal_variance_bounds
    from lll.ilvis0_long_staged import audit_truth

    config=configuration();config.update(model=model,profile=profile);n=32;dt=np.full(n,.005)
    theta=np.tile([1e-5,-2e-5,3e-6],(n,1));dv=np.tile([0.,0.,-.04905],(n,1))
    lo=np.full(27,-1.);hi=np.ones(27);center=np.zeros(27)
    reference=candidate.make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    directory=tmp_path/'kernels';configure_backend(directory)
    source,_=load_stream(directory);derivative,_=load_kernel(directory);point,_=load_point(directory)
    kernel,_=load_tangent(directory);calls=[];bounds=[];records={};charges={}
    def model(time_s,parameters):
        calls.append((time_s,np.array(parameters,copy=True)))
        assert len(calls)<=10
        return native(kernel,config,theta,dv,dt,time_s,parameters)
    def bound(time_s,proof):
        bounds.append(time_s);assert len(bounds)<=5
        return candidate.enclose(config,theta,dv,dt,time=time_s,lower=lo,upper=hi,reference=reference,
            conditioning=proof,source_kernel=source,derivative_kernel=derivative,point_kernel=point,maximum_seconds=30.)
    def reserve(**values):
        for k,v in values.items():charges[k]=charges.get(k,0)+v

    times=np.array([.015,.03,.06,.09,.13]);training=times[:4]
    truth=np.zeros(27);truth[0]=.1;truth[6]=.05;truth[25]=.25
    spec=Spec(white=np.eye(3)*1e-8,components=((.03,np.eye(3)*1e-8),))
    law=dict(origin_s=0.,accel_psd=np.eye(3)*1e-8,gyro_psd=np.eye(3)*1e-10,
        coupling=np.array([[0.,-9.81,0.],[9.81,0.,0.],[0.,0.,0.]]))
    true_clock=config['limits'][25]*truth[25]
    cov=joint_covariance(times+true_clock,spec,**law)
    variance=marginal_variance_bounds(times,receiver=spec,clock_interval_s=(-config['limits'][25],config['limits'][25]),**law)
    assert variance['variance_arithmetic_verified'] and variance['clock_interval_covered']
    assert not variance['law_adequacy_established']
    bands=allowances(variance['variance_upper_m2'],scale=known_scale(1.,source_id='fixed-law',
        covariance_id=variance['covariance_id']),covariance_id=variance['covariance_id'],alpha=.01,error_distribution='gaussian')
    noise_root=factor(cov);rng=np.random.default_rng(2468);z_training=rng.normal(size=12)
    noise_training=(noise_root[:12,:12]@z_training).reshape(4,3)
    assert np.all(np.abs(noise_training)<=bands['radius_m'][:4])
    scale=np.array([6371000.,6371000.*np.cos(config['initial_c'][0]),1.]);origin=config['initial_c']
    observed=np.array([model(float(t),truth)[0] for t in training])+noise_training/scale
    result=predict(training_times=training,observations=observed,noise_allowance=bands['radius_m'][:4],
        stage_sizes=[2,2],future_time=times[-1],reference=reference,lower=lo,upper=hi,
        coordinate_scale=scale,origin=origin,native=model,bound=bound,reserve=reserve,
        save=lambda name,value:records.__setitem__(name,value))
    assert 'future.json' in records  # No future realization was constructed before this point.
    future_noise=noise_root[12:,:12]@z_training+noise_root[12:,12:]@rng.normal(size=3)
    future_truth,_=model(float(times[-1]),truth)
    assert np.all(np.abs(future_noise)<=bands['radius_m'][4])
    latent=[(F(float(v))-F(float(o)))*F(float(s)) for v,o,s in zip(future_truth,origin,scale)]
    witness=list(truth)+list(reference.normalized_values_at(truth))
    audit_truth([records[f'stage-{i:02d}-region.json'] for i in (1,2)],witness,result['future'],latent,[1e9]*3)
    # Include future observation error when testing the receiver measurement;
    # the latent trajectory interval alone is not a measurement-error interval.
    for i in range(3):
        measured=latent[i]+F(float(future_noise[i]));radius=F(float(bands['radius_m'][4,i]))
        assert F(result['future']['lower'][i])-radius<=measured<=F(result['future']['upper'][i])+radius
    assert charges==dict(physical_proofs=1,training_proofs=2,lp_proposals=18,exact_supports=66)
    assert len(calls)==10 and len(bounds)==5 and result['parameter_count']==51
    assert bands['coordinate_count']==15 and bands['nominal_failure_probability_bound']<=.01
