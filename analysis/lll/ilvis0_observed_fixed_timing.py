# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite fixed-endpoint timing probes of eight sealed recorded-data fits."""

import json
from pathlib import Path

from . import ilvis0_observed_method_pilot_v2 as parent

ID = 'ilvis0-observed-fixed-timing-v1-20261118'
SCOPE = 'eight sealed fixed endpoints; training-only timing probes, no refits'
PLAN = 'docs/prediction-group-transfer/OBSERVED_FIXED_ENDPOINT_PLAN.md'
REQUEST = 'docs/prediction-group-transfer/observed-fixed-timing-qualified-request.json'
REPORT = 'docs/prediction-group-transfer/observed-fixed-timing-qualified-tests.xml'
RECOVERY = 'docs/prediction-group-transfer/observed-fixed-timing-recovery-request.json'
NORTH = '7df21c836bec5751f83c0cce'
SOUTH = '50f24131843071ae9312c082'
PAIRS = {NORTH: (('trust_v2', 1), ('scipy_trf', 1)),
         SOUTH: (('scipy_trf', 0), ('scipy_trf', 1))}
EXPECTED_IDENTITIES = {
    f'{segment}-{origin}-{solver}-{start}'
    for segment, pair in PAIRS.items() for origin in ('inner', 'outer')
    for solver, start in pair}


