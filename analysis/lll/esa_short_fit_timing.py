# SPDX-License-Identifier: AGPL-3.0-or-later
"""Time complete wide and selective fits on a short archived ESA input."""

import argparse
from contextlib import closing
import gzip
import io
import json
import math
from pathlib import Path
from statistics import median

from .esa_dispatch_pair_report import PREFIX, RESULT as PRIOR
from .esa_dispatch_pairs import BASE, COST_TOLERANCE, METHODS, PATH_TOLERANCE_M
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-short-fit-timing-v1'
SCOPE = 'Short recorded ESA wide and selective whole-fit timing with withheld later positions'
PLAN = BASE+'ESA_SHORT_FIT_TIMING_PLAN.md'
RESULT = BASE+'esa-short-fit-timing-result.json'
REQUEST = BASE+'esa-short-fit-timing-qualification.json'
TEST_REPORT = BASE+'esa-short-fit-timing-tests.xml'
PRIOR_SHA = '781bb1eae88ee8761bcfa800baf82c21cb470d3836f39e19b7ddb06674429d41'
TEST = 'analysis/tests/test_esa_short_fit_timing.py'
TESTS = ('test_short_prefix_retains_whole_latency_support_without_extra_packets',
         'test_fit_speed_gate_requires_same_numerical_result_in_both_cases')
TRAINING, PREDICTION, MAXIMUM = 120, 30, 20
CASES = (
    dict(model='sphere_rotating', profile=False, policy_id='reported-short-v1', start=0),
    dict(model='sphere_still', profile=True, policy_id='reported-persistent-v1', start=0),
)


def prefix_counts(intervals, times, *, training, offset):
    import numpy as np

    dt, times = np.asarray(intervals, float), np.asarray(times, float)
    if (dt.ndim != 1 or len(dt) == 0 or np.any(dt <= 0) or times.ndim != 1
            or not 2 <= training < len(times) or not np.isfinite(dt).all()
            or not np.isfinite(times).all() or np.any(np.diff(times) <= 0)
            or not math.isfinite(offset) or offset < 0.):
        raise ValueError('positive complete packet intervals and ordered query times required')
    ends = np.cumsum(dt)
    if times[0] < offset or times[-1]+offset > ends[-1]:
        raise ValueError('complete latency support required for short prefix')
    return tuple(int(np.searchsorted(ends, t+offset))+1 for t in (times[training-1], times[-1]))


def speed_gate(rows):
    valid = len(rows) == 2 and all(row.get('equivalent') is True for row in rows)
    if not valid:
        return False
    ratios = [row['fit_cpu_ratio'] for row in rows]
    return all(math.isfinite(x) and x >= 1. for x in ratios) and median(ratios) > 1.25


