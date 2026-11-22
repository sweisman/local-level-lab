# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_tangent_remainder import feasible_moves, summarize


def test_feasible_moves_keep_an_inward_exact_singular_direction():
    point = np.array([-1., .1, .2])
    design = np.diag([1., 2., 3.])
    moves = feasible_moves(point, design)
    assert len(moves) == 6
    np.testing.assert_allclose(moves[0]['point'], [-.99, .1, .2])
    np.testing.assert_allclose(moves[1]['point'], [-.90, .1, .2])
    for move in moves:
        assert np.max(np.abs(move['point'])) <= 1
        assert np.linalg.norm(move['point'] - point) == pytest.approx(move['radius'])


def test_feasible_moves_refuse_to_clip_or_shorten_an_outward_axis():
    with pytest.raises(ValueError, match='feasible'):
        feasible_moves([-1., -1., 0.], [[1., 1., 0.], [3., 3., 0.], [0., 0., 4.]])


def test_summarize_distinguishes_exact_change_from_tangent_remainder():
    change = np.array([[0., 2., 0.], [0., 4., 0.]])
    affine = np.array([[0., 1.5, 0.], [0., 3., 0.]])
    result = summarize(change, affine, np.ones((2, 3)), cut=1)
    assert result['training']['remainder_rms_m'] == .5
    assert result['forecast']['remainder_rms_m'] == 1.
    assert result['forecast']['change_rms_m'] == 4.
    assert result['forecast']['relative_remainder'] == .25
