# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import pytest


def bounds(**extra):
    from lll.ilvis0_calibration_path import enclose
    args=dict(raw=1,period=1,bias_center=0,gain_center=0,bias_direction=[0,0],
        gain_direction=[F(1,2)]*2,path=[0,1]);args.update(extra);return enclose(**args)


def test_known_reciprocal_derivatives_through_order_three():
    row=bounds()
    assert row['exact_derivatives']==[['2/3','1'],['-1/2','-2/9'],['4/27','1/2'],['-3/4','-4/27']]
    assert row['derivative_order']==3 and not row['native_motion_qualified']


def test_zero_gain_direction_keeps_the_bias_path_affine():
    row=bounds(raw=2,period=F(1,5),bias_direction=[1,1],gain_direction=[0,0])
    assert row['exact_derivatives'][1:]==[['-1/5','-1/5'],['0','0'],['0','0']]


def test_coupled_bias_gain_numerator_cancels_before_interval_evaluation():
    row=bounds(bias_direction=[-1,-1],gain_direction=[1,1])
    assert row['exact_derivatives'][1:]==[['0','0']]*3


def test_direction_box_contains_an_independent_power_series_reference():
    row=bounds(raw=F(7,5),period=F(1,200),bias_center=F(1,30),gain_center=F(1,100),
        bias_direction=[F(-1,10),F(1,5)],gain_direction=[F(-3,20),F(1,10)])
    for db in (F(-1,10),F(0),F(1,5)):
        for dg in (F(-3,20),F(0),F(1,10)):
            for s in (F(0),F(1,3),F(1)):
                numerator=F(7,5)-F(1,200)*(F(1,30)+s*db);denominator=F(101,100)+s*dg
                coefficients=[1/denominator]
                for _ in range(3):coefficients.append(-dg/denominator*coefficients[-1])
                series=[numerator*coefficients[0]]
                for n,factor in ((1,1),(2,2),(3,6)):
                    series.append(factor*(numerator*coefficients[n]-F(1,200)*db*coefficients[n-1]))
                assert all(F(lo)<=v<=F(hi) for (lo,hi),v in zip(row['exact_derivatives'],series))


def test_partial_packet_applies_the_affine_clock_leibniz_rule():
    from lll.ilvis0_calibration_path import partial_packet
    row=partial_packet(raw=2,period=1,bias_center=0,gain_center=0,bias_direction=[1,1],
        gain_direction=[0,0],path=[0,1],fraction_center=0,fraction_slope=[1,1])
    assert row['increment_exact_derivatives'][2:]==[['-2','-2'],['0','0']]
    assert row['period_exact_derivatives']==[['0','1'],['1','1'],['0','0'],['0','0']]
    assert row['packet_fraction_domain_verified'] and not row['clock_partition_verified']


@pytest.mark.parametrize('change',['gain_zero','bad_path','nonfinite','fraction_crossing'])
def test_unsupported_domains_are_rejected(change):
    if change=='gain_zero':kwargs=dict(gain_direction=[-2,-1])
    elif change=='bad_path':kwargs=dict(path=[1,0])
    elif change=='nonfinite':kwargs=dict(bias_direction=[0,float('nan')])
    else:
        from lll.ilvis0_calibration_path import partial_packet
        with pytest.raises(ValueError):partial_packet(raw=1,period=1,bias_center=0,gain_center=0,
            bias_direction=[0,0],gain_direction=[0,0],path=[0,1],fraction_center=0,fraction_slope=[2,2])
        return
    with pytest.raises(ValueError):bounds(**kwargs)
