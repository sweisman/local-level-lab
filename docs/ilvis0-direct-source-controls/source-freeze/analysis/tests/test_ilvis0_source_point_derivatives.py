# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import numpy as np
import pytest


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    from lll.ilvis0_source_point_derivatives import load_kernel
    return load_kernel(tmp_path_factory.mktemp('source-point-derivatives'))[0]


def source():
    config=dict(initial_r=np.eye(3),limits=np.ones(27))
    theta=np.tile([0.,1/1024,0.],(4,1));dv=np.tile([0.,0.,-10/256],(4,1));dt=np.full(4,1/256)
    return dict(configuration=config,theta=theta,dv=dv,dt=dt)


def test_nonzero_point_values_and_gyro_rows_enclose_rational_reference(kernel):
    from lll.ilvis0_source_point_derivatives import Stream
    from lll.ilvis0_rotation_roundoff import enclose as values
    from lll.ilvis0_rotation_derivative import enclose as derivatives
    case=source();z=np.zeros(27);z[1]=1/16;z[10]=1/1024;z[16]=z[20]=1;z[14]=1/256
    force=-(F(10)+F(1,256))/2;mount=F(1,16);corrected=(F(1,1024)-F(1,1024)/256)/2
    stream=Stream(kernel,case,z,4/256,maximum_packets=4)
    for packet in range(4):
        frame=stream.append()
        for phase,factor in enumerate((F(1,2),F(1))):
            steps=packet+factor;angle=mount+steps*corrected
            assert F(float(angle))==angle
            v=values([0.,float(angle),0.],np.eye(3));initial=values([0.,float(mount),0.],np.eye(3))
            j=derivatives([0.,float(angle),0.])
            for axis in range(3):
                initial_force=sorted(force*F(initial[k][axis][2]) for k in ('lower','upper'))
                actual_force=sorted(force*F(v[k][axis][2]) for k in ('lower','upper'))
                lo,hi=map(F,frame['point_values'][phase,0,axis])
                assert lo<=initial_force[0] and hi>=initial_force[1]
                lo,hi=map(F,frame['point_values'][phase,1,axis])
                assert lo<=actual_force[0]-initial_force[1] and hi>=actual_force[1]-initial_force[0]
                for column,slope in ((10,-steps/F(256)/2),(16,-steps*corrected/2)):
                    expected=sorted(force*F(j[k][1][axis][2])*slope for k in ('lower','upper'))
                    lo,hi=map(F,frame['point_jacobian'][phase,1,axis,column])
                    assert lo<=expected[0] and hi>=expected[1]
    unused=[3,4,5,6,7,8,21,22,23,24,26]
    assert not np.any(frame['point_jacobian'][:,:,:,unused])
    assert frame['parameter_count']==27 and frame['state_bytes']<65536


def test_point_clock_boundary_encloses_native_preceding_packet_slope(kernel):
    from lll.ilvis0_source_point_derivatives import Stream
    from lll.ilvis0_rotation_derivative import enclose
    stream=Stream(kernel,source(),np.zeros(27),2/256,maximum_packets=4)
    stream.append();frame=stream.append();j=enclose([0.,2/1024,0.])
    for axis in range(3):
        lo,hi=map(F,frame['point_jacobian'][1,1,axis,25]);assert lo<=0<=hi
        for key in ('lower','upper'):
            expected=-10*F(j[key][1][axis][2])/4
            assert lo<=expected<=hi


def test_point_stream_owns_inputs_and_rejects_excess_work(kernel):
    from lll.ilvis0_source_point_derivatives import Stream
    case=source();z=np.zeros(27);stream=Stream(kernel,case,z,2/256,maximum_packets=2)
    case['theta'][:]=np.nan;case['dt'][:]=np.nan;z[:]=np.nan
    frame=stream.append();assert np.all(np.isfinite(frame['point_jacobian']))
    assert not frame['point_values'].flags.writeable and not frame['point_jacobian'].flags.writeable
    stream.append()
    with pytest.raises(ValueError):stream.append()
    stream.close()
    with pytest.raises(ValueError):stream.append()


def _interval(value):
    value=F(value);return (value,value)


def _add(a,b):return (a[0]+b[0],a[1]+b[1])
def _negative(a):return (-a[1],-a[0])
def _product(a,b):
    corners=[x*y for x in a for y in b];return (min(corners),max(corners))


def _jet(value,rows=None):return (_interval(value),[_interval(x) for x in (rows or [0]*27)])
def _jet_add(a,b):return (_add(a[0],b[0]),[_add(x,y) for x,y in zip(a[1],b[1],strict=True)])
def _jet_product(a,b):
    return (_product(a[0],b[0]),[_add(_product(x,b[0]),_product(a[0],y))
        for x,y in zip(a[1],b[1],strict=True)])


def _matrix_product(a,b):
    return [[sum_jets([_jet_product(a[i][k],b[k][j]) for k in range(3)])
        for j in range(len(b[0]))] for i in range(3)]


