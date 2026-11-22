# SPDX-License-Identifier: AGPL-3.0-or-later
"""Qualify the opt-in trial calculation against eight sealed wider fits."""

import argparse
from contextlib import closing
from functools import partial
import json
from pathlib import Path

import numpy as np

from . import ilvis0_matched_trial_probe as points, ilvis0_matched_wide as wide
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-matched-trial-fits-v1-20261118'
ADAPTER = 'analysis/lll/ilvis0_matched_trial_fits.py'
TEST = 'analysis/tests/test_ilvis0_matched_trial_fits.py'
PLAN = wide.common.DOCS+'MATCHED_TRIAL_FITS_PLAN.md'
REQUEST = wide.common.DOCS+'matched-trial-fits-qualification.json'
REPORT = wide.common.DOCS+'matched-trial-fits-tests.xml'
SCOPE = 'eight generated fits with value-only trials and sealed wider references'
SETTINGS = (('flat_geographic_field', 20., True), ('sphere_still', 20., False))
TESTS = ('test_trial_fit_grid_keeps_both_complete_model_sets_and_finite_limits',
         'test_fit_equivalence_preserves_even_the_failed_stop_and_later_coordinates',
         'test_value_trials_preserve_solver_path_and_skip_rejected_tangents',
         'test_fit_reserves_every_actual_native_call_and_keeps_all_columns[value_trials]',
         'test_wide_adapter_preserves_matched_disc_model_and_receiver_prefix')


def tasks():
    extra_visits = wide.common.MAX_EVALUATIONS*wide.common.prefix_count()*wide.common.CUT
    rows = []
    for baseline in wide.tasks():
        spec = baseline['payload']
        setting = (spec['truth_model'], spec['cap_dph'], spec['profile'])
        if spec['arithmetic'] == 'wide' and setting in SETTINGS:
            limits = dict(baseline['limits'], native_calls=2*wide.common.MAX_EVALUATIONS+1,
                          packet_visits=baseline['limits']['packet_visits']+extra_visits)
            rows.append(dict(baseline, input_key=baseline['identity'], limits=limits,
                             native_kind='mixed'))
    return rows


