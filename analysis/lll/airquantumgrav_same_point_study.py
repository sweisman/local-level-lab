# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite saved-point derivative comparison on the ESA development interval."""
import math
from pathlib import Path


SCOPE = ('saved ESA recording-187 tangent columns at failed fitted points; '
         'no optimizer, original aircraft file or protected confirmation reads')
FAILED = (
    ('flat_still-0-reported-short-v1-1', False, 'reported-short-v1', 1),
    ('flat_still-0-reported-persistent-v1-0', False, 'reported-persistent-v1', 0),
    ('flat_still-1-reported-short-v1-0', True, 'reported-short-v1', 0),
)
TRAINING_EPOCHS = 800
PREFIX_PACKETS = 239867
VISITS_PER_CALL = TRAINING_EPOCHS * PREFIX_PACKETS


def recipe():
    return dict(version='esa-same-point-tangent-v1', training_epochs=TRAINING_EPOCHS,
                prefix_packets=PREFIX_PACKETS, calls_per_task=4,
                optimizer_starts=0, original_reads=0, protected_reads=0,
                workers=3, threads=1, maximum_wall_s=14400.,
                diagnostic_only=True, method_substitution_requalified=False)


def tasks():
    return [dict(identity=identity, input_key='interval', native_kind='tangent',
                 payload=dict(model='flat_still', profile=profile,
                              policy_id=policy, start=start),
                 limits=dict(native_calls=4, packet_visits=4*VISITS_PER_CALL,
                             bound_calls=0, bound_steps=0))
            for identity, profile, policy, start in FAILED]


def validate_points(task, points, active):
    if (not isinstance(points, dict) or set(points) != {'wide', 'hybrid'} or
            not isinstance(active, list) or not active):
        raise ValueError('both saved points and active columns required')
    for variant in ('wide', 'hybrid'):
        row = points[variant]
        if (not isinstance(row, dict) or row.get('active_parameters') != active or
                not isinstance(row.get('normalized_parameters'), list) or
                len(row['normalized_parameters']) != len(active) or
                any(type(value) not in (float, int) or not math.isfinite(value) or
                    abs(value) > 1.000001 for value in row['normalized_parameters'])):
            raise ValueError('unchanged complete saved point and active columns required')


def qualification_sources(root):
    from .studies.dependencies import source_closure
    return source_closure(root, [
        'analysis/lll/airquantumgrav_same_point_study.py',
        'analysis/lll/ilvis0_tangent_columns.py',
        'analysis/lll/ilvis0_wide_tangent.py',
        'analysis/lll/ilvis0_hybrid_tangent.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_native.c',
        'analysis/tests/test_airquantumgrav_same_point_study.py',
        'analysis/tests/test_ilvis0_tangent_columns.py',
        'analysis/tests/test_ilvis0_hybrid_tangent.py',
        'analysis/lll/studies/task_resume.py',
        'analysis/lll/studies/task_continuation.py',
        'analysis/tests/test_task_resume.py',
        'analysis/tests/test_task_continuation.py',
        'docs/esa-observed-hybrid/FAILURE_FOLLOWUP.md',
    ])


def required_tests():
    return [
        'test_same_point_tasks_are_exact_failed_pairs_with_finite_limits',
        'test_same_point_input_rejects_changed_column_order',
        'test_same_point_preparation_requires_bound_qualification',
        'test_same_point_adapter_loads_directly_from_frozen_file',
        'test_reports_column_and_time_of_same_point_difference',
        'test_rejects_missing_or_reordered_columns',
        'test_hybrid_tangent_keeps_values_and_derivatives_across_six_generated_cases',
        'test_reboot_resume_skips_sealed_and_preserves_charges',
        'test_source_input_environment_mutation_blocks',
        'test_recovery_caps_and_completed_failure',
        'test_preserves_both_completed_outcomes_and_all_charges',
    ]


