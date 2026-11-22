# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prospective wide and selective-tangent comparison on a new ESA window."""

import argparse
from contextlib import closing
import gzip
import itertools
import json
from pathlib import Path

from .esa_dispatch_clock import MAX_CLOCK_ROWS
from .esa_dispatch_window import PREDICTION, TRAINING
from .esa_repeat_turn_execution_v2 import CONTINUATION_INPUTS
from .studies.artifacts import digest, encoded


ID = 'esa-dispatch-fresh-pairs-v1'
SCOPE = 'ESA 187 fresh sixteen-pair method comparison using earlier positions and future times'
MODELS = ('sphere_rotating', 'sphere_still')
POLICIES = ('reported-short-v1', 'reported-persistent-v1')
METHODS = ('wide', 'selective')
EVALUATIONS = 200
COST_TOLERANCE = 1e-8
PATH_TOLERANCE_M = .01
MATERIAL = frozenset({'interval', 'training', 'queries', 'weights'})
INPUTS = MATERIAL | {'preparation', 'recipe', 'recovery-allowance'}
RECOVERY = dict(max_attempts_per_task=3, max_technical_interruptions=16,
                maximum_wall_s=108000, minimum_free_bytes=5*1024**3)
BASE = 'docs/mixed-tangent-hybrid/'
PLAN = BASE+'OBSERVED_DISPATCH_FRESH_PLAN_V2.md'
REQUEST = BASE+'observed-dispatch-fresh-v2-qualification.json'
REPORT = BASE+'observed-dispatch-fresh-v2-tests.xml'
GENERATED = BASE+'start-equivalence-v2-result.json'
GENERATED_SHA = '69a4c0f66d764d47ef86dadb09dd36b4987fa98f1b07cc999f3b2ba12d5aa485'
PREPARATION_SHA = '00028f5c4826e26023b60c9480244acb696f68bc97cc13d550455366272447fb'
REQUIRED = (
    'test_dispatch_pairs_keep_all_observed_settings_and_finite_native_work',
    'test_dispatch_pair_rejects_forecast_positions_before_access',
    'test_dispatch_group_requires_both_pairs_and_checks_cross_start_forecast_spread',
    'test_pair_report_retains_all_sixteen_terminal_pairs_and_failed_groups',
)


def tasks(*, native_packets, training_prefix_packets):
    if (type(native_packets) is not int or type(training_prefix_packets) is not int
            or not 0 < training_prefix_packets < native_packets < MAX_CLOCK_ROWS):
        raise ValueError('bounded stream and strict training prefix required')
    visits = EVALUATIONS*training_prefix_packets*TRAINING + native_packets*(TRAINING+PREDICTION)
    result = []
    for model, profile, policy, start in itertools.product(MODELS, (False, True), POLICIES, (0, 1)):
        result.append(dict(identity=f'{model}-{int(profile)}-{policy}-{start}', input_key='interval',
                           native_kind='tangent',
                           payload=dict(model=model, profile=profile, policy_id=policy, start=start),
                           limits=dict(native_calls=2*(EVALUATIONS+1), packet_visits=2*visits,
                                       bound_calls=0, bound_steps=0)))
    return result


def recipe():
    from .airquantumgrav_observed_dispatch import recipe as baseline

    return dict(baseline(maximum_wall_s=108000), version=ID, models=list(MODELS),
                relative_training_cost_tolerance=COST_TOLERANCE, absolute_training_cost_tolerance=0.,
                forecast_tolerance_m=PATH_TOLERANCE_M, forecast_positions_decoded=0)


