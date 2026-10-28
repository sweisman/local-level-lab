# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent origin/axis controls and complete-physics compatibility."""
import hashlib
from pathlib import Path

import numpy as np
import pytest


def test_compensated_derivation_requires_exact_supported_source():
    from lll.ilvis0_coordinate_precision import derive
    source=Path('analysis/lll/ilvis0_tangent.cpp').read_bytes();sha=hashlib.sha256(source).hexdigest()
    raw=derive(source,expected_sha256=sha)
    assert b'add_coordinate' in raw and b'ocarry' in raw
    assert b'point[25]==-1.' in raw
    with pytest.raises(ValueError,match='hash'):derive(source,expected_sha256='0'*64)
    changed=source.replace(b'c[i]+=rate[i]*dt;',b'c[i]+=2*rate[i]*dt;')
    with pytest.raises(ValueError,match='layout'):derive(changed,expected_sha256=hashlib.sha256(changed).hexdigest())


@pytest.fixture(scope='module')
def cache(tmp_path_factory):return tmp_path_factory.mktemp('coordinate-precision')


@pytest.fixture(scope='module')
def kernels(cache):
    from lll.ilvis0_timing_arithmetic import load as previous
    from lll.ilvis0_coordinate_precision import load
    calls=[];charge=lambda:calls.append(1)
    a=previous(cache,right_at_lower=False,relative_longitude=False,reserve_build=charge)[0]
    b=previous(cache,right_at_lower=True,relative_longitude=True,reserve_build=charge)[0]
    c=load(cache,reserve_build=charge)[0]
    assert len(calls)==3
    return dict(baseline=a,previous=b,compensated=c)


@pytest.mark.parametrize('axis',('north','east','height'))
@pytest.mark.parametrize('origin',('small','large'))
def test_compensated_axis_matches_independent_midpoint_polynomial(axis,origin,kernels):
    from lll.coordinate_precision_controls import calculate
    result=calculate(axis+'-'+origin,kernel=kernels['compensated'],reserve=lambda **v:None)
    assert result['analytic_relative_error']<1e-7,result
    assert max(result['difference_relative_errors'])<1e-7,result
    assert result['evaluations']==7 and result['columns']==26


@pytest.mark.parametrize('axis',('north','east','height'))
def test_original_large_origin_loses_changes_that_compensation_retains(axis,kernels):
    from lll.coordinate_precision_controls import calculate
    a=calculate(axis+'-large',kernel=kernels['baseline'],reserve=lambda **v:None)
    b=calculate(axis+'-large',kernel=kernels['compensated'],reserve=lambda **v:None)
    assert a['difference_relative_errors'][-1]>1e-4
    assert b['difference_relative_errors'][-1]<1e-7


@pytest.mark.parametrize('model',('sphere_rotating','sphere_still','flat_still'))
@pytest.mark.parametrize('profile',(False,True))
def test_compensation_preserves_full_physical_problem(model,profile,cache,tmp_path):
    from test_ilvis0_wide_tangent import _problem
    from lll.ilvis0_timing_arithmetic import load as previous
    from lll.ilvis0_coordinate_precision import load
    from lll.ilvis0_wide_tangent import evaluate,problem
    from lll.ilvis0_forecast import native_forecast
    base,anchor,m=_problem(tmp_path,model,profile);u=np.linspace(-.02,.02,len(base.bounds.active))
    a,_=previous(cache,right_at_lower=True,relative_longitude=True,
        gravity_anchor_height_m=anchor,reserve_build=lambda:None)
    b,_=load(cache,gravity_anchor_height_m=anchor,reserve_build=lambda:None)
    old=evaluate(base,u,model,kernel=a);new=evaluate(base,u,model,kernel=b)
    units=np.array([6371000.,6371000.,1.])
    assert np.max(abs(old[0]-new[0])*units)<1e-7
    assert np.allclose(old[2],new[2],rtol=2e-10,atol=1e-13)
    adapted=problem(base,kernel=b);r,j,_=adapted.residual_tangent(u,model)
    for k in range(len(u)):
        h=1e-4;plus=u.copy();minus=u.copy();plus[k]+=h;minus[k]-=h
        fd=(adapted.residual(plus,model)-adapted.residual(minus,model))/(2*h)
        assert np.allclose(j[:,k],fd,rtol=2e-4,atol=3e-5),base.bounds.active[k]
    forecast=native_forecast(adapted,u,model,**{k:m[k] for k in ('theta','dv','dt')},
        times=m['times'],maximum_interval_s=.005,reserve=lambda **v:None)
    assert forecast['jacobian'].shape==(27,26+int(profile))
    assert not forecast['prediction_receiver_positions_used']


def test_compensated_partial_step_initial_position_lever_and_wrap(cache):
    from lll.coordinate_precision_controls import fixture
    from lll.ilvis0_coordinate_precision import load
    from lll.ilvis0_timing_arithmetic import load as previous
    from lll.ilvis0_wide_tangent import evaluate,problem
    base=fixture('north-large')['problem'];base.gps_times=np.array([.503,.997]);u=np.zeros(26)
    u[6:9]=[.2,-.1,.3];u[21:24]=[.25,.1,-.2]
    base.initial['longitude_rad']=np.pi-.01;base.gps=np.tile([1.,-np.pi+.01,0.],(2,1))
    a,_=previous(cache,right_at_lower=True,relative_longitude=True,reserve_build=lambda:None)
    b,_=load(cache,reserve_build=lambda:None)
    assert np.allclose(problem(base,kernel=a).residual(u,'flat_still'),
        problem(base,kernel=b).residual(u,'flat_still'),atol=1e-12,rtol=0)


@pytest.mark.parametrize('model',('sphere_rotating','sphere_still','flat_still'))
@pytest.mark.parametrize('profile',(False,True))
def test_compensated_lower_timing_bound_all_physical_cases(model,profile,cache,tmp_path):
    from test_ilvis0_wide_tangent import _problem
    from lll.ilvis0_coordinate_precision import load
    from lll.ilvis0_wide_tangent import problem
    base,anchor,_=_problem(tmp_path,model,profile)
    offset=base.bounds.limits['time_offset']
    base.gps_times=np.array([.5,.625,.75,.875,1.,1.125])+offset
    kernel,_=load(cache,gravity_anchor_height_m=anchor,reserve_build=lambda:None)
    p=problem(base,kernel=kernel);u=np.zeros(len(p.bounds.active));col=p.bounds.active.index('time_offset');u[col]=-1.
    r,j,b=p.residual_tangent(u,model)
    assert b>0 and j.shape[1]==26+int(profile)
    for h in (1e-3,1e-4,1e-5):
        a=u.copy();z=u.copy();a[col]+=h;z[col]+=2*h
        difference=(-3*r+4*p.residual(a,model)-p.residual(z,model))/(2*h)
        assert np.linalg.norm(difference-j[:,col])<=1e-8+1e-6*max(np.linalg.norm(difference),np.linalg.norm(j[:,col]))


def test_build_denial_prevents_compilation(tmp_path):
    from lll.ilvis0_coordinate_precision import load
    def deny():raise RuntimeError('build denied')
    with pytest.raises(RuntimeError,match='build denied'):load(tmp_path,reserve_build=deny)
    assert not list(tmp_path.glob('*.so'))
