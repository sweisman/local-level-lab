# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate the score-gap budget on measured and unmeasured carrier directions."""
import argparse
import json
import math
from pathlib import Path

from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


BASE = Path('docs/prediction-observed-development')
OUTPUT = BASE/'esa-reference-error-budget-v1.json'
SOURCES = {
    'score': ('esa-carrier-score-bound-result.json', '12c0f807d4e710cf05fc3dc521ad9e05f2ba69df8e53f95bcf47dd541b6295bb'),
    'anchors': ('esa-carrier-anchor-error-result.json', '173b6541028b1e5db7cc64cec2903788a1b34eb5139d93dfa6e85eb9fdffa1fc'),
    'ground': ('esa-qaq-ground-score-result.json', '98251d43fbaed81aeb24cb3fd8555b74636fab0c1c982a296fb315772e68a185'),
    'transfer': ('esa-qaq-phase-transfer-result.json', '50508c8bc9a6777b44b27533dee56fd977c7874e4a3f1fc46d247f8a2493d61b'),
    'products': ('esa-nuuk-orbit-clock-result.json', '40b586d4e848468e41482df75353efc8d93256cf0593e8eca8a3635d7cd7261d'),
}


def evaluate_budget(gap, residual_score, coefficients, caps):
    """Report a conditional linear bound. A missing cap is never zero."""
    if (not math.isfinite(gap) or gap <= 0 or not math.isfinite(residual_score)
            or set(caps) != set(coefficients) or not coefficients
            or any(not math.isfinite(v) or v < 0 for v in coefficients.values())
            or any(v is not None and (not math.isfinite(v) or v < 0) for v in caps.values())):
        raise ValueError('positive score gap and explicit nonnegative finite error allowances required')
    missing = sorted(k for k, v in caps.items() if v is None)
    if missing:
        return dict(status='abstain', missing=missing, total_score_allowance=None, remaining_margin=None)
    total = math.fsum([abs(residual_score), *(coefficients[k]*v for k, v in caps.items())])
    margin = gap-total
    if math.isclose(total, gap, rel_tol=1e-14):
        margin = 0.
    return dict(status='inside_linear_score_budget' if margin > 0 else 'abstain', missing=[],
                total_score_allowance=total, remaining_margin=margin)


def evidence(root):
    def read(name):
        filename, expected = SOURCES[name]
        raw = (root/BASE/filename).read_bytes()
        if digest(raw) != expected:
            raise ValueError('aircraft reference evidence digest differs: '+filename)
        return json.loads(raw)

    score, anchor, ground, transfer, products = map(read, ('score', 'anchors', 'ground', 'transfer', 'products'))
    original = score['bound']
    weights, projected = original['dual_weights'], ground['projected_weights']
    ranges = [x for row in products['rows'] for x in row['fixed_residual_m']]
    complement = [a-b for a, b in zip(weights, projected, strict=True)]
    count = len(weights)
    gap = score['score_gap']
    if (count != len(ranges) or count != original['range_values'] or count != 2496
            or any(x['score_gap'] != gap for x in (anchor, ground, transfer))
            or any(x['new_fits'] or x['protected_reads'] for x in (score, anchor, ground, transfer, products))):
        raise ValueError('the complete matched score and original aircraft window are required')

    def dot(a, b):
        return math.fsum(x*y for x, y in zip(a, b, strict=True))

    total = dot(weights, ranges)
    observed, unobserved = dot(projected, ranges), dot(complement, ranges)
    combined_ground = ground['ground_score_equivalent']*transfer['trained_gain']
    residual = total-combined_ground
    visible_norm, invisible_norm = (math.sqrt(count*dot(w, w)) for w in (projected, complement))
    if (abs(dot(projected, complement)) > 1e-12
            or not math.isclose(total, observed+unobserved, rel_tol=1e-12)
            or not math.isclose(observed, ground['aircraft_score_equivalent'], rel_tol=1e-12)
            or not math.isclose(-combined_ground, transfer['later_score_shift'], rel_tol=1e-12)
            or not math.isclose(math.hypot(visible_norm, invisible_norm), original['range_rms_to_score'], rel_tol=1e-12)):
        raise ValueError('the measured score projection and its orthogonal complement must reproduce')
    observations = dict(full_aircraft_score_equivalent=total, visible_aircraft_score_equivalent=observed,
                        invisible_aircraft_score_equivalent=unobserved, earlier_ground_score_equivalent=combined_ground,
                        after_earlier_correction=residual)
    coefficients = dict(visible_range_rms_m=visible_norm, invisible_range_rms_m=invisible_norm,
                        anchor_axis_m=anchor['anchor_uncertainty']['all_anchor_axis_to_score'],
                        acceleration_rms_mps2=original['acceleration_rms_to_score'], linearization_score=1.)
    illustrative = dict(visible_range_rms_m=0., invisible_range_rms_m=.002, anchor_axis_m=1.,
                        acceleration_rms_mps2=score['test_acceleration_rms_mps2'], linearization_score=0.)
    available = evaluate_budget(gap, residual, coefficients, illustrative)['remaining_margin']
    example = dict(other_caps=illustrative, maximum_visible_range_rms_m=max(0., available)/visible_norm)
    return dict(version=1, recording=187, independent_flight_groups=0, range_values=count, score_gap=gap,
                source_sha256={name: sha for name, (_, sha) in SOURCES.items()}, observations=observations,
                coefficients=coefficients, current=evaluate_budget(gap, residual, coefficients, dict.fromkeys(coefficients)),
                illustration=example, scientific_decision='abstain')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('release', 'check'))
    args = parser.parse_args()
    root = Path.cwd()
    result = evidence(root)
    if args.action == 'release':
        _write_equal(root/OUTPUT, encoded(result))
    elif (root/OUTPUT).read_bytes() != encoded(result):
        raise ValueError('the saved reference-error budget differs')
    print(json.dumps({k: result[k] for k in ('observations', 'coefficients', 'current', 'illustration')}, sort_keys=True))
