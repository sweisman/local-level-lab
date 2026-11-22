# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib

import numpy as np
import pytest

from lll.innovations_snapshot import capture, restore
from lll.state_space_covariance import LinearInnovations


def operator():
    return LinearInnovations(
        [dict(transition=[[.8]], process_loading=[[.1]], observation=[[1.]],
              white_loading=[[.3]]) for _ in range(4)],
        epoch_count=4, state_dimension=1, observation_dimension=1,
        initial_loading=[[.1]], maximum_bytes=1000,
        design_is_fixed=True, error_distribution='gaussian')


def test_snapshot_preserves_whitening_inverse_and_prefix_across_roundtrip():
    original = operator()
    payload = capture(original)
    assert capture(original) == payload
    loaded = restore(payload, expected_sha256=hashlib.sha256(payload).hexdigest(),
                     expected_configuration=original.configuration, maximum_bytes=1000)
    data = np.array([[1., 0.], [2., 5.], [2., 6.], [1., 2.]])
    np.testing.assert_array_equal(original.whiten(data), loaded.whiten(data))
    np.testing.assert_array_equal(original.unwhiten(data), loaded.unwhiten(data))
    np.testing.assert_array_equal(original.prefix(2).whiten(data[:2]),
                                  loaded.prefix(2).whiten(data[:2]))
    assert original.log_determinant == loaded.log_determinant
    assert loaded.error_law_calibrated is False


@pytest.mark.parametrize('fault', ['hash', 'configuration', 'budget'])
def test_snapshot_rejects_invalid_receipts_and_storage(fault):
    original = operator()
    payload = capture(original)
    expected = dict(expected_sha256=hashlib.sha256(payload).hexdigest(),
                    expected_configuration=original.configuration, maximum_bytes=1000)
    field, value = {'hash': ('expected_sha256', 'a'*64),
                    'configuration': ('expected_configuration', 'a'*64),
                    'budget': ('maximum_bytes', 8)}[fault]
    expected[field] = value
    with pytest.raises(ValueError):
        restore(payload, **expected)


def test_snapshot_retains_conditioning_with_shared_process_noise():
    original = LinearInnovations(
        [dict(transition=[[.75]], process_loading=[[.4]],
              observation=[[1.]], observation_process_loading=[[.2]],
              white_loading=[[.3]]) for _ in range(6)],
        epoch_count=6, state_dimension=1, observation_dimension=1,
        initial_loading=[[.1]], maximum_bytes=1024,
        design_is_fixed=True, error_distribution='gaussian',
        observation_form='before_transition_shared_noise')
    payload = capture(original)
    loaded = restore(payload, expected_sha256=hashlib.sha256(payload).hexdigest(),
                     expected_configuration=original.configuration, maximum_bytes=1024)
    earlier = np.array([.4, .6, -.02])
    _, reference_state = original.apply_block(earlier, first_epoch=0)
    _, restored_state = loaded.apply_block(earlier, first_epoch=0)
    assert reference_state == restored_state
    expected = original.conditional_marginals(state=reference_state)
    actual = loaded.conditional_marginals(state=restored_state)
    np.testing.assert_array_equal(expected['covariance'], actual['covariance'])
    np.testing.assert_array_equal(expected['mean'], actual['mean'])
