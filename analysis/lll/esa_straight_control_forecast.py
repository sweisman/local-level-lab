# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run matched training-only forecasts on the four steady-course controls."""

import argparse
from contextlib import closing
import gzip
import io
import json
from pathlib import Path

from . import esa_repeat_turn_execution as reference
from .esa_repeat_turn_execution_v2 import CONTINUATION_INPUTS, ID as REFERENCE_ID
from .esa_straight_control_material import CLOCK_SHA, ID as MATERIAL_ID
from .studies.artifacts import atomic, digest, encoded, safe_path


ID = 'esa-straight-control-forecast-v1'
SCOPE = 'ESA 187 four steady-course controls; later receiver positions withheld'
BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_STRAIGHT_CONTROL_FORECAST_PLAN.md'
REQUEST = BASE+'esa-straight-control-forecast-timing-qualification.json'
REPORT = BASE+'esa-straight-control-forecast-timing-tests.xml'
ARCHIVE = BASE+'esa-repeat-turn-forecast-evidence/runtime'
REFERENCE_SHA = 'd9e63245684806e14fc3ac253ad0b98cfdbbb21fa831f348c344c58a6715bdd8'
MATERIAL_SHA = 'cbf50b32601176804dca47a43dd2712128b2536a205ae642eda2381520f19622'
WINDOWS = (21856, 32716, 36436, 39916)
SHARED = frozenset({'bundle', 'recipe', 'qualification-environment', 'recovery-allowance'})
WALL_S = 28800.
REQUIRED = ('test_straight_forecasts_preserve_full_turn_study_matrix_and_limits',
            'test_straight_forecast_rejects_outcome_inputs_before_any_read',
            'test_straight_forecast_requires_closed_material',
            'test_release_keeps_the_cheapest_start_even_if_its_forecast_is_missing',
            'test_control_scoring_refuses_changed_release_before_opening_positions',
            'test_turn_gain_is_a_paired_difference_and_keeps_missing_controls',
            'test_turn_timing_control_changes_only_angular_exposure')


def input_keys():
    return SHARED | {reference.key(index, field) for index in WINDOWS for field in reference.WINDOW_FILES}


