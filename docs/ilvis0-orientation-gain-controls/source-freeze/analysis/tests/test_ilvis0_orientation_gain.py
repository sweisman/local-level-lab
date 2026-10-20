# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import numpy as np
import pytest
from lll import ilvis0_orientation_gain as candidate
from lll.ilvis0_shared_reference_terms import ReferenceErrors
from lll.ilvis0_reference_acceleration import AccelerationTerms
from lll.ilvis0_common_force_transform import ForceTransform
from test_ilvis0_shared_reference_terms import config


def components(fixed=False):
    lo=-np.ones(27);hi=np.ones(27);center=np.zeros(27)
    lo[2]=0.;hi[2]=.25;center[2]=.125
    if fixed:lo=center.copy();hi=center.copy()
    r=ReferenceErrors(config(),lo,hi,center)
    return AccelerationTerms(r,[.001,-.002,-.04905],.005,9.81),ForceTransform(r)


def test_signed_gain_upper_uses_safe_chord_or_tangent():
    for h in (F(-2),F(0),F(3)):
        a,b,kind=candidate.gain_upper(h,F(-9,10),F(9,10),F(1,10))
        assert kind==('tangent' if h<0 else 'chord')
        for n in range(33):
            g=F(-9,10)+F(18,10)*F(n,32)
            assert a+b*g>=h/(1+g)
    a,b,_=candidate.gain_upper(F(-2),F(1,8),F(1,8),F(1,8))
    assert a+b*F(1,8)==F(-16,9)
    with pytest.raises(ValueError):candidate.gain_upper(F(-1),F(-1),F(0),F(0))


def test_directional_support_preserves_lower_projection_and_polynomial_tail():
    assert candidate.orientation_upper([F(-1),F(0),F(0)],[F(1),F(0),F(0)],F(0),F(1,2))==F(-7,8)
    assert candidate.orientation_upper([F(1),F(0),F(0)],[F(1),F(0),F(0)],F(0),F(1,2))==F(1)
    assert candidate.orientation_upper([F(-1),F(0),F(0)],[F(99,100),F(0),F(0)],F(1,100),F(0))>=F(-1)


def test_contracted_matrix_column_is_excluded_without_narrowing_physical_bounds():
    from lll import ilvis0_rotation_gain_support as old
    a,m=components();point=np.r_[m.reference.center,np.zeros(24)]
    for i in range(3):point[42+3*i]=-.2*m.center[i,0]/m.caps[3*i]
    assert np.all(abs(point[27:])<=1)
    assert max(old.exact_slacks(old.build(a,m),point))<=0
    cut=candidate.build(a,m)
    assert cut.design.shape==(78,51) and max(candidate.exact_slacks(cut,point))>0
    assert cut.report()['version']==candidate.VERSION


def test_known_matrix_maps_and_point_domain_are_retained():
    for fixed in (False,True):
        a,m=components(fixed);cut=candidate.build(a,m);r=m.reference
        rng=np.random.default_rng(17)
        for point in (r.center,r.lower,r.upper,*[r.lower+(r.upper-r.lower)*x for x in rng.random((8,27))]):
            lifted=np.r_[point,np.zeros(15),m.normalized_values_at(point)]
            assert max(candidate.exact_slacks(cut,lifted))<=0
    with pytest.raises(ValueError):candidate.build(None,m)
