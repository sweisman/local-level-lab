# SPDX-License-Identifier: AGPL-3.0-or-later
"""Measure two archived ESA whole fits with the original wide and selective kernels."""

import argparse
from contextlib import ExitStack, closing
import gzip
import json
import math
from pathlib import Path

from .airquantumgrav_observed_hybrid_report import compare_pair
from .esa_dispatch_pair_report import PREFIX, RESULT as PRIOR
from .esa_dispatch_pairs import (BASE, COST_TOLERANCE, MATERIAL, MAX_CLOCK_ROWS, METHODS,
                                 PATH_TOLERANCE_M, PREDICTION, TRAINING, load_kernels)
from .esa_short_fit_timing import CASES as SHORT, PRIOR_SHA, prefix_counts, speed_gate
from .ilvis0_fit_timing import measure_variant
from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-full-fit-timing-v1'
SCOPE = 'Full ESA 187 paired whole-fit timing with 800 training positions and 400 later times'
PLAN = BASE+'ESA_FULL_FIT_TIMING_PLAN.md'
RESULT = BASE+'esa-full-fit-timing-result.json'
REQUEST = BASE+'esa-full-fit-timing-qualification-v2.json'
REPORT = BASE+'esa-full-fit-timing-tests-v2.xml'
TEST = 'analysis/tests/test_esa_full_fit_timing.py'
TESTS = ('test_full_benchmark_retains_pairs_and_declares_exact_work',
         'test_full_equivalence_requires_each_method_agree_with_archived_result')
CASES = tuple(dict(spec, start=1) for spec in SHORT)
MAXIMUM = 40
WALL_S = 10800
RECOVER = dict(RECOVERY_POLICY, maximum_wall_s=WALL_S)


def identity(spec):
    return f"{spec['model']}-{int(spec['profile'])}-{spec['policy_id']}-{spec['start']}"


def tasks(*, native_packets, training_prefix_packets):
    if (type(native_packets) is not int or type(training_prefix_packets) is not int
            or not 0 < training_prefix_packets < native_packets < MAX_CLOCK_ROWS):
        raise ValueError('bounded increments and fixed earlier prefix required')
    visits = MAXIMUM*training_prefix_packets*TRAINING + native_packets*(TRAINING+PREDICTION)
    limits = dict(native_calls=2*(MAXIMUM+1), packet_visits=2*visits, bound_calls=0, bound_steps=0)
    return [dict(identity=identity(spec), input_key='interval', native_kind='tangent', payload=spec, limits=limits)
            for spec in CASES]


