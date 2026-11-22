# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent overlap verification and paired ground interpretation gates."""

import pytest


def test_short_read_must_end_at_the_long_reads_first_bytes():
    from lll.esa_girafe_ground_rate import overlap_digest
    from lll.studies.artifacts import digest

    prefix = bytes(range(256))*2
    probe = b'x'*512+prefix
    raw = prefix+b'y'*1024
    assert overlap_digest(raw, probe) == digest(prefix)
    with pytest.raises(ValueError, match='overlap'):
        overlap_digest(raw, probe[:-1]+b'Z')


def test_ground_support_requires_the_independent_clock_and_both_time_scales():
    from lll.esa_girafe_ground_rate import support_flags

    better = dict(gyro_prediction_rms_arcsec=2., no_motion_rms_arcsec=3.)
    worse = dict(gyro_prediction_rms_arcsec=4., no_motion_rms_arcsec=3.)
    assert support_flags([better, better], {'passes': True}) == (True, True, True)
    assert support_flags([better, worse], {'passes': True}) == (True, False, False)
    assert support_flags([better, better], {'passes': False}) == (False, True, False)
