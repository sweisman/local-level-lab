# SPDX-License-Identifier: AGPL-3.0-or-later
"""Retain a conditional whole-forecast guarantee across supplied error laws."""
import math
import re


def union_simultaneous_intervals(laws, *, minimum_simultaneous_coverage):
    if (not isinstance(laws, dict) or len(laws) < 2 or
            any(not isinstance(name, str) or not name for name in laws) or
            not isinstance(minimum_simultaneous_coverage, (int, float)) or
            not math.isfinite(minimum_simultaneous_coverage) or
            not 0 < minimum_simultaneous_coverage < 1):
        raise ValueError('two named laws and finite whole-forecast target required')
    rows = []
    common = None
    for name in sorted(laws):
        member = laws[name]
        if not isinstance(member, dict) or set(member) != {
                'binding_sha256', 'prediction_target',
                'operator_configuration', 'interval'}:
            raise ValueError('complete matched law binding required')
        binding = member['binding_sha256']
        target = member['prediction_target']
        operator = member['operator_configuration']
        interval = member['interval']
        support = interval.get('forecast_support_sha256') if isinstance(interval, dict) else None
        if (not isinstance(binding, str) or
                re.fullmatch('[0-9a-f]{64}', binding) is None or
                target not in ('physical_position', 'receiver_measurement') or
                not isinstance(interval, dict) or
                interval.get('scope') != 'affine_known_gaussian_box_bonferroni' or
                interval.get('affine_conditional_simultaneous_bound_derived') is not True or
                interval.get('simultaneous_coverage_established') is not False or
                interval.get('true_calibration_inside_box_assumed') is not True or
                interval.get('error_covariance_known_assumed') is not True or
                interval.get('observed_aircraft_coverage_established') is not False or
                interval.get('nonlinear_aircraft_coverage_established') is not False or
                interval.get('scientific_decision') != 'abstain'):
            raise ValueError('conditional affine simultaneous interval required')
        if (not isinstance(operator, str) or
                re.fullmatch('[0-9a-f]{64}', operator) is None or
                interval.get('prediction_target') != target or
                interval.get('error_operator_configuration') != operator or
                interval.get('later_observations_used') is not False):
            raise ValueError('interval must match its target error operator and earlier-only support')
        lower = interval.get('lower')
        upper = interval.get('upper')
        coverage = interval.get('affine_conditional_simultaneous_lower_bound')
        if (not isinstance(lower, list) or not isinstance(upper, list) or
                not lower or len(lower) != len(upper) or
                interval.get('coordinate_count') != len(lower) or
                not isinstance(support, str) or
                re.fullmatch('[0-9a-f]{64}', support) is None or
                not isinstance(coverage, (int, float)) or
                not math.isfinite(coverage) or
                coverage < minimum_simultaneous_coverage or
                any(not isinstance(v, (int, float)) or not math.isfinite(v)
                    for v in lower+upper) or
                any(a >= b for a, b in zip(lower, upper))):
            raise ValueError('finite ordered whole-forecast intervals required')
        identity = (binding, target, len(lower), support)
        if common is None:
            common = identity
        elif identity != common:
            raise ValueError('candidate laws must share target and forecast support')
        rows.append((name, lower, upper, coverage))
    binding, target, count, support = common
    return dict(
        scope='union_of_supplied_affine_simultaneous_laws',
        binding_sha256=binding, prediction_target=target,
        forecast_support_sha256=support,
        coordinate_count=count, candidate_laws=[row[0] for row in rows],
        lower=[min(row[1][i] for row in rows) for i in range(count)],
        upper=[max(row[2][i] for row in rows) for i in range(count)],
        affine_conditional_simultaneous_lower_bound=min(row[3] for row in rows),
        affine_conditional_simultaneous_bound_derived=True,
        simultaneous_coverage_established=False,
        condition='at least one supplied affine Gaussian law is correct; true calibration lies in its box',
        selected_law=None, law_family_truth_established=False,
        observed_aircraft_coverage_established=False,
        nonlinear_aircraft_coverage_established=False,
        coverage_calibrated=False, scientific_decision='abstain')