def equivalent(fit, forecast, reference_fit, reference_forecast):
    ordinary_fields = {key: value for key, value in fit.items()
                       if key != 'native_evaluations_by_kind'}
    return (encoded(ordinary_fields) == encoded(reference_fit)
            and encoded(forecast) == encoded(reference_forecast))


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (ADAPTER, PLAN, TEST, 'analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp', 'analysis/tests/test_ilvis0_solver_trust_v2.py',
        'analysis/tests/test_ilvis0_training_forecast.py',
        'analysis/tests/test_ilvis0_matched_precision.py'))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as freeze

    return freeze(root, sources=sources(root), environment=runtime_environment(),
                  output=REQUEST, report=REPORT)


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    root = Path(root).resolve()
    base = root/'data'/(ID+'-inputs')
    if (root/'data'/ID).exists():
        raise ValueError('retain the existing paired-fit allowance')
    environment, dependencies = runtime_environment(), sources(root)
    binding, tests = checked(root, REQUEST, sources=dependencies, environment=environment,
                             required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, wide.common.RECOVERY,
        sources=qualification_sources(root), environment=environment,
        required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    materials = dict(qualification=binding, qualification_tests=tests,
                     recovery=recovery, recovery_tests=recovery_tests)
    with closing(ClosedStudy(root, 'data/'+points.ID)) as probe:
        if (probe.completion['state'] != 'complete' or probe.summary['charged']['native_calls'] != 8
                or probe.summary['total'] != 3 or probe.manifest['environment'] != environment):
            raise ValueError('passing recorded fixed-point check required')
        materials['point_receipt'] = encoded(probe.completion)
    rows = tasks()
    with closing(ClosedStudy(root, 'data/'+wide.ID)) as study:
        if (study.completion['state'] != 'complete' or study.manifest['environment'] != environment
                or study.manifest['scope'] != wide.SCOPE or study.input('recipe', raw=True) != encoded(wide.recipe())):
            raise ValueError('exact generated parent required')
        for name in ('ilvis0_native.c', 'ilvis0_tangent.cpp', 'ilvis0_matched_wide.py',
                     'ilvis0_matched_generated.py', 'ilvis0_matched_truth.py', 'ilvis0_wide_tangent.py'):
            path = 'analysis/lll/'+name
            if digest((root/path).read_bytes()) != study.manifest['sources'][path]:
                raise ValueError('reference physics or generated input source changed: '+name)
        materials.update(parent_receipt=encoded(study.completion), recipe=study.input('recipe', raw=True))
        failed = []
        for entry in rows:
            identity = entry['identity']
            original = study.envelope(identity)
            fit = study.artifact(identity, 'fit.json')
            forecast = study.artifact(identity, 'forecast.json')
            if (not original['result']['passed'] or study.tasks[identity]['payload'] != entry['payload']
                    or original['charged']['native_calls'] != fit['evaluations']+1
                    or forecast['later_positions_used'] or fit['prediction_receiver_positions_used_in_training']):
                raise ValueError('changed baseline fit or forecast: '+identity)
            if not fit['converged']:
                failed.append(identity)
            materials[identity] = encoded(dict(spec=entry['payload'], fit=fit, forecast=forecast,
                compilation=study.artifact(identity, 'compilation.json')))
        if failed != ['sphere_still-sphere_rotating-cap20-removal0-wide']:
            raise ValueError('sole baseline stopping failure required')
    base.mkdir(parents=True, exist_ok=True)
    inputs = {}
    for name, raw in materials.items():
        path = base/name
        _write_equal(path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, sources=dependencies,
                      inputs=inputs, tasks=rows, workers=4, threads=1, maximum_wall_s=1200.)
    _write_equal(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(id=ID, limits=manifest['limits'], allocation=manifest['allocation'])


def evaluate(task, context):
    from .ilvis0_exploratory import load_kernel
    from .ilvis0_forecast import native_forecast
    from .ilvis0_matched_training import matched_limits, matched_training_problem
    from .ilvis0_precision_value import calculate, load as load_scalar
    from .ilvis0_shape import load_tangent
    from .ilvis0_solver_position import physical_metric
    from .ilvis0_training_forecast import fit_training
    from .ilvis0_wide_tangent import load as load_wide, problem as widen

    identity = task['identity']
    clean = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or clean not in tasks():
        raise ValueError('unchanged generated trial-fit task required')
    reference = json.loads(context.input_path().read_bytes())
    spec = task['payload']
    if (reference['spec'] != spec
            or context.input_path('recipe').read_bytes() != encoded(wide.recipe())):
        raise ValueError('changed reference fit or generated motion recipe')
    common = wide.common
    dt, theta, dv, times, earlier = wide.material(spec)
    prefix, cut = common.prefix_count(), common.CUT
    directory = context.root/'shards'/f'{context.shard:03d}'/'trial-fit-kernels'
    kernel, value_meta = load_kernel(directory)
    tangent, tangent_meta = load_tangent(directory)
    source = context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']
    precise, wide_meta = load_wide(directory, expected_source_sha256=source)
    scalar, scalar_meta = load_scalar(directory, precision='long_double', expected_source_sha256=source)
    compilation = dict(value=value_meta, tangent=tangent_meta, wide=wide_meta)
    for name, build in compilation.items():
        saved = reference['compilation'][name]
        if any(build[key] != saved[key] for key in ('source_sha256', 'compiler', 'flags')):
            raise ValueError('compiled tangent differs from the sealed reference')
    context.save('compilation.json', dict(compilation, scalar=scalar_meta))
    model = spec['model']
    sigma = (.05/physical_metric(earlier)).ravel()
    problem = matched_training_problem(times[:cut], earlier, theta=theta[:prefix],
        dv=dv[:prefix], dt=dt[:prefix], covariance=np.diag(sigma**2), model=model,
        limits=matched_limits(spec['cap_dph']), profile=spec['profile'], clock='nominal_200Hz',
        maximum_interval_s=common.MAX_INTERVAL, kernel=kernel, tangent_kernel=tangent)
    problem = widen(problem, kernel=precise)

    def trial(point, candidate):
        value = calculate(problem, point, candidate, kernel=scalar, longitude='stable')
        return value['residual'], value['boundaries']

    fit = fit_training(problem, model, start=np.zeros(len(problem.bounds.active)),
        maximum_evaluations=common.MAX_EVALUATIONS, reserve=context.charge, trial_residual=trial)
    context.save('fit.json', fit)
    future = native_forecast(problem, fit['normalized_parameters'], model, theta=theta, dv=dv,
        dt=dt, times=times, maximum_interval_s=common.MAX_INTERVAL,
        reserve=partial(context.charge, native_kind='tangent'), retain_training_difference=True)
    forecast = dict(coordinates=future['coordinates'].tolist(),
        training_coordinate_difference=future['training_coordinate_difference'].tolist(),
        training_epochs=cut, later_positions_used=False)
    context.save('forecast.json', forecast)
    return dict(passed=equivalent(fit, forecast, reference['fit'], reference['forecast']),
        identity=identity, reference_evaluations=reference['fit']['evaluations'],
        fit_evaluations=fit['evaluations'], native_evaluations_by_kind=fit['native_evaluations_by_kind'],
        reference_converged=reference['fit']['converged'], converged=fit['converged'],
        training_equal=equivalent(fit, {}, reference['fit'], {}),
        forecast_equal=encoded(forecast)==encoded(reference['forecast']), forecast_native_calls=1,
        observed_fit_starts=0, scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare'))
    root = Path.cwd()
    result = request(root) if parser.parse_args().action == 'request' else prepare(root)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
