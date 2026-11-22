# SPDX-License-Identifier: AGPL-3.0-or-later
"""Controls for excluding only scores proved incompatible with training."""

from fractions import Fraction as F


def test_score_floor_rounds_outward():
    from lll.esa_linked_score_floor import score_floor_row

    row, limit = score_floor_row([1.25, -.25], F(1, 9), F(2, 3))
    assert row == [-1.25, .25]
    assert F(limit) >= F(1, 9)-F(2, 3)


def test_exact_loss_inequality_can_exclude_a_high_score_slice():
    from lll.esa_linked_score_floor import floor_certificate, score_floor_row

    rows, bounds = zip(score_floor_row([1.], 0., .75))
    # A high score needs x >= .75. The necessary training row is x <= .5.
    assert floor_certificate([0.], [1.], list(rows), list(bounds), [1.], .5, [1.]) == F(-1, 4)
    # Equality supplies no strict separation.
    assert floor_certificate([0.], [1.], list(rows), list(bounds), [1.], .75, [1.]) == 0
