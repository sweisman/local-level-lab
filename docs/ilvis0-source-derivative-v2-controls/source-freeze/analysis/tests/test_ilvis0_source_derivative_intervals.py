# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent rational references for source derivative intervals."""
import importlib.util
from fractions import Fraction as F
import numpy as np
import pytest


def test_source_derivative_component_exists():
    assert importlib.util.find_spec('lll.ilvis0_source_derivative_intervals') is not None


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    from lll.ilvis0_source_derivative_intervals import load_kernel
    return load_kernel(tmp_path_factory.mktemp('source-derivatives'))[0]


@pytest.mark.parametrize('angle',[[0,0,0],[1e-12,-2e-12,3e-12],[.01,-.02,.003],[1.,-.3,.2],[8.,0,0]])
def test_rotation_values_and_derivatives_enclose_rational_reference(angle,kernel):
    from lll.ilvis0_source_derivative_intervals import rotation_intervals
    from lll.ilvis0_rotation_roundoff import enclose as values
    from lll.ilvis0_rotation_derivative import enclose as derivatives
    actual=rotation_intervals(kernel,angle);v=values(angle,np.eye(3));j=derivatives(angle)
    for i in range(3):
        for k in range(3):
            # Both computations enclose the exact value. The independent
            # rational reference is much sharper; require full containment.
            assert F(actual['values'][i,k,0])<=F(v['lower'][i][k])
            assert F(actual['values'][i,k,1])>=F(v['upper'][i][k])
            for axis in range(3):
                assert F(actual['jacobian'][i,k,axis,0])<=F(j['lower'][axis][i][k])
                assert F(actual['jacobian'][i,k,axis,1])>=F(j['upper'][axis][i][k])


def test_zero_motion_force_calibration_and_clock_crossing(kernel):
    from lll.ilvis0_source_derivative_intervals import Stream
    from test_ilvis0_native_box_bounds import configuration
    config=configuration();config['initial_r']=np.eye(3);z=np.zeros(27)
    theta=np.zeros((13,3));dv=np.tile([0.,0.,-.05],(13,1));dt=np.full(13,.005)
    bundle=dict(configuration=config,theta=theta,dv=dv,dt=dt)
    lo=z.copy();hi=z.copy();lo[12:15]=-.2;hi[12:15]=.2
    stream=Stream(kernel,bundle,z,lo,hi,.05,maximum_packets=len(dt))
    for _ in dt:frame=stream.append()
    for phase in range(2):
        for axis in range(3):
            force_z=F(-.05)/F(.005)
            expected=force_z if axis==2 else F(0)
            assert F(frame['point_values'][phase,0,axis,0])<=expected<=F(frame['point_values'][phase,0,axis,1])
            assert frame['values'][phase,1,axis,0]==frame['values'][phase,1,axis,1]==0.
            for column in range(27):
                expected=-F(float(config['limits'][column])) if column==12+axis else F(0)
                if column==20 and axis==2:expected=-force_z*F(float(config['limits'][column]))
                if column==1 and axis==0:expected=force_z*F(float(config['limits'][column]))
                if column==0 and axis==1:expected=-force_z*F(float(config['limits'][column]))
                low,high=frame['jacobian'][phase,0,axis,column]
                assert F(low)<=expected<=F(high)
    assert frame['parameter_count']==27 and frame['state_bytes']<65536
    with pytest.raises(ValueError):stream.append()


def test_mean_value_bound_accounts_for_arbitrary_supplied_rows_and_center():
    from lll.ilvis0_source_derivative_intervals import mean_value_radius
    # Independent cubic source on [-.25,.5], anchored at .125. Its derivative
    # is [0,.75]. The supplied numerical center and row are deliberately off.
    z=np.zeros(27);z[11]=.125;lo=z.copy();hi=z.copy();lo[11]=-.25;hi[11]=.5
    point=np.zeros((2,2,3,2));point[:]=.125**3
    derivative=np.zeros((2,2,3,27,2));derivative[:,:,:,11,1]=.75
    values=np.full((2,2,3),.002);rows=np.zeros((2,2,3,27));rows[:,:,:,11]=.05
    frame=dict(point_values=point,jacobian=derivative,center=z,lower=lo,upper=hi)
    result=mean_value_radius(frame,values,rows,phase=0)
    expected=abs(F(.125)**3-F(.002))+max(abs(F(0)-F(.05)),abs(F(.75)-F(.05)))*F(.375)
    assert all(F(v)>=expected for v in result.flat)
    for x in (-.25,-.125,0.,.125,.5):
        error=abs(F(x)**3-F(.002)-F(.05)*(F(x)-F(.125)))
        assert all(F(v)>=error for v in result.flat)
    with pytest.raises(ValueError):mean_value_radius(frame,values,rows[:,:,:,:26],phase=0)


