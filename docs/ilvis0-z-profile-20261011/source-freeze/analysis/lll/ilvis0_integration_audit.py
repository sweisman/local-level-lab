# SPDX-License-Identifier: AGPL-3.0-or-later
"""Matched saved integration fits. No measurement extraction, integration or fitting."""
import math
from statistics import median

from . import ilvis0_clock_calibration_audit as calibration
from . import ilvis0_saved_audit as saved

VERSION = 'ilvis0-saved-integration-audit-v1'
MODELS = calibration.MODELS
TARGET = '570b37d23af5e245dd461051'
DIAGNOSTICS = ('gradient', 'projected_gradient', 'scaled_projected_gradient',
               'right_singular_vectors', 'accepted_step_history')


def finite(value, *, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or
            not math.isfinite(value) or value < 0 or (positive and value == 0)):
        raise ValueError('invalid saved numerical statistic')
    return value


def index(summary, expected):
    if summary['state'] != 'complete' or summary['starts'] != len(expected):
        raise ValueError('incomplete or mismatched study')
    ids = [c['case_id'] for c in summary['cases']]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate processing case')
    return calibration._index(summary['cases'], expected)


def spectrum(fit):
    values = fit['singular_values']
    if len(values) != len(fit['active_parameters']) or not values:
        raise ValueError('invalid saved singular spectrum dimensions')
    for v in values:
        finite(v)
    if any(a < b for a, b in zip(values, values[1:])):
        raise ValueError('unordered saved singular spectrum')
    return dict(largest_singular_value=values[0], smallest_singular_value=values[-1],
        jacobian_condition_ratio=values[0]/values[-1] if values[-1] else None,
        zero_singular_values=values.count(0))


