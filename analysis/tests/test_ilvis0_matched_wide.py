# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify matching and finite budgets for prospective wider arithmetic."""

import numpy as np
import pytest

from lll import ilvis0_matched_wide as study


def test_matched_wide_grid_pairs_identical_physics_and_bounds():
    rows = study.tasks()
    assert len(rows) == 128 == len({row['identity'] for row in rows})
    assert sum(row['limits']['native_calls'] for row in rows) == 10368
    assert sum(row['limits']['packet_visits'] for row in rows) == 402780160
    for a, b in zip(rows[::2], rows[1::2], strict=True):
        assert {a['payload']['arithmetic'], b['payload']['arithmetic']} == {'binary64', 'wide'}
        assert {k: v for k, v in a['payload'].items() if k != 'arithmetic'} == {
            k: v for k, v in b['payload'].items() if k != 'arithmetic'}
        assert a['limits'] == b['limits']
    for a, b in zip(study.material(rows[0]['payload']), study.material(rows[1]['payload']), strict=True):
        np.testing.assert_array_equal(a, b)


def test_matched_wide_rejects_mutated_task_before_reading_inputs():
    class Context:
        manifest = {'scope': study.SCOPE}

        def input_path(self):
            pytest.fail('mutated task read its input')

    entry = study.tasks()[0]
    entry['payload']['latitude_deg'] += 1.
    with pytest.raises(ValueError, match='unchanged prospective'):
        study.evaluate(entry, Context())
