# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import math

import numpy as np
import pytest


def test_actual_derivative_leibniz_and_reciprocal_conventions():
    from lll.ilvis0_path_jets import Jet3
    s=Jet3.affine(0,[1,1],[0,0]);q=s.square()/(1+s)
    assert q.exact==((F(0),F(0)),(F(0),F(0)),(F(2),F(2)),(F(-6),F(-6)))
    with pytest.raises(ValueError):Jet3.constant([-1,1]).inverse()


def test_calibration_derivative_bounds_feed_the_same_jet_convention():
    from lll.ilvis0_path_jets import Jet3
    from lll.ilvis0_calibration_path import enclose
    row=enclose(raw=1,period=1,bias_center=0,gain_center=0,bias_direction=[0,0],
        gain_direction=['1/2','1/2'],path=[0,0])
    q=Jet3(row['exact_derivatives'])
    assert q.exact[3]==(F(-3,4),F(-3,4))
    assert not q.report()['native_motion_qualified']
    with pytest.raises(ValueError):Jet3(row['exact_derivatives'][:3])


def test_zero_angle_noncommuting_rotation_derivatives_are_exact():
    from lll.ilvis0_path_jets import Jet3,exp_skew
    x=Jet3([[0,0],[1,1],[0,0],[0,0]])
    y=Jet3([[0,0],[0,0],[2,2],[0,0]])
    z=Jet3([[0,0],[0,0],[0,0],[6,6]])
    q=exp_skew([x,y,z])
    a=np.array([[0,0,0],[0,0,-1],[0,1,0]])
    b=np.array([[0,0,1],[0,0,0],[-1,0,0]])
    c=np.array([[0,-1,0],[1,0,0],[0,0,0]])
    known=[np.eye(3,dtype=int),a,2*b+a@a,6*c+3*(a@b+b@a)+a@a@a]
    for n,value in enumerate(known):
        for i in range(3):
            for j in range(3):assert q.matrix[i][j].exact[n]==(F(int(value[i,j])),)*2


def trig_interval(x,cosine):
    # Independent alternating scalar series, not a matrix exponential.
    degree=lambda j:2*j if cosine else 2*j+1
    partial=sum(((-1)**j*x**degree(j)/math.factorial(degree(j)) for j in range(20)),F(0))
    following=x**degree(20)/math.factorial(degree(20))
    return partial,partial+following


def test_nonzero_rotation_encloses_independent_trigonometric_derivatives():
    from lll.ilvis0_path_jets import Jet3,exp_skew
    zero=Jet3.constant(0);z=Jet3.affine(0,[1,1],[F(1,4)]*2)
    result=exp_skew([zero,zero,z]);co=trig_interval(F(1,4),True);si=trig_interval(F(1,4),False)
    expected=[co,tuple(-v for v in si),tuple(-v for v in co),si]
    for order,values in enumerate(expected):
        lo,hi=result.matrix[0][0].exact[order]
        assert lo<=min(values)<=max(values)<=hi
    assert not result.report()['native_motion_qualified']


def test_rotation_enclosure_rejects_an_unsupported_norm_or_degree():
    from lll.ilvis0_path_jets import Jet3,exp_skew
    zero=Jet3.constant(0)
    with pytest.raises(ValueError):exp_skew([zero,zero,Jet3.constant(9)])
    with pytest.raises(ValueError):exp_skew([zero]*3,terms=2)


def test_dyadic_rounding_encloses_each_derivative_and_limits_denominators():
    from lll.ilvis0_path_jets import Jet3
    source=Jet3([[F(-1,3),F(1,7)],[F(1,3)]*2,[F(-1,7)]*2,[0,0]])
    rounded=source.rounded(binary_bits=48)
    for old,new in zip(source.exact,rounded.exact):
        assert new[0]<=old[0]<=old[1]<=new[1]
        assert all((1<<48)%v.denominator==0 for v in new)
        assert old[0]-new[0]<F(1,1<<48) and new[1]-old[1]<F(1,1<<48)
    with pytest.raises(ValueError):source.rounded(binary_bits=1)
