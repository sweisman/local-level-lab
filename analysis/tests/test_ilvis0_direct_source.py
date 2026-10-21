# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import numpy as np
import pytest
from test_ilvis0_source_point_derivatives import source,_rational_frames


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    from lll.ilvis0_source_point_derivatives import load_kernel
    return load_kernel(tmp_path_factory.mktemp('direct-source'))[0]


@pytest.mark.parametrize('time',(3/512,2/256))
@pytest.mark.parametrize('wide_gains',(False,True))
def test_direct_remainders_contain_independent_calibrated_rotation_chains(kernel,time,wide_gains):
    from lll.ilvis0_direct_source import DirectStream,radius
    case=source();case['configuration']['limits']=np.full(27,1/2)
    case['configuration']['initial_r']=np.diag([1.,1+1/1024,1-1/1024])
    case['theta']=np.array([[1,2,-1],[-2,1,3],[2,-3,1],[1,1,-2]],float)/1024
    case['dv'][:]=[1/512,-1/1024,-10/256]
    center=np.zeros(27);center[:3]=[1/32,-1/16,1/64];center[9:15]=np.arange(1,7)/1024
    center[15:21]=2.
    lo=center-np.full(27,1/1024);hi=center+np.full(27,1/1024)
    # Keep sampled gains dyadic with unit denominators for the independent
    # rational angle reference, while retaining a nonzero gain-error domain.
    samples=[]
    for sign in (-1,0,1):
        z=center.copy();z[:15]+=sign/1024;z[25]+=sign/1024;samples.append(z)
    if wide_gains:
        lo[15:21]=0.
        z=center.copy();z[:15]+=1/1024;z[15:21]=0.;samples.append(z)
    independent=[list(_rational_frames(case,z,time)) for z in samples]
    nominal=list(_rational_frames(case,center,time))
    stream=DirectStream(kernel,case,center,lo,hi,time,maximum_packets=4)
    for packet in range(4):
        frame=stream.append()
        for phase in range(2):
            # Deliberately displaced centers/rows exercise the reconciliation,
            # not only a perfect reference with no numerical mismatch.
            values=frame.point_values[...,0].copy();rows=frame.point_jacobian[...,0].copy()
            values[phase,1,0]+=1/65536;rows[phase,1,0,1]+=1/1024
            radii=radius(frame,values,rows,phase=phase)
            for s,z in enumerate(samples):
                delta=list(map(F,z-center))
                for component in range(2):
                    for axis in range(3):
                        actual=independent[s][packet][phase][component][axis][0][0]
                        native=F(values[phase,component,axis])+sum((F(rows[phase,component,axis,j])*delta[j] for j in range(27)),F(0))
                        assert abs(actual[0]-native)<=F(radii[component,axis])
                        assert abs(actual[1]-native)<=F(radii[component,axis])
                        ref_v,ref_j=nominal[packet][phase][component][axis][0]
                        ideal=ref_v
                        for j in range(27):
                            products=[x*delta[j] for x in ref_j[j]]
                            ideal=(ideal[0]+min(products),ideal[1]+max(products))
                        remainder=F(frame.ideal_remainder[phase][component])
                        assert actual[0]-ideal[1]>=-remainder
                        assert actual[1]-ideal[0]<=remainder


def test_bridge_accounts_for_all_columns_and_rejects_domain_mismatch(kernel):
    from lll.ilvis0_direct_source import DirectStream,radius
    center=np.zeros(27);lo=np.full(27,-1/1024);hi=np.full(27,1/1024)
    stream=DirectStream(kernel,source(),center,lo,hi,3/512,maximum_packets=2)
    frame=stream.append();values=np.zeros((2,2,3));rows=np.zeros((2,2,3,27))
    a=radius(frame,values,rows,phase=0)
    rows[0,0,0,26]=1024
    b=radius(frame,values,rows,phase=0)
    assert b[0,0]>=a[0,0]+1
    assert not a.flags.writeable and not frame.point_values.flags.writeable
    with pytest.raises(ValueError):radius(frame,values,rows[:,:,:,:26],phase=0)
    with pytest.raises(ValueError):radius(frame,values,rows,phase=True)
    lo[25]=-1
    with pytest.raises(ValueError):DirectStream(kernel,source(),center,lo,hi,3/512,maximum_packets=2)
    stream.append()
    with pytest.raises(ValueError):stream.append()
    stream.close()
    with pytest.raises(ValueError):stream.append()
