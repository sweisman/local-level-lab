# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util

import numpy as np
import pytest
from scipy.linalg import expm
from test_ilvis0_source_norm_preflight import fixture


def test_source_reference_component_exists():
    assert importlib.util.find_spec('lll.ilvis0_source_reference') is not None


@pytest.fixture(scope='module')
def compiled(tmp_path_factory):
    from lll.ilvis0_source_reference import load_source
    return load_source(tmp_path_factory.mktemp('source-reference'))[0]


def independent_complex_values(case, point, time_s):
    """Matrix exponential oracle, with branch selection on real query time only."""
    config=case['configuration'];p=np.asarray(config['limits'])*point
    def skew(v):
        x,y,z=v
        return np.array([[0,-z,y],[z,0,-x],[-y,x,0]],dtype=np.result_type(v))
    r=np.asarray(config['initial_r'])@expm(skew(p[:3]));dt0=case['dt'][0]
    f=(np.asarray(case['dv'][0])-p[12:15]*dt0)/(1+p[18:21])/dt0
    body=np.eye(3,dtype=np.result_type(point));elapsed=0.;query=time_s+p[25]
    for raw,dt in zip(case['theta'],case['dt'],strict=True):
        end=elapsed+dt
        partial=query.real<=end
        fraction=(query-elapsed)/dt if partial else 1
        theta=(np.asarray(raw)-p[9:12]*dt)/(1+p[15:18])
        body=body@expm(skew(theta*fraction))
        if partial:break
        elapsed=end
    return np.array([r@f,r@(body-np.eye(3))@f])


def test_all_columns_match_two_independent_maps(compiled):
    from lll.ilvis0_source_reference import native_reference, analytic_reference
    case,reference,_,_=fixture();point=reference.parent.center;time=.04123
    native=native_reference(compiled,case,point,time);analytic=analytic_reference(case,point,time)
    expected=independent_complex_values(case,point.astype(complex),time).real
    jac=np.empty((2,3,27))
    for axis in range(27):
        probe=point.astype(complex);probe[axis]+=1e-24j
        jac[:,:,axis]=independent_complex_values(case,probe,time).imag/1e-24
    for report in (native,analytic):
        np.testing.assert_allclose(report['values'],expected,atol=1e-12,rtol=1e-10)
        np.testing.assert_allclose(report['jacobian'],jac,atol=2e-11,rtol=2e-8)
        assert np.asarray(report['jacobian']).shape==(2,3,27)
        assert np.count_nonzero(np.asarray(report['jacobian'])[:,:,[3,4,5,6,7,8,21,22,23,24,26]])==0


def test_nonuniform_periods_and_nonzero_mount(compiled):
    from lll.ilvis0_source_reference import native_reference,analytic_reference
    case,_,_,_=fixture();case['dt']=[.004+.0001*i for i in range(13)]
    point=np.linspace(-.15,.3,27);point[:3]=[.35,-.22,.41]
    native=native_reference(compiled,case,point,.03671);independent=analytic_reference(case,point,.03671)
    np.testing.assert_allclose(native['values'],independent['values'],atol=1e-12)
    np.testing.assert_allclose(native['jacobian'],independent['jacobian'],atol=2e-11,rtol=2e-8)


def test_clock_boundary_uses_preceding_packet_slope(compiled):
    from lll.ilvis0_source_reference import native_reference,analytic_reference
    case,_,_,_=fixture();case['dt']=[.005,.005]
    case['theta']=[[0,.001,0],[0,.005,0]];case['dv']=[[0,0,-.04905]]*2
    case['configuration']['limits'][25]=.001
    point=np.zeros(27);at=native_reference(compiled,case,point,.005)
    independent=analytic_reference(case,point,.005)
    assert at['packet_index']==0 and at['boundary_distance_s']==0
    np.testing.assert_allclose(at['jacobian'],independent['jacobian'],atol=1e-11)
    value=np.asarray(at['values']);jac=np.asarray(at['jacobian'])[:,:,25]
    delta=np.zeros(27);delta[25]=1e-4
    left=np.asarray(native_reference(compiled,case,point-delta,.005)['values'])
    right=np.asarray(native_reference(compiled,case,point+delta,.005)['values'])
    np.testing.assert_allclose((value-left)/1e-4,jac,atol=1e-8,rtol=1e-5)
    assert np.max(abs((right-value)/1e-4-jac))>1e-3


@pytest.mark.parametrize('time',[-.1,1.,float('nan')])
def test_unsupported_time_rejected(compiled,time):
    from lll.ilvis0_source_reference import native_reference,analytic_reference
    case,_,_,_=fixture()
    for function,args in ((native_reference,(compiled,)),(analytic_reference,())):
        with pytest.raises(ValueError,match='support|finite'):
            function(*args,case,np.zeros(27),time)


def test_affine_radius_bounds_any_specified_row_with_asymmetric_domain():
    from fractions import Fraction as F
    from lll.ilvis0_source_reference import affine_radius
    result=affine_radius(F(1),F(3),2.,[2.,-3.],[-.5,-.1],[.25,.7],[0.,.2])
    assert F(result['value_radius'])==1
    assert F(result['linear_radius'])==F(2)*F(.5)+F(3)*max(F(.7)-F(.2),F(.2)-F(-.1))
    assert F(result['affine_radius'])==F(result['value_radius'])+F(result['linear_radius'])
    for x in (-.5,.25):
        for y in (-.1,.7):
            for value in (1.,3.):
                assert abs(value-2.-2*x+3*(y-.2))<=result['upper_float']
    with pytest.raises(ValueError):affine_radius(3,1,2,[1],[0],[1],[0])
