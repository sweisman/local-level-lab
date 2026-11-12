# SPDX-License-Identifier: AGPL-3.0-or-later
"""Synthetic packet-header timing error with unchanged sensor increments."""
import copy

import numpy as np
import pytest


def material():
    from lll.airquantumgrav_noisy_inputs import construct, noise_settings
    from lll.airquantumgrav_training_controls import recipe
    r = dict(recipe(), rate_hz=200, duration_s=2., queries=9,
             query_start_s=.1, query_step_s=.2, noise=noise_settings())
    spec = dict(model='sphere_rotating', latitude_deg=55., profile=False,
                start=0, policy_id='reported-short-v1')
    return construct(spec, r, reserve=lambda **work: None)


def test_header_jitter_changes_only_logged_intervals_and_binds_new_hash():
    from lll.airquantumgrav_clock_disturbance import apply_header_timestamp_jitter
    from lll.studies.artifacts import digest
    original = material()
    before = copy.deepcopy(original)
    changed = apply_header_timestamp_jitter(original, amplitude_s=.0004,
                                             cycles=19)
    np.testing.assert_array_equal(original['dt'], before['dt'])
    assert original['training_rows'] == changed['training_rows']
    np.testing.assert_array_equal(original['theta'], changed['theta'])
    np.testing.assert_array_equal(original['dv'], changed['dv'])
    assert np.all(changed['dt'] > 0)
    assert np.all(changed['dt'] < .0075)
    assert np.max(abs(changed['dt'] - .005)) > 1e-5
    assert np.sum(changed['dt']) == pytest.approx(np.sum(original['dt']), abs=1e-14)
    assert changed['binding']['measured_raw_array_sha256']['dt'] == digest(
        np.asarray(changed['dt'], dtype='<f8').tobytes())
    assert (changed['binding']['clean_raw_array_sha256'] ==
            original['binding']['clean_raw_array_sha256'])
    assert changed['binding']['timestamp_disturbance']['increment_period_s'] == .005
    assert changed['binding']['timestamp_disturbance']['imposed_on'] == 'packet_headers_only'


@pytest.mark.parametrize('amplitude,cycles', [(.003, 19), (.0004, 0),
                                             (-.0004, 19)])
def test_header_jitter_rejects_unsupported_disturbance(amplitude, cycles):
    from lll.airquantumgrav_clock_disturbance import apply_header_timestamp_jitter
    with pytest.raises(ValueError):
        apply_header_timestamp_jitter(material(), amplitude_s=amplitude,
                                      cycles=cycles)


def test_header_jitter_rejects_mutated_imu_increments_before_rebinding():
    from lll.airquantumgrav_clock_disturbance import apply_header_timestamp_jitter
    changed = material()
    changed['theta'][0, 0] += .01
    with pytest.raises(ValueError, match='unchanged nominal inputs'):
        apply_header_timestamp_jitter(changed, amplitude_s=.0004, cycles=19)
