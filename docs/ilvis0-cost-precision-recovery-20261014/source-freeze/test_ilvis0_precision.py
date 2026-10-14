# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent exact-motion and derivative controls for diagnostic arithmetic."""
import ctypes
from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np
import pytest

from lll import ilvis0_precision as precision, ilvis0_shape as shape
from lll import ilvis0_exploratory as explore
from test_ilvis0_shape import problem


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    directory=tmp_path_factory.mktemp('precision-kernels')
    original=shape.load_tangent(directory)[0]
    extended,meta=precision.load_tangent(directory)
    assert meta['internal_mantissa_bits']>53
    return original,extended,meta,explore.load_kernel(directory)[0]


def test_exact_straight_disc_motion_has_less_accumulation_error(kernels):
    original,extended,meta,_=kernels
    count=20002; theta=np.zeros((count,3)); velocity=np.zeros_like(theta)
    dt=np.full(count,.005);times=np.array([100.])
    initial=np.array([.8,.1,1000.]);speed=np.array([250.,0.,0.]);rotation=np.eye(3).ravel()
    limits=np.zeros(27);limits[3]=1.;point=np.zeros(27)
    results=[]
    for kernel in (original,extended):
        out=np.empty((1,3));jac=np.empty((3,27));boundaries=ctypes.c_int()
        code=kernel(count,theta,velocity,dt,1,times,initial,speed,rotation,limits,point,2,0,0.,6371000.,out,jac,ctypes.byref(boundaries))
        assert code==0
        results.append((out,jac))
    with localcontext() as context:
        context.prec=60
        expected=float(Decimal.from_float(.8)+Decimal(250)*Decimal(100)/Decimal(6371000))
    old_error=abs(results[0][0][0,0]-expected)
    new_error=abs(results[1][0][0,0]-expected)
    assert old_error>1e-14
    assert new_error<old_error*.05
    assert results[1][1][0,3]==pytest.approx(100/6371000.,rel=1e-10)
    assert results[1][0][0,1]==.1
    assert results[1][0][0,2]==1000.


@pytest.mark.parametrize('model',explore.MODELS)
@pytest.mark.parametrize('profile',[False,True])
def test_extended_values_and_every_derivative_match_independent_difference(kernels,model,profile):
    original,extended,meta,value=kernels
    p=problem((value,extended),profile=profile)
    point=np.full(len(p.bounds.active),.03)
    if profile:point[-1]=-.3
    predicted,jac,boundaries=p.prediction_tangent(point,model)
    metric=np.tile([6371000.,6371000.,1.],len(p.gps))
    assert np.max(abs((predicted-p.predict(point,model)).ravel()*metric))<3e-7
    assert boundaries==0
    for index in range(len(point)):
        plus=point.copy();minus=point.copy();plus[index]+=.001;minus[index]-=.001
        independent=(p.predict(plus,model)-p.predict(minus,model)).ravel()/.002
        np.testing.assert_allclose(jac[:,index]*metric,independent*metric,atol=8e-5,rtol=3e-5,
                                   err_msg=p.bounds.active[index])


def test_source_adapter_rejects_an_unrecognized_layout():
    with pytest.raises(ValueError,match='layout'):
        precision.extended_source('unrecognized source')


def test_source_keeps_double_abi_and_packet_clock():
    source=Path(shape.__file__).with_name('ilvis0_tangent.cpp').read_text()
    adapted=precision.extended_source(source)
    assert 'const double *theta,const double *dv,const double *dt' in adapted
    assert 'double start=0;size_t j=0;' in adapted
    assert 'double end=start+dt[k]' in adapted
    assert 'std::array<long double,27>' in adapted
    assert 'times[j]+static_cast<double>(p[25].v)<=end' in adapted
