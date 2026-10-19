# SPDX-License-Identifier: AGPL-3.0-or-later
import io
import math

import pytest

HEADER=b'GPSTime [sec] X-Acc [m/s^2] Y-Acc [m/s^2] Z-Acc [m/s^2] X-Omg [rad/s] Y-Omg [rad/s] Z-Omg [rad/s] Temp [degC]\n'


def rows(body,header=HEADER):
    from lll.airquantumgrav import records
    return list(records(io.BytesIO(header+body.encode())))


def test_engineering_units_axes_signs_and_actual_time_steps():
    result=rows('100.000000 -1 2 -9.8 -.01 .02 -.03 35\n100.003334 1 -2 -9.7 .01 -.02 .03 36\n')
    assert result[0]['acceleration_mps2']==[-1.,2.,-9.8]
    assert result[0]['angular_rate_rads']==[-.01,.02,-.03]
    assert result[0]['dt_s'] is None and result[1]['dt_s']==pytest.approx(.003334)
    assert result[1]['temperature_c']==36. and result[0]['line_number']==2


@pytest.mark.parametrize('bad',['100 0 0 0 0 0 0','100 0 0 0 0 0 0 35 9','100 0 0 nan 0 0 0 35',
    '100 0 0 0 inf 0 0 35','604801 0 0 0 0 0 0 35','-1 0 0 0 0 0 0 35'])
def test_malformed_nonfinite_or_unsupported_times_are_rejected(bad):
    with pytest.raises(ValueError):rows(bad+'\n')


@pytest.mark.parametrize('time',['100','99.99'])
def test_duplicate_and_reversed_times_are_rejected(time):
    with pytest.raises(ValueError):rows('100 0 0 -9.8 0 0 0 35\n'+time+' 0 0 -9.8 0 0 0 35\n')


def test_gap_is_preserved_and_flagged_without_interpolation():
    result=rows('100 0 0 -9.8 0 0 0 35\n100.02 0 0 -9.8 0 0 0 35\n')
    assert len(result)==2 and result[-1]['dt_s']==pytest.approx(.02)
    assert result[-1]['gap_above_1p5_nominal_periods']


def test_header_units_cannot_silently_change_and_empty_data_rejected():
    with pytest.raises(ValueError):rows('100 0 0 -9.8 0 0 0 35\n',HEADER.replace(b'rad/s',b'deg/s'))
    with pytest.raises(ValueError):rows('')
