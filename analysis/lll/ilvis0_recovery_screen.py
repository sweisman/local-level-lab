# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare actual bounded algorithms on small equations; no archive inputs."""
from unittest.mock import patch

import numpy as np
from scipy.optimize import least_squares

from . import ilvis0_solver_controls as controls
from . import ilvis0_solver_recovery as recovery
from . import ilvis0_solver_screen as old_screen

VERSION = 'ilvis0-bounded-recovery-screen-v1'
VARIANTS = ('trf', 'dogbox')
NAMES = controls.ANALYTIC + ('mixed_interior', 'mixed_boundary',
                             'coupled_interior', 'coupled_boundary')


def coupled_problem(name):
    """Known optimum with correlated columns and a 1e8 singular-value ratio."""
    if name not in ('coupled_interior', 'coupled_boundary'):
        raise ValueError('unknown coupled control')
    rng = np.random.default_rng(20261012)
    left = np.linalg.qr(rng.normal(size=(27, 27)))[0]
    right = np.linalg.qr(rng.normal(size=(27, 27)))[0]
    matrix = left @ np.diag(np.geomspace(1e4, 1e-4, 27)) @ right.T
    optimum = rng.uniform(-.4, .4, 27)
    if name.endswith('boundary'):
        optimum[:2] = [1., -1.]
    return old_screen.Mixed(matrix, matrix @ optimum), optimum


def run_one(name, start_index, variant):
    if variant not in VARIANTS or type(start_index) is not int or not 0 <= start_index < 3:
        raise ValueError('fixed screen variant and start required')
    if name in controls.ANALYTIC:
        problem, optimum, expected, unique = controls.analytic_problem(name)
    elif name.startswith('mixed_'):
        problem, optimum = old_screen.mixed_problem(name)
        expected, unique = 1., False
    else:
        problem, optimum = coupled_problem(name)
        expected, unique = 1., False
    n = len(optimum)
    initial = controls.starts(n, 3)[start_index]
    if name.startswith('coupled_') and start_index == 2:
        # A prescribed near-boundary point independent of any model preference.
        initial = np.where(np.arange(n) % 2 == 0, .99998, -.99998)

    def chosen(fun, point, **kwargs):
        return least_squares(fun, point, method=variant, **kwargs)

    # Replace only dispatch inside this serial software call. Both paths execute
    # real SciPy optimizers, with the identical frozen evaluator and final checks.
    # No frozen source is edited; this entry point has no archive reader/launcher.
    with patch.object(recovery, 'least_squares', chosen):
        fit = recovery.fit_candidate(problem, 'control', start=initial,
                                     maximum_evaluations=600, x_scale='jac')
    point = np.array(fit['normalized_parameters'])
    actual = problem.residual_tangent(point, 'control')[0]
    reference = problem.residual_tangent(optimum, 'control')[0]
    prediction_error = float(np.linalg.norm(actual-reference))
    parameter_error = float(np.max(abs(point-optimum))) if unique else None
    answer_passed = (abs(fit['residual_sum_squares']-expected) <= 1e-7
                     and prediction_error <= 1e-4
                     and (not unique or parameter_error <= 1e-5))
    return dict(identity=f'{variant}::{name}::{start_index}', variant=variant, control=name,
                start_index=start_index, passed=bool(fit['converged'] and answer_passed),
                known_answer_passed=bool(answer_passed), converged=fit['converged'],
                evaluations=fit['evaluations'], maximum_evaluations=600,
                objective=fit['residual_sum_squares'], reference_objective=expected,
                prediction_error=prediction_error, parameter_error=parameter_error,
                stationarity=fit['exact_projected_gradient_relative'], stationarity_tolerance=1e-4,
                probe=fit['stability_probe'], stable_callbacks=fit['stable_accepted_iterations'],
                message=fit['message'], analytic_reference_checks=2,
                observed_fit_starts=0, native_predictions=0, scientific_decision='abstain')


def run():
    rows = [run_one(name, index, variant) for variant in VARIANTS for name in NAMES
            for index in range(3)]
    return dict(version=VERSION, results=rows, maximum_evaluations_per_start=600,
                numerical_threads=2, observed_fit_starts=0, native_predictions=0,
                qualifies_archival_solver=False, scientific_decision='abstain')
