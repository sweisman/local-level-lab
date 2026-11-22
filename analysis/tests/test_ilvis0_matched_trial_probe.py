# SPDX-License-Identifier: AGPL-3.0-or-later
"""Keep the recorded point comparison finite and tied to the sealed case IDs."""

import numpy as np
import pytest

from lll import ilvis0_matched_trial_probe as probe


def test_probe_grid_counts_only_the_four_declared_points():
    parent = {identity: dict(identity=identity, training_packets=30, training_epochs=3,
                            limits={'native_calls': 31})
              for identity in (*probe.POINT_COUNTS, 'unused')}
    tasks = probe.tasks(parent)
    assert [task['identity'] for task in tasks] == list(probe.POINT_COUNTS)
    assert [task['limits']['native_calls'] for task in tasks] == [4, 2, 2]
    assert [task['native_kind'] for task in tasks] == ['mixed'] * 3
    assert sum(task['limits']['packet_visits'] for task in tasks) == 720
    assert all(task['limits']['bound_calls'] == 0 for task in tasks)


def test_probe_rejects_any_difference_even_at_sub_coordinate_roundoff():
    residual = np.array([1e-16, 0., 0.])
    coordinates = np.array([[.3, .4, 1000.]])
    coordinate_difference = residual.reshape((1, 3)).copy()
    value = dict(coordinates=coordinates.copy(), residual=residual.copy(),
                 coordinate_difference=coordinate_difference.copy(), boundaries=0)
    assert probe.exact(value, coordinates, coordinate_difference, residual, 0)
    value['coordinate_difference'][0, 0] = np.nextafter(1e-16, 1.)
    assert not probe.exact(value, coordinates, coordinate_difference, residual, 0)
    with pytest.raises(ValueError, match='missing sealed fit'):
        probe.tasks({})
