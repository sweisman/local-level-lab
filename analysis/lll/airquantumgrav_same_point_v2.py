# SPDX-License-Identifier: AGPL-3.0-or-later
"""Six frozen ESA saved-point checks of the revised selective tangent."""
import json
import math
from pathlib import Path

from lll.airquantumgrav_same_point_study import (
    FAILED, PREFIX_PACKETS, TRAINING_EPOCHS, VISITS_PER_CALL, validate_points)


IDENTITY = 'esa-same-point-tangent-v2-20261111-r1'
PARENT = 'data/esa-same-point-tangent-20261111-v2'
PARENT_MANIFEST = '4be1d42c843769c4d627c0b7c0f616e25a68c99337478edfc3bc89b126a66be8'
PARENT_SUMMARY = 'd7bc82ef97e43475ff3e53e99f02bc3138623554a294e6b777e49b952561b8ec'
SCOPE = ('six saved ESA development tangent points; revised attitude precision; '
         'no fits, original files, protected groups or scientific decision')


def recipe():
    return dict(version='esa-same-point-attitude-wide-v1', workers=3, threads=1,
                maximum_wall_s=3600., native_calls=6,
                packet_visits=6*VISITS_PER_CALL,
                optimizer_starts=0, original_reads=0, protected_reads=0,
                maximum_difference_fraction=.1,
                attitude_difference_limit_m=1e-8)


def tasks():
    return [dict(identity=identity, input_key='interval', native_kind='tangent',
                 payload=dict(model='flat_still', profile=profile,
                              policy_id=policy, start=start),
                 limits=dict(native_calls=2, packet_visits=2*VISITS_PER_CALL,
                             bound_calls=0, bound_steps=0))
            for identity, profile, policy, start in FAILED]


def gate(new, old, *, fraction=.1, attitude_limit=1e-8):
    """Only a large derivative improvement advances this prototype."""
    if (not new['values_bitwise_identical'] or
            not new['boundary_counts_identical'] or
            new['maximum_position_difference_m'] != 0):
        return False
    old_max = old['largest_column']['maximum_difference_m_per_normalized_unit']
    new_max = new['largest_column']['maximum_difference_m_per_normalized_unit']
    columns = {row['name']: row['maximum_difference_m_per_normalized_unit']
               for row in new['columns']}
    if (not math.isfinite(old_max) or old_max <= 0 or
            not math.isfinite(new_max) or new_max < 0 or
            not {'attitude_x', 'attitude_y'} <= columns.keys()):
        raise ValueError('complete finite saved tangent columns required')
    return (new_max <= fraction*old_max and
            all(columns[name] < attitude_limit
                for name in ('attitude_x', 'attitude_y')))


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/airquantumgrav_same_point_v2.py',
        'analysis/lll/ilvis0_hybrid_tangent_v2.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/test_airquantumgrav_same_point_v2.py',
        'analysis/tests/test_ilvis0_hybrid_tangent_v2.py',
        'docs/mixed-tangent-hybrid/V2_SAVED_POINT_PLAN.md'])


def prepare(root):
    """Copy only hash-checked parent inputs and six saved wide tangents."""
    from .studies.artifacts import atomic, encoded
    from .studies.closed import ClosedStudy
    from .studies.runtime import Definition

    root = Path(root).resolve()
    base = root/'data'/(IDENTITY+'-inputs')
    if base.exists() or (root/'data'/IDENTITY).exists():
        raise ValueError('fresh finite allowance required')
    parent = ClosedStudy(root, PARENT)
    try:
        if (parent.completion['state'] != 'complete' or
                parent.completion['manifest_sha256'] != PARENT_MANIFEST or
                parent.completion['summary_sha256'] != PARENT_SUMMARY or
                list(parent.tasks) != [task['identity'] for task in tasks()] or
                len(parent.rows) != 3 or
                not all(row['passed'] for row in parent.rows.values())):
            raise ValueError('exact sealed three-pair saved-point parent required')
        material = {key: parent.input(key, raw=True) for key in
                    ('interval', 'training', 'query-layout', 'layout',
                     'recipe', 'points')}
        material['v2-recipe'] = encoded(recipe())
        material['parent-binding'] = encoded(dict(
            manifest_sha256=PARENT_MANIFEST, summary_sha256=PARENT_SUMMARY,
            identities=[task['identity'] for task in tasks()]))
        for identity in parent.tasks:
            for source in ('wide', 'hybrid'):
                material[identity+'-'+source+'-reference'] = parent.artifact(
                    identity, source+'-tangents.npz', raw=True)
                material[identity+'-'+source+'-old-comparison'] = encoded(
                    parent.artifact(identity, source+'-comparison.json'))
    finally:
        parent.close()
    base.mkdir(parents=True)
    inputs = {}
    for index, (key, raw) in enumerate(material.items()):
        path = base/f'input-{index:03d}'
        atomic(path, raw)
        inputs[key] = str(path.relative_to(root))
    definition = dict(id=IDENTITY, scope=SCOPE,
                      adapter='analysis/lll/airquantumgrav_same_point_v2.py',
                      sources=sources(root), inputs=inputs, tasks=tasks(),
                      workers=3, threads=1, maximum_wall_s=3600.)
    atomic(base/'definition.json', encoded(definition))
    return Definition.from_dict(definition, root).prepare(root)


