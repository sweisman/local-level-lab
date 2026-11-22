# SPDX-License-Identifier: AGPL-3.0-or-later
"""Preserve the preselected cells while aligning the receiver clock."""

import numpy as np
import pytest

from lll.esa_direction_holdout_clock import verify_shift, whole_second_selection


def test_second_leg_selection_shifts_each_query_inside_the_fixed_cell():
    def window(start, leg):
        return dict(first_index=start, last_index=start+839, leg=leg, course='turn',
                    query_first_index=start+21, query_last_index=start+819)

    rows = [window(1000, 1)] + [window(i, 2) for i in (2000, 3000, 4000, 5000)]
    selected = whole_second_selection(rows)
    for old, new in zip(rows[1:], selected, strict=True):
        assert new['query_first_index'] == old['query_first_index']-1
        assert new['query_last_index'] == old['query_last_index']-1
        assert new['first_index'] == old['first_index']
        assert new['last_index'] == old['last_index']
    rows[1]['query_first_index'] -= 1
    with pytest.raises(ValueError, match='edge guards'):
        whole_second_selection(rows)


def test_clock_verification_rejects_a_change_of_support_or_phase():
    new = np.arange(400.)+400000.0002
    old = new+.5001
    verify_shift(old, new)
    for wrong in (new+1., new+.004, new[:-1], np.full(400, np.nan)):
        with pytest.raises(ValueError, match='whole-second'):
            verify_shift(old, wrong)
