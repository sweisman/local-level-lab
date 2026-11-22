# SPDX-License-Identifier: AGPL-3.0-or-later
"""Add position-reference uncertainty to the saved ESA 187 carrier bound."""
import argparse
from contextlib import ExitStack, closing
import gzip
import json
from pathlib import Path

from . import esa_carrier_score_bound as prior
from . import esa_shared_motion_carrier as carrier
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .esa_precise_gps_support import read_orbit_positions
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded


ID = 'esa-carrier-anchor-error-v1'
SCOPE = 'Position-reference uncertainty in the saved ESA 187 linear carrier bound'
PLAN = carrier.FOLDER+'ESA_CARRIER_ANCHOR_ERROR_PLAN.md'
RESULT = carrier.FOLDER+'esa-carrier-anchor-error-result.json'
REQUEST = carrier.FOLDER+'esa-carrier-anchor-error-qualification.json'
XML = carrier.FOLDER+'esa-carrier-anchor-error-tests.xml'
ARTIFACT = 'carrier-anchor-error.json'
PARENT_SHA = '12c0f807d4e710cf05fc3dc521ad9e05f2ba69df8e53f95bcf47dd541b6295bb'
PAIRS = 10
GRID = prior.products.N+1
TASK = dict(identity='carrier-anchor-error', input_key='parent', payload=dict(pairs=PAIRS),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=PAIRS+2,
                        bound_steps=1+66*PAIRS+GRID))


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
                                    'analysis/tests/test_carrier_anchor_error.py',
                                    'analysis/tests/test_carrier_score_bound.py'))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=(
        'test_anchor_adjoint_uses_both_pair_signs_and_removes_common_clock',
        'test_anchor_box_bound_separates_common_and_independent_errors',
        'test_range_gradient_agrees_with_signed_exact_range_change'), minimum_tests=6)
    return sources, environment


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite reference uncertainty study')
    sources, environment = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        saved, result = _parent(root, prior.RESULT, PARENT_SHA, prior.ID, prior.TASK, prior.ARTIFACT, stack)
        if saved.envelope(prior.TASK['identity'])['charged'] != prior.TASK['limits'] or result['pairs'] != GRID-1:
            raise ValueError('complete accounting for the original carrier bound is required')
        values = {key: saved.input(key, raw=True) for key in
                  ('rinex', 'navigation', 'orbit', 'anchor', 'path', 'continuity', 'metric', 'original', 'score')}
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, parent=prior.RESULT, qualification=REQUEST, qualification_tests=XML)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=carrier.WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    from itertools import accumulate

    from .carrier_anchor_error import anchor_residuals, anchor_uncertainty
    from .carrier_score_bound import score_interpolation
    from .esa_carrier_phase_support import phase_epochs
    from .esa_rinex_code import read_navigation
    from .esa_rinex_code_comparison import coordinates

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen reference uncertainty task is required')
    context.charge(bound_calls=1, bound_steps=1)

    def read(key):
        return context.input_path(key).read_bytes()

    phase = list(phase_epochs(gzip.decompress(read('rinex'))))
    navigation, _ = read_navigation(gzip.decompress(read('navigation')).decode('ascii'))
    orbits = read_orbit_positions(gzip.decompress(read('orbit')).decode('ascii'))
    anchor, path, score, metric, continuity, original, parent = [json.loads(read(key)) for key in
        ('anchor', 'path', 'score', 'metric', 'continuity', 'original', 'parent')]
    times = [phase[carrier.START]['seconds'], *(row['seconds'] for row in original['rows'])]
    positions = [coordinates([anchor])[0], *(row['position'] for row in path)]
    if (len(times) != GRID or [row['seconds'] for row in path] != times[1:]
            or parent['endpoint_gps_s'] != [times[0], times[-1]]):
        raise ValueError('the original carrier grid and path are required')
    blocks = [row['common_satellites'] for row in original['rows']]
    boundaries = [0, *accumulate(map(len, blocks))]
    saved = parent['bound']
    dual = saved['dual_weights']
    if len(dual) != saved['range_values'] or boundaries[-1] != len(dual):
        raise ValueError('the original signed weights and satellite support are required')
    anchors = [times[0], *parent['ground_anchors_gps_s'], times[-1]]
    indices = [times.index(t) for t in anchors]
    needed = sorted({j for i in indices for j in (i-1, i) if 0 <= j < GRID-1})
    if len(needed) != PAIRS:
        raise ValueError('the ten original anchor-adjacent pairs are required')
    adjacent = {}
    for pair in needed:
        context.charge(bound_calls=1, bound_steps=66)
        index = carrier.START+pair
        first, second = phase[index:index+2]
        if ([first['seconds'], second['seconds']] != times[pair:pair+2]
                or first['week'] != second['week'] or second['week'] != anchor['gps_week']):
            raise ValueError('the exact matched pair times and GPS week are required')
        expected = continuity['result']['per_pair'][index]['accepted_prns']
        endpoints = prior.pair_range_gradients(first, second, blocks[pair], expected,
                                               positions[pair:pair+2], navigation, orbits, metric)
        adjacent[pair] = (*endpoints, dual[boundaries[pair]:boundaries[pair+1]])

    context.charge(bound_calls=1, bound_steps=GRID)
    scoring, taps = prior.score_grid(score, anchor)
    weights, _ = score_interpolation(times, scoring, taps)
    residual = anchor_residuals(weights, indices, adjacent)
    gain = anchor_uncertainty(residual, free_count=GRID-len(anchors), free_weight_norm=saved['residual_weight_norm'])
    cap = parent['test_acceleration_rms_mps2']
    gap = parent['score_gap']-saved['acceleration_rms_to_score']*cap
    range_examples = [.0, .0005, .001, .0015]
    tolerances = [{
        'range_rms_m': limit,
        'maximum_anchor_axis_error_m': max(0., gap-saved['range_rms_to_score']*limit)/gain['all_anchor_axis_to_score'],
        'maximum_common_axis_error_m': max(0., gap-saved['range_rms_to_score']*limit)/gain['common_axis_to_score'],
    } for limit in range_examples]
    result = dict(anchor_uncertainty=gain, anchors_gps_s=anchors, signed_anchor_weights=residual.tolist(),
                  tolerances=tolerances, score_gap=parent['score_gap'], acceleration_example_rms_mps2=cap,
                  range_rms_to_score=saved['range_rms_to_score'], acceleration_rms_to_score=saved['acceleration_rms_to_score'],
                  new_fits=0, protected_reads=0, passed=True, scientific_decision='abstain')
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
            raise ValueError('sealed and complete anchor uncertainty result required')
        _write_equal(root/RESULT, encoded(dict(result, parent_sha256=PARENT_SHA, completion=study.completion)))
    return {key: result[key] for key in ('anchor_uncertainty', 'tolerances')}


if __name__ == '__main__':
    from functools import partial

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    result = {'request': partial(qualification, verify=False), 'prepare': prepare, 'report': report,
              'recover': partial(carrier.recover_signature, study_id=ID, task=TASK)}[action](Path.cwd())
    print(json.dumps(result, sort_keys=True))
