# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import numpy as np
import pytest
from lll import ilvis0_calibration_consistency as cuts
from lll.ilvis0_shared_reference_terms import ReferenceErrors
from lll.ilvis0_reference_acceleration import AccelerationTerms
from lll.ilvis0_common_force_transform import ForceTransform
from test_ilvis0_shared_reference_terms import config


def components(*,fixed=False):
    center=np.full(27,.1);lo=center if fixed else -np.ones(27);hi=center if fixed else np.ones(27)
    ref=ReferenceErrors(config(),lo,hi,center)
    return AccelerationTerms(ref,[.001,-.002,-.04905],.005,9.81),ForceTransform(ref)


def test_full_calibrations_satisfy_exported_necessary_cuts():
    a,m=components();out=cuts.build(a,m)
    assert out.design.shape==(6,51) and out.upper.shape==(6,)
    rng=np.random.default_rng(402)
    for point in [m.reference.lower,m.reference.upper,*rng.uniform(-1,1,(24,27))]:
        x=np.r_[point,np.zeros(6),a.normalized_values_at(point),m.normalized_values_at(point)]
        assert max(cuts.exact_slacks(out,x))<=F(1,10**11)
    with pytest.raises(ValueError):out.design[0,0]=1.


def test_point_domain_retains_its_center_and_zero_error_coordinates():
    a,m=components(fixed=True);out=cuts.build(a,m)
    x=np.r_[m.reference.center,np.zeros(24)]
    assert max(cuts.exact_slacks(out,x))<=0
    assert out.product_allowance==0


def test_common_error_coordinates_cannot_take_arbitrary_independent_values():
    a,m=components();out=cuts.build(a,m)
    # The pair's independent cube permits acceleration and matrix remainders
    # that no one physical calibration can jointly produce.
    violations=[]
    for row,b in zip(out.design,out.upper):
        box=np.r_[m.reference.center,np.where(row[27:]>=0,1.,-1.)]
        violations.append(sum((F(float(v))*F(float(w)) for v,w in zip(row,box)),F(0))-F(float(b)))
    assert max(violations)>0


def test_rejects_another_physical_reference():
    a,m=components();other=ReferenceErrors(dict(config(),source_id='other'),
        m.reference.lower,m.reference.upper,m.reference.center)
    with pytest.raises(ValueError,match='reference'):cuts.build(a,ForceTransform(other))


def test_certified_rotation_polynomial_covers_known_quarter_turn():
    mid,radius=cuts.rotation_polynomial([F(0),F(0),F(3)])
    import math
    expected=np.array([[math.cos(3),-math.sin(3),0],[math.sin(3),math.cos(3),0],[0,0,1.]])
    # The test oracle has floating-point trig error; the analytic tail is
    # checked separately from that independent oracle's numerical precision.
    assert max(abs(float(mid[i][j])-expected[i,j]) for i in range(3) for j in range(3))<2e-15
    assert 0<radius<F(1,10**25)
    with pytest.raises(ValueError):cuts.rotation_polynomial([F(0),F(0),F(20)])


def test_exact_affine_case_keeps_bias_and_gravity_without_error_freedom():
    c=config();c['limits'][:3]=0.;c['limits'][18:21]=0.
    ref=ReferenceErrors(c,-np.ones(27),np.ones(27),np.zeros(27))
    a=AccelerationTerms(ref,[.125,-.25,-1.],.125,8.);m=ForceTransform(ref)
    out=cuts.build(a,m)
    for point in (ref.lower,ref.center,ref.upper):
        assert max(cuts.exact_slacks(out,np.r_[point,np.zeros(24)]))==0
    assert np.count_nonzero(out.design)==0
