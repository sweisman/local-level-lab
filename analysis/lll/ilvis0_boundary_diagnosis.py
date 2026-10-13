# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inspect saved boundary-trial tangents/tracks without native observation calls."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import lsq_linear

from . import ilvis0_rectangular_diagnosis as tangent
from . import ilvis0_recovery_diagnosis as saved

VERSION = 'ilvis0-saved-boundary-diagnosis-v1'


def inspect_fit(identity, fit, value):
    row = saved.inspect_fit(identity, fit)
    if (value['active_parameters'] != fit['active_parameters']
            or value['normalized_parameters'] != fit['normalized_parameters']):
        raise ValueError('local tangent disagrees with saved fit')
    residual = np.asarray(value['residual'], float)
    jac = np.asarray(value['jacobian'], float)
    point = np.asarray(value['normalized_parameters'], float)
    cost = float(residual @ residual)
    if not np.isclose(cost, fit['residual_sum_squares'], rtol=1e-12, atol=1e-12):
        raise ValueError('local cost disagrees with saved fit')
    tangent.check_saved_gradient(value, fit['gradient'])
    history = fit['step_history']
    previous_evaluation = 1
    previous_cost = fit['initial_cost']
    last_accepted = -1
    for index, step in enumerate(history):
        numeric = [step[k] for k in ('cost', 'fraction', 'normalized_step')]
        if (not np.all(np.isfinite(numeric)) or step['cost'] < 0
                or not 0 < step['fraction'] <= 1 or step['normalized_step'] < 0
                or type(step['evaluation']) is not int
                or not previous_evaluation < step['evaluation'] <= fit['evaluations']
                or type(step['accepted']) is not bool):
            raise ValueError('invalid saved step history')
        if step['accepted']:
            if step['cost'] > previous_cost:
                raise ValueError('accepted cost increased')
            previous_cost = step['cost']
            last_accepted = index
        previous_evaluation = step['evaluation']
    tail = history[last_accepted+1:]
    full = [step for step in tail if step['fraction'] == 1.]
    correction = lsq_linear(jac, -residual, bounds=(-1-point, 1-point),
                            method='bvls', tol=1e-10, max_iter=100)
    if not correction.success or not np.all(np.isfinite(correction.x)):
        raise ValueError('saved affine correction unfinished')
    delta = jac @ correction.x
    predicted = residual+delta
    predicted_cost = float(predicted @ predicted)
    stalled = fit['message'] == 'no decreasing feasible nonlinear step'
    category = ('passed' if fit['converged'] else
                'budget_exhausted' if 'allowance exhausted' in fit['message'] else
                'stationary_stability_stall' if stalled and row['stationarity_passed'] else
                'nonstationary_stall' if stalled else row['failure_class'])
    slack = 1-abs(point)
    order = np.argsort(-abs(correction.x))[:4]
    row.update(version=VERSION, failure_class=category,
               roundoff_bound_count=int(np.count_nonzero((slack > 0) & (slack <= 1e-12))),
               accepted_steps=sum(step['accepted'] for step in history),
               rejected_steps=sum(not step['accepted'] for step in history),
               rejected_tail_count=len(tail),
               last_full_step_cost_change=(full[-1]['cost']-cost if full else None),
               smallest_rejected_fraction=(min(step['fraction'] for step in tail) if tail else None),
               smallest_step_cost_change=(tail[-1]['cost']-cost if tail else None),
               predicted_cost_drop=cost-predicted_cost,
               predicted_relative_cost_drop=(cost-predicted_cost)/max(cost, predicted_cost, 1.),
               predicted_residual_step=float(np.linalg.norm(delta)/max(np.linalg.norm(residual), 1.)),
               normalized_correction_norm=float(np.linalg.norm(correction.x)),
               dominant_correction=[dict(parameter=value['active_parameters'][i],
                                         correction=float(correction.x[i])) for i in order],
               native_predictions=0, observed_fit_starts=0, qualifies_archival_fit=False)
    return row


def load_epochs(directory, fit):
    name = fit['epoch_file']
    if Path(name).name != name or not name.endswith('.json.gz'):
        raise ValueError('invalid epoch filename')
    content = (Path(directory)/name).read_bytes()
    if hashlib.sha256(content).hexdigest() != fit['epoch_sha256']:
        raise ValueError('epoch hash mismatch')
    value = json.loads(gzip.decompress(content))
    times = np.asarray(value['times_s'], float)
    errors = np.asarray(value['errors_neu_m'], float)
    if (times.ndim != 1 or not times.size or errors.shape != (times.size, 3)
            or not np.all(np.isfinite(times)) or not np.all(np.isfinite(errors))
            or np.any(np.diff(times) <= 0)):
        raise ValueError('invalid saved epochs')
    return times, errors


def compare_saved_predictions(directory, primary, repeat):
    time_a, error_a = load_epochs(directory, primary)
    time_b, error_b = load_epochs(directory, repeat)
    if not np.array_equal(time_a, time_b):
        raise ValueError('saved epoch times disagree')
    change = np.sqrt(np.mean((error_a-error_b)**2, axis=0))
    cost_a, cost_b = primary['residual_sum_squares'], repeat['residual_sum_squares']
    if not np.all(np.isfinite([cost_a, cost_b])) or min(cost_a, cost_b) < 0:
        raise ValueError('invalid saved costs')
    relative = abs(cost_a-cost_b)/max(cost_a, cost_b, 1.)
    agreement = bool(relative <= 1e-6 and np.all(change <= .01))
    return dict(relative_cost_difference=relative, track_difference_rms_neu_m=change.tolist(),
                numerical_agreement=agreement,
                primary_converged=bool(primary['converged']), repeat_converged=bool(repeat['converged']),
                qualified_repeatability=bool(agreement and primary['converged'] and repeat['converged']),
                native_predictions=0, observed_fit_starts=0, qualifies_archival_fit=False)