def tasks():
    return [dict(identity=f'{index}-{law}-{start}', input_key=reference.key(index, 'interval'),
                 native_kind='tangent', payload=dict(first_index=index, law=law, start=start),
                 limits=reference.LIMITS.copy())
            for index in WINDOWS for law in reference.LAWS for start in (0, 1)]


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request
    from .studies.task_resume import qualification_sources, REQUIRED_TESTS

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
        BASE+'ESA_STRAIGHT_CONTROL_RELEASE_PLAN.md', BASE+'ESA_STRAIGHT_CONTROL_TIMING_CHECK.md',
        'analysis/tests/test_esa_straight_control_forecast.py',
        'analysis/tests/test_esa_straight_control_release.py', 'analysis/lll/esa_straight_control_release.py',
        'analysis/lll/ilvis0_tangent.cpp', 'analysis/lll/ilvis0_noise_bridge.cpp',
        reference.RECOVERY_REQUEST, reference.RECOVERY_REPORT))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=REQUIRED,
            minimum_tests=len(REQUIRED))
    checked(root, reference.RECOVERY_REQUEST, sources=qualification_sources(root), environment=environment,
            required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    return sources


def material_bundle(root):
    from .ilvis0_control_shards import verify_completion
    from .studies.closed import ClosedStudy

    path = 'data/'+MATERIAL_ID
    if not (root/path/'completion.json').is_file():
        raise ValueError('closed straight-control material required before preparation')
    verify_completion(root/path)
    with closing(ClosedStudy(root, path)) as study:
        if (study.completion['manifest_sha256'] != MATERIAL_SHA or study.completion['state'] != 'complete'
                or set(study.rows) != {MATERIAL_ID}):
            raise ValueError('exact successful straight-control preparation required')
        result = study.envelope(MATERIAL_ID)['result']
        raw = study.artifact(MATERIAL_ID, 'bundle.json', raw=True)
        bundle = json.loads(raw)
        if (result['passed'] is not True or result['material_files'] != 12
                or result['later_receiver_positions_decoded'] != 0 or result['protected_reads'] != 0
                or bundle['clock_sha256'] != CLOCK_SHA
                or tuple(w['window']['first_index'] for w in bundle['windows']) != WINDOWS):
            raise ValueError('complete verified training and clock material required')
        files = {}
        for bound in bundle['windows']:
            index = bound['window']['first_index']
            for field, filename in reference.WINDOW_FILES.items():
                data = study.artifact(MATERIAL_ID, f'{index}/{filename}', raw=True)
                if digest(data) != bound['files'][filename]:
                    raise ValueError('prepared control file does not match bundle')
                files[reference.key(index, field)] = data
    return raw, files


def prepare(root):
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as thread_environment
    from .esa_repeat_turn_inputs import RECIPE_SHA
    from .esa_repeat_turn_scoring import qualification as scoring_qualification
    from .studies.closed import ClosedStudy
    from .studies.runtime import Definition

    sources = qualification(root, verify=True)
    bundle, inputs = material_bundle(root)
    env = environment()
    if env['numerical_environment'] != thread_environment(workers=4, threads=1):
        raise ValueError('guarded four-worker allocation required')
    scoring_qualification(root, 'verify')
    with closing(ClosedStudy(root, ARCHIVE)) as study:
        recipe = study.input('recipe', raw=True)
        if (study.completion['manifest_sha256'] != REFERENCE_SHA or study.summary['completed'] != 16
                or digest(recipe) != RECIPE_SHA or study.completion['state'] != 'complete'):
            raise ValueError('exact completed repeat-turn reference recipe required')
    payload = dict(inputs, bundle=bundle, recipe=recipe,
                   **{'qualification-environment': encoded(env), 'recovery-allowance': encoded(reference.RECOVERY)})
    if set(payload) != input_keys() or (root/'data'/ID).exists():
        raise ValueError('exact new control forecast input roster required')
    staging = safe_path(root, 'data/'+ID+'-inputs')
    named = {}
    for name, raw in payload.items():
        path = staging/(name+'.npz' if name.endswith('-interval') else name)
        if path.is_file():
            if path.read_bytes() != raw:
                raise ValueError('staged control forecast input changed')
        else:
            atomic(path, raw)
        named[name] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
        sources=sorted(set(sources) | {REQUEST, REPORT}), inputs=named, tasks=tasks(),
        workers=4, threads=1, maximum_wall_s=WALL_S)
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, manifest_sha256=digest((root/'data'/ID/'manifest.json').read_bytes()),
                total=len(manifest['tasks']), launched=False)


