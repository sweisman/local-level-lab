# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate saved carrier weights with measured ground ranges and uncertain anchors."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path

from . import esa_carrier_weight_tradeoff as prior
from .esa_nkar_error_budget import OUTPUT as ORIGINAL_BUDGET, SOURCES as BUDGET_INPUTS
from .studies.artifacts import digest, encoded


ID = 'esa-carrier-reweighted-budget-v1'
SCOPE = 'ESA 187 reweighted carrier score with observed ranges and uncertain anchors'
FOLDER = prior.parent.lever.FOLDER
PLAN = FOLDER+'ESA_CARRIER_REWEIGHTED_BUDGET_PLAN.md'
RESULT = FOLDER+'esa-carrier-reweighted-budget-result.json'
PRIOR_SHA = 'a306d8948c7514920dc525013e1ef06b92a2f4aa62c3289c31e54eadefe59080'
ORIGINAL_SHA = '803317aa17a3e6ed98f0bbe3f8434cdfa9e0313b1ff7ac30950e0add2d820cc6'
CHECKS = 1+prior.N
TASK = dict(identity='anchored-reweighted-budget', input_key='tradeoff', payload={},
            limits=dict(native_calls=0, packet_visits=0, bound_calls=1+prior.parent.PAIRS+CHECKS,
                        bound_steps=1+66*prior.parent.PAIRS+CHECKS*prior.parent.SOLVE_STEPS))


def linear_anchor_basis(times, anchors):
    """Return each site's interpolation weights on the enclosing position anchors."""
    import numpy as np

    times, anchors = map(lambda x: np.asarray(x, dtype=float), (times, anchors))
    if (times.ndim != 1 or not len(times) or anchors.ndim != 1 or len(anchors) < 2
            or not all(np.isfinite(x).all() for x in (times, anchors))
            or np.any(np.diff(anchors) <= 0)
            or np.any(times < anchors[0]) or np.any(times > anchors[-1])):
        raise ValueError('finite site times within ordered anchors required')
    left = np.minimum(np.searchsorted(anchors, times, side='right')-1, len(anchors)-2)
    share = (times-anchors[left])/(anchors[left+1]-anchors[left])
    basis = np.zeros((len(times), len(anchors)))
    rows = np.arange(len(times))
    basis[rows, left], basis[rows, left+1] = 1-share, share
    return basis


def anchor_box(times, anchors, score_times, taps, operator, weights):
    """Signed score sensitivity to each unknown anchor position component."""
    range_taps = (operator.T@weights).reshape(-1, 3)
    return (linear_anchor_basis(score_times, anchors).T@taps
            - linear_anchor_basis(times, anchors).T@range_taps)


def ground_score(projection, station_rows):
    terms = []
    for row in projection['intervals']:
        observed = station_rows[row['first'], row['last']]
        ranges = dict(zip(observed['satellites'], observed['ground_range_m'], strict=True))
        terms.extend(weight*ranges[prn] for prn, weight in
                     zip(row['satellites'], row['aggregate_weights'], strict=True))
    return math.fsum(terms)


