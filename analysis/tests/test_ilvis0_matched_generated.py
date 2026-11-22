# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the frozen matrix and the withholding boundary before worker launch."""

import numpy as np
import pytest

from lll import ilvis0_matched_generated as study


def test_full_matched_grid_charges_are_finite_and_unique():
    tasks = study.tasks()
    assert len(tasks) == len({task['identity'] for task in tasks}) == 128
    assert sum(task['limits']['native_calls'] for task in tasks) == 10368
    assert sum(task['limits']['packet_visits'] for task in tasks) == 402780160
    assert {task['payload']['cap_dph'] for task in tasks} == {1., 3., 10., 20.}


def test_mutated_case_does_not_read_inputs():
    class Context:
        manifest = {'scope': study.SCOPE}

        def input_path(self):
            pytest.fail('mutated task attempted to access a frozen input')

    task = study.tasks()[0]
    task['payload']['cap_dph'] = 5.
    with pytest.raises(ValueError, match='unchanged matched generated'):
        study.evaluate(task, Context())


def test_generated_training_truth_never_returns_withheld_positions():
    spec = next(task['payload'] for task in study.tasks()
                if task['payload']['truth_model'] == 'flat_geographic_field')
    dt, theta, delta_v, times, earlier = study.training_material(spec)
    assert len(dt) == 4800
    assert theta.shape == delta_v.shape == (4800, 3)
    assert len(times) == 23 and earlier.shape == (14, 3)
    assert np.isfinite(theta).all() and np.isfinite(delta_v).all()
    assert np.cumsum(dt)[study.prefix_count()-1] > times[13] + .15
    assert np.cumsum(dt)[study.prefix_count()-1] < times[14]