def evaluate(task, context):
    declared = {name: value for name, value in task.items() if name not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or declared not in tasks()
            or set(context.manifest['inputs']) not in (input_keys(), input_keys() | CONTINUATION_INPUTS)):
        raise ValueError('exact training and forecast clock inputs required')

    import numpy as np
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import error_law
    from .airquantumgrav_prediction import train_and_forecast
    from .esa_repeat_turn_inputs import RECIPE_SHA
    from .esa_repeat_turn_material import array_hashes
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_native_error_training import ErrorTrainingFactory
    from .maneuver_error_roots import turn_exposure
    from .structured_noisy_study import _kernels

    read = lambda name: context.input_path(name).read_bytes()
    spec = task['payload']
    index, law = spec['first_index'], spec['law']
    env = environment()
    raw_recipe, bundle = read('recipe'), json.loads(read('bundle'))
    if (digest(raw_recipe) != RECIPE_SHA or bundle['clock_sha256'] != CLOCK_SHA
            or json.loads(read('qualification-environment')) != env
            or json.loads(read('recovery-allowance')) != reference.RECOVERY):
        raise ValueError('unchanged control recipe, environment and work limits required')
    recipe = json.loads(raw_recipe)
    bound, = [w for w in bundle['windows'] if w['window']['first_index'] == index]
    material = {field: read(reference.key(index, field)) for field in reference.WINDOW_FILES}
    if {name: digest(material[field]) for field, name in reference.WINDOW_FILES.items()} != bound['files']:
        raise ValueError('control forecast package hash changed')
    rows = json.loads(gzip.decompress(material['training']))
    times = np.asarray(json.loads(material['times']), float)
    with np.load(io.BytesIO(material['interval']), allow_pickle=False) as contents:
        if set(contents.files) != {'dt', 'theta', 'dv'}:
            raise ValueError('unexpected control interval arrays')
        arrays = {name: contents[name] for name in contents.files}
    if (len(rows) != reference.TRAIN or digest(encoded(rows)) != bound['training_receiver_sha256']
            or times.tolist() != bound['query_times_s'] or len(arrays['dt']) != bound['forecast_packets']
            or array_hashes(arrays) != bound['increment_hashes']):
        raise ValueError('control measurements differ from the completed preparation')
    check = lambda: _check_continue(context.root, context.manifest)
    check()
    noise, compiled = _kernels(context, env)
    kernel, tangent, compilation = compiled(rows[0]['height_m'])
    context.save('compilation.json', compilation)
    factory = ErrorTrainingFactory(noise=error_law(recipe['noise_by_law'][law]), noise_kernel=noise,
        gravity_anchor_height_m=rows[0]['height_m'], maximum_packets=len(arrays['dt']),
        maximum_queries=len(times), maximum_bytes=recipe['maximum_covariance_bytes'],
        anchor_policy=recipe['covariance_anchor_policy'])
    retained = {}

    def save(name, value):
        if name in ('training-observations.json', 'forecast.json'):
            retained[name] = value
        context.save(name, value)

    budget = None
    try:
        with context.prepay_native(native_calls=reference.LIMITS['native_calls'],
                                   packet_visits=reference.LIMITS['packet_visits']) as budget:
            result = train_and_forecast(**arrays, times=times, training_rows=rows, time_origin_s=bound['raw_first_s'],
                model=reference.MODEL, profile=True, policy_id='reported-short-v1', start=spec['start'],
                limits=recipe['limits'], maximum_evaluations=recipe['maximum_evaluations'],
                maximum_interval_s=recipe['maximum_interval_s'], kernel=kernel, tangent_kernel=tangent,
                reserve=budget.reserve, save=save, check_continue=check,
                training_error_factory=factory, clock=recipe['clock'])
            fit = result['fit']
            if not fit['converged']:
                return dict(passed=False, **spec, numerical_converged=False,
                            evaluations=fit['evaluations'], scientific_decision='abstain')
            earlier = retained['training-observations.json']
            if (earlier['native_prefix_packets'] != bound['training_packets']
                    or earlier['training_prefix_sha256'] != bound['training_prefix_hashes']
                    or len(fit['active_parameters']) != 27):
                raise ValueError('control fit changed the training prefix or nuisance parameters')
            operator, description = reference.full_operator(arrays=arrays, times=times,
                training=dict(earlier, rows=rows), recipe=recipe, law=law, noise_kernel=noise, reserve=budget.reserve)
            cut = reference.TRAIN
            exposure = turn_exposure(arrays['dt'], arrays['theta'], times[cut:],
                                     previous_time=times[cut-1], threshold_deg_s=1.)
            if np.count_nonzero(exposure) != bound['angular_exposure_counts']['scoring']:
                raise ValueError('control angular exposure differs from the prepared interval')
            seal, replay = reference.seal_conditional(operator, retained['forecast.json'],
                dict(residual_sum_squares=fit['residual_sum_squares'],
                     expected_logdet=fit['gaussian_training_score']['log_determinant']),
                times=times, anchor=earlier['coordinates'][-1], exposure=exposure,
                training_sha256=bound['training_receiver_sha256'], law=law, cut=cut)
            context.save('conditional-operator.json', description)
            context.save('training-prefix-replay.json', replay)
            context.save_bytes('sealed-receiver-forecast.json', seal)
            return dict(passed=True, **spec, numerical_converged=True, evaluations=fit['evaluations'],
                training_cost=fit['residual_sum_squares'], forecast_sha256=digest(seal),
                later_receiver_positions_used=False, protected_reads=0, scientific_decision='abstain')
    finally:
        if budget is not None:
            context.save('native-prepayment.json', budget.snapshot())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare'))
    action = parser.parse_args().action
    root = Path.cwd()
    print(json.dumps(prepare(root) if action == 'prepare' else qualification(root, verify=False), sort_keys=True))
