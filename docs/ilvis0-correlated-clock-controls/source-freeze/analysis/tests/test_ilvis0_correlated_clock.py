# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import pytest
from lll import ilvis0_correlated_clock as clock


def clipped(t,start,dt):return min(max(t-start,F(0)),dt)


def test_shared_interior_clock_removes_independent_packet_kinks():
    model=clock.PrefixClock(1.8,1.8-.15,1.8+.15)
    for _ in range(400):result=model.append(.005)
    assert result.slope==1
    assert .44<float(result.independent_remainder)<.45
    assert float(result.remainder)<1e-12
    assert result.clock_defect>0 and result.packets==400


def test_dyadic_clock_is_exactly_linear_when_interval_is_interior():
    model=clock.PrefixClock(F(1,2),F(1,4),F(3,4))
    for _ in range(256):result=model.append(1/256)
    assert result.center==F(1,2) and result.lower==F(1,4) and result.upper==F(3,4)
    assert result.remainder==0 and result.clock_defect==0


def test_all_prefix_bounds_contain_independent_exact_oracle_at_every_knot():
    model=clock.PrefixClock(F(1,16),F(0),F(1,8));packets=[];elapsed=0.
    for i in range(25):
        duration=(.003,.005,.0075)[i%3];packets.append((F(elapsed),F(duration)));elapsed+=duration
        result=model.append(duration)
        points={model.lower,model.upper,model.center}
        points.update(t for start,dt in packets for t in (start,start+dt) if model.lower<=t<=model.upper)
        for t in points:
            value=sum((clipped(t,start,dt) for start,dt in packets),F(0))
            assert result.lower<=value<=result.upper
            assert abs(value-result.center-result.slope*(t-model.center))<=result.remainder


def test_initial_and_internal_one_sided_boundary_slopes():
    first=clock.PrefixClock(0.,0.,.25);assert first.append(.25).slope==1
    boundary=clock.PrefixClock(.5,.25,.75)
    boundary.append(.25);assert boundary.append(.25).slope==1
    assert boundary.append(.25).slope==1  # preceding packet, not following start


def test_upstream_time_remainder_is_retained():
    model=clock.PrefixClock(.5,.25,.75,time_remainder=F(1,100))
    for _ in range(4):result=model.append(.25)
    assert result.remainder==F(1,100)


def test_invalid_duration_tag_and_limits_do_not_advance_state():
    model=clock.PrefixClock(.1,0.,.2,maximum_packets=2);model.append(.125)
    before=model.last
    for value in (0.,-.01,float('nan')):
        with pytest.raises(ValueError):model.append(value)
        assert model.last==before
    with pytest.raises(ValueError,match='contiguous'):model.append(.125,start=.25)
    assert model.last==before
    model.append(.125,start=.125)
    with pytest.raises(clock.Unsupported,match='packet'):model.append(.125)


def test_cooperative_time_and_precision_limits_are_explicit():
    with pytest.raises(clock.Unsupported,match='time'):
        clock.PrefixClock(.1,0.,.2,maximum_seconds=0).append(.005)
    with pytest.raises(clock.Unsupported,match='precision'):
        clock.PrefixClock(.1,0.,.2,maximum_bits=64).append(2.**-100)
