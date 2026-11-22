import numpy as np
import pytest
from scipy.stats import chi2

from lll import calibrated_linear_prediction, covariance_scale_fit
from lll.state_space_covariance import LinearInnovations


def _fit(roots, sample, design):
    return covariance_scale_fit.fit_training(
        [(roots, sample, design, np.ones(design.shape[1]))],
        log_bounds=(-5., 5.), max_evaluations=100, rank_rtol=1e-10)


def test_abstains_when_fitted_path_absorbs_the_acceleration_error():
    t = np.linspace(0., 1., 9)
    design = np.column_stack((np.ones_like(t), t, t**2))
    roots = dict(native=np.eye(t.size),
                 persistent=(0.5*t**2)[:, None],
                 maneuver=np.maximum(t - .5, 0.)[:, None])
    result = _fit(roots, np.ones((1, t.size)), design)
    assert result == dict(status='unidentifiable', rank=2, evaluations=0, variances=None)


def test_later_roots_are_rejected_at_training_fit_boundary():
    design = np.arange(5.)[:, None]
    with pytest.raises(ValueError, match='training'):
        _fit(dict(native=np.eye(7), persistent=design), np.ones((1, 5)), design)


def test_recovered_variances_predict_independent_paths_with_fitted_mean():
    t = np.linspace(0., 2., 17)
    cut = 12
    rng = np.random.default_rng(34982)
    design = np.column_stack((np.ones_like(t), t))
    lag = np.maximum(t - .625, 0.)
    # Integrated exponentially decaying acceleration beginning during training.
    loading = np.column_stack((t**2 / 2., 3.*(lag + np.expm1(-lag))))
    true_variances = np.array([.003, .3, .6])

    def generated_paths(count):
        mean = rng.normal(0., 3., (count, 2)) @ design.T
        white = rng.normal(0., np.sqrt(true_variances[0]), (count, t.size))
        acceleration = rng.normal(size=(count, 2)) * np.sqrt(true_variances[1:])
        return mean + white + acceleration @ loading.T

    roots = dict(native=.1*np.eye(cut), persistent=loading[:cut, :1], maneuver=loading[:cut, 1:])
    result = _fit(roots, generated_paths(6000)[:, :cut], design[:cut])
    assert result['status'] == 'interior'
    variances = np.array(list(result['variances'].values())) * [0.01, 1., 1.]
    assert variances == pytest.approx(true_variances, rel=.1)

    step = [dict(transition=np.eye(2), process_loading=np.zeros((2, 0)),
                 observation=row[None, :], white_loading=np.sqrt(variances[:1])[None, :])
            for row in loading]
    operator = LinearInnovations(step, epoch_count=len(step), state_dimension=2,
                                observation_dimension=1, initial_loading=np.diag(np.sqrt(variances[1:])),
                                maximum_bytes=8192, design_is_fixed=True, error_distribution='gaussian')

    def predict(earlier):
        return calibrated_linear_prediction.predict(
            operator, design, earlier, training_epochs=cut,
            parameter_scales=np.ones(2), prediction_scales=np.ones(len(t)-cut),
            rank_rtol=1e-10, estimability_rtol=1e-10, estimability_atol=1e-12, maximum_parameters=2)

    basis = np.eye(cut)
    forecasts = [predict(row) for row in basis]
    assert all(result['status'] == 'estimable' for result in forecasts)
    weights = np.array([result['mean'][:, 0] for result in forecasts]).T
    predicted = forecasts[0]
    covariance = variances[0]*np.eye(t.size) + (loading * variances[1:]) @ loading.T

    # Independently solve for the minimum-variance linear weights with an
    # unbiasedness constraint. This retains the covariance across the cut.
    t_design, f_design = design[:cut], design[cut:]
    system = np.block([[covariance[:cut, :cut], t_design], [t_design.T, np.zeros((2, 2))]])
    rhs = np.vstack((covariance[:cut, cut:], f_design.T))
    reference_weights = np.linalg.solve(system, rhs)[:cut].T
    assert weights == pytest.approx(reference_weights, abs=1e-12)
    difference = np.column_stack((-reference_weights, np.eye(t.size-cut)))
    reference_covariance = difference @ covariance @ difference.T
    assert predicted['covariance'][:, 0, 0] == pytest.approx(reference_covariance.diagonal(), abs=1e-12)

    later = generated_paths(4000)
    errors = later[:, cut:] - later[:, :cut] @ weights.T
    joint_score = np.sum(errors.T * np.linalg.solve(reference_covariance, errors.T), axis=0)
    assert .93 < np.mean(joint_score <= chi2.ppf(.95, t.size-cut)) < .97


def test_calibration_projection_removes_only_its_own_direction():
    from lll import esa_fitted_scale_support

    design = np.array([[1.], [0.], [0.]])
    roots = dict(persistent=np.array([[1.], [1.], [0.]]),
                 maneuver=np.array([[1.], [0.], [0.]]))
    answer = esa_fitted_scale_support.support(design, roots, rank_rtol=1e-10,
                                             reference_sd=(1.,))
    assert answer['mean_rank'] == 1
    assert answer['persistent']['retained_squared_loading_fraction'] == pytest.approx(.5)
    assert answer['persistent']['information_before'] == pytest.approx([2./9.])
    assert answer['persistent']['information_after'] == pytest.approx([1./8.])
    assert answer['maneuver']['information_after'] == [0.]