def prepare(root, *, qualification,
            identity='esa-same-point-tangent-20261111'):
    if qualification is None:
        raise ValueError('source-bound software qualification required')
    import json
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_observed_hybrid_combined_audit import (
        CombinedStudy, verify_publication)
    from .compute_budget import environment as numerical_environment
    from .studies.artifacts import atomic, digest, encoded, safe_path
    from .studies.combined_task_evidence import inspect as inspect_lineage
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    r = recipe()
    env = environment()
    if env['numerical_environment'] != numerical_environment(
            workers=r['workers'], threads=r['threads']):
        raise ValueError('declared three-thread numerical environment required')
    base = safe_path(root, 'data/ilvis0-source-point-development/' + identity + '-inputs')
    if base.exists() or safe_path(root, 'data/' + identity).exists():
        raise ValueError('fresh finite diagnostic identity required')
    request, tests = checked(root, qualification,
                             sources=qualification_sources(root),
                             environment=env, required_tests=required_tests(),
                             minimum_tests=5)
    receipt = verify_publication(root)
    report_raw = (root/'docs/esa-observed-hybrid/combined/verified-report.json').read_bytes()
    report = json.loads(report_raw)
    if (report.get('verified') is not True or report.get('total') != 24 or
            report.get('passed') != 21 or report.get('qualified') is not False or
            {row['identity'] for row in report['rows'] if row['passed'] is False}
            != {task['identity'] for task in tasks()}):
        raise ValueError('exact verified failed parent identities required')
    ledger = inspect_lineage(root, root/'data/esa-observed-hybrid-continuation-20261111')
    view = CombinedStudy(root, ledger)
    try:
        copied = {key: view.input(key, raw=True)
                  for key in ('interval', 'training', 'query-layout', 'layout', 'recipe')}
        if (any(digest(copied[key]) != view.manifest['inputs'][key]['sha256']
                for key in copied) or
                json.loads(copied['layout'])['training_prefix_packets'] != PREFIX_PACKETS or
                len(json.loads(copied['query-layout'])['times_s']) != 1200):
            raise ValueError('unchanged prepared ESA measurements and split required')
        points = {}
        for task in tasks():
            identity_key = task['identity']
            points[identity_key] = {}
            for variant in ('wide', 'hybrid'):
                fit = view.artifact(identity_key, variant+'-fit.json')
                path = 'artifacts/'+identity_key+'/'+variant+'-fit.json'
                points[identity_key][variant] = dict(
                    active_parameters=fit['active_parameters'],
                    normalized_parameters=fit['normalized_parameters'],
                    fit_artifact_sha256=view.envelope(identity_key)['artifacts'][path])
            active = points[identity_key]['wide']['active_parameters']
            validate_points(task, points[identity_key], active)
            if len(active) != 26+int(task['payload']['profile']):
                raise ValueError('all original nuisance columns required')
    finally:
        view.close()
    proof = dict(combined_report_sha256=digest(report_raw),
                 combined_receipt_sha256=receipt['receipt_sha256'],
                 combined_lineage_sha256=ledger['lineage_sha256'],
                 selected_parent_input_sha256={key:digest(value) for key,value in copied.items()},
                 failed_identities=[task['identity'] for task in tasks()],
                 original_reads=0, protected_reads=0)
    materials = dict(copied, points=encoded(points), proof=encoded(proof),
                     diagnostic_recipe=encoded(r), qualification_request=request,
                     qualification_report=tests, qualification_environment=encoded(env))
    base.mkdir(parents=True)
    inputs = {}
    for index, (key, raw) in enumerate(materials.items()):
        path = base/f'input-{index:03d}'
        atomic(path, raw)
        inputs[key] = str(path.relative_to(root))
    definition = dict(id=identity, scope=SCOPE,
                      adapter='analysis/lll/airquantumgrav_same_point_study.py',
                      sources=qualification_sources(root), inputs=inputs,
                      tasks=tasks(), workers=r['workers'], threads=r['threads'],
                      maximum_wall_s=r['maximum_wall_s'])
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+identity, total=3,
                limits=manifest['limits'], allocation=manifest['allocation'])


