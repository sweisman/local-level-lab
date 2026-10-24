# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent gravity/derivative controls; no fit or original aircraft data."""
import ctypes
import math
from pathlib import Path
import subprocess

import numpy as np
import pytest

from lll import ilvis0_estimator as estimator,ilvis0_exploratory as explore,ilvis0_shape as shape
from lll.ilvis0_latitude_controls import fixture


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    directory=tmp_path_factory.mktemp('height-gravity')
    constant=explore.load_kernel(directory/'value')[0]
    tangent=shape.load_tangent(directory/'tangent')[0]
    height=explore.load_kernel(directory/'value',gravity_anchor_height_m=1000.)[0]
    height_tangent=shape.load_tangent(directory/'tangent',gravity_anchor_height_m=1000.)[0]
    # Restore only the two declared source artifacts, never measurements. Compile
    # under this test's compiler so compatibility is independent of compiler version.
    from lll.studies.closed import ClosedStudy
    root=Path(__file__).resolve().parents[2];closed=ClosedStudy(root,'docs/esa-development-pilot')
    previous=[]
    try:
        for filename,compiler,flags,symbol,current in (
            ('ilvis0_native.c','cc',['-std=c99','-D_DEFAULT_SOURCE'],'ilvis0_predict',constant),
            ('ilvis0_tangent.cpp','c++',['-std=c++17'],'ilvis0_tangent',tangent)):
            key='analysis/lll/'+filename;source=directory/filename
            source.write_bytes(closed.read('source-freeze/'+key,closed.manifest['sources'][key],raw=True))
            binary=source.with_suffix('.so')
            subprocess.run([compiler,'-O2',*flags,'-fPIC','-shared',str(source),'-lm','-o',str(binary)],
                check=True,capture_output=True)
            function=getattr(ctypes.CDLL(str(binary)),symbol)
            function.argtypes=current.argtypes;function.restype=current.restype;previous.append(function)
    finally:closed.close()
    return constant,tangent,height,height_tangent,*previous


def problem(f,value,tangent,profile):
    sigma=np.tile(.01/f['metric'],len(f['gps_times']))
    return shape.TangentProblem(f['theta'],f['dv'],f['dt'],f['gps_times'],f['gps'],np.diag(sigma**2),
        f['initial'],estimator.Bounds(shape.instrument_limits(1.)),fit_earth_removal=profile,
        kernel=value,tangent_kernel=tangent,clock_hypothesis='header_elapsed',
        processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.0075,
        gravity_mps2=9.81,disc_radius_m=6371000.)


@pytest.mark.parametrize('model',explore.MODELS)
@pytest.mark.parametrize('profile',(False,True))
def test_constant_mode_preserves_archived_values_and_all_derivatives(model,profile,kernels):
    value,tangent,_,_,old_value,old_tangent=kernels;f=fixture(model,55.,'near_roll')
    a=problem(f,value,tangent,profile);b=problem(f,old_value,old_tangent,profile)
    point=.03*np.sin(np.arange(len(a.bounds.active))+.4)
    np.testing.assert_array_equal(a.predict(point,model),b.predict(point,model))
    actual,jac,_=a.prediction_tangent(point,model);expected,old_jac,_=b.prediction_tangent(point,model)
    np.testing.assert_array_equal(actual,expected);np.testing.assert_array_equal(jac,old_jac)


@pytest.mark.parametrize('model',explore.MODELS)
@pytest.mark.parametrize('profile',(False,True))
def test_height_gravity_values_and_every_active_column_match(model,profile,kernels):
    _,_,value,tangent,_,_=kernels;f=fixture(model,-55.,'near_roll');p=problem(f,value,tangent,profile)
    point=.03*np.sin(np.arange(len(p.bounds.active))+.4)
    actual,jac,_=p.prediction_tangent(point,model)
    np.testing.assert_allclose((actual-p.predict(point,model))*f['metric'],0.,atol=2e-7,rtol=0)
    assert len(p.bounds.active)==26+int(profile)
    for column in range(len(point)):
        step=np.eye(len(point))[column]*.01
        coarse=(p.predict(point+step,model)-p.predict(point-step,model)).ravel()/.02
        fine=(p.predict(point+step/2,model)-p.predict(point-step/2,model)).ravel()/.01
        numerical=(4*fine-coarse)/3
        np.testing.assert_allclose(numerical.reshape(-1,3)*f['metric'],jac[:,column].reshape(-1,3)*f['metric'],
            atol=2e-5,rtol=2e-6,err_msg=p.bounds.active[column])


@pytest.mark.parametrize('vertical_mps',(0.,50.,-50.))
def test_known_vertical_motion_uses_predicted_midpoint_height(vertical_mps,kernels):
    value=kernels[2];dt=np.full(2000,.005);ends=np.cumsum(dt);middle=ends-dt/2
    # Analytic straight vertical motion on a zero-field candidate. No navigation
    # code generates its position, rate or specific force.
    heights=1000.+vertical_mps*middle
    gravity=9.81/(1+(heights-1000.)/6372000.)**2
    theta=np.zeros((len(dt),3));dv=np.zeros_like(theta);dv[:,2]=-gravity*dt
    times=np.array([.503,2.503,5.503,9.503]);out=np.empty((len(times),3))
    code=value(len(dt),theta,dv,dt,len(times),times,np.array([math.radians(55.),0.,1000.]),
        np.array([0.,0.,-vertical_mps]),np.eye(3),np.zeros(3),1,9.81,6371000.,0.,out)
    assert code==0
    np.testing.assert_allclose(out[:,2],1000.+vertical_mps*times,atol=1e-6,rtol=0)


@pytest.mark.parametrize('anchor',(float('nan'),float('inf'),-6371000.,-6371001.))
def test_invalid_gravity_anchor_rejected_before_compilation(anchor,tmp_path):
    for loader in (explore.load_kernel,shape.load_tangent):
        with pytest.raises(ValueError,match='gravity anchor'):
            loader(tmp_path/'invalid',gravity_anchor_height_m=anchor)
    assert not (tmp_path/'invalid').exists()