def prepare(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the original finite reweighted budget')
    inputs = {'plan': PLAN}
    for key, (path, sha) in {
        'tradeoff': (prior.RESULT, PRIOR_SHA), 'legacy_budget': (str(ORIGINAL_BUDGET), ORIGINAL_SHA),
        'remainder': (FOLDER+BUDGET_INPUTS['geometry'][0], BUDGET_INPUTS['geometry'][1]),
    }.items():
        if digest((root/path).read_bytes()) != sha:
            raise ValueError('prior report differs: '+path)
        inputs[key] = path
    report = json.loads((root/prior.RESULT).read_bytes())
    with closing(ClosedStudy(root, 'data/'+prior.ID)) as study:
        identity = prior.TASK['identity']
        if (study.completion != report['completion']
                or study.envelope(identity)['charged'] != prior.TASK['limits']
                or study.artifact(identity, 'weight-tradeoff.json') != report['histories']):
            raise ValueError('verified complete weight histories required')
        for key in ('prior', 'motion', 'baseline', 'nkar', 'phase', 'score', 'anchor', 'path',
                    'metric', 'continuity', 'original', 'rinex', 'navigation', 'orbit'):
            path = f'data/{ID}-inputs/{key}'
            _write_equal(root/path, study.input(key, raw=True))
            inputs[key] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, 'analysis/tests/test_esa_carrier_reweighted_budget.py'))
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=90)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .carrier_range_remainder import bound_score_remainder, position_cap
    from .carrier_score_bound import range_operator
    from .carrier_score_cadence import project_cadence
    from .esa_nkar_error_budget import split_score
    from .esa_reference_error_budget import evaluate_budget

    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('the frozen reweighted budget is required')
    context.charge(bound_calls=1, bound_steps=1)

    def raw(key):
        return context.input_path(key).read_bytes()

    def read(key):
        return json.loads(raw(key))

    times, _, gradients, _, support, fixed, score_times, taps, baseline, ground = (
        prior.parent.reconstruct_geometry(raw, context.charge))
    anchors = [times[i] for i in fixed]
    original, legacy, remainder, screen, tradeoff = (
        read(key) for key in ('original', 'legacy_budget', 'remainder', 'prior', 'tradeoff'))
    station = {(r['first'], r['last']): r for r in ground['intervals']}
    available = {key: row['satellites'] for key, row in station.items()}
    caps = legacy['illustration']['other_caps'] | {'visible_range_rms_m': 0.}
    gap = baseline['score_gap']
    if (anchors != remainder['anchor_times_gps_s'] or remainder['metric'] != read('metric')
            or not gap == legacy['score_gap'] == tradeoff['score_gap'] == remainder['score_gap']
            or caps['acceleration_rms_mps2'] != tradeoff['illustrative_acceleration_rms_mps2']):
        raise ValueError('original anchors, metric and example acceleration required')
    interior_cap = position_cap(anchors, caps['anchor_axis_m'], caps['acceleration_rms_mps2'])

    def compare(initial, kept, weights, accel, *, legacy_case=False):
        context.charge(bound_calls=1, bound_steps=prior.parent.SOLVE_STEPS)
        selected, values = [], []
        for pair, block, retained, original_row in zip(gradients, support, kept, original['rows'], strict=True):
            mask = np.isin(block, retained)
            if np.asarray(block)[mask].tolist() != retained or block != original_row['common_satellites']:
                raise ValueError('preserve the screened satellite identities and order')
            selected.append(tuple(side[mask] for side in pair))
            values.extend(np.asarray(original_row['fixed_residual_m'])[mask].tolist())
        operator = range_operator(selected, len(times), allow_missing=True)
        if operator.shape[0] != len(weights) or len(values) != len(weights):
            raise ValueError('signed weights must match retained observations')
        projected = project_cadence(kept, weights, sorted(station), interval_satellites=available)
        parts = split_score(weights, projected['projected_weights'], values)
        station_score = ground_score(projected, station)
        signed = anchor_box(times, anchors, score_times, taps, operator, weights)
        per_axis = float(np.abs(signed).sum())
        effects = dict(visible_range_rms_m=parts['covered_rms_to_score'],
                       invisible_range_rms_m=parts['uncovered_rms_to_score'],
                       anchor_axis_m=legacy['coefficients']['anchor_axis_m'] if legacy_case else per_axis,
                       acceleration_rms_mps2=accel)
        geometric = float(bound_score_remainder(weights, [len(r) for r in kept if r], remainder['metric'],
                          remainder['max_absolute_path_height_m'], interior_cap)['max_score_remainder'])
        margin = evaluate_budget(gap, abs(parts['full_aircraft_score'])+geometric, effects, caps)['remaining_margin']
        allowance = max(0., margin)/effects['visible_range_rms_m']
        current = evaluate_budget(gap, parts['full_aircraft_score'], effects, dict.fromkeys(effects))
        return dict(initial_tilt_allowance_deg=initial, legacy_case=legacy_case, coefficients=effects,
                    aircraft_score=parts, ground_score=station_score,
                    covered_aircraft_minus_ground_score=parts['covered_aircraft_score']-station_score,
                    covered_norm_fraction=projected['observable_norm_fraction'],
                    exact_anchor_box_coefficient=per_axis, geometric_remainder_score=geometric,
                    signed_anchor_weights=signed.tolist(), illustrative_margin_before_covered_error=margin,
                    illustrative_max_covered_range_rms_m=allowance, current=current)

    control = compare(None, support, baseline['bound']['dual_weights'],
                      baseline['bound']['acceleration_rms_to_score'], legacy_case=True)
    tolerance = {'rel_tol': 1e-11, 'abs_tol': 1e-13}
    if (not math.isclose(control['illustrative_max_covered_range_rms_m'],
                         legacy['illustration']['max_covered_rms_m'], **tolerance)
            or not math.isclose(control['ground_score'], ground['ground_score_equivalent'], **tolerance)
            or not math.isclose(control['covered_aircraft_minus_ground_score'],
                                ground['air_minus_ground_score_equivalent'], **tolerance)
            or control['exact_anchor_box_coefficient'] > legacy['coefficients']['anchor_axis_m']+1e-12):
        raise ValueError('legacy allowance, matched range scores and anchor bound must reproduce')
    cases = []
    for row, weights in zip(screen['screened_support'], tradeoff['histories'], strict=True):
        initial = row['initial_tilt_allowance_deg']
        if weights['initial_tilt_allowance_deg'] != initial:
            raise ValueError('original weight pairings are required')
        best = weights['histories'][weights['selected_index']]
        cases.append(compare(initial, row['support'], weights['selected_weights'], best['acceleration_rms_to_score']))
    return dict(passed=True, scientific_decision='abstain', aircraft_error_cap_established=False,
                original_reads=0, new_fits=0, protected_reads=0, score_gap=gap,
                anchor_gps_s=anchors, illustrative_caps=caps, legacy_control=control, cases=cases)


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('the verified completed reweighted budget is required')
        result = dict(envelope['result'], completion=study.completion, inputs=study.manifest['inputs'],
                      charged=envelope['charged'])
    _write_equal(root/RESULT, encoded(result))
    return dict(state='complete', legacy_mm=1000*result['legacy_control']['illustrative_max_covered_range_rms_m'],
                examples=[dict(tilt_deg=row['initial_tilt_allowance_deg'],
                               covered_allowance_mm=1000*row['illustrative_max_covered_range_rms_m'],
                               anchor_score_per_m=row['exact_anchor_box_coefficient'],
                               aircraft_score=row['aircraft_score']['full_aircraft_score'],
                               aircraft_minus_ground=row['covered_aircraft_minus_ground_score'],
                               margin=row['illustrative_margin_before_covered_error']) for row in result['cases']])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    print(json.dumps({'prepare': prepare, 'report': report}[parser.parse_args().action](Path.cwd()), sort_keys=True))