def task_for(spec, train_packets, all_packets):
    per_method_visits = MAXIMUM*train_packets*TRAINING+all_packets*(TRAINING+PREDICTION)
    return dict(identity=spec['model'], input_key='interval', native_kind='tangent', payload=spec,
        limits=dict(native_calls=2*(MAXIMUM+1), packet_visits=2*per_method_visits, bound_calls=0, bound_steps=0))


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST,
        'analysis/lll/ilvis0_native.c', 'analysis/lll/ilvis0_tangent.cpp'))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def prepare(root):
    import numpy as np

    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('reuse the existing short timing study')
    prior = (root/PRIOR).read_bytes()
    if digest(prior) != PRIOR_SHA:
        raise ValueError('exact sealed parent comparison report required')
    prior = json.loads(prior)
    deps, environment = sources(root), runtime_environment()
    qualification, tests = checked(root, REQUEST, sources=deps, environment=environment,
                                   required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    staged = dict(qualification=qualification, qualification_tests=tests, recovery=recovery,
        recovery_tests=recovery_tests, recovery_policy=encoded(dict(RECOVERY_POLICY, maximum_wall_s=900)))
    with closing(ClosedStudy(root, PREFIX)) as parent:
        if (prior['closures'].get(PREFIX) != parent.completion or not parent.summary['passed']
                or prior['equivalent_groups'] != 8 or prior['passing_pairs'] != 16
                or prior['protected_reads'] or prior['forecast_positions_decoded']
                or parent.manifest['environment'] != environment):
            raise ValueError('the complete matched earlier-only parent and environment must agree')
        for source in ('ilvis0_native.c', 'ilvis0_tangent.cpp', 'ilvis0_wide_tangent.py',
                       'ilvis0_hybrid_tangent.py', 'airquantumgrav_prediction.py'):
            name = 'analysis/lll/'+source
            if digest((root/name).read_bytes()) != parent.manifest['sources'][name]:
                raise ValueError('short benchmark must use the same native and prediction implementation')
        training = json.loads(gzip.decompress(parent.input('training', raw=True)))[:TRAINING]
        queries = parent.input('queries')
        queries['times_s'] = queries['times_s'][:TRAINING+PREDICTION]
        recipe = parent.input('recipe')
        with np.load(io.BytesIO(parent.input('interval', raw=True)), allow_pickle=False) as whole:
            if set(whole.files) != {'dt', 'theta', 'dv'}:
                raise ValueError('original prepared increments are required')
            earlier, all_packets = prefix_counts(whole['dt'], queries['times_s'], training=TRAINING,
                                                  offset=recipe['limits']['time_offset'])
            buffer = io.BytesIO()
            np.savez_compressed(buffer, **{key: whole[key][:all_packets] for key in whole.files})
        layout = dict(training=TRAINING, prediction=PREDICTION, training_packets=earlier, packets=all_packets,
                      parent=parent.completion, parent_inputs={k: parent.manifest['inputs'][k]['sha256']
                                                              for k in ('interval', 'queries', 'training')})
        if len(training) != TRAINING or len(queries['times_s']) != TRAINING+PREDICTION:
            raise ValueError('exact short window and query-only forecast are required')
        staged.update(interval=buffer.getvalue(), layout=encoded(layout), recipe=encoded(recipe),
                      training=encoded(training), queries=encoded(queries))
    inputs = dict(plan=PLAN, prior=PRIOR)
    for key, material in staged.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, material)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, sources=deps, inputs=inputs,
        tasks=[task_for(spec, earlier, all_packets) for spec in CASES],
        adapter=Path(__file__).relative_to(root).as_posix(), workers=2, threads=1, maximum_wall_s=900.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .airquantumgrav_observed_hybrid_report import compare_pair
    from .esa_dispatch_pairs import load_kernels
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_fit_timing import measure_variant
    from .ilvis0_wide_training import SOURCES, bind

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    spec, layout, recipe = task['payload'], read('layout'), read('recipe')
    declared = {k: v for k,v in task.items() if k not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or spec not in CASES or declared !=
            task_for(spec, layout['training_packets'], layout['packets'])):
        raise ValueError('exact short-prefix timings and finite allowance required')
    training, queries = read('training'), read('queries')
    with np.load(context.input_path('interval'), allow_pickle=False) as artifact:
        intervals = {key: artifact[key] for key in artifact.files}
    times = queries['times_s']
    native_counts = prefix_counts(intervals['dt'], times, training=TRAINING,
                                  offset=recipe['limits']['time_offset'])
    if ((len(training), len(times)) != (TRAINING, TRAINING+PREDICTION)
            or native_counts != (layout['training_packets'], layout['packets'])
            or len(intervals['dt']) != layout['packets']):
        raise ValueError('short prefix and saved latency support must match')
    run, _, binding = bind(expected_sources={name: context.manifest['sources']['analysis/lll/'+name]
                                             for name in SOURCES})
    context.save('protocol-binding.json', binding)
    order = METHODS if spec == CASES[0] else tuple(reversed(METHODS))
    summaries, artifacts, times_by_method = {}, {}, {}

    def check():
        _check_continue(context.root, context.manifest)

    for method in order:
        def calculate(spec, recipe, *, kernel_factory, reserve, reserve_construction, save, check_continue):
            kernel, tangent = kernel_factory(training[0]['height_m'])
            return run(**intervals, times=times, training_rows=training, time_origin_s=queries['time_origin_gps_sow_s'],
                **spec, limits=recipe['limits'], maximum_evaluations=MAXIMUM,
                maximum_interval_s=recipe['maximum_interval_s'], kernel=kernel, tangent_kernel=tangent,
                reserve=reserve, save=save, check_continue=check_continue)

        saved = {}

        def save(name, value):
            context.save(method+'-'+name, value)
            if name in ('fit.json', 'forecast.json'):
                saved[name] = value

        check()
        result, duration = measure_variant(calculate, spec, recipe,
            kernel_factory=lambda anchor: load_kernels(context, method, spec['model'], anchor),
            reserve=context.charge, reserve_construction=lambda **_: None, save=save, check_continue=check)
        fit = saved['fit.json']
        summaries[method] = dict(spec, converged=fit['converged'], evaluations=fit['evaluations'],
            passed=bool(fit['converged'] and result['all_columns_retained']),
            all_columns_retained=result['all_columns_retained'], training_cost=fit['residual_sum_squares'])
        artifacts[method], times_by_method[method] = saved, duration

    wide, selective = (artifacts[key] for key in METHODS)
    comparison = compare_pair(summaries['wide'], summaries['selective'], wide['fit.json'],
        selective['fit.json'], wide['forecast.json'], selective['forecast.json'], tolerance_m=PATH_TOLERANCE_M)
    a, b = (summaries[key]['training_cost'] for key in METHODS)
    equivalent = comparison['passed'] and all(row['passed'] for row in summaries.values()) and math.isclose(
        a, b, rel_tol=COST_TOLERANCE, abs_tol=0.)
    fit_cpu_ratio = times_by_method['wide']['fit_cpu_ns']/times_by_method['selective']['fit_cpu_ns']
    result = dict(spec=spec, order=order, fit_summaries=summaries, timing=times_by_method,
                  fit_cpu_ratio=fit_cpu_ratio, equivalent=equivalent, comparison=comparison,
                  passed=True, later_positions_read=0, scientific_decision='abstain')
    context.save('timing.json', result)
    return result


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if len(study.rows) != 2 or study.manifest['scope'] != SCOPE:
            raise ValueError('both terminal timing pairs required')
        layout = study.input('layout')
        rows = []
        for identity in study.rows:
            envelope = study.envelope(identity)
            row = envelope['result']
            if row['passed']:
                evaluations = sum(v['evaluations'] for v in row['fit_summaries'].values())
                visits = (evaluations*layout['training_packets']*TRAINING
                          +2*layout['packets']*(TRAINING+PREDICTION))
                if (row != study.artifact(identity, 'timing.json')
                        or envelope['charged']['native_calls'] != evaluations+2
                        or envelope['charged']['packet_visits'] != visits):
                    raise ValueError('sealed measured timing or call accounting differs')
            rows.append(row)
        value = dict(study.completion, pairs=rows, speed_gate_passed=speed_gate(rows),
                     charged=study.summary['charged'], scientific_decision='abstain')
    raw = encoded(value)
    _write_equal(root/RESULT, raw)
    return dict(result_sha256=digest(raw), passed=value['speed_gate_passed'],
                ratios=[row.get('fit_cpu_ratio') for row in rows])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    result = {'request': request, 'prepare': prepare, 'report': report}[action](Path.cwd())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