def evaluate(task, context):
    """Four charged evaluations at two saved points; no optimization or scoring."""
    import gzip
    import io
    import json
    import numpy as np
    from lll.airquantumgrav_error_policy import build
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_hybrid_tangent import load as load_hybrid
    from lll.ilvis0_tangent_columns import compare
    from lll.ilvis0_training_forecast import training_problem
    from lll.ilvis0_wide_tangent import evaluate as tangent_evaluate
    from lll.ilvis0_wide_tangent import load as load_wide

    read = lambda name: json.loads(context.input_path(name).read_bytes())
    r = read('diagnostic_recipe')
    layout, query, parent = (read(name) for name in
                             ('layout', 'query-layout', 'recipe'))
    points, proof = read('points'), read('proof')
    declared = {key:value for key,value in task.items()
                if key not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or r != recipe() or
            declared != {row['identity']:row for row in tasks()}.get(task['identity']) or
            set(points) != {row['identity'] for row in tasks()} or
            proof['failed_identities'] != [row['identity'] for row in tasks()] or
            proof['original_reads'] != 0 or proof['protected_reads'] != 0 or
            layout['training_prefix_packets'] != PREFIX_PACKETS or
            parent['training_epochs'] != TRAINING_EPOCHS or
            parent['maximum_interval_s'] != .005):
        raise ValueError('exact frozen saved-point diagnostic required')
    with np.load(context.input_path('interval'), allow_pickle=False) as archive:
        arrays = {key:archive[key] for key in ('theta', 'dv', 'dt')}
    training = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    times = np.asarray(query['times_s'][:TRAINING_EPOCHS], float)
    if (len(training) != TRAINING_EPOCHS or len(query['times_s']) != 1200 or
            len(arrays['dt']) != layout['native_packets'] or
            int(np.searchsorted(np.cumsum(arrays['dt']),
                                times[-1]+parent['limits']['time_offset'],
                                side='left'))+1 != PREFIX_PACKETS):
        raise ValueError('unchanged earlier-only native and receiver split required')
    weight = build(training, policy_id=task['payload']['policy_id'])
    if not np.array_equal(weight.times-query['time_origin_gps_sow_s'], times):
        raise ValueError('training receiver time binding differs')
    gps = np.asarray([[math.radians(row['latitude_deg']),
                       math.radians(row['longitude_deg']), row['height_m']]
                      for row in training], float)
    model = task['payload']['model']
    prefix = {key:value[:PREFIX_PACKETS]
              for key,value in arrays.items()}
    base = training_problem(times, gps, theta=prefix['theta'], dv=prefix['dv'],
                            dt=prefix['dt'], covariance=weight.dense(maximum_epochs=1024),
                            model=model, limits=parent['limits'],
                            profile=task['payload']['profile'], clock='header_elapsed',
                            maximum_interval_s=parent['maximum_interval_s'],
                            kernel=None, tangent_kernel=None)
    active = list(base.bounds.active)
    validate_points(task, points[task['identity']], active)
    anchor = float(training[0]['height_m'])
    directory = context.root/'shards'/f'{context.shard:03d}'/'kernels'
    kwargs = dict(gravity_anchor_height_m=anchor,
                  expected_source_sha256=context.manifest['sources'][
                      'analysis/lll/ilvis0_tangent.cpp'])
    wide, wide_meta = load_wide(directory, **kwargs)
    hybrid, hybrid_meta = load_hybrid(
        directory, **kwargs,
        expected_loader_sha256=context.manifest['sources'][
            'analysis/lll/ilvis0_wide_tangent.py'])
    context.save('compilation.json', dict(wide=wide_meta, hybrid=hybrid_meta))
    comparisons = {}
    for source in ('wide', 'hybrid'):
        point = np.asarray(points[task['identity']][source]['normalized_parameters'],
                           dtype=float)
        outputs = {}
        for variant, kernel in (('wide', wide), ('hybrid', hybrid)):
            _check_continue(context.root, context.manifest)
            context.charge(native_calls=1, packet_visits=VISITS_PER_CALL)
            outputs[variant] = tangent_evaluate(base, point, model, kernel=kernel)
        first, second = outputs['wide'], outputs['hybrid']
        report = compare(times, first[0], second[0], first[2], second[2],
                         active, boundaries=(first[3], second[3]))
        report.update(point_source=source,
                      boundaries=[first[3], second[3]],
                      point_fit_artifact_sha256=points[task['identity']][source][
                          'fit_artifact_sha256'])
        buffer = io.BytesIO()
        np.savez_compressed(buffer, times_s=times, wide_coordinates=first[0],
                            hybrid_coordinates=second[0],
                            wide_jacobian=first[2], hybrid_jacobian=second[2])
        context.save_bytes(source+'-tangents.npz', buffer.getvalue())
        context.save(source+'-comparison.json', report)
        comparisons[source] = report
    return dict(passed=True, identity=task['identity'], comparisons=comparisons,
                native_calls=4, optimizer_starts=0, original_reads=0,
                protected_reads=0, method_substitution_requalified=False,
                scientific_decision='abstain')


