# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound ideal receiver phase wind-up in the saved ESA range score."""

import argparse
import json
from math import fsum, isclose, isfinite
from pathlib import Path
from platform import python_version

from .esa_nkar_error_budget import BASE, SOURCES
from .studies.artifacts import digest, encoded


PLAN = BASE/'ESA_PHASE_WINDUP_PLAN.md'
RESULT = BASE/'esa-phase-windup-budget.json'
INPUTS = {k: SOURCES[k] for k in ('score', 'products', 'nkar')}
INPUTS['budget'] = ('esa-nkar-error-budget-v1.json',
                    '803317aa17a3e6ed98f0bbe3f8434cdfa9e0313b1ff7ac30950e0add2d820cc6')


def phase_gradient(satellite_direction, antenna_normal):
    """Phase radians per radian of antenna rotation in a common frame."""
    import numpy as np

    ray, normal = map(lambda v: np.asarray(v, float),
                      (satellite_direction, antenna_normal))
    if any(v.shape != (3,) or not isclose(float(v@v), 1., abs_tol=1e-12)
           for v in (ray, normal)):
        raise ValueError('unit ray and antenna normal required')
    elevation = float(ray@normal)
    if elevation < 0:
        raise ValueError('ray outside the upper antenna hemisphere')
    return -(normal + ray)/(1 + elevation)


def endpoint_weights(support, weights):
    """Transpose interval differencing and within-interval mean removal."""
    if (not support or sum(map(len, support)) != len(weights)
            or any(len(row) < 2 or len(set(row)) != len(row) for row in support)
            or not all(map(isfinite, weights))):
        raise ValueError('complete finite weights and unique satellite support required')
    endpoints = [{} for _ in range(len(support)+1)]
    offset = 0
    for i, satellites in enumerate(support):
        row = weights[offset:offset+len(satellites)]
        centre = fsum(row)/len(row)
        offset += len(row)
        for prn, weight in zip(satellites, row, strict=True):
            w = weight-centre
            endpoints[i][prn] = endpoints[i].get(prn, 0.) - w
            endpoints[i+1][prn] = endpoints[i+1].get(prn, 0.) + w
    return endpoints


def tilt_budget(support, weights, allowance):
    """Bound the score effect per degree of maximum antenna tilt."""
    from .esa_carrier_phase_support import C, F1, F2

    if not isfinite(allowance) or allowance <= 0:
        raise ValueError('positive finite score allowance required')
    endpoints = endpoint_weights(support, weights)
    total = fsum(abs(w) for row in endpoints for w in row.values())
    per_degree = total*C/((F1+F2)*360)
    return dict(endpoint_absolute_weight_sum=total, per_degree=per_degree,
                equal_allowance_tilt_deg=allowance/per_degree if per_degree else None)


def evidence(root):
    def read(key):
        name, sha = INPUTS[key]
        raw = (root/BASE/name).read_bytes()
        if digest(raw) != sha:
            raise ValueError('source digest differs: '+name)
        return json.loads(raw)

    score, ranges, ground, budget = map(read, INPUTS)
    gap = score['score_gap']
    support = [row['common_satellites'] for row in ranges['rows']]
    full, covered = score['bound']['dual_weights'], ground['projected_weights']
    if (not all(row['passed'] and not row['new_fits'] and not row['protected_reads']
                for row in (score, ranges, ground))
            or ground['score_gap'] != gap
            or ground['bound_sha256'] != SOURCES['score'][1]
            or ground['orbit_sha256'] != SOURCES['products'][1]
            or budget['score_gap'] != gap or budget['matched_intervals'] != 120
            or len(support) != 240 or len(full) != len(covered) or len(full) != 2496
            or ground['matched_intervals'] != 120):
        raise ValueError('the same sealed score and ground support are required')
    missed = [a-b for a, b in zip(full, covered, strict=True)]
    parts = {k: tilt_budget(support, w, gap) for k, w in (
        ('full', full), ('covered', covered), ('missed', missed))}
    remaining = (budget['illustration']['max_covered_rms_m']
                 * budget['coefficients']['visible_range_rms_m'])
    covered_per_degree = parts['covered']['per_degree']
    return dict(version='ideal-receiver-phase-windup-v1', recording=187,
                interval_count=len(support), range_values=len(full), score_gap=gap,
                input_sha256={k: value[1] for k, value in INPUTS.items()},
                plan_sha256=digest((root/PLAN).read_bytes()),
                source_sha256=digest(Path(__file__).read_bytes()), python=python_version(),
                covered_example_score_allowance=remaining,
                equal_covered_example_allowance_tilt_deg=(
                    remaining/covered_per_degree if covered_per_degree else None),
                common_rotation_cancels=True, results=parts, new_fits=0, protected_reads=0,
                scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('release', 'check'))
    args = parser.parse_args()
    root = Path.cwd()
    result = evidence(root)
    if args.action == 'release':
        from .ilvis0_matched_observed_inputs import _write_equal

        _write_equal(root/RESULT, encoded(result))
    elif (root/RESULT).read_bytes() != encoded(result):
        raise ValueError('the saved phase wind-up budget differs')
    print(json.dumps(result['results'], sort_keys=True))


if __name__ == '__main__':
    main()