def assess(fits, paths, archived_fits, archived_paths):
    def compare(a, b, av, bv):
        if not a['passed'] or not b['passed']:
            return dict(passed=False, reason='training fit did not meet the original stopping checks')
        result = compare_pair(a, b, av['fit'], bv['fit'], av['forecast'], bv['forecast'], tolerance_m=PATH_TOLERANCE_M)
        result['costs_match'] = math.isclose(a['training_cost'], b['training_cost'], rel_tol=COST_TOLERANCE, abs_tol=0.)
        result['passed'] &= result['costs_match']
        return result

    fresh = compare(fits['wide'], fits['selective'], paths['wide'], paths['selective'])
    replays = {m: compare(archived_fits[m], fits[m], archived_paths[m], paths[m]) for m in METHODS}
    return dict(fresh=fresh, replays=replays, equivalent=fresh['passed'] and all(r['passed'] for r in replays.values()))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST,
        'analysis/lll/ilvis0_native.c', 'analysis/lll/ilvis0_tangent.cpp'))
    env = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=env, output=REQUEST, report=REPORT)
    qualification, tests = checked(root, REQUEST, sources=sources, environment=env,
                                   required_tests=TESTS, minimum_tests=len(TESTS))
    return sources, env, qualification, tests


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the already frozen timing study and allowance')
    raw = (root/PRIOR).read_bytes()
    if digest(raw) != PRIOR_SHA:
        raise ValueError('the exact original full-window comparison is required')
    prior = json.loads(raw)
    sources, env, qualification_bytes, tests = qualification(root, verify=True)
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=env,
                                       required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, PREFIX)) as parent:
        if (parent.completion != prior['closures'][PREFIX] or not parent.summary['passed']
                or parent.manifest['environment'] != env or prior['equivalent_groups'] != 8
                or prior['passing_pairs'] != 16 or prior['protected_reads'] or prior['forecast_positions_decoded']):
            raise ValueError('complete verified matches under the original environment required')
        for basename in ('ilvis0_native.c', 'ilvis0_tangent.cpp', 'ilvis0_wide_tangent.py', 'ilvis0_hybrid_tangent.py',
                         'ilvis0_wide_training.py', 'airquantumgrav_prediction.py'):
            name = 'analysis/lll/'+basename
            if digest((root/name).read_bytes()) != parent.manifest['sources'][name]:
                raise ValueError('timing must preserve the original solver implementation: '+name)
        binding = parent.input('preparation')
        layout = binding['result']
        selected = tasks(native_packets=layout['native_packets'], training_prefix_packets=layout['training_prefix_packets'])
        material_hashes = {key: parent.manifest['inputs'][key]['sha256'] for key in MATERIAL}
        if (material_hashes != binding['files'] or layout['training_positions'] != TRAINING
                or layout['forecast_times'] != PREDICTION or layout['forecast_positions_decoded'] or layout['protected_reads']):
            raise ValueError('verified receiver-free future query inputs required')
        staged = {key: parent.input(key, raw=True) for key in sorted(MATERIAL | {'recipe'})}
        staged['binding'] = encoded(dict(closure=parent.completion, layout=layout, hashes=material_hashes))
        for task in selected:
            key = task['identity']
            prior_pair = next(row for row in prior['pairs'] if row['identity'] == key)
            sealed = parent.envelope(key)
            pairs = {method: {name: parent.artifact(key, f'{method}-{name}.json') for name in ('fit', 'forecast')}
                     for method in METHODS}
            if (not prior_pair['passed'] or prior_pair['source'] != PREFIX or sealed['status'] != 'complete'
                    or sealed['result_sha256'] != prior_pair['result_sha256']
                    or prior_pair['fits'] != sealed['result']['fits']
                    or any(row['evaluations'] > MAXIMUM for row in prior_pair['fits'].values())
                    or any(row['forecast']['prediction_receiver_positions_used'] for row in pairs.values())):
                raise ValueError('exact two previously converged training-only pairs required')
            staged[key] = encoded(dict(fits=prior_pair['fits'], paths=pairs))
    staged.update(qualification=qualification_bytes, qualification_tests=tests, recovery=recovery,
                  recovery_tests=recovery_tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=PRIOR)
    for key, value in staged.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=inputs,
                      sources=sources, tasks=selected, workers=2, threads=1, maximum_wall_s=WALL_S)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_wide_training import SOURCES, bind

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    original, spec = read('binding'), task['payload']
    layout = original['layout']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    materials = {key: context.manifest['inputs'][key]['sha256'] for key in MATERIAL}
    if (context.manifest['scope'] != SCOPE or original['hashes'] != materials
            or declared not in tasks(native_packets=layout['native_packets'],
                                     training_prefix_packets=layout['training_prefix_packets'])):
        raise ValueError('exact frozen full timing case required')
    earlier = json.loads(gzip.decompress(context.input_path('training').read_bytes()))
    queries, recipe, weights = read('queries'), read('recipe'), read('weights')
    if set(queries) != {'times_s', 'time_origin_gps_sow_s'}:
        raise ValueError('future input must contain query times only')
    times, origin = queries['times_s'], queries['time_origin_gps_sow_s']
    with np.load(context.input_path('interval'), allow_pickle=False) as archive:
        if set(archive.files) != {'dt', 'theta', 'dv'}:
            raise ValueError('the prepared increments are required')
        motion = {key: archive[key] for key in archive.files}
    earlier_count, _ = prefix_counts(motion['dt'], times, training=TRAINING, offset=recipe['limits']['time_offset'])
    if (len(earlier), len(times), earlier_count, len(motion['dt'])) != (
            TRAINING, TRAINING+PREDICTION, layout['training_prefix_packets'], layout['native_packets']):
        raise ValueError('original full recorded-window dimensions are required')
    run, _, protocol = bind(expected_sources={name: context.manifest['sources']['analysis/lll/'+name]
                                               for name in SOURCES})
    context.save('protocol-binding.json', protocol)
    archived = read(task['identity'])
    order = METHODS if spec == CASES[0] else tuple(reversed(METHODS))
    fits, paths, timing = {}, {}, {}

    def check():
        _check_continue(context.root, context.manifest)

    def calculate(spec, recipe, *, kernel_factory, reserve, reserve_construction, save, check_continue):
        kernel, tangent = kernel_factory(earlier[0]['height_m'])
        return run(**motion, times=np.asarray(times), training_rows=earlier, time_origin_s=origin, **spec,
                   limits=recipe['limits'], maximum_evaluations=MAXIMUM, maximum_interval_s=recipe['maximum_interval_s'],
                   kernel=kernel, tangent_kernel=tangent, reserve=reserve, save=save, check_continue=check_continue)

    for method in order:
        check()
        saved = {}

        def save(name, value):
            context.save(method+'-'+name, value)
            if name in ('fit.json', 'forecast.json'):
                saved[name.removesuffix('.json')] = value

        result, timing[method] = measure_variant(calculate, spec, recipe,
            kernel_factory=lambda anchor: load_kernels(context, method, spec['model'], anchor),
            reserve=context.charge, reserve_construction=lambda **_: None, save=save, check_continue=check)
        if result['weight_configuration'] != weights[spec['policy_id']]:
            raise ValueError('training weighting differs from the original frozen setting')
        fit = saved['fit']
        fits[method] = dict(spec, converged=fit['converged'], all_columns_retained=result['all_columns_retained'],
                            training_cost=fit['residual_sum_squares'], evaluations=fit['evaluations'],
                            passed=bool(fit['converged'] and result['all_columns_retained']))
        paths[method] = saved
    comparison = assess(fits, paths, archived['fits'], archived['paths'])
    result = dict(spec=spec, order=order, fits=fits, timing=timing, comparison=comparison,
                  equivalent=comparison['equivalent'], fit_cpu_ratio=timing['wide']['fit_cpu_ns']/timing['selective']['fit_cpu_ns'],
                  passed=comparison['equivalent'], later_positions_read=0, scientific_decision='abstain')
    context.save('timing.json', result)
    return result