def sum_jets(items):
    result=_jet(0)
    for item in items:result=_jet_add(result,item)
    return result


def _rational_rotation(angle,rows):
    from lll.ilvis0_rotation_roundoff import enclose as values
    from lll.ilvis0_rotation_derivative import enclose as derivatives
    assert all(F(float(x))==x for x in angle)
    value=values(list(map(float,angle)),np.eye(3));jac=derivatives(list(map(float,angle)))
    out=[]
    for i in range(3):
        row=[]
        for j in range(3):
            d=[]
            for col in range(27):
                total=_interval(0)
                for axis in range(3):
                    part=tuple(F(jac[key][axis][i][j]) for key in ('lower','upper'))
                    total=_add(total,_product(part,_interval(rows[axis][col])))
                d.append(total)
            row.append((tuple(F(value[key][i][j]) for key in ('lower','upper')),d))
        out.append(row)
    return out


def _rational_frames(case,z,time):
    """Separate rational product/chain rule; no interval-AD source kernel."""
    limits=list(map(F,case['configuration']['limits']));p=[a*F(b) for a,b in zip(limits,z,strict=True)]
    mount_rows=[[limits[j] if axis==j else F(0) for j in range(27)] for axis in range(3)]
    mount=_rational_rotation(p[:3],mount_rows)
    initial=[[_jet(v) for v in row] for row in case['configuration']['initial_r']]
    r=_matrix_product(initial,mount);f=[];t=F(case['dt'][0])
    for axis in range(3):
        force=(F(case['dv'][0,axis])/t-p[12+axis])/(1+p[18+axis]);rows=[F(0)]*27
        rows[12+axis]=-limits[12+axis]/(1+p[18+axis])
        rows[18+axis]=-force*limits[18+axis]/(1+p[18+axis])
        f.append([_jet(force,rows)])
    a=_matrix_product(r,f);body=[[_jet(int(i==j)) for j in range(3)] for i in range(3)]
    start=F(0);query=F(time)+p[25]
    for packet,period in enumerate(case['dt']):
        t=F(period);fraction=max(F(0),min(F(1),(query-start)/t))
        slope=1/t if start<query<=start+t or start==query==0 else F(0)
        corrected=[];rows=[]
        for axis in range(3):
            unscaled=(F(case['theta'][packet,axis])-p[9+axis]*t)/(1+p[15+axis])
            row=[F(0)]*27;row[9+axis]=-t*limits[9+axis]*fraction/(1+p[15+axis])
            row[15+axis]=-unscaled*limits[15+axis]*fraction/(1+p[15+axis])
            row[25]=unscaled*slope*limits[25];corrected.append(unscaled*fraction);rows.append(row)
        frame=[]
        for factor in (F(1,2),F(1)):
            step=_rational_rotation([factor*x for x in corrected],[[factor*x for x in row] for row in rows])
            current=_matrix_product(body,step)
            departure=[[_jet_add(current[i][j],_jet(-int(i==j))) for j in range(3)] for i in range(3)]
            b=_matrix_product(r,_matrix_product(departure,f));frame.append((a,b))
        yield frame
        body=current;start+=t


@pytest.mark.parametrize('time',(0.,3/512,2/256))
def test_all_columns_noncommuting_source_against_rational_chain_rule(kernel,time):
    from lll.ilvis0_source_point_derivatives import Stream
    case=source();case['configuration']['initial_r']=np.diag([1.,1+1/1024,1-1/1024])
    case['configuration']['limits']=np.full(27,1/2)
    case['theta']=np.array([[1,2,-1],[-2,1,3],[2,-3,1],[1,1,-2]],float)/1024
    case['dv'][:]=[1/512,-1/1024,-10/256]
    z=np.zeros(27);z[:3]=[1/32,-1/16,1/64];z[9:15]=np.arange(1,7)/1024
    z[15:21]=2.;stream=Stream(kernel,case,z,time,maximum_packets=4)
    for expected in _rational_frames(case,z,time):
        actual=stream.append()
        for phase in range(2):
            for source_index in range(2):
                for axis in range(3):
                    v,j=expected[phase][source_index][axis][0]
                    lo,hi=map(F,actual['point_values'][phase,source_index,axis])
                    assert lo<=v[0]<=v[1]<=hi
                    for col in range(27):
                        lo,hi=map(F,actual['point_jacobian'][phase,source_index,axis,col])
                        assert lo<=j[col][0]<=j[col][1]<=hi,(phase,source_index,axis,col)


def test_point_inputs_reject_invalid_shapes_domains_and_limits(kernel):
    from lll.ilvis0_source_point_derivatives import Stream
    for limit in (0,5,True):
        with pytest.raises(ValueError):Stream(kernel,source(),np.zeros(27),0.,maximum_packets=limit)
    for time in (-1.,1.,float('nan')):
        with pytest.raises(ValueError):Stream(kernel,source(),np.zeros(27),time,maximum_packets=1)
    z=np.zeros(27);z[15]=-1.
    with pytest.raises(ValueError):Stream(kernel,source(),z,0.,maximum_packets=1)
