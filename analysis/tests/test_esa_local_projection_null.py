"""The local fitted-error null uses saved tangents and finite draws."""

import numpy as np
import pytest


def test_projected_white_draws_are_orthogonal_and_repeatable():
    from lll.esa_local_projection_null import projected_draws

    jacobian = np.array([[1., 0.], [0., 1.], [1., 0.], [0., 1.],
                         [1., 0.], [0., 1.]])
    first, rank = projected_draws(jacobian, draws=20, seed=21)
    second, second_rank = projected_draws(jacobian, draws=20, seed=21)
    assert rank == second_rank == 2
    assert first.shape == (6, 20)
    np.testing.assert_array_equal(first, second)
    np.testing.assert_allclose(jacobian.T @ first, 0., atol=1e-12)


def test_rejects_degenerate_or_unbounded_projection():
    from lll.esa_local_projection_null import projected_draws

    with pytest.raises(ValueError):
        projected_draws(np.zeros((6, 2)), draws=20, seed=21)
    with pytest.raises(ValueError):
        projected_draws(np.eye(6), draws=20, seed=21)


def test_saved_esa_projection_control_uses_no_new_fit():
    from pathlib import Path
    from lll.esa_local_projection_null import build

    result = build(Path(__file__).resolve().parents[2], draws=32)
    assert result['verified'] is True
    assert result['training_epochs'] == 600
    assert result['draws_per_law'] == 32
    assert set(result['laws']) == {'increment', 'point'}
    assert all(row['rank'] == 26 for row in result['laws'].values())
    assert result['new_fits'] == 0
    assert result['original_reads'] == 0
    assert result['protected_reads'] == 0
    assert result['scientific_decision'] == 'abstain'