def qualification(root, *, verify):
    from .esa_repeat_turn_execution import RECOVERY_REQUEST, RECOVERY_REPORT
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request
    from .studies.task_resume import qualification_sources, REQUIRED_TESTS

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
        BASE+'OBSERVED_DISPATCH_FRESH_PLAN.md',
        'analysis/tests/test_esa_dispatch_pairs.py', 'analysis/tests/test_esa_dispatch_pair_report.py',
        'analysis/lll/esa_dispatch_pair_report.py', 'analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp', GENERATED, RECOVERY_REQUEST, RECOVERY_REPORT))
    env = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=env, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=env, required_tests=REQUIRED,
            minimum_tests=len(REQUIRED))
    checked(root, RECOVERY_REQUEST, sources=qualification_sources(root), environment=env,
            required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    return sources


def prepared_material(root):
    from .esa_dispatch_inputs import ID as PREPARATION
    from .ilvis0_control_shards import verify_completion
    from .studies.closed import ClosedStudy

    prefix = 'data/'+PREPARATION
    if not (root/prefix/'completion.json').is_file():
        raise ValueError('the single input preparation must finish before staging pairs')
    verify_completion(root/prefix)
    with closing(ClosedStudy(root, prefix)) as study:
        if (study.completion['manifest_sha256'] != PREPARATION_SHA
                or set(study.rows) != {PREPARATION} or study.completion['state'] != 'complete'):
            raise ValueError('exact completed paired input preparation required')
        result = study.envelope(PREPARATION)['result']
        material = {name: study.artifact(PREPARATION, name, raw=True) for name in sorted(MATERIAL)}
        binding = dict(study=PREPARATION, result=result, closure=study.completion,
                       files={name: digest(value) for name, value in material.items()})
    return binding, material


def prepare(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.runtime import Definition

    sources = qualification(root, verify=True)
    proof = (root / GENERATED).read_bytes()
    report = json.loads(proof)
    if (digest(proof) != GENERATED_SHA or report['qualified'] is not True
            or report['complete'] != 12 or len(report['groups']) != 6):
        raise ValueError('verified generated method comparison required')
    binding, payload = prepared_material(root)
    settings = recipe()
    payload.update(preparation=encoded(binding), recipe=encoded(settings),
                   **{'recovery-allowance': encoded(RECOVERY)})
    directory = root/'data'/(ID+'-inputs')
    inputs = {}
    for name, value in payload.items():
        target = directory / (name+'.npz' if name == 'interval' else name)
        _write_equal(target, value)
        inputs[name] = target.relative_to(root).as_posix()
    result = binding['result']
    selected = tasks(native_packets=result['native_packets'],
                     training_prefix_packets=result['training_prefix_packets'])
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
        sources=sorted(set(sources) | {REQUEST, REPORT}), inputs=inputs, tasks=selected,
        workers=4, threads=1, maximum_wall_s=settings['maximum_wall_s'])
    _write_equal(directory/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, limits=manifest['limits'], allocation=manifest['allocation'],
                manifest_sha256=digest((root/'data'/ID/'manifest.json').read_bytes()), launched=False)


def assess_group(pairs, *, times, materials):
    """Compare both saved starts within one model and assumption setting."""
    from .airquantumgrav_scoring import receiver_errors
    from .ilvis0_start_equivalence_v2 import compare_start_sets_v2

    if not set(pairs) <= {0, 1}:
        raise ValueError('exact solver start identities required')
    if set(pairs) != {0, 1}:
        return dict(state='incomplete', equivalent=False)
    if not all(pair['passed'] for pair in pairs.values()):
        return dict(state='pair_failed', equivalent=False)
    if len(times) != TRAINING+PREDICTION:
        raise ValueError('exact later forecast grid required')

    common = digest(encoded(dict(materials=materials, times_s=times)))
    base = pairs[0]['forecasts']['wide']['coordinates'][TRAINING:]
    methods = {method: [] for method in METHODS}
    settings = set()
    for start in (0, 1):
        for method in METHODS:
            fit = pairs[start]['fits'][method]
            forecast = pairs[start]['forecasts'][method]
            settings.add((fit['model'], fit['profile'], fit['policy_id']))
            if (fit['start'] != start or forecast['times_s'] != times
                    or len(forecast['coordinates']) != len(times)
                    or forecast['training_epochs'] != TRAINING or forecast['prediction_epochs'] != PREDICTION
                    or forecast['prediction_receiver_positions_used'] is not False):
                raise ValueError('unchanged start, earlier split and future clock required')
            differences = receiver_errors(forecast['coordinates'][TRAINING:], base)
            methods[method].append(dict(start=start, training_cost=fit['training_cost'],
                                        forecast=differences.tolist(), binding=common,
                                        passed=fit['passed'] and fit['converged']))
    if len(settings) != 1:
        raise ValueError('matched model, processing assumption and GPS error policy required')
    result = compare_start_sets_v2(methods['wide'], methods['selective'],
        relative_cost_tolerance=COST_TOLERANCE, absolute_cost_tolerance=0.,
        forecast_tolerance_m=PATH_TOLERANCE_M)
    return dict(state='equivalent' if result['equivalent'] else 'different',
                equivalent=result['equivalent'], rule=result)


def load_kernels(context, method, model, anchor):
    from .airquantumgrav_inventory import environment
    from .ilvis0_exploratory import load_kernel
    from .ilvis0_tangent_dispatch import load_for_model
    from .ilvis0_wide_tangent import load as load_wide

    directory = context.root/'shards'/f'{context.shard:03d}'/'kernels'/method
    hashes = context.manifest['sources']
    value, value_meta = load_kernel(directory, gravity_anchor_height_m=anchor)
    kwargs = dict(expected_source_sha256=hashes['analysis/lll/ilvis0_tangent.cpp'],
                  gravity_anchor_height_m=anchor)
    if method == 'wide':
        tangent, tangent_meta = load_wide(directory, **kwargs)
    else:
        tangent, tangent_meta = load_for_model(model, directory,
            expected_wide_loader_sha256=hashes['analysis/lll/ilvis0_wide_tangent.py'],
            expected_selective_loader_sha256=hashes['analysis/lll/ilvis0_hybrid_tangent.py'], **kwargs)
        if (tangent_meta['dispatch_method'] != 'selective'
                or tangent_meta.get('shared_loader_unchanged') is not True):
            raise ValueError('expected model-declared selective tangent')
    compilers = environment()['compilers']
    if (value_meta['source_sha256'] != hashes['analysis/lll/ilvis0_native.c']
            or value_meta['compiler'] != compilers['cc'] or tangent_meta['compiler'] != compilers['c++']):
        raise ValueError('prepared native source or compiler differs')
    context.save(method+'-compilation.json', dict(value=value_meta, tangent=tangent_meta))
    return value, tangent


def evaluate(task, context):
    from .esa_dispatch_inputs import ID as PREPARATION

    inputs = context.manifest['inputs']
    if context.manifest['scope'] != SCOPE or set(inputs) not in (INPUTS, INPUTS | CONTINUATION_INPUTS):
        raise ValueError('exact training inputs and no later positions required')
    if task.get('payload', {}).get('model') not in MODELS:
        raise ValueError('prepared comparison applies to the two globe solver implementations')
    receipt = json.loads(context.input_path('preparation').read_bytes())
    prepared = receipt['result']
    if (receipt['study'] != PREPARATION or receipt['closure']['manifest_sha256'] != PREPARATION_SHA
            or not prepared['passed']
            or prepared['training_positions'] != TRAINING or prepared['forecast_times'] != PREDICTION
            or prepared['forecast_positions_decoded'] != 0 or prepared['protected_reads'] != 0
            or receipt['files'] != {key: inputs[key]['sha256'] for key in MATERIAL}):
        raise ValueError('exact verified earlier-only preparation required')
    possible = tasks(native_packets=prepared['native_packets'],
                     training_prefix_packets=prepared['training_prefix_packets'])
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    settings = recipe()
    if (declared not in possible or json.loads(context.input_path('recipe').read_bytes()) != settings
            or json.loads(context.input_path('recovery-allowance').read_bytes()) != RECOVERY):
        raise ValueError('unchanged paired solver case and recipe required')

    import numpy as np
    from .airquantumgrav_observed_hybrid_report import compare_pair
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_wide_training import SOURCES, bind

    run, _, protocol = bind(expected_sources={
        name: context.manifest['sources']['analysis/lll/'+name] for name in SOURCES})
    context.save('protocol-binding.json', protocol)
    with np.load(context.input_path('interval'), allow_pickle=False) as archive:
        if set(archive.files) != {'dt', 'theta', 'dv'}:
            raise ValueError('only original prepared inertial increments are allowed')
        motion = {name: archive[name] for name in archive.files}
    earlier = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    time_layout = json.loads(context.input_path('queries').read_bytes())
    if set(time_layout) != {'times_s', 'time_origin_gps_sow_s'}:
        raise ValueError('exact typed query-time-only format required')
    times = np.asarray(time_layout['times_s'])
    origin = time_layout['time_origin_gps_sow_s']
    offset = settings['limits']['time_offset']
    count = int(np.searchsorted(np.cumsum(motion['dt']), times[TRAINING-1]+offset))+1
    if (len(earlier) != TRAINING or len(times) != TRAINING+PREDICTION
            or len(motion['dt']) != prepared['native_packets'] or count != prepared['training_prefix_packets']):
        raise ValueError('prepared training and forecast layout differs')
    weights = json.loads(context.input_path('weights').read_bytes())
    anchor = earlier[0]['height_m']
    spec = task['payload']
    check = lambda: _check_continue(context.root, context.manifest)
    summaries, details = {}, {}

    for method in METHODS:
        check()
        kernel, tangent = load_kernels(context, method, spec['model'], anchor)
        saved = {}

        def save(name, value):
            context.save(method+'-'+name, value)
            if name in ('fit.json', 'forecast.json'):
                saved[name] = value

        result = run(**motion, times=times, training_rows=earlier, time_origin_s=origin, **spec,
                     limits=settings['limits'], maximum_evaluations=settings['maximum_evaluations'],
                     maximum_interval_s=settings['maximum_interval_s'],
                     kernel=kernel, tangent_kernel=tangent, reserve=context.charge, save=save,
                     check_continue=check)
        if result['weight_configuration'] != weights[spec['policy_id']]:
            raise ValueError('paired training weighting differs from the input freeze')
        fit = saved['fit.json']
        passed = bool(fit['converged'] and result['all_columns_retained'])
        summaries[method] = dict(spec, converged=fit['converged'], passed=passed,
                                 all_columns_retained=result['all_columns_retained'],
                                 training_cost=fit['residual_sum_squares'], evaluations=fit['evaluations'])
        details[method] = saved

    if all(result['passed'] for result in summaries.values()):
        wide, selective = (details[method] for method in METHODS)
        comparison = compare_pair(summaries['wide'], summaries['selective'],
                                  wide['fit.json'], selective['fit.json'],
                                  wide['forecast.json'], selective['forecast.json'],
                                  tolerance_m=PATH_TOLERANCE_M)
    else:
        comparison = dict(passed=False, reason='one or both training fits did not converge')
    context.save('comparison.json', comparison)
    return dict(passed=comparison['passed'], comparison=comparison, fits=summaries,
                forecast_positions_decoded=0, protected_reads=0, scientific_decision='abstain')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = prepare(root) if action == 'prepare' else qualification(root, verify=False)
    print(json.dumps(result, sort_keys=True))
