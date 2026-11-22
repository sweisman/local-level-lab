# SPDX-License-Identifier: AGPL-3.0-or-later
"""Measure how ground sampling exposes the saved ESA 187 carrier score."""
import argparse
from contextlib import ExitStack, closing
import json
from pathlib import Path

from . import esa_carrier_anchor_error as anchors
from . import esa_carrier_score_bound as carrier_bound
from . import esa_nuuk_orbit_clock as orbit
from . import esa_nuuk_phase_transfer as ground
from . import esa_shared_motion_carrier as carrier
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded


ID = 'esa-carrier-score-cadence-v1'
SCOPE = 'Observable carrier score on the verified and ideal Nuuk receiver grids'
PLAN = carrier.FOLDER+'ESA_CARRIER_SCORE_CADENCE_PLAN.md'
RESULT = carrier.FOLDER+'esa-carrier-score-cadence-result.json'
REQUEST = carrier.FOLDER+'esa-carrier-score-cadence-qualification.json'
XML = carrier.FOLDER+'esa-carrier-score-cadence-tests.xml'
ARTIFACT = 'carrier-score-cadence.json'
GROUND_SHA = '0779e5d7362e17176ade66268f45276b2158db7989ff4a1c1dacd01b48a4d58e'
PARENTS = (
    ('ground', ground, GROUND_SHA),
    ('ranges', orbit, carrier_bound.PRODUCT_SHA),
    ('score', carrier_bound, anchors.PARENT_SHA),
)
TASK = dict(identity='carrier-score-cadence', input_key='score', payload=dict(pairs=orbit.N),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=4, bound_steps=1+3*orbit.N))


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
                                    'analysis/tests/test_carrier_score_cadence.py',
                                    'analysis/tests/test_carrier_score_bound.py'))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=(
        'test_projection_matches_dense_ground_observation_operator',
        'test_projected_score_uses_centered_satellite_totals_without_interpolation'), minimum_tests=6)
    return sources, environment


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite cadence comparison')
    sources, environment = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    inputs = dict(plan=PLAN, qualification=REQUEST, qualification_tests=XML)
    with ExitStack() as stack:
        for key, parent, sha in PARENTS:
            saved, _ = _parent(root, parent.RESULT, sha, parent.ID, parent.TASK, parent.ARTIFACT, stack)
            if saved.envelope(parent.TASK['identity'])['charged'] != parent.TASK['limits']:
                raise ValueError('the complete charged parent evidence is required')
            inputs[key] = parent.RESULT
    values = dict(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=carrier.WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .carrier_score_cadence import project_cadence
    from .gnss_position import GAMMA

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen carrier cadence task is required')
    context.charge(bound_calls=1, bound_steps=1)
    station, ranges, score = [json.loads(context.input_path(key).read_bytes()) for key in ('ground', 'ranges', 'score')]
    start, end = score['endpoint_gps_s']
    rows = ranges['rows']
    times = [start, *(row['seconds'] for row in rows)]
    support = [row['common_satellites'] for row in rows]
    dual = score['bound']['dual_weights']
    observed = station['withheld_indices']
    ground_sats = station['satellites']
    intervals = [(times.index(station['times'][i]), times.index(station['times'][i+1])) for i in observed]
    if (times != [start+j*.5 for j in range(orbit.N+1)] or end != times[-1]
            or observed != [13, 14, 15] or any(j-i != 60 for i, j in intervals)
            or len(dual) != score['bound']['range_values']):
        raise ValueError('exact matched half-second grid and three held-out ground intervals required')

    results = {}
    for key, grid, sats in (('observed_30s', intervals, ground_sats),
                           ('ideal_1s', [(i, i+2) for i in range(0, orbit.N, 2)], None),
                           ('ideal_30s', [(i, i+60) for i in range(0, orbit.N, 60)], None)):
        context.charge(bound_calls=1, bound_steps=orbit.N)
        results[key] = project_cadence(support, dual, grid, available=sats)

    coeff = np.array([GAMMA, -1.])/(GAMMA-1.)
    ground_totals = np.asarray(station['ground_band_residual_m'])@coeff
    corrections = []
    for i, row, interval in zip(observed, results['observed_30s']['intervals'], intervals, strict=True):
        if (row['first'], row['last']) != interval:
            raise ValueError('each observed ground interval must contribute to the score')
        y = row['aggregate_weights']
        correction = [ground_totals[i, ground_sats.index(prn)] for prn in row['satellites']]
        corrections.append(float(np.dot(y, correction)))
        row['signed_ground_total_m'] = correction
    multiplier = station['summary']['ionosphere_free']['trained_gain']
    raw = sum(corrections)
    result = dict(cadences=results, range_values=len(dual), score_gap=score['score_gap'],
                  ground_score_by_interval=corrections, ground_score_equivalent=raw, earlier_multiplier=multiplier,
                  adjusted_ground_score_equivalent=multiplier*raw, new_fits=0, protected_reads=0,
                  passed=True, scientific_decision='abstain')
    context.save(ARTIFACT, result)
    return result


def report(root):
    from .studies.closed import ClosedStudy

    prefix, identity = 'data/'+ID, TASK['identity']
    with ExitStack() as stack:
        study = stack.enter_context(closing(ClosedStudy(root, prefix)))
        if (root/(prefix+'-recovery')).is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, root/(prefix+'-recovery'))['selected'][identity]['origin']
            if origin != prefix:
                study = stack.enter_context(closing(ClosedStudy(root, origin, store=study.store)))
        envelope, result = study.envelope(identity), study.artifact(identity, ARTIFACT)
        if envelope['charged'] != TASK['limits'] or envelope['result'] != result or not result['passed']:
            raise ValueError('sealed and complete cadence evidence required')
        _write_equal(root/RESULT, encoded(dict(result, parents={key: sha for key, _, sha in PARENTS},
                                               completion=study.completion)))
    return dict(observable_norm_fraction={key: row['observable_norm_fraction']
                for key, row in result['cadences'].items()}, ground_score_equivalent=result['ground_score_equivalent'],
                adjusted_ground_score_equivalent=result['adjusted_ground_score_equivalent'], score_gap=result['score_gap'])


if __name__ == '__main__':
    from functools import partial

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    result = {'request': partial(qualification, verify=False), 'prepare': prepare, 'report': report,
              'recover': partial(carrier.recover_signature, study_id=ID, task=TASK)}[action](Path.cwd())
    print(json.dumps(result, sort_keys=True))
