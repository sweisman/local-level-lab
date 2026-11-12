# SPDX-License-Identifier: AGPL-3.0-or-later
"""Retain ambiguity across supplied, matched forecast-error laws.

This combines already computed affine known-law marginal intervals. It neither
estimates an error law nor establishes that any candidate describes an aircraft.
"""
import math
import re


def union_marginal_intervals(laws, *, minimum_marginal_coverage):
    """Union candidate intervals without choosing a law by training score.

    If one supplied law is the true Gaussian law, its calibration lies in the
    supplied box and its affine model applies, the union inherits at least the
    requested per-coordinate coverage. Those conditions are not verified here.
    """
    if (not isinstance(laws, dict) or len(laws) < 2 or
            any(not isinstance(name, str) or not name for name in laws) or
            not isinstance(minimum_marginal_coverage, (int, float)) or
            not math.isfinite(minimum_marginal_coverage) or
            not 0 < minimum_marginal_coverage < 1):
        raise ValueError('two named laws and a finite marginal target required')
    rows = []
    common = None
    for name in sorted(laws):
        member = laws[name]
        if not isinstance(member, dict) or set(member) != {
                'binding_sha256', 'prediction_target', 'interval'}:
            raise ValueError('complete law binding, target and interval required')
        binding = member['binding_sha256']
        target = member['prediction_target']
        interval = member['interval']
        if (not isinstance(binding, str) or
                re.fullmatch('[0-9a-f]{64}', binding) is None or
                target not in ('physical_position', 'receiver_measurement') or
                not isinstance(interval, dict) or
                interval.get('scope') != 'affine_known_gaussian_box' or
                interval.get('true_calibration_inside_box_assumed') is not True or
                interval.get('error_covariance_known_assumed') is not True or
                interval.get('simultaneous_coverage_established') is not False or
                interval.get('nonlinear_aircraft_coverage_established') is not False or
                interval.get('scientific_decision') != 'abstain'):
            raise ValueError('qualified affine known-law interval required')
        coverage = interval.get('marginal_coverage_lower_bound')
        lower = interval.get('lower')
        upper = interval.get('upper')
        if (not isinstance(coverage, (int, float)) or
                not math.isfinite(coverage) or coverage < minimum_marginal_coverage or
                not isinstance(lower, list) or not isinstance(upper, list) or
                not lower or len(lower) != len(upper) or
                any(not isinstance(v, (int, float)) or not math.isfinite(v)
                    for v in lower + upper) or
                any(a >= b for a, b in zip(lower, upper))):
            raise ValueError('finite ordered intervals with sufficient marginal coverage required')
        identity = (binding, target, len(lower))
        if common is None:
            common = identity
        elif identity != common:
            raise ValueError('candidate laws must share target and epoch support')
        rows.append((name, lower, upper))
    _, target, count = common
    return dict(
        scope='union_of_supplied_affine_known_laws',
        binding_sha256=common[0], prediction_target=target,
        coordinate_count=count, candidate_laws=[row[0] for row in rows],
        lower=[min(row[1][i] for row in rows) for i in range(count)],
        upper=[max(row[2][i] for row in rows) for i in range(count)],
        minimum_marginal_coverage=minimum_marginal_coverage,
        condition='at least one supplied Gaussian law is correct; calibration lies in its box; affine model applies',
        selected_law=None, law_family_truth_established=False,
        nonlinear_aircraft_coverage_established=False,
        simultaneous_coverage_established=False,
        coverage_calibrated=False, scientific_decision='abstain')
