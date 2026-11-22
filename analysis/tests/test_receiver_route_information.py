# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def test_each_model_can_use_its_own_offset_allowance():
    from lll.receiver_route_information import bounded_pair

    rate = np.deg2rad(np.array([[3., 0., 0.], [5., 0., 0.]])) / 3600.
    result = bounded_pair(rate, np.zeros_like(rate), limit_dph=1.)
    # The two models may use opposite offsets of one degree per hour.
    assert result['rms_dph'] == pytest.approx(np.sqrt(5.))
    assert result['bias_difference_dph'] == pytest.approx([2., 0., 0.])
    assert bounded_pair(rate, np.zeros_like(rate), limit_dph=3.)['rms_dph'] == pytest.approx(1.)


def test_unlimited_constant_allowance_retains_only_the_changing_rate():
    from lll.receiver_route_information import bounded_pair

    rate = np.deg2rad(np.array([[3., 2., 10.], [3., -2., 10.]])) / 3600.
    value = bounded_pair(rate, np.zeros_like(rate), limit_dph=None)
    assert value['rms_dph'] == pytest.approx(2.)
    assert value['bias_difference_dph'] == pytest.approx([3., 0., 10.])


def test_geodetic_rate_conversion_recovers_the_declared_north_and_east_components():
    from lll.receiver_route_information import receiver_terms
    from lll.models import radii

    lat = np.deg2rad(55.)
    m, n = radii(lat)
    rows = [dict(time_s=float(t), latitude_deg=55., height_m=2000.,
                 north_mps=(m + 2000.) * 1e-6,
                 east_mps=(n + 2000.) * np.cos(lat) * 2e-6) for t in range(4)]
    answer = receiver_terms(rows)
    for row in answer['globe']:
        assert row == pytest.approx([np.cos(lat)*2e-6, -1e-6, -np.sin(lat)*2e-6])
    assert answer['disc'][:, 2] == pytest.approx([-2e-6]*4)


def test_gapped_training_interval_cannot_pass_geometry_check():
    from lll.receiver_route_information import receiver_terms

    rows = [dict(time_s=t, latitude_deg=55., height_m=1000., north_mps=60., east_mps=60.)
            for t in (0., 1., 2., 4.)]
    with pytest.raises(ValueError):
        receiver_terms(rows)
