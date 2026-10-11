# SPDX-License-Identifier: AGPL-3.0-or-later
"""Matched calibration changes in saved clock fits; no native predictions or fits."""
import math
from statistics import median

from . import ilvis0_saved_audit as saved

VERSION = 'ilvis0-clock-calibration-audit-v1'
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')


def correction_coefficients(gain, bias_dph):
    """Corrected rate = a * logged rate + c, with rates in degrees/hour."""
    if not all(math.isfinite(v) for v in (gain, bias_dph)) or gain <= -1:
        raise ValueError('invalid gyro correction')
    return 1/(1+gain), -bias_dph/(1+gain)


def _index(cases, expected):
    result = {}
    for case in cases:
        for fit in case['fits']:
            key = case['case_id'], fit['model']
            if key in result:
                raise ValueError('duplicate matched fit')
            result[key] = fit
    if set(result) != expected:
        raise ValueError('missing or unexpected matched fits')
    return result


def _stat(value):
    if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError('invalid residual statistic')
    return value


def compare(summary, cases):
    if summary['state'] != 'complete':
        raise ValueError('incomplete clock trial')
    case_ids = [c['case_id'] for c in cases]
    if len(set(case_ids)) != len(case_ids) or not case_ids:
        raise ValueError('invalid processing cases')
    expected = {(c, m) for c in case_ids for m in MODELS}
    nominal = _index(summary['nominal_reference']['cases'], expected)
    header = _index(summary['cases'], expected)
    if summary['starts'] != len(expected):
        raise ValueError('start count disagrees with matched scope')
    parameter_changes, fits, corrections, comparisons, rates = [], [], [], [], []
    for case in cases:
        complete = True
        costs = {}
        for model in MODELS:
            key = case['case_id'], model
            old, new = nominal[key], header[key]
            if old['active_parameters'] != new['active_parameters']:
                raise ValueError('active parameter definitions changed with clock')
            before = saved.parameter_rows(old, case['limits'], profile=case['profile'])
            after = saved.parameter_rows(new, case['limits'], profile=case['profile'])
            for a, b in zip(before, after):
                parameter_changes.append(dict(case_id=key[0], model=model,
                    parameter=a['parameter'], unit=a['unit'], nominal_value=a['value'],
                    header_value=b['value'], change=b['value']-a['value'],
                    normalized_change=b['normalized_value']-a['normalized_value'],
                    nominal_boundary=a['boundary'], header_boundary=b['boundary'],
                    lower_limit=a['lower_limit'], upper_limit=a['upper_limit']))
            old_cost, new_cost = map(_stat, (old['residual_sum_squares'], new['residual_sum_squares']))
            statuses = saved.fit_status(old), saved.fit_status(new)
            complete &= statuses == ('converged', 'converged')
            costs[model] = new_cost
            rms = [_stat(v) for v in new['residual_rms_neu_m']]
            if len(rms) != 3:
                raise ValueError('invalid residual axes')
            fits.append(dict(case_id=key[0], model=model,
                nominal_status=statuses[0], header_status=statuses[1],
                nominal_cost=old_cost, header_cost=new_cost,
                cost_change_percent=100*(new_cost/old_cost-1) if old_cost else None,
                nominal_boundary_count=len(old['active_bounds']),
                header_boundary_count=len(new['active_bounds']),
                header_horizontal_rms_m=math.hypot(*rms[:2]), header_vertical_rms_m=rms[2]))
            for clock, fit in [('nominal', old), ('header', new)]:
                gain = fit['parameters']['gyro_gain_z']
                bias = fit['parameters']['gyro_bias_z']*648000/math.pi
                scale, offset = correction_coefficients(gain, bias)
                corrections.append(dict(case_id=key[0], model=model, clock=clock,
                    gain_percent=gain*100, bias_dph=bias, rate_multiplier=scale,
                    rate_addition_dph=offset))
            evaluations, elapsed = new.get('evaluations'), new.get('elapsed_s')
            if isinstance(evaluations, int) and evaluations > 0 and elapsed is not None:
                rates.append(_stat(elapsed)/evaluations)
        globe = min(costs['sphere_rotating'], costs['sphere_still'])
        preference = ('globe' if globe < costs['flat_still'] else
                      'flat' if globe > costs['flat_still'] else 'tie') if complete else 'unresolved'
        reveal = complete and preference == 'globe'
        comparisons.append(dict(case_id=case['case_id'], all_matched_fits_converged=complete,
            shape_preference=preference, rotation_revealed=reveal,
            rotation_preference=('rotating' if costs['sphere_rotating'] < costs['sphere_still'] else
                'still' if costs['sphere_rotating'] > costs['sphere_still'] else 'tie') if reveal else None))
    # Shape must agree across processing cases before reporting the rotation comparison.
    if any(r['shape_preference'] != 'globe' for r in comparisons):
        for row in comparisons:
            row['rotation_revealed'] = False
            row['rotation_preference'] = None
    return dict(version=VERSION, optimizer_starts=0, native_predictions=0,
        parameters=parameter_changes, fits=fits, z_correction=corrections,
        comparisons=comparisons, scientific_decision='abstain',
        measured_seconds_per_evaluation=dict(median=median(rates), maximum=max(rates)) if rates else None)
