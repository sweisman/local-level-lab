# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite training-only reference forecasts on the four preselected ESA turns."""

import argparse
from contextlib import closing
import gzip
import io
import json
from pathlib import Path


ID = 'esa-repeat-turn-forecast-v1'
SCOPE = 'ESA recording 187 repeat-turn reference forecasts with later receiver positions withheld'
BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_REPEAT_TURN_EXECUTION_PLAN.md'
REQUEST = BASE+'esa-repeat-turn-execution-qualification.json'
REPORT = BASE+'esa-repeat-turn-execution-tests.xml'
RECOVERY_REQUEST = BASE+'esa-repeat-turn-recovery-qualification.json'
RECOVERY_REPORT = BASE+'esa-repeat-turn-recovery-tests.xml'
MATERIAL_SHA = 'da55fe8bfd9357f040853f42b8dbbbad0ed83659c160c1bd6e7323c141c0b700'
WINDOWS = (22936, 33796, 37516, 41116)
LAWS = ('increment', 'point')
MODEL = 'sphere_rotating'
TRAIN, LATER = 400, 120
LIMITS = dict(native_calls=900000, packet_visits=45100000000, bound_calls=0, bound_steps=0)
RECOVERY = dict(max_attempts_per_task=2, max_technical_interruptions=4,
                maximum_wall_s=14400, minimum_free_bytes=2*1024**3)
WINDOW_FILES = {'training': 'training.json.gz', 'times': 'forecast-times.json', 'interval': 'interval.npz'}
SHARED = frozenset(('material-receipt', 'input-preflight', 'recipe', 'qualification-environment',
                    'execution-qualification', 'execution-tests', 'recovery-qualification',
                    'recovery-tests', 'scoring-qualification', 'scoring-tests', 'recovery-allowance'))
TEST = 'analysis/tests/test_esa_repeat_turn_execution.py'
TEST_NAMES = ('test_repeat_turn_tasks_match_fixed_windows_laws_and_starts',
              'test_repeat_turn_worker_rejects_extra_receiver_input_before_access',
              'test_sealed_generated_forecast_replays_prefix_and_joint_operator')


def key(index, field):
    return f'{index}-{field}'


def input_keys():
    return SHARED | {key(index, field) for index in WINDOWS for field in WINDOW_FILES}


def tasks():
    return [dict(identity=f'{index}-{law}-{start}', input_key=key(index, 'interval'), native_kind='tangent',
                 payload=dict(first_index=index, law=law, start=start), limits=LIMITS.copy())
            for index in WINDOWS for law in LAWS for start in (0,1)]


def sources(root):
    from .studies.dependencies import source_closure

    own = Path(__file__).relative_to(root).as_posix()
    return source_closure(root, (own, PLAN, TEST, 'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp', 'analysis/tests/test_esa_conditional_forecast_v3_study.py',
        'analysis/tests/test_task_resume.py'))


def request_qualifications(root):
    from .airquantumgrav_inventory import environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    from .studies.task_resume import qualification_sources

    return dict(execution=request(root, sources=sources(root), environment=environment(), output=REQUEST, report=REPORT),
                recovery=request(root, sources=qualification_sources(root), environment=runtime_environment(),
                                 output=RECOVERY_REQUEST, report=RECOVERY_REPORT))


def prepare(root):
    from . import esa_innovation_transfer as sealed
    from . import esa_native_rolling_transfer as prior
    from . import esa_repeat_turn_material as material
    from . import esa_repeat_turn_scoring as scoring
    from .esa_repeat_turn_inputs import RESULT as INPUT, RECIPE_SHA
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic, digest, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources, REQUIRED_TESTS

    root = root.resolve()
    staging = safe_path(root, 'data/'+ID+'-inputs')
    if staging.exists() or safe_path(root, 'data/'+ID).exists():
        raise ValueError('fresh execution identity required')
    env = environment()
    if env['numerical_environment'] != numerical_environment(workers=4, threads=1):
        raise ValueError('guarded four-worker and one-thread allocation required')
    req, tests = checked(root, REQUEST, sources=sources(root), environment=env,
                         required_tests=TEST_NAMES, minimum_tests=len(TEST_NAMES))
    recovery_req, recovery_tests = checked(root, RECOVERY_REQUEST, sources=qualification_sources(root),
        environment=runtime_environment(), required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    score_verified = scoring.qualification(root, 'verify')
    verified = material.verify(root)
    preflight, receipt = ((root/name).read_bytes() for name in (INPUT, material.RECEIPT))
    if (verified['sha256'] != MATERIAL_SHA or digest(receipt) != MATERIAL_SHA or digest(preflight) != material.INPUT_SHA
            or score_verified['request_sha256'] != material.SCORING_REQUEST_SHA):
        raise ValueError('unchanged prepared windows and sealed scoring qualification required')
    checked_receipt = json.loads(receipt)
    if tuple(w['first_index'] for w in checked_receipt['windows']) != WINDOWS:
        raise ValueError('all four preselected windows must be bound')
    with closing(ClosedStudy(root, 'data/'+prior.ID)) as source:
        recipe = source.input('400-recipe', raw=True)
        if source.completion['manifest_sha256'] != sealed.SOURCE_SHA or digest(recipe) != RECIPE_SHA:
            raise ValueError('original fixed reference forecast recipe required')
    shared = {'material-receipt':receipt, 'input-preflight':preflight, 'recipe':recipe,
              'qualification-environment':encoded(env), 'execution-qualification':req, 'execution-tests':tests,
              'recovery-qualification':recovery_req, 'recovery-tests':recovery_tests,
              'scoring-qualification':(root/scoring.REQUEST).read_bytes(), 'scoring-tests':(root/scoring.REPORT).read_bytes(),
              'recovery-allowance':encoded(RECOVERY)}
    inputs = {}
    for name, value in shared.items():
        path = staging/name
        atomic(path, value)
        inputs[name] = path.relative_to(root).as_posix()
    for index in WINDOWS:
        for field, filename in WINDOW_FILES.items():
            inputs[key(index, field)] = f'{material.STAGE}/{index}/{filename}'
    if set(inputs) != input_keys():
        raise ValueError('training-only input whitelist differs')
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
        sources=sources(root), inputs=inputs, tasks=tasks(), workers=4, threads=1, maximum_wall_s=28800.)
    atomic(staging/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=len(manifest['tasks']), allocation=manifest['allocation'], launched=False)


