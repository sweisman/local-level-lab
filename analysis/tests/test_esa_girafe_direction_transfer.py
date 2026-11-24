# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


@pytest.mark.parametrize('reflection', [1., -1.])
def test_alignment_recovers_offset_and_either_orthogonal_handedness(reflection):
    from lll.esa_girafe_direction_transfer import align, residual

    angle = .37
    transform = np.array([[np.cos(angle), -np.sin(angle)],
                          [np.sin(angle), np.cos(angle)]]) @ np.diag([reflection, 1.])
    source = np.array([[0., 1.], [0.5, 1.], [3., 0.], [-1., .7], [1., 3.]])
    bias = np.array([.005, -.007])
    target = source@transform + bias
    fit = align(source, target)
    np.testing.assert_allclose(fit['transform'], transform, atol=1e-14)
    np.testing.assert_allclose(fit['offset_mps2'], bias, atol=1e-14)
    np.testing.assert_allclose(residual(fit, source, target), 0., atol=1e-14)
    assert fit['source_singular_values'][1] > 0


def test_direction_transfer_exposes_rank_loss_and_does_not_fix_held_error():
    from lll.esa_girafe_direction_transfer import align, residual

    source = np.array([[1., 0.], [2., 0.], [3., 0.]])
    fit = align(source, source)
    assert fit['source_singular_values'][1] == 0.
    held = np.array([[.5, .5], [.4, .5]])
    np.testing.assert_allclose(residual(fit, held, held+[.2, -.1]), [[-.2, .1], [-.2, .1]])
    with pytest.raises(ValueError, match='matched'):
        align(source, held)
