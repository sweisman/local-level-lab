# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_packet_bound_growth import INDICES, extend_prefix


def example():
    increments = dict(dt=np.full(40, .25), theta=np.arange(120).reshape(40, 3), dv=np.zeros((40, 3)))
    times = np.arange(10)*.5+.125
    positions = np.arange(30.).reshape(10, 3)
    jacobian = np.arange(810.).reshape(30, 27)
    limit = np.zeros(27)
    limit[25] = .1
    prefix = {name: value[:4] for name, value in increments.items()}
    prefix.update(times=times[:2], center=np.zeros(27), lower=np.full(27, -.1),
                  upper=np.full(27, .1), positions=positions[:2], jacobian=jacobian[:6])
    return increments, times, positions, jacobian, limit, prefix


def test_extension_keeps_query_triplets_and_clock_support():
    arrays, times, path, jac, limit, original = example()
    extended, edge = extend_prefix(arrays, times, path, jac, limit, original)
    np.testing.assert_array_equal(extended['times'], times[list(INDICES)])
    expected = np.concatenate([jac[3*i:3*i+3] for i in INDICES])
    np.testing.assert_array_equal(extended['jacobian'], expected)
    assert edge > extended['times'][-1]
    assert np.cumsum(extended['dt'])[-2] > edge
    np.testing.assert_array_equal(extended['center'], original['center'])


def test_extension_rejects_changed_prefix_and_missing_clock_support():
    arrays, times, path, jac, limit, original = example()
    original['theta'] = original['theta']+1
    with pytest.raises(ValueError, match='original verified prefix'):
        extend_prefix(arrays, times, path, jac, limit, original)
    *_, original = example()
    arrays = {key: value[:15] for key, value in arrays.items()}
    with pytest.raises(ValueError, match='bounded clock support'):
        extend_prefix(arrays, times, path, jac, limit, original)
