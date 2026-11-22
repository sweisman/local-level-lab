# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.ilvis0_solver_trust_v2 import fit_candidate


class Cubic:
    class bounds:
        active = ('x',)

        @staticmethod
        def decode(point):
            return {'x': float(point[0])}

    def __init__(self):
        self.tangents = 0
        self.values = 0

    @staticmethod
    def residual(point):
        return np.array([point[0]**3-.005])

    def residual_tangent(self, point, model):
        self.tangents += 1
        return self.residual(point), np.array([[3*point[0]**2]]), 0

    def trial(self, point, model):
        self.values += 1
        return self.residual(point), 0


def meters(delta):
    return np.column_stack((delta, np.zeros((len(delta), 2))))


@pytest.mark.parametrize('screened', [False, True])
def test_repeated_full_trial_reuses_only_an_identical_rejection(screened):
    before, after = Cubic(), Cubic()
    options = dict(start=[.001], maximum_evaluations=30, physical_step=meters)
    old = fit_candidate(before, 'control', trial_residual=before.trial if screened else None, **options)
    new = fit_candidate(after, 'control', trial_residual=after.trial if screened else None,
                        reuse_rejected_full=True, **options)
    assert old['converged'] and new['converged']
    assert new['reused_full_rejections']
    assert new['evaluations'] < old['evaluations']
    assert new['normalized_parameters'] == old['normalized_parameters']
    assert new['residual_sum_squares'] == old['residual_sum_squares']
    assert new['stability_probe'] == old['stability_probe']
    assert any(row['fresh'] for row in new['evaluation_trace'])
    assert before.tangents+before.values > after.tangents+after.values


def test_reuse_does_not_qualify_an_unfinished_physical_stop():
    fit = fit_candidate(Cubic(), 'control', start=[.001], maximum_evaluations=7,
                        physical_step=meters, reuse_rejected_full=True)
    assert not fit['converged']
    assert fit['evaluations'] <= 7


@pytest.mark.parametrize('case', ['curved_boundary', 'curved_redundant', 'gain_offset', 'nonlinear27'])
@pytest.mark.parametrize('index', range(4))
def test_opt_in_retains_known_objective_and_position(case, index):
    from lll.ilvis0_boundary_controls import problem_for, starts

    problem, optimum, expected, unique = problem_for(case)
    fit = fit_candidate(problem, 'control', start=starts(len(optimum))[index],
                        maximum_evaluations=200, physical_step=meters, reuse_rejected_full=True)
    point = np.asarray(fit['normalized_parameters'])
    assert fit['converged'] and fit['stability_verified']
    assert fit['residual_sum_squares'] == pytest.approx(expected, abs=1e-7, rel=0.)
    assert np.linalg.norm(problem.residual(point)-problem.residual(optimum)) <= 1e-4
    if unique:
        assert point == pytest.approx(optimum, abs=1e-5)
    assert problem.calls == fit['evaluations'] <= 200