def seal_conditional(operator, forecast, fit, *, times, anchor, exposure, training_sha256, law, cut):
    import numpy as np
    from .esa_conditional_forecast_v2_study import fixed_receiver_mean
    from .esa_conditional_forecast_v3_study import replay_training_prefix
    from .esa_repeat_turn_scoring import seal
    from .ilvis0_solver_position import physical_metric

    replay = replay_training_prefix(operator, forecast, training_epochs=cut,
        expected_cost=fit['residual_sum_squares'], expected_logdet=fit['expected_logdet'])
    conditional = fixed_receiver_mean(operator, forecast, training_epochs=cut)
    dimension = 3*(len(times)-cut)
    innovations = np.zeros((3*len(times), dimension))
    innovations[3*cut:] = np.eye(dimension)
    covariance_root = operator.unwhiten(innovations)[3*cut:]
    metric = np.tile(physical_metric([anchor])[0], len(times)-cut)
    payload = seal(training_sha256=training_sha256, law=law, previous_time=times[cut-1], times=times[cut:],
                   anchor=anchor, mean=conditional['mean'], native_root=covariance_root*metric[:,None], exposure=exposure)
    return payload, replay


def full_operator(*, arrays, times, training, recipe, law, noise_kernel, reserve):
    from dataclasses import replace
    import numpy as np
    from .airquantumgrav_error_policy import build
    from .airquantumgrav_noisy_inputs import error_law
    from .ilvis0_exploratory import ConditionalBounds
    from .ilvis0_native_error_training import build_training_operator
    from .ilvis0_training_forecast import initialize_training

    count = training['native_prefix_packets']
    gps = np.asarray(training['coordinates'])
    prefix = {name:value[:count] for name, value in arrays.items()}
    initial, gravity = initialize_training(times[:TRAIN], gps, **prefix, model=MODEL,
        maximum_interval_s=recipe['maximum_interval_s'], clock=recipe['clock'])
    weight = build(training['rows'], policy_id='reported-short-v1')
    if (weight.source_sha256 != training['weight_source_sha256'] or weight.configuration != training['weight_configuration']
            or not np.array_equal(weight.times-training['time_origin_gps_sow_s'], times[:TRAIN])):
        raise ValueError('full law must preserve the original earlier receiver weights')
    spec = replace(weight.spec, drift_origin_s=weight.spec.drift_origin_s-training['time_origin_gps_sow_s'])
    transforms = np.concatenate((weight.transforms, np.repeat(weight.transforms[-1:], LATER, axis=0)))
    return build_training_operator(**arrays, times=times, initial=initial,
        bounds=ConditionalBounds(recipe['limits'], fit_earth_removal=True), model=MODEL, gravity_mps2=gravity,
        disc_radius_m=6371000., noise=error_law(recipe['noise_by_law'][law]), receiver_spec=spec,
        receiver_transforms=transforms, noise_kernel=noise_kernel, gravity_anchor_height_m=float(gps[0,2]),
        maximum_packets=len(arrays['dt']), maximum_queries=len(times), maximum_bytes=recipe['maximum_covariance_bytes'],
        anchor_policy=recipe['covariance_anchor_policy'],
        reserve=lambda *, native_calls, packet_steps: reserve(native_calls=native_calls, packet_visits=packet_steps))


