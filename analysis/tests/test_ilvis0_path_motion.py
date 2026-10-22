# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import pytest


def test_native_polynomial_rotation_has_known_noncommuting_zero_derivatives():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_motion import exponential
    s=J.affine(0,[1,1],[0,0]);matrix=exponential([s,s.square(),s**3])
    # Entry -s³ + (s*s²)/2 has third derivative -6+3 = -3.
    assert matrix[0][1].exact[3]==(F(-3),)*2
    assert matrix[1][2].exact[1]==(F(-1),)*2
    assert matrix[0][2].exact[2]==(F(2),)*2


def test_native_rotation_rejects_a_domain_crossing_its_polynomial_switch():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_motion import exponential
    with pytest.raises(ValueError):exponential([J.constant(0),J.constant(0),J.constant(['0.009','0.011'])])


def test_large_rotation_encloses_an_independent_scalar_series():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_motion import exponential
    from test_ilvis0_path_jets import trig_interval
    matrix=exponential([J.constant(0),J.constant(0),J.constant(F(1,4))])
    lo,hi=matrix[0][0].exact[0];a,b=trig_interval(F(1,4),True)
    assert lo<=a<=b<=hi


def test_disc_north_leg_has_exact_acceleration_and_height_path_derivatives():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_motion import State,step
    c=lambda v:J.constant(v)
    identity=tuple(tuple(c(int(i==j)) for j in range(3)) for i in range(3))
    state=State((c(0),c(0),c(1000)),(c(200),c(0),c(0)),identity)
    s=J.affine(0,[1,1],[0,0]);period=c(F(1,200));gravity=c(F(49,5))
    result=step(2,state,[c(0)]*3,[c(0),c(0),(-gravity+s)*period],period,gravity,c(6000000),c(0))
    for value,expected in ((result.velocity[2],F(1,200)),(result.coordinates[2],F(-1,80000))):
        lo,hi=value.exact[1]
        assert lo<=expected<=hi and hi-lo<F(1,2**80)
    assert result.coordinates[0].exact[0][0]<=F(1,6000000)<=result.coordinates[0].exact[0][1]
    assert result.coordinates[2].exact[0][0]<=1000<=result.coordinates[2].exact[0][1]
    assert result.report()['floating_point_execution_covered'] is False


def test_zero_field_globe_stationary_balance_keeps_position_and_velocity():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_motion import State,step
    c=lambda v:J.constant(v)
    identity=tuple(tuple(c(int(i==j)) for j in range(3)) for i in range(3))
    state=State((c(0),c(0),c(1000)),(c(0),)*3,identity)
    period=c(F(1,200));g=c(F(49,5))
    answer=step(1,state,[c(0)]*3,[c(0),c(0),-g*period],period,g,c(6000000),c(0))
    for value,expected in zip((*answer.coordinates,*answer.velocity),(0,0,1000,0,0,0)):
        lo,hi=value.exact[0]
        assert lo<=expected<=hi and hi-lo<F(1,2**80)


def test_gain_error_reaches_velocity_and_height_through_third_order():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_motion import State,step
    c=lambda v:J.constant(v)
    identity=tuple(tuple(c(int(i==j)) for j in range(3)) for i in range(3))
    state=State((c(0),c(0),c(1000)),(c(0),)*3,identity)
    s=J.affine(0,[1,1],[0,0]);dt=c(F(1,200));g=c(F(49,5))
    answer=step(2,state,[c(0)]*3,[c(0),c(0),-g*dt/(1+s/2)],dt,g,c(6000000),c(0))
    # a(s)=g*(1-1/(1+s/2)); v=a*dt and height change=-a*dt²/2.
    for n,acceleration in enumerate((F(0),F(49,10),F(-49,10),F(147,20))):
        for value,expected in ((answer.velocity[2],acceleration/200),
                (answer.coordinates[2],(1000 if n==0 else 0)-acceleration/80000)):
            lo,hi=value.exact[n]
            assert lo<=expected<=hi and hi-lo<F(1,2**80)


def test_invalid_state_and_period_cannot_silently_produce_bounds():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_motion import State,step
    with pytest.raises(ValueError):State((J.constant(0),)*2,(J.constant(0),)*3,())
    c=lambda v:J.constant(v)
    identity=tuple(tuple(c(int(i==j)) for j in range(3)) for i in range(3))
    state=State((c(0),)*3,(c(0),)*3,identity)
    with pytest.raises(ValueError):step(0,state,[c(0)]*3,[c(0)]*3,c(-1),c(10),c(6000000),c(0))


@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('removal',[F(0),F(1,2)])
def test_stationary_equatorial_controls_preserve_the_common_removal_convention(model,removal):
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_motion import State,step
    c=lambda v:J.constant(v)
    identity=tuple(tuple(c(int(i==j)) for j in range(3)) for i in range(3))
    state=State((c(0),c(0),c(1000)),(c(0),)*3,identity)
    dt=F(1,200);omega=F(7.2921150e-5);g=F(49,5)
    # At the equator a stationary body has only the north component.
    # Upstream removal subtracts the same specified vector in every model.
    angle=((1 if model==0 else 0)-removal)*omega*dt
    answer=step(model,state,[c(angle),c(0),c(0)],[c(0),c(0),c(-g*dt)],
        c(dt),c(g),c(6000000),c(removal))
    for value,expected in zip((*answer.coordinates,*answer.velocity),(0,0,1000,0,0,0)):
        lo,hi=value.exact[0]
        assert lo<=expected<=hi and hi-lo<F(1,10**20)
    for i in range(3):
        for j in range(3):
            lo,hi=answer.attitude[i][j].exact[0]
            assert lo<=int(i==j)<=hi and hi-lo<F(1,10**20)
