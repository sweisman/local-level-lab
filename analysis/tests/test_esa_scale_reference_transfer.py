import numpy as np

from lll.esa_motion_innovation_scale import InnovationScore
from lll.esa_scale_reference_transfer import fit_reference, score_gradient


def test_scale_score_gradient_agrees_with_correlated_likelihood_differences():
    rng = np.random.default_rng(17)
    score = InnovationScore(rng.normal(size=9), rng.normal(size=(9, 2)),
                            np.repeat([.1, .4, .9], 3), 0.)
    point = np.linspace(-1., 1., 6)
    energy, gradient = score_gradient(score, point)
    from lll.esa_axis_innovation_scale import axis_score

    np.testing.assert_allclose(energy, axis_score(score, point)['quadratic'])
    for j in range(6):
        delta = np.zeros(6)
        delta[j] = 1e-5
        direct = (axis_score(score, point+delta)['quadratic']-axis_score(score, point-delta)['quadratic'])/2e-5
        np.testing.assert_allclose(gradient[j], direct, rtol=2e-6, atol=1e-8)


def test_reference_fit_finds_compatible_setting_and_obeys_charge_limit():
    scores = [InnovationScore(y, np.empty((3, 0)), np.zeros(3), 0.)
              for y in np.diag([6., 4., 5.])]
    calls = []
    result = fit_reference(scores, np.zeros(6), maximum=64, reserve=lambda: calls.append(True))
    assert result['deviation'] < .01
    assert len(calls) == result['evaluations'] <= 64
    limited = fit_reference(scores, np.zeros(6), maximum=1, reserve=lambda: None)
    assert limited['status'] == 'evaluation_limit' and limited['evaluations'] == 1