def evaluate(task, context):
    import gzip
    import io
    import numpy as np
    from lll.airquantumgrav_error_policy import build as receiver_weight
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_hybrid_tangent_v2 import load as load_revised
    from lll.ilvis0_tangent_columns import compare
    from lll.ilvis0_training_forecast import training_problem
    from lll.ilvis0_wide_tangent import evaluate as tangent_evaluate

    read = lambda name: json.loads(context.input_path(name).read_bytes())
    r = read('v2-recipe')
    binding = read('parent-binding')
    if (context.manifest['scope'] != SCOPE or r != recipe() or
            binding != dict(manifest_sha256=PARENT_MANIFEST,
                            summary_sha256=PARENT_SUMMARY,
                            identities=[row['identity'] for row in tasks()]) or
            {key: value for key, value in task.items()
             if key not in ('index', 'shard')} !=
            {row['identity']: row for row in tasks()}.get(task['identity'])):
        raise ValueError('unchanged six-call saved-point scope required')
    layout, query, parent = (read(name) for name in
                             ('layout', 'query-layout', 'recipe'))
    points = read('points')[task['identity']]
    with np.load(context.input_path('interval'), allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in ('theta', 'dv', 'dt')}
    training = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    times = np.asarray(query['times_s'][:TRAINING_EPOCHS], float)
    if (len(training) != TRAINING_EPOCHS or len(query['times_s']) != 1200 or
            layout['training_prefix_packets'] != PREFIX_PACKETS or
            len(arrays['dt']) != layout['native_packets'] or
            parent['training_epochs'] != TRAINING_EPOCHS or
            parent['maximum_interval_s'] != .005):
        raise ValueError('unchanged earlier-only recording and split required')
    weight = receiver_weight(training, policy_id=task['payload']['policy_id'])
    if not np.array_equal(weight.times-query['time_origin_gps_sow_s'], times):
        raise ValueError('training receiver time binding differs')
    gps = np.asarray([[math.radians(row['latitude_deg']),
                       math.radians(row['longitude_deg']), row['height_m']]
                      for row in training], float)
    prefix = {key: value[:PREFIX_PACKETS] for key, value in arrays.items()}
    model = task['payload']['model']
    base = training_problem(
        times, gps, theta=prefix['theta'], dv=prefix['dv'], dt=prefix['dt'],
        covariance=weight.dense(maximum_epochs=1024), model=model,
        limits=parent['limits'], profile=task['payload']['profile'],
        clock='header_elapsed', maximum_interval_s=.005,
        kernel=None, tangent_kernel=None)
    active = list(base.bounds.active)
    validate_points(task, points, active)
    directory = context.root/'shards'/f'{context.shard:03d}'/'kernels'
    kernel, metadata = load_revised(
        directory, gravity_anchor_height_m=float(training[0]['height_m']),
        expected_source_sha256=context.manifest['sources'][
            'analysis/lll/ilvis0_tangent.cpp'],
        expected_loader_sha256=context.manifest['sources'][
            'analysis/lll/ilvis0_wide_tangent.py'])
    context.save('compilation.json', metadata)
    reports = {}
    for source in ('wide', 'hybrid'):
        old = read(task['identity']+'-'+source+'-old-comparison')
        with np.load(context.input_path(task['identity']+'-'+source+'-reference'),
                     allow_pickle=False) as reference:
            wide_coordinates = reference['wide_coordinates'].copy()
            wide_jacobian = reference['wide_jacobian'].copy()
            saved_times = reference['times_s'].copy()
        if not np.array_equal(times, saved_times):
            raise ValueError('saved wide tangent times differ')
        point = np.asarray(points[source]['normalized_parameters'], float)
        _check_continue(context.root, context.manifest)
        context.charge(native_calls=1, packet_visits=VISITS_PER_CALL)
        coordinates, _, jacobian, boundaries = tangent_evaluate(
            base, point, model, kernel=kernel)
        result = compare(times, wide_coordinates, coordinates,
                         wide_jacobian, jacobian, active,
                         boundaries=(old['boundaries'][0], boundaries))
        result['passes_improvement_gate'] = gate(
            result, old, fraction=r['maximum_difference_fraction'],
            attitude_limit=r['attitude_difference_limit_m'])
        result['point_source'] = source
        reports[source] = result
        buffer = io.BytesIO()
        np.savez_compressed(buffer, times_s=times, coordinates=coordinates,
                            jacobian=jacobian)
        context.save_bytes(source+'-revised-tangent.npz', buffer.getvalue())
        context.save(source+'-comparison.json', result)
    return dict(passed=all(row['passes_improvement_gate'] for row in reports.values()),
                comparisons=reports, native_calls=2, optimizer_starts=0,
                original_reads=0, protected_reads=0,
                observed_substitution_qualified=False,
                scientific_decision='abstain')
