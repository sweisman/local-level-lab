# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import numpy as np
import pytest
from lll.ilvis0_directional_values import Value
from lll.ilvis0_directional_scalar import multiply,reciprocal,square_root,recenter,vertical_departure


@pytest.mark.parametrize('kind',['multiply','reciprocal','square_root'])
def test_scalar_operators_cover_exact_known_curves_and_derivatives(kind):
    if kind=='square_root':
        value=Value(4.,F(41,100),F(1,100));result=square_root(value);linear=F(1,10)
    elif kind=='reciprocal':
        value=Value(2.,F(3,8),F(1,8));result=reciprocal(value);linear=F(-1,16)
    else:
        result=multiply(Value(2.,F(3,8),F(1,8)),Value(3.,F(3,16),F(1,16)));linear=F(1,2)
    for k in range(-32,33):
        t=F(k,32)
        if kind=='square_root':truth=2+t/10  # input = (2+t/10)^2
        elif kind=='reciprocal':truth=1/(2+t/4+t*t/8)
        else:truth=(2+t/4+t*t/8)*(3-t/8+t*t/16)
        assert abs(truth-F(result.center.item()))<=F(result.change.item())
        assert abs(truth-F(result.center.item())-linear*t)<=F(result.remainder.item())


def test_recenter_accounts_for_constant_shift_in_both_bounds():
    value=Value(.1,.01,.001);result=recenter(value,.2)
    assert F(result.change.item())>=F(.01)+abs(F(.2)-F(.1))
    assert F(result.remainder.item())>=F(.001)+abs(F(.2)-F(.1))


@pytest.mark.parametrize('sign',[-1,1])
def test_norm_preserving_small_tilt_recovers_quadratic_vertical_change(sign):
    eps=F(1,1000);a=Value([0.,0.,float(sign)],[0.]*3,[0.]*3)
    b=Value([0.]*3,[eps,0.,eps],[eps**2/2,0.,eps**2/2])
    result=vertical_departure(a,b,norm_identity=True,linearization_consistent=True)
    assert result.change<.000001 and result.remainder<.000001
    for t in np.linspace(-1,1,65):
        actual=sign*(np.cos(float(eps)*t)-1)
        assert abs(actual-result.center)<=result.change+2e-15
        assert abs(actual-result.center)<=result.remainder+2e-15


def test_two_horizontal_uncertainties_keep_their_combined_quadratic_allowance():
    eps=F(1,1000);a=Value([0.,0.,-1.],[0.]*3,[0.]*3)
    b=Value([0.]*3,[eps]*3,[eps**2]*3)
    result=vertical_departure(a,b,norm_identity=True,linearization_consistent=True)
    assert result.change>=float(eps**2) and result.change<float(2*eps**2)


def test_variable_force_and_rotation_share_the_same_parameter():
    from lll import ilvis0_local_step_bounds as old,ilvis0_relative_rotation as relative
    eps=.001;center=np.array([.05,-.03,-9.81]);first=np.array([.1,.05,.1])
    a=Value(center,abs(first),[0.]*3)
    raw=relative.apply(relative.minus_identity(old.exponential(old.Value([0.,0.,0.],eps,0.))),
        old.Value(center,float(np.linalg.norm(first)),0.))
    b=Value(raw.center,[raw.change]*3,[raw.remainder]*3)
    result=vertical_departure(a,b,norm_identity=True,linearization_consistent=True);linear=-eps*center[0]
    for t in np.linspace(-1,1,129):
        force=center+first*t;angle=eps*t
        actual=-np.sin(angle)*force[0]+(np.cos(angle)-1)*force[2]
        assert abs(actual-result.center)<=result.change+2e-14
        assert abs(actual-result.center-linear*t)<=result.remainder+2e-14


@pytest.mark.parametrize('kind',['reciprocal','square_root'])
def test_domains_crossing_singularities_are_rejected(kind):
    with pytest.raises(ValueError):{'reciprocal':reciprocal,'square_root':square_root}[kind](Value(1.,2.,0.))


def test_vertical_closure_requires_identity_and_unambiguous_sign_branch():
    a=Value([0.,0.,-1.],[0.]*3,[0.]*3);b=Value([0.]*3,[.01]*3,[.001]*3)
    with pytest.raises(ValueError,match='identity'):vertical_departure(a,b)
    with pytest.raises(ValueError,match='linearization'):vertical_departure(a,b,norm_identity=True)
    with pytest.raises(ValueError,match='branch'):vertical_departure(a,Value([0.]*3,[2.]*3,[1.]*3),norm_identity=True,linearization_consistent=True)
