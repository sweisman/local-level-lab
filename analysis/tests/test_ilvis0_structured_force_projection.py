"""Matrix-free receiver covariance projection against the dense reference."""

import numpy as np
import pytest


def _case(n=8):
    from lll.ilvis0_error_model import Spec
    times = np.cumsum(np.linspace(.7, 1.3, n))
    spec = Spec(
        white=np.diag([.03, .04, .05]),
        components=((2.5, np.diag([.1, .2, .3])),
                    (12., np.diag([.02, .03, .04]))),
        offset=np.diag([.05, .06, .07]),
        drift=np.diag([.01, .02, .03]),
        drift_origin_s=0., drift_span_s=20.)
    transforms = np.stack([np.diag([1.+i/100., 2.-i/100., 1.])
                           for i in range(n)])
    weights = np.random.default_rng(81).normal(size=(5, 3*n))
    return times, spec, transforms, weights


@pytest.mark.parametrize('transformed', [False, True])
def test_structured_projection_matches_dense_all_error_components(transformed):
    from lll.ilvis0_error_model import covariance
    from lll.ilvis0_structured_force_projection import project_covariance
    times, spec, transforms, weights = _case()
    transforms = transforms if transformed else None
    dense = covariance(times, spec, transforms)
    projected = project_covariance(times, spec, weights,
                                   transforms=transforms)
    np.testing.assert_allclose(projected, weights@dense@weights.T,
                               rtol=2e-12, atol=2e-12)


def test_structured_projection_uses_linear_epoch_storage():
    from lll.ilvis0_structured_force_projection import project_covariance
    times, spec, _, _ = _case(2000)
    weights = np.random.default_rng(19).normal(size=(3, 3*len(times)))
    projected = project_covariance(times, spec, weights)
    assert projected.shape == (3, 3)
    assert np.linalg.eigvalsh(projected).min() > 0.


def test_structured_projection_rejects_invalid_support():
    from lll.ilvis0_structured_force_projection import project_covariance
    times, spec, transforms, weights = _case()
    with pytest.raises(ValueError, match='epochs'):
        project_covariance(times[::-1], spec, weights)
    with pytest.raises(ValueError, match='weights'):
        project_covariance(times, spec, weights[:, :-1])
    transforms[0, 0, 0] = 0.
    with pytest.raises(ValueError, match='transforms'):
        project_covariance(times, spec, weights, transforms=transforms)


def test_structured_three_candidate_force_projection_matches_dense_reference():
    from lll.ilvis0_error_model import Spec, covariance
    from lll.ilvis0_force_magnitude_covariance import propagate
    from lll.ilvis0_structured_force_projection import project_candidate_forces
    times = np.arange(4., dtype=float)
    spec = Spec(white=np.eye(3)*.04,
                components=((3., np.eye(3)*.01),),
                offset=np.eye(3)*.02)
    jets = np.repeat([[.3, .5, 1000., 0., 0., 0., 0., 0., 0.]], 2, axis=0)
    weights = np.zeros((2, 9, 12))
    weights[0, 8, 2:9:3] = [1., -2., 1.]
    weights[1, 8, 5:12:3] = [1., -2., 1.]
    actual = project_candidate_forces(
        times, spec, jets, weights, background_rate_rads=7.292115e-5,
        gravity_mps2=9.8, disc_radius_m=6371000.)
    dense = covariance(times, spec)
    sensitivity = []
    for model in actual['model_order']:
        result = propagate(
            jets, weights, dense, model=model,
            background_rate_rads=7.292115e-5 if model == 'sphere_rotating' else 0.,
            gravity_mps2=9.8, disc_radius_m=6371000.)
        sensitivity.append(result['receiver_sensitivity'])
        np.testing.assert_allclose(
            actual['required_force_magnitude_mps2'][model],
            result['required_force_magnitude_mps2'])
    joined = np.vstack(sensitivity)
    np.testing.assert_allclose(actual['joint_covariance_mps4'],
                               joined@dense@joined.T, rtol=2e-12, atol=2e-12)
    assert actual['scientific_decision'] == 'abstain'


def test_structured_three_candidate_force_projection_exceeds_dense_local_cap():
    from lll.ilvis0_structured_force_projection import project_candidate_forces
    times, spec, _, _ = _case(2000)
    jets = np.array([[.3, .5, 1000., 0., 0., 0., 0., 0., 0.]])
    weights = np.zeros((1, 9, 3*len(times)))
    weights[0, 8, 2] = 1.
    result = project_candidate_forces(
        times, spec, jets, weights, background_rate_rads=7.292115e-5,
        gravity_mps2=9.8, disc_radius_m=6371000.)
    assert result['joint_covariance_mps4'].shape == (3, 3)


def test_matched_disc_uses_same_receiver_windows_and_cross_candidate_noise():
    from lll.ilvis0_error_model import Spec, covariance
    from lll.ilvis0_force_magnitude_covariance import propagate
    from lll.ilvis0_matched_field import evaluate
    from lll.ilvis0_structured_force_projection import project_candidate_forces

    times = np.array([0., 1., 2.])
    spec = Spec(white=np.diag([1e-15, 1e-15, .01]))
    jets = np.array([[-.9, .3, 1200., -2e-5, 1e-5, 0., 2e-7, 3e-7, 0.]])
    weights = np.zeros((1, 9, 9))
    weights[0, 8, 2::3] = [1., -2., 1.]
    constants = dict(gravity_mps2=9.81, disc_radius_m=6371000.)
    result = project_candidate_forces(
        times, spec, jets, weights, background_rate_rads=7.292115e-5,
        include_matched_disc=True, **constants)
    candidate = result['model_order'][-1]
    assert candidate == 'flat_geographic_field'
    physical = evaluate(*np.split(jets[0], 3), geometry='disc', field='geographic',
                        removed_fraction=.35, **constants)
    np.testing.assert_allclose(result['required_force_magnitude_mps2'][candidate],
                               np.linalg.norm(physical['specific_force_ned_mps2']))
    dense = covariance(times, spec)
    rows = [propagate(jets, weights, dense, model=m,
                      background_rate_rads=7.292115e-5 if m in
                      ('sphere_rotating', candidate) else 0., **constants)['receiver_sensitivity'][0]
            for m in result['model_order']]
    assert result['joint_covariance_mps4'][0, 3] > 0.
    np.testing.assert_allclose(result['joint_covariance_mps4'],
                               np.stack(rows) @ dense @ np.stack(rows).T)