def evaluate(task, context):
    declared = {name: value for name, value in task.items() if name not in ('index', 'shard')}
    if (context.manifest.get('scope') != SCOPE or set(context.manifest.get('inputs', {})) != input_keys()
            or declared not in tasks()):
        raise ValueError('exact training-only repeat-turn task required before accessing inputs')

    import numpy as np
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import error_law
    from .airquantumgrav_prediction import train_and_forecast
    from .esa_repeat_turn_inputs import RECIPE_SHA
    from .esa_repeat_turn_material import INPUT_SHA, array_hashes
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_native_error_training import ErrorTrainingFactory
    from .maneuver_error_roots import turn_exposure
    from .studies.artifacts import digest, encoded
    from .structured_noisy_study import _kernels

    def raw(name):
        return context.input_path(name).read_bytes()

    spec = task['payload']
    index, law = spec['first_index'], spec['law']
    env = environment()
    receipt, preflight, recipe = (raw(name) for name in ('material-receipt', 'input-preflight', 'recipe'))
    if (digest(receipt) != MATERIAL_SHA or digest(preflight) != INPUT_SHA or digest(recipe) != RECIPE_SHA
            or json.loads(raw('qualification-environment')) != env or json.loads(raw('recovery-allowance')) != RECOVERY):
        raise ValueError('unchanged staged material, source environment and recovery allowance required')
    bound, = [w for w in json.loads(preflight)['windows'] if w['window']['first_index'] == index]
    recipe = json.loads(recipe)
    rows = json.loads(gzip.decompress(raw(key(index, 'training'))))
    times = np.asarray(json.loads(raw(key(index, 'times'))), float)
    with np.load(io.BytesIO(raw(key(index, 'interval'))), allow_pickle=False) as contents:
        if set(contents.files) != {'dt', 'theta', 'dv'}:
            raise ValueError('unexpected forecast interval fields')
        arrays = {name:contents[name] for name in contents.files}
    if (len(rows) != TRAIN or digest(encoded(rows)) != bound['training_receiver_sha256']
            or times.tolist() != bound['query_times_s'] or array_hashes(arrays) != bound['increment_hashes']
            or len(arrays['dt']) != bound['forecast_packets']):
        raise ValueError('training-only material differs from original preflight')
    check = lambda: _check_continue(context.root, context.manifest)
    check()
    noise_kernel, compiled = _kernels(context, env)
    kernel, tangent, compilation = compiled(rows[0]['height_m'])
    context.save('compilation.json', compilation)
    factory = ErrorTrainingFactory(noise=error_law(recipe['noise_by_law'][law]), noise_kernel=noise_kernel,
        gravity_anchor_height_m=rows[0]['height_m'], maximum_packets=len(arrays['dt']), maximum_queries=len(times),
        maximum_bytes=recipe['maximum_covariance_bytes'], anchor_policy=recipe['covariance_anchor_policy'])
    retained = {}

    def save(name, value):
        if name in ('training-observations.json', 'forecast.json'):
            retained[name] = value
        context.save(name, value)

    budget = None
    try:
        with context.prepay_native(native_calls=LIMITS['native_calls'], packet_visits=LIMITS['packet_visits']) as budget:
            result = train_and_forecast(**arrays, times=times, training_rows=rows, time_origin_s=bound['raw_first_s'],
                model=MODEL, profile=True, policy_id='reported-short-v1', start=spec['start'], limits=recipe['limits'],
                maximum_evaluations=recipe['maximum_evaluations'], maximum_interval_s=recipe['maximum_interval_s'],
                kernel=kernel, tangent_kernel=tangent, reserve=budget.reserve, save=save, check_continue=check,
                training_error_factory=factory, clock=recipe['clock'])
            fit = result['fit']
            if not fit['converged']:
                return dict(passed=False, **spec, numerical_converged=False, evaluations=fit['evaluations'])
            earlier = retained['training-observations.json']
            if (earlier['native_prefix_packets'] != bound['training_packets']
                    or earlier['training_prefix_sha256'] != bound['training_prefix_hashes']
                    or len(fit['active_parameters']) != 27):
                raise ValueError('forecast engine used a different original training prefix')
            operator, description = full_operator(arrays=arrays, times=times, training=dict(earlier, rows=rows),
                recipe=recipe, law=law, noise_kernel=noise_kernel, reserve=budget.reserve)
            nominal = retained['forecast.json']
            exposure = turn_exposure(arrays['dt'], arrays['theta'], times[TRAIN:], previous_time=times[TRAIN-1], threshold_deg_s=1.)
            if np.count_nonzero(exposure) != bound['angular_exposure_counts']['scoring']:
                raise ValueError('original later angular exposure count differs')
            seal, replay = seal_conditional(operator, nominal,
                dict(residual_sum_squares=fit['residual_sum_squares'], expected_logdet=fit['gaussian_training_score']['log_determinant']),
                times=times, anchor=earlier['coordinates'][-1], exposure=exposure,
                training_sha256=bound['training_receiver_sha256'], law=law, cut=TRAIN)
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
    print(json.dumps((prepare if action == 'prepare' else request_qualifications)(Path.cwd()), sort_keys=True))
