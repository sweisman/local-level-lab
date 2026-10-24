# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small precision controls; no recorded telemetry or optimization."""
import hashlib
import math
from pathlib import Path

import numpy as np
import pytest


def test_precision_derivation_requires_exact_source_and_supported_precision():
    from lll.ilvis0_precision_value import derive
    source=Path('analysis/lll/ilvis0_tangent.cpp').read_bytes()
    sha=hashlib.sha256(source).hexdigest()
    with pytest.raises(ValueError,match='hash'):derive(source,expected_sha256='0'*64,precision='double')
    with pytest.raises(ValueError,match='precision'):derive(source,expected_sha256=sha,precision='float')
    changed=source.replace(b'p[i].d[i]=limits[i];',b'p[i].d[i]=2*limits[i];')
    with pytest.raises(ValueError,match='layout'):
        derive(changed,expected_sha256=hashlib.sha256(changed).hexdigest(),precision='double')
    assert derive(source,expected_sha256=sha,precision='double')==derive(source,expected_sha256=sha,precision='double')


def test_precision_longitude_wrap_preserves_small_residual_and_branch_convention():
    from lll.ilvis0_precision_value import longitude_residual
    tiny=math.ldexp(1.,-55)
    values=np.array([-math.pi,math.pi,3*math.pi,-3*math.pi,tiny,-tiny,0.])
    got=longitude_residual(values)
    assert np.array_equal(got[:4],np.full(4,-math.pi))
    assert np.array_equal(got[4:],values[4:])
    assert np.array_equal(values,np.array([-math.pi,math.pi,3*math.pi,-3*math.pi,tiny,-tiny,0.]))
    assert ((tiny+math.pi)%(2*math.pi)-math.pi)==0.
    with pytest.raises(ValueError):longitude_residual([float('nan')])


def _stationary_problem(tmp_path,*,north_speed=0.):
    from lll.ilvis0_shape import TangentProblem
    from lll.ilvis0_estimator import Bounds
    from lll.airquantumgrav_training_controls import parameter_limits
    dt=np.full(10,.1);gps=np.tile([1.,1.2,1000.],(3,1))
    initial=dict(latitude_rad=1.,longitude_rad=1.2,height_m=1000.,
        velocity_ned_mps=np.array([north_speed,0.,0.]),attitude_body_to_ned=np.eye(3))
    return TangentProblem(np.zeros((10,3)),np.column_stack((np.zeros((10,2)),-9.8*dt)),dt,
        np.array([.2,.5,.9]),gps,np.eye(9),initial,Bounds(parameter_limits()),
        tangent_kernel=None,kernel=None,fit_earth_removal=False,clock_hypothesis='header_elapsed',
        processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.11,
        gravity_mps2=9.8,disc_radius_m=6371000.)


def test_precision_extended_residual_keeps_sub_ulp_accumulated_motion(tmp_path):
    from lll.ilvis0_precision_value import load,calculate
    p=_stationary_problem(tmp_path,north_speed=1e-9);point=np.zeros(len(p.bounds.active))
    double,dm=load(tmp_path,precision='double');wide,wm=load(tmp_path,precision='long_double')
    a=calculate(p,point,'flat_still',kernel=double,longitude='stable')
    b=calculate(p,point,'flat_still',kernel=wide,longitude='stable')
    expected=p.gps_times*1e-9/6371000.
    assert np.array_equal(a['coordinate_difference'][:,0],np.zeros(3))
    assert np.allclose(b['coordinate_difference'][:,0],expected,rtol=.01,atol=1e-19)
    # Residuals must be formed before casting absolute coordinates back to binary64.
    assert np.array_equal(b['coordinates'][:2,0],p.gps[:2,0])
    assert wm['mantissa_bits']>dm['mantissa_bits']==53
    assert wm['clock_mantissa_bits']==dm['clock_mantissa_bits']==53
    assert wm['clock_dispatch']=='binary64-frozen' and wm['profile_mapping']=='binary64-frozen'


@pytest.mark.parametrize('model',('sphere_rotating','sphere_still','flat_still'))
@pytest.mark.parametrize('profile',(False,True))
def test_precision_double_matches_frozen_tangent_values_and_legacy_residual(model,profile,tmp_path):
    from lll.ilvis0_precision_value import load,calculate
    from lll.ilvis0_exploratory import load_kernel
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_training_forecast import training_problem
    from lll.airquantumgrav_training_controls import recipe,generated_training,training_covariance
    r=dict(recipe(),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2)
    m=generated_training(dict(model=model,latitude_deg=55.,profile=profile,start=0),r,
        reserve=lambda **v:None,height_profile='climb',gravity_model='inverse_square_height')
    anchor=float(m['training_gps'][0,2]);times=m['times'][:m['training_epochs']]
    value,_=load_kernel(tmp_path,gravity_anchor_height_m=anchor)
    tangent,_=load_tangent(tmp_path,gravity_anchor_height_m=anchor)
    p=training_problem(times,m['training_gps'],**{k:m[k] for k in ('theta','dv','dt')},
        covariance=training_covariance(m['training_gps'],model,sigma_m=.05),model=model,
        limits=r['limits'],profile=profile,clock='header_elapsed',maximum_interval_s=.005,
        kernel=value,tangent_kernel=tangent)
    point=np.linspace(-.02,.02,len(p.bounds.active))
    kernel,meta=load(tmp_path,precision='double',gravity_anchor_height_m=anchor)
    baseline,jac,boundaries=p.prediction_tangent(point,model)
    result=calculate(p,point,model,kernel=kernel,longitude='legacy')
    assert np.array_equal(result['coordinates'],baseline)
    assert np.array_equal(result['coordinate_difference'],baseline-p.gps)
    assert np.array_equal(result['residual'],p.whiten(baseline-p.gps))
    assert result['boundaries']==boundaries
    assert meta['source_sha256']==hashlib.sha256(Path('analysis/lll/ilvis0_tangent.cpp').read_bytes()).hexdigest()
    # A nonzero latitude, complete calibration vector and fractional query clock remain active.
    wide,_=load(tmp_path,precision='long_double',gravity_anchor_height_m=anchor)
    extended=calculate(p,point,model,kernel=wide,longitude='stable')
    assert np.max(np.abs(extended['coordinates']-baseline))<1e-8
    assert extended['boundaries']==boundaries


def test_precision_calculate_rejects_bad_mode_and_unsupported_points_before_native(tmp_path):
    from lll.ilvis0_precision_value import calculate
    p=_stationary_problem(tmp_path);point=np.zeros(len(p.bounds.active))
    def forbidden(*args):raise AssertionError('native call before validation')
    with pytest.raises(ValueError,match='longitude'):calculate(p,point,'flat_still',kernel=forbidden,longitude='other')
    with pytest.raises(ValueError):calculate(p,point,'unknown',kernel=forbidden,longitude='stable')
    point[0]=2.
    with pytest.raises(ValueError):calculate(p,point,'flat_still',kernel=forbidden,longitude='stable')
