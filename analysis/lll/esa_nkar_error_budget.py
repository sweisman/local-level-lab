# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay the development score budget with the measured Nuuk Museum support."""
import argparse
from fractions import Fraction
import json
from math import fsum, isclose, sqrt
from pathlib import Path

from .esa_reference_error_budget import BASE, SOURCES as EARLIER, evaluate_budget
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


PLAN = BASE/'ESA_NKAR_ERROR_BUDGET_PLAN.md'
OUTPUT = BASE/'esa-nkar-error-budget-v1.json'
SOURCES = {
    **{key: EARLIER[key] for key in ('score', 'anchors', 'products')},
    'nkar': ('esa-nkar-ground-score-result.json', 'ab8fcb08bbf97d43538e0020649fce3f810bd4d488b1c52dadbc93ae5690aa75'),
    'geometry': ('esa-carrier-range-remainder-result.json', '8db0d4ae89708015fa6b8026aac2da522fbbb4aabd64f0f9501ad722abc67844'),
    'qaqortoq': ('esa-reference-error-budget-v1.json', '9c0678e6c6c75e5fe45ff31d0c9905669e3b0789bee926570ba7c4a13f7347a6'),
}


def dot(a, b):
    return fsum(x*y for x, y in zip(a, b, strict=True))


def split_score(weights, projected, ranges):
    outside = [a-b for a, b in zip(weights, projected, strict=True)]
    full, covered, uncovered = (dot(w, ranges) for w in (weights, projected, outside))
    if (not isclose(dot(projected, outside), 0., abs_tol=1e-12)
            or not isclose(full, covered+uncovered, rel_tol=1e-12, abs_tol=1e-14)):
        raise ValueError('an orthogonal score projection is required')
    count = len(weights)
    return dict(full_aircraft_score=full, covered_aircraft_score=covered, uncovered_aircraft_score=uncovered,
                covered_rms_to_score=sqrt(count*dot(projected, projected)),
                uncovered_rms_to_score=sqrt(count*dot(outside, outside)))


def evidence(root):
    from .carrier_range_remainder import bound_score_remainder, position_cap
    from .carrier_score_cadence import project_cadence

    def read(key):
        name, sha = SOURCES[key]
        raw = (root/BASE/name).read_bytes()
        if digest(raw) != sha:
            raise ValueError('source digest differs: '+name)
        return json.loads(raw)

    score, anchor, products, ground, geometry, old = map(
        read, ('score', 'anchors', 'products', 'nkar', 'geometry', 'qaqortoq'))
    gap = score['score_gap']
    rows = products['rows']
    weights = score['bound']['dual_weights']
    start, stop = score['endpoint_gps_s']
    if (not all(r['score_gap'] == gap for r in (anchor, ground, geometry, old))
            or not all(r['passed'] and not r['new_fits'] and not r['protected_reads']
                       for r in (score, anchor, products, ground, geometry))
            or len(rows) != 240 or len(weights) != 2496 or stop-start != 120
            or [r['seconds'] for r in rows] != [start+.5*i for i in range(1, 241)]
            or ground['bound_sha256'] != SOURCES['score'][1] or ground['orbit_sha256'] != SOURCES['products'][1]
            or geometry['parent_sha256'] != SOURCES['score'][1]):
        raise ValueError('the original complete score and ground comparison are required')

    support = [r['common_satellites'] for r in rows]
    intervals = [(i, i+2) for i in range(0, 240, 2)]
    if [(r['first'], r['last']) for r in ground['intervals']] != intervals:
        raise ValueError('the complete matched one-second support is required')
    selected = {key: row['satellites'] for key, row in zip(intervals, ground['intervals'], strict=True)}
    replay = project_cadence(support, weights, intervals, interval_satellites=selected)
    projected = ground['projected_weights']
    if not all(isclose(a, b, rel_tol=1e-12, abs_tol=1e-14)
               for a, b in zip(replay['projected_weights'], projected, strict=True)):
        raise ValueError('the measured ground projection differs from its replay')
    values = [value for row in rows for value in row['fixed_residual_m']]
    parts = split_score(weights, projected, values)
    if (not isclose(parts['covered_aircraft_score'], ground['aircraft_score_equivalent'], rel_tol=1e-12)
            or not isclose(fsum((parts['covered_aircraft_score'], -ground['ground_score_equivalent'])),
                           ground['air_minus_ground_score_equivalent'], rel_tol=1e-12)):
        raise ValueError('the observed range score differs from its replay')
    coefficients = dict(visible_range_rms_m=parts['covered_rms_to_score'],
                        invisible_range_rms_m=parts['uncovered_rms_to_score'],
                        anchor_axis_m=anchor['anchor_uncertainty']['all_anchor_axis_to_score'],
                        acceleration_rms_mps2=score['bound']['acceleration_rms_to_score'])
    limits = dict(visible_range_rms_m=0., invisible_range_rms_m=.002, anchor_axis_m=1.,
                  acceleration_rms_mps2=score['test_acceleration_rms_mps2'])
    axis_cap = position_cap(geometry['anchor_times_gps_s'], limits['anchor_axis_m'], limits['acceleration_rms_mps2'])
    bound_args = (weights, list(map(len, support)), geometry['metric'], geometry['max_absolute_path_height_m'])
    if bound_score_remainder(*bound_args, 1)['max_score_remainder'] != Fraction(geometry['exact_score_bound_per_square_m']):
        raise ValueError('the original geometric coefficient differs')
    remainder = float(bound_score_remainder(*bound_args, axis_cap)['max_score_remainder'])
    residual = abs(parts['full_aircraft_score'])

    def max_covered(factors):
        margin = evaluate_budget(gap, residual+remainder, factors, limits)['remaining_margin']
        return max(0., margin)/factors['visible_range_rms_m']

    old_coefficients = {key: old['coefficients'][key] for key in coefficients}
    return dict(version=1, recording=187, source_sha256={k: sha for k, (_, sha) in SOURCES.items()},
                plan_sha256=digest((root/PLAN).read_bytes()), score_gap=gap, range_values=len(weights),
                matched_intervals=len(intervals), observable_norm_fraction=ground['observable_norm_fraction'],
                values=parts, coefficients=coefficients,
                current=evaluate_budget(gap, residual, coefficients, dict.fromkeys(coefficients)),
                illustration=dict(other_caps={k: v for k, v in limits.items() if k != 'visible_range_rms_m'},
                                  geometric_remainder_score=remainder, interior_axis_cap_m=float(axis_cap),
                                  max_covered_rms_m=max_covered(coefficients),
                                  qaqortoq_matched_comparison_max_covered_rms_m=max_covered(old_coefficients)),
                new_fits=0, protected_reads=0, scientific_decision='abstain')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('release', 'check'))
    args = parser.parse_args()
    root = Path.cwd()
    result = evidence(root)
    if args.action == 'release':
        _write_equal(root/OUTPUT, encoded(result))
    elif (root/OUTPUT).read_bytes() != encoded(result):
        raise ValueError('the saved Nuuk Museum error budget differs')
    print(json.dumps({k: result[k] for k in ('current', 'coefficients', 'illustration')}, sort_keys=True))
