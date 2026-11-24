# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay the exact-anchor carrier score with balanced range and motion weights."""

import argparse
from contextlib import closing
import json
from pathlib import Path

from . import esa_carrier_elevation_screen as parent
from .studies.artifacts import digest, encoded


ID = 'esa-carrier-weight-tradeoff-v1'
SCOPE = 'ESA 187 exact-anchor motion response and damped carrier score geometry'
PLAN = parent.lever.FOLDER+'ESA_CARRIER_WEIGHT_TRADEOFF_PLAN.md'
RESULT = parent.lever.FOLDER+'esa-carrier-weight-tradeoff-result.json'
PARENT_SHA = '24c87d5c118b042e42f4985ac1de43dd81719d3113480bb5f1694a47dfc01777'
RATIOS = (1e-5, 3e-5, 1e-4, 3e-4, .001, .003, .01, .03, .1, .3, 1.)
N = 1+len(parent.CASES)
CHECKS = N*(2+len(RATIOS))
TASK = dict(identity='carrier-motion-tradeoff', input_key='prior', payload={},
            limits=dict(native_calls=0, packet_visits=0, bound_calls=1+parent.PAIRS+CHECKS,
                        bound_steps=1+66*parent.PAIRS+CHECKS*parent.SOLVE_STEPS))


def prepare(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the original finite carrier weighting study')
    report = (root/parent.RESULT).read_bytes()
    if digest(report) != PARENT_SHA:
        raise ValueError('the original satellite screen report is required')
    prior = json.loads(report)
    inputs = {'plan': PLAN, 'prior': parent.RESULT}
    with closing(ClosedStudy(root, 'data/'+parent.ID)) as study:
        identity = parent.TASK['identity']
        if (study.completion != prior['completion']
                or study.envelope(identity)['charged'] != parent.TASK['limits']
                or study.artifact(identity, 'screened-support.json') != prior['screened_support']):
            raise ValueError('exact closed screen and weights required')
        for key in ('motion', 'baseline', 'nkar', 'phase', 'score', 'anchor', 'path', 'metric',
                    'continuity', 'original', 'rinex', 'navigation', 'orbit'):
            path = f'data/{ID}-inputs/{key}'
            _write_equal(root/path, study.input(key, raw=True))
            inputs[key] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, 'analysis/tests/test_carrier_weight_tradeoff.py'))
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=120)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .carrier_score_bound import range_operator
    from .carrier_score_cadence import project_cadence
    from .carrier_weight_tradeoff import anchor_response, weighted_candidates

    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('frozen carrier weighting tradeoff required')
    context.charge(bound_calls=1, bound_steps=1)

    def raw(key):
        return context.input_path(key).read_bytes()

    prior = json.loads(raw('prior'))
    times, _, gradients, _, support, fixed, score_times, taps, baseline, ground = (
        parent.reconstruct_geometry(raw, context.charge))
    times = np.asarray(times)
    free = np.ones(len(times), dtype=bool)
    free[fixed] = False
    union = np.union1d(times, score_times)
    response = anchor_response(union-times[0], times[fixed]-times[0])
    response_range = response[:, np.searchsorted(union, times[free])]
    response_score = response[:, np.searchsorted(union, score_times)]@taps
    elapsed = times[-1]-times[0]
    acceleration = baseline['test_acceleration_rms_mps2']
    gap = baseline['score_gap']
    station_support = {(r['first'], r['last']): r['satellites'] for r in ground['intervals']}
    results = []
    for initial, row in zip((None, *parent.CASES), prior['screened_support'], strict=True):
        if row['initial_tilt_allowance_deg'] != initial:
            raise ValueError('unchanged satellite screen case order required')
        selected = []
        for pair, all_prns, retained in zip(gradients, support, row['support'], strict=True):
            mask = np.isin(all_prns, retained)
            if np.asarray(all_prns)[mask].tolist() != retained:
                raise ValueError('unchanged satellite support required')
            selected.append(tuple(side[mask] for side in pair))
        context.charge(bound_calls=1, bound_steps=parent.SOLVE_STEPS)
        operator = range_operator(selected, len(times), allow_missing=True)[:, np.repeat(free, 3)]
        if operator.shape[0] != row['range_values']:
            raise ValueError('the original screened range count must reproduce')
        previous = np.array(row['dual_weights'])
        candidates = weighted_candidates(response_range, response_score, operator, RATIOS)
        choices = []
        for ratio, weights in zip((None, *RATIOS), (previous, *candidates), strict=True):
            context.charge(bound_calls=1, bound_steps=parent.SOLVE_STEPS)
            surrogate = (operator.T@weights).reshape(-1, 3)
            distance = float(np.linalg.norm(response_score-response_range@surrogate))*np.sqrt(elapsed)
            range_coefficient = float(np.linalg.norm(weights)*np.sqrt(len(weights)))
            slack = max(0., gap-acceleration*distance)
            allowance = slack/range_coefficient if range_coefficient else 0.
            if not np.isfinite(allowance) or not np.isfinite(distance):
                raise ValueError('bound must be finite')
            choices.append(dict(damping_ratio=ratio, acceleration_rms_to_score=distance,
                                range_rms_to_score=range_coefficient, range_allowance_m=allowance))
        original = choices[0]
        if (not np.isclose(original['range_rms_to_score'], row['range_rms_to_score'], rtol=1e-12)
                or original['acceleration_rms_to_score'] > row['acceleration_rms_to_score']+2e-10):
            raise ValueError('the old weights must match and the exact motion norm must respect their prior bound')
        index = max(range(len(choices)), key=lambda i: choices[i]['range_allowance_m'])
        weights = (previous, *candidates)[index]
        projection = project_cadence(row['support'], weights, sorted(station_support),
                                     interval_satellites=station_support)
        results.append(dict(initial_tilt_allowance_deg=initial, histories=choices, selected_index=index,
                            prior_range_allowance_m=row['exact_anchor_range_rms_allowance_m'],
                            prior_ground_norm_fraction=row['ground_norm_fraction'],
                            ground_norm_fraction=projection['observable_norm_fraction'],
                            selected_weights=weights.tolist()))
    context.save('weight-tradeoff.json', results)
    return dict(passed=True, scientific_decision='abstain', aircraft_error_cap_established=False,
                illustrative_acceleration_rms_mps2=acceleration, score_gap=gap,
                original_reads=0, new_fits=0, protected_reads=0,
                cases=[{key: value for key, value in row.items() if key not in ('selected_weights', 'histories')}
                       | row['histories'][row['selected_index']] for row in results])


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('the verified complete carrier weight tradeoff is required')
        result = dict(envelope['result'], completion=study.completion, inputs=study.manifest['inputs'],
                      charged=envelope['charged'], histories=study.artifact(TASK['identity'], 'weight-tradeoff.json'))
    _write_equal(root/RESULT, encoded(result))
    return {key: value for key, value in result.items() if key not in ('inputs', 'histories')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    print(json.dumps({'prepare': prepare, 'report': report}[parser.parse_args().action](Path.cwd()), sort_keys=True))