def inspect(root, prefix='data/esa-same-point-tangent-20261111'):
    """Verify all frozen calls and independently replay saved column summaries."""
    import io
    import numpy as np
    from .airquantumgrav_observation_report import native_accounting
    from .ilvis0_tangent_columns import compare
    from .studies.artifacts import encoded
    from .studies.closed import ClosedStudy
    from .studies.source_binding import verify

    root = Path(root).resolve()
    study = ClosedStudy(root, prefix)
    try:
        if (study.manifest['scope'] != SCOPE or
                study.input('diagnostic_recipe') != recipe() or
                {key:{k:v for k,v in task.items() if k not in ('index','shard')}
                 for key,task in study.tasks.items()}
                != {task['identity']:task for task in tasks()}):
            raise ValueError('unchanged three-task source-bound diagnostic required')
        verify(root, declared=study.input('qualification_request')['sources'],
               manifest=study.manifest['sources'])
        points = study.input('points')
        rows = []
        charged = {key:0 for key in study.summary['charged']}
        for shard in range(study.manifest['allocation']['workers']):
            assigned = {identity for identity,task in study.tasks.items()
                        if task['shard'] == shard}
            counts = native_accounting(
                study.read(f'shards/{shard:03d}/charges/journal.sqlite', raw=True),
                study.completion['manifest_sha256'], assigned,
                per_call_visits=VISITS_PER_CALL)
            for identity in sorted(assigned):
                if identity not in study.rows:
                    rows.append(dict(identity=identity, complete=False))
                    continue
                envelope = study.envelope(identity)
                result = envelope['result']
                for key in charged:
                    charged[key] += envelope['charged'][key]
                if (result.get('passed') is not True or result.get('native_calls') != 4 or
                        result.get('optimizer_starts') != 0 or
                        result.get('original_reads') != 0 or
                        result.get('protected_reads') != 0 or
                        result.get('method_substitution_requalified') is not False or
                        counts[identity]['tangent'] != 4 or
                        counts[identity]['packet_visits'] != 4*VISITS_PER_CALL or
                        envelope['charged']['native_calls'] != 4 or
                        envelope['charged']['packet_visits'] != 4*VISITS_PER_CALL):
                    raise ValueError('saved native accounting or nonfitting scope differs')
                for source in ('wide', 'hybrid'):
                    saved = study.artifact(identity, source+'-comparison.json')
                    with np.load(io.BytesIO(study.artifact(
                            identity, source+'-tangents.npz', raw=True)),
                            allow_pickle=False) as archive:
                        arrays = {key:archive[key] for key in archive.files}
                    replay = compare(arrays['times_s'],
                                     arrays['wide_coordinates'],
                                     arrays['hybrid_coordinates'],
                                     arrays['wide_jacobian'],
                                     arrays['hybrid_jacobian'],
                                     points[identity][source]['active_parameters'],
                                     boundaries=tuple(saved['boundaries']))
                    replay.update(point_source=source,
                                  boundaries=saved['boundaries'],
                                  point_fit_artifact_sha256=points[identity][source][
                                      'fit_artifact_sha256'])
                    if encoded(replay) != encoded(saved) or encoded(saved) != encoded(
                            result['comparisons'][source]):
                        raise ValueError('saved same-point columns differ on replay')
                rows.append(dict(identity=identity, complete=True,
                                 comparisons=result['comparisons']))
        if charged != study.summary['charged']:
            raise ValueError('whole-study charged totals differ')
        return dict(verified=True, total=3,
                    complete=sum(row['complete'] for row in rows),
                    rows=rows, charged=charged,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    optimizer_starts=0, original_reads=0, protected_reads=0,
                    method_substitution_requalified=False,
                    scientific_decision='abstain')
    finally:
        study.close()
