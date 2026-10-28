# SPDX-License-Identifier: AGPL-3.0-or-later
"""Diagnostic arithmetic must preserve physics, columns and original kernels."""
import hashlib
from pathlib import Path

import numpy as np
import pytest


def test_derivation_changes_only_lower_bound_packet_dispatch():
    from lll.ilvis0_timing_arithmetic import derive
    from lll.ilvis0_wide_tangent import derive as baseline
    raw=Path('analysis/lll/ilvis0_tangent.cpp').read_bytes();sha=hashlib.sha256(raw).hexdigest()
    assert derive(raw,expected_sha256=sha,right_at_lower=False)==baseline(raw,expected_sha256=sha)
    alternate=derive(raw,expected_sha256=sha,right_at_lower=True)
    assert b'point[25]==-1.' in alternate
    with pytest.raises(ValueError,match='hash'):derive(raw,expected_sha256='0'*64,right_at_lower=True)
    with pytest.raises(ValueError):derive(raw,expected_sha256=sha,right_at_lower=1)


@pytest.fixture(scope='module')
def build_cache(tmp_path_factory):
    return tmp_path_factory.mktemp('arithmetic')


@pytest.fixture(scope='module')
def kernels(build_cache):
    from lll.ilvis0_timing_arithmetic import load
    directory=build_cache;charges=[];values={}
    for right in (False,True):
        for relative in (False,True):
            values[right,relative]=load(directory,right_at_lower=right,relative_longitude=relative,
                reserve_build=lambda:charges.append(1))[0]
    assert len(charges)==2
    return values


@pytest.mark.parametrize('identity',('turning-slow','turning-fast'))
def test_feasible_timing_branch_matches_right_hand_reference(identity,kernels):
    from lll.timing_precision_controls import fixture,turning_reference
    from lll.ilvis0_wide_tangent import evaluate
    f=fixture(identity);p=f['problem'];u=f['point'];col=p.bounds.active.index('time_offset')
    a=evaluate(p,u,'flat_still',kernel=kernels[False,False])
    b=evaluate(p,u,'flat_still',kernel=kernels[True,False])
    expected=turning_reference(f['force'],f['omega'],f['duration'])
    scale=np.array([p.radius,p.radius*np.pi/2])/p.bounds.limits['time_offset']
    assert np.allclose(b[2][:2,col]*scale,expected['right'],rtol=1e-12,atol=1e-12)
    assert np.array_equal(a[0],b[0]) and np.array_equal(a[1],b[1])
    assert np.array_equal(np.delete(a[2],col,axis=1),np.delete(b[2],col,axis=1))


def test_relative_longitude_recovers_weak_gyro_sensitivity(kernels):
    from lll.timing_precision_controls import calculate
    before=calculate('gyro-origin-one',kernel=kernels[False,False],reserve=lambda **v:None)
    after=calculate('gyro-origin-one',kernel=kernels[False,True],reserve=lambda **v:None)
    assert before['finite_difference_relative_error'][-1]==1.
    assert max(after['finite_difference_relative_error'])<1e-8
    assert before['analytic']==after['analytic']


@pytest.mark.parametrize('model',('sphere_rotating','sphere_still','flat_still'))
@pytest.mark.parametrize('profile',(False,True))
def test_lower_bound_timing_difference_across_all_physical_cases(model,profile,build_cache):
    from lll.timing_precision_controls import fixture
    from lll.ilvis0_timing_arithmetic import load
    from lll.ilvis0_shape import TangentProblem
    from lll.ilvis0_wide_tangent import problem
    b=fixture('turning-fast')['problem']
    base=TangentProblem(b.theta,b.dv,b.dt,b.gps_times,b.gps,np.eye(6),b.initial,b.bounds.base,
        tangent_kernel=None,kernel=None,fit_earth_removal=profile,clock_hypothesis=b.clock_hypothesis,
        processing_hypothesis=b.processing_hypothesis,maximum_interval_s=.25,
        gravity_mps2=b.gravity,disc_radius_m=b.radius)
    kernel,_=load(build_cache,right_at_lower=True,relative_longitude=True,
        gravity_anchor_height_m=1000.,reserve_build=lambda:None)
    adapted=problem(base,kernel=kernel);u=np.zeros(len(base.bounds.active));col=base.bounds.active.index('time_offset');u[col]=-1.
    r,j,boundary=adapted.residual_tangent(u,model)
    assert boundary>0 and j.shape[1]==26+int(profile)
    for h in (1e-3,1e-4,1e-5):
        a=u.copy();a[col]+=h;z=u.copy();z[col]+=2*h
        difference=(-3*r+4*adapted.residual(a,model)-adapted.residual(z,model))/(2*h)
        scale=1e-8+1e-6*max(np.linalg.norm(j[:,col]),np.linalg.norm(difference))
        assert np.linalg.norm(difference-j[:,col])<=scale


