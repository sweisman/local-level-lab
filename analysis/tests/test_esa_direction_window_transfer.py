# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from lll.esa_direction_window_transfer import PASSES, TASKS, check_disjoint


def test_transfer_keeps_all_preselected_windows_and_rejects_reused_support():
    assert len(TASKS) == 8 and PASSES == 13
    assert len({row['identity'] for row in TASKS}) == 8
    assert sum(row['payload']['kind'] == 'straight' for row in TASKS) == 4
    check_disjoint([1., 2.], [[3., 4.], [0., .5]])
    with pytest.raises(ValueError, match='strictly disjoint'):
        check_disjoint([1., 2.], [[2., 4.]])
    with pytest.raises(ValueError, match='strictly disjoint'):
        check_disjoint([1., 2.], [[3., 4.], [3.7, 4.7]])
