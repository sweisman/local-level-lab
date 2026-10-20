# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import math
from types import SimpleNamespace
import numpy as np
import pytest
from lll import ilvis0_column_orientation as candidate
from lll.ilvis0_shared_reference_terms import ReferenceErrors
from lll.ilvis0_reference_acceleration import AccelerationTerms
from lll.ilvis0_common_force_transform import ForceTransform
from test_ilvis0_shared_reference_terms import config


def reference(fixed=False):
    lo=-np.ones(27);hi=np.ones(27);center=np.zeros(27)
    lo[2]=0.;hi[2]=.25;center[2]=.125
    if fixed:lo=center.copy();hi=center.copy()
    return ReferenceErrors(config(),lo,hi,center)


def rotation(v):
    x,y,z=v;angle=float(np.linalg.norm(v));k=np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
    return np.eye(3) if not angle else np.eye(3)+math.sin(angle)/angle*k+(1-math.cos(angle))/angle**2*(k@k)


def test_pure_axial_rotation_and_point_domain_have_zero_column_motion():
    for axis in range(3):
        cfg=config();cfg['limits']=np.array(cfg['limits']);cfg['limits'][:3]=0.;cfg['limits'][axis]=math.pi
        r=ReferenceErrors(cfg,-np.ones(27),np.ones(27),np.zeros(27))
        assert candidate.column_distance(r,axis)==0
    r=reference(True)
    assert all(candidate.column_distance(r,j)==0 for j in range(3))


def test_column_distances_retain_source_box_and_improve_the_vertical_column():
    r=reference();delta=[F(float(r.limits[k]))*max(F(float(r.center[k]))-F(float(r.lower[k])),
        F(float(r.upper[k]))-F(float(r.center[k]))) for k in range(3)]
    previous=min(F(2),candidate._norm(delta))
    assert all(0<=candidate.column_distance(r,j)<=previous for j in range(3))
    assert candidate.column_distance(r,2)<previous
    with pytest.raises(ValueError):candidate.column_distance(r,3)
    with pytest.raises(ValueError):candidate.column_distance(SimpleNamespace(),0)


def test_independent_rodrigues_pairs_are_contained():
    r=reference();center=r.limits[:3]*r.center[:3];base=rotation(center)
    rng=np.random.default_rng(20261020)
    for point in (r.lower,r.upper,*[r.lower+(r.upper-r.lower)*v for v in rng.random((32,27))]):
        actual=rotation(r.limits[:3]*point[:3])
        for axis in range(3):
            assert np.linalg.norm(actual[:,axis]-base[:,axis])<=float(candidate.column_distance(r,axis))+1e-13


def test_extra_contracted_vertical_column_is_excluded():
    from lll import ilvis0_orientation_gain as previous
    r=reference();a=AccelerationTerms(r,[.001,-.002,-.04905],.005,9.81);m=ForceTransform(r)
    point=np.r_[r.center,np.zeros(24)]
    for i in range(3):point[42+3*i+2]=-.06*m.center[i,2]/m.caps[3*i+2]
    assert np.all(abs(point[27:])<=1)
    assert max(previous.exact_slacks(previous.build(a,m),point))<=0
    cut=candidate.build(a,m)
    assert max(candidate.exact_slacks(cut,point))>0
    assert cut.report()['version']==candidate.VERSION and cut.design.shape==(78,51)
