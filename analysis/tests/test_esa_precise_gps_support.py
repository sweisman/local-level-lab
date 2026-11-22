# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path

import pytest

from lll.esa_precise_gps_support import missing_support, scan


def test_requires_every_orbit_and_clock_sample_around_transmit_times():
    receive = 390_000.
    orbits = {1: set(range(385_200, 393_301, 900))}
    clocks = {1: {389_970, 390_000}}
    assert missing_support(1, receive, orbits, clocks) == []
    assert missing_support(1, receive, orbits, {1: {390_000}}) == ['clock']
    assert missing_support(1, receive, {1: orbits[1] - {387_000}}, clocks) == ['orbit']


def test_known_products_audit_every_saved_gps_code_observation():
    root = Path(__file__).resolve().parents[2]
    prefix = root / 'data/external-imu-survey-20261018/esa-sample/rinex-400-120-stream'
    required = (
        prefix / 'code-position/positions.json.gz',
        prefix / 'products/IGS0OPSFIN_20231870000_01D_15M_ORB.SP3.gz',
        prefix / 'products/IGS0OPSFIN_20231870000_01D_30S_CLK.CLK.gz',
    )
    if not all(path.is_file() for path in required):
        pytest.skip('sealed recording 187 products are required for this replay')
    result = scan(root)
    assert result['epochs'] == 1041
    assert result['dual_frequency_epoch_satellite_count'] == 12354
    assert result['new_receiver_solutions'] == 0
    assert result['missing_support_epoch_satellites'] == {'clock': {17: 1041}, 'orbit': {}}
    assert result['minimum_gps_satellites_supported_by_both'] == 10
    assert result['maximum_gps_satellites_supported_by_both'] == 11
    assert not result['can_preserve_satellites_with_both_products']
