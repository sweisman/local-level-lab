# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved stopping evidence only; no integration, fitting or result promotion."""
import math

VERSION = 'ilvis0-shared-leg-stopping-audit-v1'
RELATIVE_COST_TOLERANCE = 1e-8
AXES = ('north', 'east', 'down')


def stopping_gates(fit):
    """Reconstruct gate ratios without treating a small failure as a success."""
    probe = fit.get('stability_probe') or {}
    tolerance = fit.get('stationarity_tolerance', 1e-4)
    stationarity = fit.get('exact_projected_gradient_relative')
    endpoint_ratio = stationarity / tolerance if stationarity is not None else None
    failed = ['endpoint_stationarity'] if endpoint_ratio is not None and endpoint_ratio > 1 else []
    out = dict(converged=bool(fit.get('converged')), endpoint_stationarity_ratio=endpoint_ratio,
               cost_change_ratio=None, fresh_stationarity_ratio=None,
               maximum_position_rms_m=None, maximum_position_change_m=None,
               position_rms_ratios=None, position_max_ratios=None)
    if 'actual_cost_change' not in probe:
        if not failed:
            failed.append(probe.get('reason', 'probe_unavailable'))
        out['failed_gates'] = failed
        return out
    values = [probe['actual_cost_change'], probe['fresh_stationarity'],
              *probe['position_rms_neu_m'], *probe['position_max_abs_neu_m']]
    if (len(probe['position_rms_neu_m']) != 3 or len(probe['position_max_abs_neu_m']) != 3
            or not all(math.isfinite(v) and v >= 0 for v in values)
            or tolerance <= 0 or probe['position_rms_tolerance_m'] <= 0
            or probe['position_max_tolerance_m'] <= 0):
        raise ValueError('invalid saved stability probe')
    cost_ratio = probe['actual_cost_change'] / RELATIVE_COST_TOLERANCE
    fresh_ratio = probe['fresh_stationarity'] / tolerance
    rms_ratios = [v/probe['position_rms_tolerance_m'] for v in probe['position_rms_neu_m']]
    maximum_ratios = [v/probe['position_max_tolerance_m'] for v in probe['position_max_abs_neu_m']]
    if cost_ratio > 1:
        failed.append('relative_cost')
    if fresh_ratio > 1:
        failed.append('fresh_stationarity')
    failed.extend('position_rms_'+axis for axis, value in zip(AXES, rms_ratios) if value > 1)
    failed.extend('position_max_'+axis for axis, value in zip(AXES, maximum_ratios) if value > 1)
    out.update(cost_change_ratio=cost_ratio, fresh_stationarity_ratio=fresh_ratio,
               maximum_position_rms_m=max(probe['position_rms_neu_m']),
               maximum_position_change_m=max(probe['position_max_abs_neu_m']),
               position_rms_ratios=rms_ratios, position_max_ratios=maximum_ratios,
               failed_gates=failed)
    return out


def history_summary(fit):
    history = fit.get('step_history', [])
    last = max((i for i, step in enumerate(history) if step['accepted']), default=-1)
    tail = history[last+1:]
    cost = fit.get('residual_sum_squares')
    delta = (tail[-1]['cost']-cost)/max(abs(cost), 1.) if tail and cost is not None else None
    return dict(accepted_steps=sum(step['accepted'] for step in history),
                rejected_steps=sum(not step['accepted'] for step in history),
                rejected_tail_steps=len(tail),
                smallest_rejected_fraction=min((step['fraction'] for step in tail), default=None),
                last_rejected_relative_cost_change=delta,
                establishes_prediction_noise_floor=False)
