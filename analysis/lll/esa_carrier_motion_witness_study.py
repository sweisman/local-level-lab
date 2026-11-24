# SPDX-License-Identifier: AGPL-3.0-or-later
"""Search for a smooth, bounded position error in four saved ESA carrier geometries."""

import argparse
from contextlib import closing
import json
from pathlib import Path

from . import esa_carrier_reweighted_budget as parent
from .studies.artifacts import digest, encoded


ID = 'esa-carrier-motion-witness-v1'
SCOPE = 'ESA 187 smooth bounded displacement witness on fixed carrier supports'
PLAN = parent.FOLDER+'ESA_CARRIER_MOTION_WITNESS_PLAN.md'
RESULT = parent.FOLDER+'esa-carrier-motion-witness-result.json'
PARENT_SHA = '186e969bfa23002e1ecf1ab9af67c9cf8b6675475f92508058416aa2612ec5a1'
PAIRS = parent.prior.parent.PAIRS
CASES = parent.prior.parent.CASES
CASE_STEPS = (160+2)*parent.prior.parent.SOLVE_STEPS
TASK = dict(identity='smooth-score-witness', input_key='budget', payload={},
            limits=dict(native_calls=0, packet_visits=0, bound_calls=1+PAIRS+1+len(CASES),
                        bound_steps=1+66*PAIRS+(1+len(CASES))*CASE_STEPS))


def prepare(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the original finite motion witness search')
    report = (root/parent.RESULT).read_bytes()
    if digest(report) != PARENT_SHA:
        raise ValueError('original uncertain-anchor report required')
    budget = json.loads(report)
    inputs = {'plan': PLAN, 'budget': parent.RESULT}
    with closing(ClosedStudy(root, 'data/'+parent.ID)) as study:
        envelope = study.envelope(parent.TASK['identity'])
        if (study.completion != budget['completion'] or envelope['charged'] != parent.TASK['limits']
                or any(budget[key] != value for key, value in envelope['result'].items())):
            raise ValueError('verified complete uncertain-anchor study required')
        for key in ('prior', 'motion', 'baseline', 'nkar', 'phase', 'score', 'anchor', 'path',
                    'metric', 'continuity', 'original', 'rinex', 'navigation', 'orbit', 'remainder'):
            path = f'data/{ID}-inputs/{key}'
            _write_equal(root/path, study.input(key, raw=True))
            inputs[key] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, 'analysis/tests/test_carrier_motion_witness.py'))
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=120)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def reconstruct_problem(raw, charge):
    import numpy as np

    from .carrier_range_remainder import bound_score_remainder, position_cap

    times, _, gradients, _, support, fixed, score_times, taps, baseline, ground = (
        parent.prior.parent.reconstruct_geometry(raw, charge))
    budget, screen, geometry, metric = (json.loads(raw(key)) for key in ('budget', 'prior', 'remainder', 'metric'))
    gap = baseline['score_gap']
    anchors = [times[i] for i in fixed]
    if (not gap == budget['score_gap'] == geometry['score_gap'] == screen['original_score_gap']
            or anchors != budget['anchor_gps_s'] or anchors != geometry['anchor_times_gps_s']
            or metric != geometry['metric'] or times[-1]-times[0] != 120):
        raise ValueError('the unchanged gap, carrier metric and anchors are required')
    caps = budget['illustrative_caps'] | {'visible_range_rms_m': .001}
    offset = times[0]
    times = np.asarray(times)-offset
    score_times = np.asarray(score_times)-offset
    station = {(r['first'], r['last']): r['satellites'] for r in ground['intervals']}
    max_coordinate = position_cap(anchors, caps['anchor_axis_m'], caps['acceleration_rms_mps2'])
    endpoint_m = bound_score_remainder([1, -1], [2], metric, geometry['max_absolute_path_height_m'],
                                       max_coordinate)['endpoint_range_remainder_m']
    buffer_m = float(np.nextafter(float(2*endpoint_m), np.inf))
    problem = dict(times=times, anchor_indices=fixed, score_times=score_times, taps=taps, station=station,
                   caps=caps, geometric_buffer_m=buffer_m, gap=gap)
    return problem, float(np.nextafter(float(max_coordinate), np.inf)), offset, gradients, support, screen


