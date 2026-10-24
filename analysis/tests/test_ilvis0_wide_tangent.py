# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-motion and every-column controls for a wider residual tangent."""
import hashlib
from pathlib import Path

import numpy as np
import pytest


def test_wide_tangent_requires_bound_source_and_keeps_clock_values_binary64():
    from lll.ilvis0_wide_tangent import derive
    source=Path('analysis/lll/ilvis0_tangent.cpp').read_bytes();sha=hashlib.sha256(source).hexdigest()
    with pytest.raises(ValueError,match='hash'):derive(source,expected_sha256='0'*64)
    result=derive(source,expected_sha256=sha).decode()
    assert 'std::array<long double,27>' in result
    assert 'difference[3*j+i]' in result and 'value.d[h]' in result
    assert 'double start=0;size_t j=0;' in result
    assert 'fraction.v=(times[j]+static_cast<double>(p[25].v)-start)/dt[k];' in result
    assert 'p[26].v=(point[26]*limits[26]+1)/2;' in result


def test_wide_residual_and_independent_straight_motion_derivative_survive_coordinate_cast(tmp_path):
    from lll.ilvis0_wide_tangent import load,problem
    from test_ilvis0_precision_value import _stationary_problem
    base=_stationary_problem(tmp_path,north_speed=1e-9);kernel,meta=load(tmp_path)
    wide=problem(base,kernel=kernel);u=np.zeros(len(base.bounds.active))
    r,j,b=wide.residual_tangent(u,'flat_still');col=wide.bounds.active.index('velocity_x')
    assert np.allclose(r.reshape(-1,3)[:,0],base.gps_times*1e-9/6371000.,atol=1e-19,rtol=.01)
    assert np.array_equal(wide.residual(u,'flat_still'),r)
    assert np.allclose(j.reshape(-1,3,len(u))[:,0,col],base.gps_times*base.bounds.limits['velocity_x']/6371000.,rtol=1e-12)
    assert np.array_equal(wide.predict(u,'flat_still')[:2,0],base.gps[:2,0])
    assert j.shape==(9,26) and meta['internal_mantissa_bits']>53
    assert base.tangent_kernel is None and wide is not base


def _problem(tmp_path,model,profile):
    from lll.airquantumgrav_training_controls import recipe,generated_training,training_covariance
    from lll.ilvis0_training_forecast import training_problem
    r=dict(recipe(),duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2)
    m=generated_training(dict(model=model,latitude_deg=55.,profile=profile,start=0),r,
        reserve=lambda **v:None,height_profile='climb',gravity_model='inverse_square_height')
    times=m['times'][:m['training_epochs']];anchor=float(m['training_gps'][0,2])
    base=training_problem(times,m['training_gps'],**{k:m[k] for k in ('theta','dv','dt')},
        covariance=training_covariance(m['training_gps'],model,sigma_m=.05),model=model,limits=r['limits'],
        profile=profile,clock='header_elapsed',maximum_interval_s=.005,kernel=None,tangent_kernel=None)
    return base,anchor,m


@pytest.mark.parametrize('model',('sphere_rotating','sphere_still','flat_still'))
@pytest.mark.parametrize('profile',(False,True))
def test_wide_every_derivative_matches_finite_difference_and_independent_binary64_reference(model,profile,tmp_path):
    from lll.ilvis0_wide_tangent import load,problem
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_precision_value import load as scalar_load,calculate
    from scipy.linalg import solve_triangular
    base,anchor,m=_problem(tmp_path,model,profile)
    kernel,meta=load(tmp_path,gravity_anchor_height_m=anchor);wide=problem(base,kernel=kernel)
    u=np.linspace(-.02,.02,len(wide.bounds.active));r,j,b=wide.residual_tangent(u,model)
    scalar,_=scalar_load(tmp_path,precision='long_double',gravity_anchor_height_m=anchor)
    reference=calculate(base,u,model,kernel=scalar,longitude='stable')
    assert np.array_equal(r,reference['residual'])
    assert np.array_equal(wide.predict(u,model),reference['coordinates']) and b==reference['boundaries']
    # Independent C++ binary64 derivative implementation and widened value-only
    # differences both constrain the complete 26/27-column result.
    original,_=load_tangent(tmp_path,gravity_anchor_height_m=anchor);base.tangent_kernel=original
    _,old_j,_=base.prediction_tangent(u,model)
    old_j=solve_triangular(base.cholesky,old_j,lower=True)
    assert np.allclose(j,old_j,rtol=2e-9,atol=2e-8)
    for index in range(len(u)):
        differences=[]
        for step in (2e-4,1e-4):
            plus=u.copy();minus=u.copy();plus[index]+=step;minus[index]-=step
            a=calculate(base,plus,model,kernel=scalar,longitude='stable')['residual']
            z=calculate(base,minus,model,kernel=scalar,longitude='stable')['residual']
            differences.append((a-z)/(2*step))
        assert np.allclose(j[:,index],differences[1],rtol=2e-4,atol=3e-5),wide.bounds.active[index]
        assert np.allclose(differences[0],differences[1],rtol=2e-4,atol=3e-5),wide.bounds.active[index]


def test_wide_forecast_uses_no_later_coordinates_and_keeps_all_columns(tmp_path):
    from lll.ilvis0_wide_tangent import load,problem
    from lll.ilvis0_forecast import native_forecast
    base,anchor,m=_problem(tmp_path,'sphere_rotating',True)
    kernel,_=load(tmp_path,gravity_anchor_height_m=anchor);wide=problem(base,kernel=kernel)
    charges=[];u=np.zeros(len(wide.bounds.active))
    out=native_forecast(wide,u,'sphere_rotating',**{k:m[k] for k in ('theta','dv','dt')},times=m['times'],
        maximum_interval_s=.005,reserve=lambda **v:charges.append(v))
    assert out['jacobian'].shape==(27,27) and out['active_parameters']==list(wide.bounds.active)
    assert len(charges)==1 and charges[0]==dict(native_calls=1,packet_visits=600*9)
    assert not out['prediction_receiver_positions_used']
