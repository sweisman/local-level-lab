"""Earlier-only adapter from a flight-style tangent to the affine box control."""
import numpy as np
import pytest


def _operator():
    from lll.state_space_covariance import LinearInnovations
    steps = [dict(transition=np.eye(3) * .9,
                  process_loading=np.eye(3) * .05,
                  observation=np.eye(3),
                  white_loading=np.eye(3) * .2) for _ in range(4)]
    return LinearInnovations(steps, epoch_count=4, state_dimension=3,
                             observation_dimension=3,
                             initial_loading=np.eye(3) * .1,
                             maximum_bytes=100000, design_is_fixed=True,
                             error_distribution='gaussian')


def test_boundary_tangent_returns_finite_earlier_only_intervals():
    from lll.bounded_aircraft_tangent import diagnose
    operator = _operator()
    jacobian = np.arange(12., dtype=float).reshape(12, 1) * .01
    result = diagnose(operator, np.zeros((4, 3)), jacobian,
                      np.ones((2, 3)) * .02, [1.], training_epochs=2,
                      coordinate_chart='local_unwrapped_geodetic',
                      calibration_alpha=.025, future_alpha=.025,
                      rank_rtol=1e-10)
    assert result['training_epochs'] == 2
    assert result['prediction_epochs'] == 2
    assert len(result['lower']) == len(result['upper']) == 6
    assert all(a < b for a, b in zip(result['lower'], result['upper']))
    assert result['later_observations_used'] is False
    assert result['nonlinear_aircraft_coverage_established'] is False
    assert result['scientific_decision'] == 'abstain'


def test_adapter_matches_independent_dense_conditional_calculation():
    from scipy.stats import chi2, norm
    from lll.bounded_aircraft_tangent import diagnose
    operator = _operator()
    design = (np.arange(12., dtype=float) + 1).reshape(12, 1) * .01
    earlier = np.array([.02, -.01, .03, -.02, .01, .04])
    result = diagnose(operator, np.zeros((4, 3)), design,
                      earlier.reshape(2, 3), [1.], training_epochs=2,
                      coordinate_chart='local_unwrapped_geodetic',
                      calibration_alpha=.025, future_alpha=.025,
                      rank_rtol=1e-10)
    root = operator.unwhiten(np.eye(12))
    covariance = root @ root.T
    carry = np.linalg.solve(covariance[:6, :6], covariance[:6, 6:]).T
    contrast = design[6:, 0] - carry @ design[:6, 0]
    information = float(design[:6, 0] @ np.linalg.solve(
        covariance[:6, :6], design[:6, 0]))
    estimate = float(design[:6, 0] @ np.linalg.solve(
        covariance[:6, :6], earlier)) / information
    center = carry @ earlier + contrast * estimate
    conditional = covariance[6:, 6:] - carry @ covariance[:6, 6:]
    half = (np.sqrt(chi2.ppf(.975, 1) / information) * np.abs(contrast) +
            norm.ppf(.9875) * np.sqrt(np.diag(conditional)))
    np.testing.assert_allclose(result['lower'], center - half, rtol=1e-10)
    np.testing.assert_allclose(result['upper'], center + half, rtol=1e-10)


def test_rejects_missing_calibration_column_or_outside_box():
    from lll.bounded_aircraft_tangent import diagnose
    operator = _operator()
    with pytest.raises(ValueError):
        diagnose(operator, np.zeros((4, 3)), np.ones((12, 1)),
                 np.zeros((2, 3)), [1.1], training_epochs=2,
                 coordinate_chart='local_unwrapped_geodetic',
                 calibration_alpha=.025, future_alpha=.025,
                 rank_rtol=1e-10)
    with pytest.raises(ValueError):
        diagnose(operator, np.zeros((4, 3)), np.ones((12, 0)),
                 np.zeros((2, 3)), [], training_epochs=2,
                 coordinate_chart='local_unwrapped_geodetic',
                 calibration_alpha=.025, future_alpha=.025,
                 rank_rtol=1e-10)