def recover(root):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = f'data/{ID}'
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as original:
            if original.input('recovery_policy') != RECOVER:
                raise ValueError('unchanged prelaunch recovery allowances required')
            if all(identity in original.rows and original.envelope(identity)['status'] == 'complete'
                   for identity in original.tasks):
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVER)
    return resume_campaign(root, continuation)


def report(root):
    prefix = 'data/'+ID
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        continuation = root/(prefix+'-recovery')
        sources = {prefix: original}
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            selected = {identity: value['origin'] for identity, value in inspect(root, continuation)['selected'].items()}
        else:
            selected = {identity: prefix for identity in original.rows
                        if original.envelope(identity)['status'] == 'complete'}
        rows = {}
        for identity, origin in selected.items():
            if origin not in sources:
                sources[origin] = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
            study = sources[origin]
            envelope = study.envelope(identity)
            row = envelope['result']
            if row != study.artifact(identity, 'timing.json') or row['spec'] != original.tasks[identity]['payload']:
                raise ValueError('verified timed outcome and original identity required')
            rows[identity] = row
        result = dict(fits=rows, closures={key: st.completion for key, st in sources.items()},
                      passed=speed_gate(list(rows.values())), scheduled=len(original.tasks), complete=len(rows))
    _write_equal(root/RESULT, encoded(result))
    return {key: result[key] for key in ('passed', 'scheduled', 'complete')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