@pytest.mark.parametrize('model',('sphere_rotating','sphere_still','flat_still'))
@pytest.mark.parametrize('profile',(False,True))
def test_complete_physics_calibration_and_height_gravity_unchanged(model,profile,tmp_path,build_cache):
    from test_ilvis0_wide_tangent import _problem
    from lll.ilvis0_timing_arithmetic import load
    from lll.ilvis0_wide_tangent import evaluate,problem
    from lll.ilvis0_forecast import native_forecast
    base,anchor,m=_problem(tmp_path,model,profile);u=np.linspace(-.02,.02,len(base.bounds.active))
    original,_=load(build_cache,right_at_lower=False,relative_longitude=False,
        gravity_anchor_height_m=anchor,reserve_build=lambda:None)
    a=evaluate(base,u,model,kernel=original)
    for right in (False,True):
        for relative in (False,True):
            kernel,_=load(build_cache,right_at_lower=right,relative_longitude=relative,
                gravity_anchor_height_m=anchor,reserve_build=lambda:None)
            b=evaluate(base,u,model,kernel=kernel)
            assert b[2].shape==(base.gps.size,26+int(profile))
            assert np.array_equal(a[2],b[2]) and a[3]==b[3]
            assert np.max(abs(a[0]-b[0]))<1e-10
            assert np.max(abs(a[1]-b[1]))<1e-14
    adapted=problem(base,kernel=kernel);r,j,_=adapted.residual_tangent(u,model)
    for k in range(len(u)):
        h=1e-4;plus=u.copy();minus=u.copy();plus[k]+=h;minus[k]-=h
        difference=(adapted.residual(plus,model)-adapted.residual(minus,model))/(2*h)
        assert np.allclose(j[:,k],difference,rtol=2e-4,atol=3e-5),base.bounds.active[k]
    forecast=native_forecast(adapted,u,model,**{k:m[k] for k in ('theta','dv','dt')},
        times=m['times'],maximum_interval_s=.005,reserve=lambda **v:None)
    assert forecast['jacobian'].shape==(27,26+int(profile))
    assert not forecast['prediction_receiver_positions_used']


def test_relative_longitude_preserves_wrapping_and_upper_bound_left_branch(kernels):
    from lll.timing_precision_controls import fixture
    from lll.ilvis0_wide_tangent import problem
    p=fixture('vertical-interior')['problem'];u=np.zeros(26);u[25]=1.
    a=problem(p,kernel=kernels[False,False]);b=problem(p,kernel=kernels[True,True])
    # The saved query is at a packet end at the upper bound: the feasible
    # backward branch must retain the original derivative.
    p.gps_times=np.array([.25,.75])-p.bounds.limits['time_offset']
    for value in (a,b):value.gps_times=p.gps_times
    r,j,_=a.residual_tangent(u,'flat_still');rr,jj,_=b.residual_tangent(u,'flat_still')
    assert np.array_equal(r,rr) and np.array_equal(j,jj)
    p.initial['longitude_rad']=np.pi-.01
    p.gps=np.tile([0.,-np.pi+.01,1000.],(2,1))
    a=problem(p,kernel=kernels[False,False]);b=problem(p,kernel=kernels[False,True])
    assert np.allclose(a.residual(u,'flat_still'),b.residual(u,'flat_still'),atol=2e-15,rtol=0)


def test_build_denial_prevents_native_compilation(tmp_path):
    from lll.ilvis0_timing_arithmetic import load
    def deny():raise RuntimeError('build denied')
    with pytest.raises(RuntimeError,match='build denied'):
        load(tmp_path,right_at_lower=True,relative_longitude=True,reserve_build=deny)
    assert not list(tmp_path.glob('*.so'))
