# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import pytest

from lll.gnss_sounding import Sounding, read_sounding, zenith_delay


def test_log_pressure_and_dewpoint_are_interpolated_between_observations():
    profile = Sounding('example', 0., 0.,
                       ((100., math.log(1000.)), (2100., math.log(800.))),
                       ((math.log(800.), 270., 260.), (math.log(1000.), 290., 280.)))
    pressure, temperature, dewpoint = profile.weather_at(1100.)
    assert pressure == pytest.approx(math.sqrt(1000. * 800.))
    assert (temperature, dewpoint) == pytest.approx((280., 270.))
    with pytest.raises(ValueError, match='outside'):
        profile.weather_at(2200.)


def test_pressure_and_water_vapour_contribute_to_delay():
    dry = zenith_delay(0., 0., 1000., 280., 0.)
    assert dry == pytest.approx(2.2768 / .99734)
    assert zenith_delay(0., 0., 1000., 280., 5.) - dry == pytest.approx(
        .002277 * (1255. / 280. + .05) * 5.)


def test_fixed_columns_and_missing_height_on_surface_only():
    header = '#GLM00004270 2023 07 06 12 1110    3 ncdc-gts           611667  -454167'
    rows = ['21 -9999 102000B-9999   120B-9999    50   230    10 ',
            '20 -9999  91600 -9999   104B-9999   100 -9999 -9999 ',
            '10 -9999  85000  1525B  116B-9999    80   345    30 ']
    profile = read_sounding('\n'.join([header, *rows]), surface_height_m=34.)
    assert (profile.latitude_deg, profile.longitude_deg) == pytest.approx((61.1667, -45.4167))
    assert len(profile.heights) == 2
    assert len(profile.weather) == 3
    assert profile.weather_at(34.) == pytest.approx((1020., 285.15, 280.15))
    with pytest.raises(ValueError, match='level count'):
        read_sounding('\n'.join([header, *rows[:-1]]), surface_height_m=34.)
