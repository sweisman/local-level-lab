# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent rational quadrature checks for one common clipped-packet clock."""
from fractions import Fraction as F
import math
import pytest
from lll import ilvis0_force_integrals as integral


def oracle(periods,forces,t):
    tag=0.;parts=[]
    for period,force in zip(periods,forces,strict=True):
        q=min(max(F(t)-F(tag),F(0)),F(period));parts.append((q,tuple(F(v) for v in force)));tag+=period
    g=tuple(sum((q*force[axis] for q,force in parts),F(0)) for axis in range(3))
    h=tuple(sum((force[axis]*q*(q/2+sum((r for r,_ in parts[i+1:]),F(0))) for i,(q,force) in enumerate(parts)),F(0)) for axis in range(3))
    return g,h


def test_exact_constant_force_and_clock_taylor_terms():
    result=integral.enclose([.25]*8,[[2.,-3.,0.]]*8,center=1.,lower=.5,upper=1.5)
    assert result.g_center==(F(2),F(-3),F(0))
    assert result.h_center==(F(1),F(-3,2),F(0))
    assert result.g_remainder==(F(0),)*3
    assert result.h_remainder==(F(1,4),F(3,8),F(0))


def test_varying_force_and_rounded_tags_use_one_clock():
    periods=[.005,.007,.003,.006]*12
    forces=[[math.sin(i)*.2,(-1.)**i*.3,i*.01] for i in range(len(periods))]
    result=integral.enclose(periods,forces,center=.1,lower=.015,upper=.22)
    assert result.clock_defect>0
    gc,hc=oracle(periods,forces,F(.1));assert gc==result.g_center and hc==result.h_center
    for i in range(81):
        t=F(.015)+(F(.22)-F(.015))*i/80;g,h=oracle(periods,forces,t);delta=t-F(.1)
        for axis in range(3):
            assert abs(g[axis]-gc[axis]-result.g_linear[axis]*delta)<=result.g_remainder[axis]
            assert abs(h[axis]-hc[axis]-result.h_linear[axis]*delta)<=result.h_remainder[axis]


def test_point_domain_has_no_manufactured_remainder_and_source_binds_force():
    periods=[.005]*40;forces=[[.1,.2,.3]]*40
    first=integral.enclose(periods,forces,center=.1,lower=.1,upper=.1)
    assert first.g_remainder==first.h_remainder==(F(0),)*3
    second=integral.enclose(periods,[[.1,.2,.4]]*40,center=.1,lower=.1,upper=.1)
    assert first.source_id!=second.source_id


def test_invalid_data_and_finite_allowances_fail_without_repair():
    for periods,forces in (([0.],[[1.,2.,3.]]),([.25],[[1.,2.]]),([.25],[[1.,float('nan'),3.]]),([.25,.25],[[1.,2.,3.]])):
        with pytest.raises(ValueError):integral.enclose(periods,forces,center=.1,lower=0.,upper=.2)
    with pytest.raises(ValueError):integral.enclose([.25],[[1.,2.,3.]],center=.1,lower=0.,upper=.3)
    with pytest.raises(integral.Unsupported):integral.enclose([.25]*2,[[1.,2.,3.]]*2,center=.1,lower=0.,upper=.2,maximum_packets=1)
    with pytest.raises(integral.Unsupported):integral.enclose([.25],[[1.,2.,3.]],center=.1,lower=0.,upper=.2,maximum_seconds=0.)