def screened_operators(times, gradients, support, screen, charge, steps):
    import numpy as np

    from .carrier_score_bound import range_operator

    for initial, saved in zip((None, *CASES), screen['screened_support'], strict=True):
        charge(bound_calls=1, bound_steps=steps)
        if saved['initial_tilt_allowance_deg'] != initial:
            raise ValueError('unchanged archived satellite sets required')
        pairs = []
        for arrays, all_prns, retained in zip(gradients, support, saved['support'], strict=True):
            keep = np.isin(all_prns, retained)
            if np.asarray(all_prns)[keep].tolist() != retained:
                raise ValueError('unchanged satellite identities and sorting required')
            pairs.append(tuple(array[keep] for array in arrays))
        operator = range_operator(pairs, len(times), allow_missing=True)
        if operator.shape[0] != saved['range_values']:
            raise ValueError('original range row count required')
        yield initial, operator, saved['support']


def evaluate(task, context):
    import numpy as np

    from .carrier_motion_witness import ITERATIONS, search, verify

    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK
            or ITERATIONS != 160):
        raise ValueError('the fixed bounded path search is required')
    context.charge(bound_calls=1, bound_steps=1)

    def raw(key):
        return context.input_path(key).read_bytes()

    problem, _, offset, gradients, support, screen = reconstruct_problem(raw, context.charge)
    times, caps, buffer_m = (problem[key] for key in ('times', 'caps', 'geometric_buffer_m'))
    knots = np.union1d(np.arange(0., 120.1, 2.5), times[problem['anchor_indices']])
    results = []
    for initial, operator, retained in screened_operators(times, gradients, support, screen, context.charge, CASE_STEPS):
        inputs = dict(problem, knots=knots, operator=operator, support=retained)
        positions, outcome = search(**inputs)
        raw_metrics = verify(positions, **inputs)
        limit = max(
            1.,
            raw_metrics['anchor_max_abs_m']/caps['anchor_axis_m'],
            raw_metrics['acceleration_rms_mps2']/caps['acceleration_rms_mps2'],
            raw_metrics['range_rms_in_ground_m']/(caps['visible_range_rms_m']-buffer_m),
            raw_metrics['range_rms_outside_ground_m']/(caps['invisible_range_rms_m']-buffer_m),
        )
        scale = (1.-1e-10)/limit
        if scale*raw_metrics['score_fraction'] > 1.+1e-12:
            scale = (1.+1e-12)/raw_metrics['score_fraction']
        positions *= scale
        checked = verify(positions, **inputs)
        if not checked['within_linear_and_geometry_caps'] or not np.isfinite(positions).all():
            raise ValueError('witness failed the direct cap check')
        results.append(dict(initial_tilt_allowance_deg=initial, witness=checked['score_fraction'] >= 1.,
                            positions_m=positions.tolist(), optimizer_success=bool(outcome.success),
                            optimizer_status=int(outcome.status), iterations=int(outcome.nit),
                            unscaled_score_fraction=raw_metrics['score_fraction'], **checked))
    context.save('witness-paths.json', dict(knot_gps_s=(knots+offset).tolist(), rows=results))
    return dict(passed=True, scientific_decision='abstain', aircraft_error_cap_established=False,
                score_gap=problem['gap'], caps=caps, geometric_buffer_rms_m=buffer_m,
                original_reads=0, protected_reads=0, new_fits=0,
                cases=[{key: value for key, value in case.items() if key != 'positions_m'} for case in results])


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('complete verified motion witness search required')
        result = dict(envelope['result'], completion=study.completion, inputs=study.manifest['inputs'],
                      charged=envelope['charged'], paths=study.artifact(TASK['identity'], 'witness-paths.json'))
    _write_equal(root/RESULT, encoded(result))
    return {key: value for key, value in result.items() if key not in ('inputs', 'paths')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    print(json.dumps({'prepare': prepare, 'report': report}[parser.parse_args().action](Path.cwd()), sort_keys=True))