def tasks(layouts):
    if (len(layouts) != 2 or tuple(row['segment_id'] for row in layouts)
            != (NORTH, SOUTH)):
        raise ValueError('exact two sealed recording layouts required')
    result = []
    for row in layouts:
        count, outer, packets = (row[key] for key in
                                 ('receiver_epochs', 'training_epochs',
                                  'native_packets'))
        if (type(count) is not int or type(outer) is not int or
                type(packets) is not int or count < 9 or
                outer != 2*count//3 or packets < 1):
            raise ValueError('exact finite receiver layout required')
        for origin, cut in (('inner', count//3), ('outer', outer)):
            for solver, start in PAIRS[row['segment_id']]:
                identity = f"{row['segment_id']}-{origin}-{solver}-{start}"
                result.append(dict(identity=identity,
                    input_key=row['segment_id']+'-common',
                    payload=dict(segment_id=row['segment_id'], origin=origin,
                                 solver=solver, start=start,
                                 model='sphere_rotating', profile=False,
                                 clock='header_elapsed'),
                    limits=dict(native_calls=10,
                                packet_visits=10*packets*cut,
                                bound_calls=0, bound_steps=0)))
    return result


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/ilvis0_observed_fixed_timing.py',
        'analysis/lll/ilvis0_observed_training_builder.py',
        'analysis/lll/ilvis0_observed_method_diagnosis.py',
        'analysis/lll/ilvis0_timing_probes.py',
        'analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/test_ilvis0_observed_fixed_timing.py', PLAN])


def required_tests():
    return ('test_fixed_timing_grid_uses_saved_maximum_pairs_and_matched_controls',
            'test_changed_task_is_rejected_before_training_input_access',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    root = Path(root).resolve()
    return request(root, sources=sources(root), environment=runtime_environment(),
                   output=REQUEST, report=REPORT)


def prepare(root):
    import shutil
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_observed_method_diagnosis import build as diagnosis
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources, REQUIRED_TESTS

    root = Path(root).resolve()
    base = safe_path(root, 'data/'+ID+'-inputs')
    if (base.exists() or safe_path(root, 'data/'+ID).exists() or
            shutil.disk_usage(root).free < 5*1024**3):
        raise ValueError('fresh fixed-endpoint study and five GiB free required')
    environment = runtime_environment()
    request, report = checked(root, REQUEST, sources=sources(root),
        environment=environment, required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery, recovery_report = checked(root, RECOVERY,
        sources=qualification_sources(root), environment=environment,
        required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    audited = diagnosis(root)
    if (audited['study'] != 'data/'+parent.ID or
            audited['numerical_stops'] != 7 or
            {tuple(row['largest_path_pair']) for row in
             audited['path_disagreements']} !=
            {tuple(f'{segment}-inner-{solver}-{start}'
                   for solver, start in PAIRS[segment])
             for segment in (NORTH, SOUTH)}):
        raise ValueError('sealed maximum-disagreement endpoints differ')
    source = ClosedStudy(root, 'data/'+parent.ID)
    try:
        if (source.completion['state'] != 'complete' or
                source.completion['manifest_sha256'] !=
                audited['manifest_sha256'] or
                len(source.tasks) != 24 or len(source.rows) != 24):
            raise ValueError('exact completed observed pilot required')
        layouts = [next(row for row in source.input('layouts')
                        if row['segment_id'] == segment)
                   for segment in (NORTH, SOUTH)]
        frozen_tasks = tasks(layouts)
        material = dict(recipe=source.input('recipe', raw=True),
            layouts=encoded(layouts), diagnosis=encoded(audited),
            source_completion=encoded(source.completion),
            environment=encoded(environment), qualification_request=request,
            qualification_report=report, recovery_request=recovery,
            recovery_report=recovery_report)
        for segment in (NORTH, SOUTH):
            material[segment+'-common'] = source.input(segment+'-common',raw=True)
            for origin in ('inner', 'outer'):
                key = segment+'-'+origin+'-training'
                material[key] = source.input(key,raw=True)
        for task in frozen_tasks:
            identity = task['identity']
            fit = source.artifact(identity, 'fit.json')
            if (source.tasks[identity]['payload'] != task['payload'] or
                    source.envelope(identity)['result']['converged'] !=
                    fit['converged']):
                raise ValueError('saved endpoint and sealed task disagree')
            material['fit-'+identity] = encoded(fit)
    finally:
        source.close()
    base.mkdir(parents=True)
    inputs = {}
    for index, (key, raw) in enumerate(material.items()):
        path = base/f'input-{index:03d}'
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE,
        adapter='analysis/lll/ilvis0_observed_fixed_timing.py',
        sources=sources(root), inputs=inputs, tasks=frozen_tasks,
        workers=4, threads=1, maximum_wall_s=3600.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, tasks=len(frozen_tasks),
                allocation=manifest['allocation'], limits=manifest['limits'])


def evaluate(task, context):
    declared = {key:value for key,value in task.items()
                if key not in ('index','shard')}
    spec = task.get('payload', {})
    segment, origin, solver, start = (spec.get(key) for key in
                                      ('segment_id','origin','solver','start'))
    if (context.manifest['scope'] != SCOPE or
            segment not in PAIRS or origin not in ('inner','outer') or
            (solver,start) not in PAIRS[segment] or
            task.get('identity') != f'{segment}-{origin}-{solver}-{start}' or
            task.get('input_key') != segment+'-common' or
            spec != dict(segment_id=segment,origin=origin,solver=solver,
                         start=start,model='sphere_rotating',profile=False,
                         clock='header_elapsed')):
        raise ValueError('exact selected timing endpoint required')
    layouts = json.loads(context.input_path('layouts').read_bytes())
    if declared not in tasks(layouts):
        raise ValueError('exact selected timing endpoint required')
    import numpy as np
    from .ilvis0_observed_training_builder import build
    from .ilvis0_timing_probes import inspect

    fit = json.loads(context.input_path('fit-'+task['identity']).read_bytes())
    problem, model, packets, cut = build(context, spec)
    point = np.asarray(fit['normalized_parameters'], float)
    if (point.shape != (len(problem.bounds.active),) or
            not np.all(np.isfinite(point)) or np.any(abs(point) > 1)):
        raise ValueError('complete feasible saved endpoint required')
    def charged(fn, *args):
        context.charge(native_calls=1, packet_visits=packets*cut)
        return fn(*args)
    result = inspect(problem, point, model, charged)
    if result['native_evaluations'] != 10:
        raise ValueError('exact ten-call fixed timing probe required')
    context.save('timing-probe.json', result)
    return dict(passed=True, technical_completion_only=True,
        source_fit_converged=fit['converged'],
        baseline_repeat_maximum_neu_m=result['center_repeat_maximum_neu_m'],
        native_evaluations=result['native_evaluations'],
        later_receiver_positions_used=False, observed_fit_starts=0,
        scientific_decision='abstain')


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'run'))
    args = parser.parse_args(argv)
    root = Path('.').resolve()
    if args.action == 'request':
        result = request_qualification(root)
    elif args.action == 'prepare':
        result = prepare(root)
    else:
        from .ilvis0_control_shards import launch
        summary = launch(root/'data'/ID, reserved_threads=0)
        result = {key:summary[key] for key in
                  ('state','completed','total','passed','charged')}
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
