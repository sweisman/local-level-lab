"""Known-Gaussian calibration envelopes, including a true box boundary."""
import numpy as np
import pytest


def _envelope(design, observed, contrast, base, sigma, lo, hi):
    from lll.bounded_linear_prediction import envelope
    return envelope(design, observed, contrast, base, sigma, lo, hi,
                    calibration_alpha=.025, future_alpha=.025,
                    rank_rtol=1e-10)


def test_active_boundary_does_not_remove_calibration_uncertainty():
    rng = np.random.default_rng(31415)
    a = np.array([[1.], [1.]])
    covered = 0
    for _ in range(3000):
        earlier = a[:, 0] + rng.normal(size=2)
        future = 2. + rng.normal(scale=.5)
        result = _envelope(a, earlier, [[2.]], [0.], [.5], [-1.], [1.])
        assert result['scope'] == 'affine_known_gaussian_box'
        assert result['calibration_directions'] == 1
        covered += result['lower'][0] <= future <= result['upper'][0]
    assert covered / 3000 > .93


def test_rank_deficient_training_retains_full_box_null_direction():
    result = _envelope([[1., 1.], [1., 1.]], [0., 0.],
                       [[1., -1.]], [0.], [.1], [-1., -1.], [1., 1.])
    assert result['calibration_directions'] == 1
    assert result['discarded_directions'] == 1
    assert result['lower'][0] < -2.
    assert result['upper'][0] > 2.
    assert result['scientific_decision'] == 'abstain'


@pytest.mark.parametrize('design,observed,contrast,base,sigma,lo,hi', [
    ([[1.]], [0.], [[1.]], [0.], [0.], [-1.], [1.]),
    ([[1.]], [0.], [[1.]], [0.], [1.], [1.], [-1.]),
    ([[1., 2.]], [0.], [[1.]], [0.], [1.], [-1., -1.], [1., 1.]),
    ([[1.]], [float('nan')], [[1.]], [0.], [1.], [-1.], [1.]),
])
def test_rejects_invalid_or_incomplete_inputs(design, observed, contrast,
                                               base, sigma, lo, hi):
    with pytest.raises(ValueError):
        _envelope(design, observed, contrast, base, sigma, lo, hi)