def test_nonzero_prefix_values_and_bias_gain_rows_match_independent_rational_rotation(kernel):
    from lll.ilvis0_source_derivative_intervals import Stream
    from lll.ilvis0_rotation_roundoff import enclose as values
    from lll.ilvis0_rotation_derivative import enclose as derivatives
    from test_ilvis0_native_box_bounds import configuration
    config=configuration();config['initial_r']=np.eye(3);z=np.zeros(27)
    dt=np.full(4,1/256);theta=np.tile([0.,1/1024,0.],(4,1));dv=np.tile([0.,0.,-10/256],(4,1))
    bundle=dict(configuration=config,theta=theta,dv=dv,dt=dt)
    stream=Stream(kernel,bundle,z,z,z,float(sum(dt)),maximum_packets=4)
    for packet in range(4):
        frame=stream.append()
        for phase,factor in enumerate((F(1,2),F(1))):
            steps=F(packet)+factor;angle=[0.,float(steps/1024),0.]
            v=values(angle,np.eye(3));j=derivatives(angle)
            for axis in range(3):
                baseline=F(-10) if axis==2 else F(0)
                expected=sorted([-10*F(v[key][axis][2])-baseline for key in ('lower','upper')])
                actual=frame['point_values'][phase,1,axis]
                assert F(actual[0])<=expected[0] and F(actual[1])>=expected[1]
                for column,unit in ((10,F(1,256)),(16,F(1,1024))):
                    slope=-steps*unit*F(float(config['limits'][column]))
                    expected=sorted([-10*F(j[key][1][axis][2])*slope for key in ('lower','upper')])
                    actual=frame['jacobian'][phase,1,axis,column]
                    assert F(actual[0])<=expected[0] and F(actual[1])>=expected[1]


def test_clock_domain_crossing_packet_end_contains_both_one_sided_slopes(kernel):
    from lll.ilvis0_source_derivative_intervals import Stream
    from lll.ilvis0_rotation_derivative import enclose
    from test_ilvis0_native_box_bounds import configuration
    config=configuration();z=np.zeros(27);lo=z.copy();hi=z.copy();lo[25]=-.1;hi[25]=.1
    dt=np.full(4,1/256);theta=np.tile([0.,1/1024,0.],(4,1));dv=np.tile([0.,0.,-10/256],(4,1))
    stream=Stream(kernel,dict(configuration=config,theta=theta,dv=dv,dt=dt),z,lo,hi,2/256,maximum_packets=4)
    stream.append();frame=stream.append();derivative=enclose([0.,2/1024,0.])
    for axis in range(3):
        lower,upper=map(F,frame['jacobian'][1,1,axis,25]);assert lower<=0<=upper
        for end in ('lower','upper'):
            slope=-10*F(derivative[end][1][axis][2])*F(1,4)*F(float(config['limits'][25]))
            assert lower<=slope<=upper


def test_invalid_source_domains_and_stream_mutation_are_rejected(kernel):
    from lll.ilvis0_source_derivative_intervals import Stream,rotation_intervals
    from test_ilvis0_native_box_bounds import configuration
    config=configuration();z=np.zeros(27);dt=np.full(2,.005)
    case=dict(configuration=config,theta=np.zeros((2,3)),dv=np.zeros((2,3)),dt=dt)
    for lo,hi in ((np.zeros(26),z),(z,np.full(27,np.nan)),(z+1,z)):
        with pytest.raises(ValueError):Stream(kernel,case,z,lo,hi,.005,maximum_packets=2)
    lower=z.copy();upper=z.copy();lower[18]=-2000.
    with pytest.raises(ValueError):Stream(kernel,case,z,lower,upper,.005,maximum_packets=2)
    with pytest.raises(ValueError):rotation_intervals(kernel,[float('nan'),0,0])
    stream=Stream(kernel,case,z,z,z,.005,maximum_packets=2)
    case['theta'][:]=np.nan;case['dt'][:]=np.nan
    frame=stream.append();assert np.all(np.isfinite(frame['values']))
    assert not frame['values'].flags.writeable
    stream.close()
    with pytest.raises(ValueError):stream.append()
