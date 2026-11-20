# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_rinex_code_comparison import paired_epochs


def test_selects_same_distinct_epochs_with_and_without_clock_adjustment():
    raw = [388214.5, 388215.0, 388215.5, 388216.0]
    indices, offsets = paired_epochs([388215.0002, 388216.0003], raw, [.0004] * 4)
    assert indices == [1, 3]
    assert offsets == pytest.approx([.0003, .0007])


@pytest.mark.parametrize('queries, error', [
    ([388215.0002, 388215.0003], 'distinct'),
    ([388215.0020], '1 ms'),
    ([388215.0008], '1 ms'),
])
def test_refuses_duplicate_or_excessive_time_difference(queries, error):
    with pytest.raises(ValueError, match=error):
        paired_epochs(queries, [388215., 388215.5], [.0004, .0004])
