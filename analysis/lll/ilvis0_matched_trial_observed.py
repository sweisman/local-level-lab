# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the trial calculation on a passing and a stopped aircraft fit."""

import argparse
from contextlib import closing
from functools import partial
import json
from pathlib import Path

import numpy as np

from . import ilvis0_matched_observed_preflight as parent, ilvis0_matched_trial_fits as generated
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-matched-trial-observed-v1-20261118'
ADAPTER = 'analysis/lll/ilvis0_matched_trial_observed.py'
TEST = 'analysis/tests/test_ilvis0_matched_trial_observed.py'
PLAN = parent.FOLDER+'MATCHED_TRIAL_OBSERVED_PLAN.md'
REQUEST = parent.FOLDER+'matched-trial-observed-qualification.json'
REPORT = parent.FOLDER+'matched-trial-observed-tests.xml'
SCOPE = 'two recorded IMU8 fits with value-only trials and sealed wider references'
FORECASTS = {'3df34ea39a6cbdbe15bb0f36-flat_still': False,
             '3df34ea39a6cbdbe15bb0f36-sphere_rotating': True}
TESTS = (*generated.TESTS, 'test_recorded_trial_tasks_allow_only_one_control_forecast')


def tasks(original):
    rows = []
    for identity, forecast in FORECASTS.items():
        task = {key: value for key, value in original[identity].items() if key not in ('index', 'shard')}
        calls = 2*parent.EVALUATIONS
        cut, prefix = task['training_epochs'], task['training_packets']
        visits = calls*cut*prefix + int(forecast)*task['full_packets']*(cut+task['scoring_epochs'])
        rows.append(dict(task, native_kind='mixed', limits=dict(native_calls=calls+int(forecast),
            packet_visits=visits, bound_calls=0, bound_steps=0)))
    return rows


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (*generated.sources(root), ADAPTER, PLAN, TEST))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=runtime_environment(),
                   output=REQUEST, report=REPORT)


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    root = Path(root).resolve()
    base = root/'data'/(ID+'-inputs')
    if (root/'data'/ID).exists():
        raise ValueError('retain the existing recorded trial-fit allowance')
    environment, dependencies = runtime_environment(), sources(root)
    binding, tests = checked(root, REQUEST, sources=dependencies, environment=environment,
                             required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, parent.RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    materials = dict(qualification=binding, qualification_tests=tests,
                     recovery=recovery, recovery_tests=recovery_tests)
    with closing(ClosedStudy(root, 'data/'+generated.ID)) as gate:
        if (gate.completion['state'] != 'complete' or gate.summary['total'] != 8
                or gate.manifest['environment'] != environment or not gate.summary['passed']):
            raise ValueError('passing generated full-fit gate required')
        materials['generated_gate'] = encoded(gate.completion)
    with closing(ClosedStudy(root, 'data/'+parent.ID)) as study:
        if (study.completion['state'] != 'terminal' or study.manifest['scope'] != parent.SCOPE
                or study.manifest['environment'] != environment or study.input('recipe') != parent.recipe()):
            raise ValueError('unchanged recorded parent and environment required')
        rows = tasks(study.tasks)
        materials.update(recipe=study.input('recipe', raw=True), parent_receipt=encoded(study.completion))
        for task in rows:
            identity, segment = task['identity'], task['segment_id']
            envelope = study.envelope(identity)
            expected_forecast = FORECASTS[identity]
            fit = study.artifact(identity, 'fit.json')
            forecast = study.artifact(identity, 'forecast.json') if expected_forecast else None
            if (fit['converged'] != expected_forecast or envelope['result']['passed'] != expected_forecast
                    or fit['model'] != task['model'] or fit['maximum_evaluations'] != parent.EVALUATIONS
                    or fit['prediction_receiver_positions_used_in_training']
                    or envelope['charged']['native_calls'] != fit['evaluations']+int(expected_forecast)
                    or (expected_forecast and forecast['later_positions_used'])
                    or (not expected_forecast and (fit['evaluations'] != parent.EVALUATIONS
                        or fit['stability_probe']['reason'] != 'fresh_position_probe_not_stable'
                        or envelope['result']['error_type'] != 'BudgetStopped'))):
                raise ValueError('sealed training outcome differs from the recorded control: '+identity)
            materials[identity+'-reference'] = encoded(dict(fit=fit, forecast=forecast,
                compilation=study.artifact(identity, 'compilation.json')))
            for name in (task['input_key'], segment+'-training', segment+'-queries'):
                if name not in materials:
                    materials[name] = study.input(name, raw=True)
    base.mkdir(parents=True, exist_ok=True)
    inputs = {}
    for name, raw in materials.items():
        path = base/name
        _write_equal(path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, sources=dependencies,
                      inputs=inputs, tasks=rows, workers=2, threads=1, maximum_wall_s=1800.)
    _write_equal(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(id=ID, limits=manifest['limits'], allocation=manifest['allocation'])


def evaluate(task, context):
    from .ilvis0_forecast import native_forecast
    from .ilvis0_precision_value import calculate, load as load_value
    from .ilvis0_training_forecast import fit_training
    from .ilvis0_wide_tangent import load as load_wide, problem as widen

    identity, model = task['identity'], task['model']
    n = int(FORECASTS[identity])
    if context.manifest['scope'] != SCOPE or task['limits']['native_calls'] != 2*parent.EVALUATIONS+n:
        raise ValueError('unchanged recorded fit allowance required')
    reference = parent._json(context, identity+'-reference')
    base, directory, motion, compilation = parent.load_training(task, context)
    source = context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']
    tangent, compilation['wide'] = load_wide(directory, expected_source_sha256=source)
    scalar, scalar_meta = load_value(directory, precision='long_double', expected_source_sha256=source)
    for name, build in compilation.items():
        saved = reference['compilation'][name]
        if any(build[key] != saved[key] for key in ('source_sha256', 'compiler', 'flags')):
            raise ValueError('compiled calculation differs from the sealed trial reference')
    context.save('compilation.json', dict(compilation, scalar=scalar_meta))
    problem = widen(base, kernel=tangent)

    def trial(point, candidate):
        values = calculate(problem, point, candidate, kernel=scalar, longitude='stable')
        return values['residual'], values['boundaries']

    fit = fit_training(problem, model, start=np.zeros(len(problem.bounds.active)),
        maximum_evaluations=parent.EVALUATIONS, reserve=context.charge, trial_residual=trial)
    context.save('fit.json', fit)
    forecast = None
    if n:
        prediction = native_forecast(problem, fit['normalized_parameters'], model, **motion,
            maximum_interval_s=parent.MAX_INTERVAL, retain_training_difference=True,
            reserve=partial(context.charge, native_kind='tangent'))
        forecast = dict(coordinates=prediction['coordinates'].tolist(), query_times_s=motion['times'].tolist(),
            training_epochs=task['training_epochs'], later_positions_used=False,
            training_coordinate_difference=prediction['training_coordinate_difference'].tolist())
        context.save('forecast.json', forecast)
    return dict(passed=generated.equivalent(fit, forecast, reference['fit'], reference['forecast']),
        identity=identity, model=model, fit_evaluations=fit['evaluations'],
        reference_converged=reference['fit']['converged'], converged=fit['converged'],
        training_equal=generated.equivalent(fit, None, reference['fit'], None),
        native_evaluations_by_kind=fit['native_evaluations_by_kind'], forecast_native_calls=n,
        forecast_equal=encoded(forecast)==encoded(reference['forecast']), later_positions_used=False,
        recorded_fit_starts=1, scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare'))
    root = Path.cwd()
    result = request(root) if parser.parse_args().action == 'request' else prepare(root)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