def compare(original, revised, cases):
    if revised['header_reference'] != original:
        raise ValueError('embedded reference differs from frozen original')
    if original['provenance'] != revised['provenance']:
        raise ValueError('measurement provenance differs')
    ids = [c['case_id'] for c in cases]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError('invalid processing definitions')
    expected = {(c, m) for c in ids for m in MODELS}
    old, new = index(original, expected), index(revised, expected)
    fits, parameters, corrections, rates, comparisons = [], [], [], [], []
    for case in cases:
        complete, costs = True, {}
        for model in MODELS:
            key = case['case_id'], model
            a, b = old[key], new[key]
            if a['active_parameters'] != b['active_parameters']:
                raise ValueError('active parameter definitions changed')
            if any(f.get('clock_hypothesis') != 'header_elapsed' for f in (a, b)):
                raise ValueError('clock hypothesis differs')
            if (b.get('integration_mode') != 'combined' or
                    b.get('increment_convention') != 'ordinary_rate_integrals'):
                raise ValueError('unexpected revised integration convention')
            before = saved.parameter_rows(a, case['limits'], profile=case['profile'])
            after = saved.parameter_rows(b, case['limits'], profile=case['profile'])
            for x, y in zip(before, after):
                parameters.append(dict(case_id=key[0], model=model, parameter=x['parameter'],
                    unit=x['unit'], original_value=x['value'], revised_value=y['value'],
                    change=y['value']-x['value'], normalized_change=y['normalized_value']-x['normalized_value'],
                    original_boundary=x['boundary'], revised_boundary=y['boundary'],
                    lower_limit=x['lower_limit'], upper_limit=x['upper_limit']))
            statuses = saved.fit_status(a), saved.fit_status(b)
            complete &= statuses == ('converged', 'converged')
            old_cost, cost = finite(a['residual_sum_squares']), finite(b['residual_sum_squares'])
            costs[model] = cost
            rms = []
            for f in (a, b):
                axes = f['residual_rms_neu_m']
                if len(axes) != 3:
                    raise ValueError('invalid residual axes')
                rms.append([finite(v) for v in axes])
            gradient = finite(b['exact_projected_gradient_relative'])
            tolerance = finite(b['stationarity_tolerance'], positive=True)
            sweeps = b['actual_tangent_sweeps']
            if isinstance(sweeps, bool) or not isinstance(sweeps, int) or sweeps <= 0:
                raise ValueError('invalid native sweep count')
            predictions = b['diagnostic_predictions']
            if (isinstance(predictions, bool) or not isinstance(predictions, int) or
                    predictions < 0 or b['evaluations'] != sweeps+predictions):
                raise ValueError('saved native accounting disagrees')
            rates.append(finite(b['elapsed_s'])/(sweeps+predictions))
            fits.append(dict(case_id=key[0], model=model, original_status=statuses[0],
                revised_status=statuses[1], original_cost=old_cost, revised_cost=cost,
                cost_change_percent=100*(cost/old_cost-1) if old_cost else None,
                original_horizontal_rms_m=math.hypot(*rms[0][:2]),
                revised_horizontal_rms_m=math.hypot(*rms[1][:2]),
                original_vertical_rms_m=rms[0][2], revised_vertical_rms_m=rms[1][2],
                original_boundary_count=len(a['active_bounds']), revised_boundary_count=len(b['active_bounds']),
                stationarity=gradient, stationarity_limit_ratio=gradient/tolerance,
                evaluations=b['evaluations'], tangent_sweeps=sweeps,
                diagnostic_predictions=predictions, native_sweeps=sweeps+predictions, message=b['message'],
                missing_diagnostics=[name for name in DIAGNOSTICS if name not in b], **spectrum(b)))
            for treatment, f in [('original', a), ('combined', b)]:
                gain = f['parameters']['gyro_gain_z']
                bias = f['parameters']['gyro_bias_z']*648000/math.pi
                scale, offset = calibration.correction_coefficients(gain, bias)
                corrections.append(dict(case_id=key[0], model=model, integration=treatment,
                    gain_percent=100*gain, bias_dph=bias, rate_multiplier=scale, rate_addition_dph=offset))
        globe = min(costs['sphere_rotating'], costs['sphere_still'])
        shape = ('globe' if globe < costs['flat_still'] else
                 'flat' if globe > costs['flat_still'] else 'tie') if complete else 'unresolved'
        field = ('specified_field' if costs['sphere_rotating'] < costs['sphere_still'] else
                 'zero_field' if costs['sphere_rotating'] > costs['sphere_still'] else 'tie')
        comparisons.append(dict(case_id=case['case_id'], complete=complete,
                                shape_preference=shape, background_field_preference=field))
    full = all(c['complete'] for c in comparisons)
    shape = comparisons[0]['shape_preference'] if full and len({c['shape_preference'] for c in comparisons}) == 1 else 'unresolved'
    reveal = full and shape == 'globe'
    for c in comparisons:
        if not reveal:
            c['background_field_preference'] = None
    field_values = {c['background_field_preference'] for c in comparisons}
    return dict(version=VERSION, native_predictions=0, optimizer_starts=0,
        fits=fits, parameters=parameters, z_corrections=corrections, comparisons=comparisons,
        complete_matched_comparison=full, shape_preference=shape,
        background_field_preference=next(iter(field_values)) if reveal and len(field_values) == 1 else None,
        joint_calibration_identified=False, scientific_decision='abstain',
        native_sweeps=sum(f['native_sweeps'] for f in fits),
        tangent_sweeps=sum(f['tangent_sweeps'] for f in fits),
        measured_seconds_per_sweep=dict(median=median(rates), maximum=max(rates)))


def profile_scope():
    """Proposed first stage only; identities are not an execution authorization."""
    identities = [f'{TARGET}::bias1_unsubtracted::{model}::gain{gain:+d}::bias{bias:+d}'
                  for gain in (-2, 0, 2) for bias in (-1, 0, 1) for model in MODELS]
    return dict(version='ilvis0-joint-z-profile-proposal-v1', authorized_starts=0,
        identities=identities, gain_percent=[-2, 0, 2], bias_dph=[-1, 0, 1],
        case_id='bias1_unsubtracted', clock='header_elapsed', integration='original',
        requested_starts=27, maximum_per_identity=1, retries=0,
        maximum_native_sweeps_per_start=200, maximum_native_sweeps=5400,
        numerical_threads=2, scientific_decision='abstain')
