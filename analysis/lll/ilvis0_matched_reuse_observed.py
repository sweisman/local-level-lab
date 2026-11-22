# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare two passing recorded controls with exact rejected-proposal reuse."""

import argparse
from contextlib import closing
from functools import partial
import json
from pathlib import Path

from . import ilvis0_matched_observed_preflight as parent, ilvis0_matched_reuse_generated as generated
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_matched_unstarted_recovery import ARCHIVE, MANIFEST, SUMMARY
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-matched-reuse-observed-v1'
ADAPTER = 'analysis/lll/ilvis0_matched_reuse_observed.py'
PLAN = parent.FOLDER+'MATCHED_REUSE_OBSERVED_PLAN.md'
RESULT = parent.FOLDER+'matched-reuse-observed-result.json'
REQUEST = parent.FOLDER+'matched-reuse-observed-qualification.json'
TEST_REPORT = parent.FOLDER+'matched-reuse-observed-tests.xml'
TEST = 'analysis/tests/test_ilvis0_matched_reuse_observed.py'
SCOPE = 'two previously passing NASA aircraft fits for exact rejected-proposal reuse'
CONTROLS = ('3df34ea39a6cbdbe15bb0f36-sphere_rotating', '2791235ca0b11b1ef4386e21-sphere_still')
GENERATED_MANIFEST = 'e432d976abd1ca1151a4a8e69b8fee8289b4d16928ec3301692f05f6ba83ec36'
GENERATED_SUMMARY = '6b351fd7e7fa73a1b93f20d63e59134779279dffddbb7b16c9d596fa2e17c69f'
TESTS = (*generated.TESTS,
    'test_recorded_controls_reuse_original_limits_and_exclude_failed_case',
    'test_recorded_comparison_checks_same_queries_and_training_isolation',
    'test_recorded_comparison_requires_stop_agreement_and_no_extra_calls',
    'test_recorded_sources_include_the_forecast_adapter_and_plan')


def tasks(original):
    return [{key: value for key, value in original[identity].items() if key not in ('index', 'shard')}
            for identity in CONTROLS]


def compare(old, old_forecast, current, current_forecast):
    if not old['converged']:
        raise ValueError('a previously converged recorded control is required')
    if any(fit['prediction_receiver_positions_used_in_training'] for fit in (old, current)):
        raise ValueError('receiver positions available only during training are required')
    if old_forecast['query_times_s'] != current_forecast['query_times_s']:
        raise ValueError('recorded query epochs differ')
    result = generated.assess(old, current, old_forecast, current_forecast)
    result['passed'] = result['passed'] and current['evaluations'] <= old['evaluations']
    return result


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (*generated.sources(root), ADAPTER, PLAN, TEST))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('retain the existing recorded control allowance')
    deps, environment = sources(root), runtime_environment()
    binding, tests = checked(root, REQUEST, sources=deps, environment=environment,
                             required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, parent.RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    staged = dict(qualification=binding, qualification_tests=tests,
                  recovery=recovery, recovery_tests=recovery_tests,
                  recovery_policy=encoded(generated.RECOVERY))
    with closing(ClosedStudy(root, 'data/'+generated.ID)) as gate:
        if ((gate.completion['manifest_sha256'], gate.completion['summary_sha256']) !=
                (GENERATED_MANIFEST, GENERATED_SUMMARY) or not gate.summary['passed']
                or len(gate.rows) != 8 or gate.manifest['environment'] != environment):
            raise ValueError('the verified eight-case generated gate is required')
        staged['generated_completion'] = encoded(gate.completion)
    with closing(ClosedStudy(root, ARCHIVE)) as preflight:
        if ((preflight.completion['manifest_sha256'], preflight.completion['summary_sha256']) !=
                (MANIFEST, SUMMARY) or preflight.manifest['environment'] != environment
                or preflight.input('recipe') != parent.recipe()):
            raise ValueError('the exact recorded preflight and environment are required')
        staged.update(preflight_completion=encoded(preflight.completion),
                      recipe=preflight.input('recipe', raw=True))
        rows = tasks(preflight.tasks)
        for task in rows:
            identity, segment = task['identity'], task['segment_id']
            fit = preflight.artifact(identity, 'fit.json')
            forecast = preflight.artifact(identity, 'forecast.json')
            envelope = preflight.envelope(identity)
            if (not envelope['result']['passed'] or fit['model'] != task['model']
                    or fit['maximum_evaluations'] != parent.EVALUATIONS
                    or envelope['charged']['native_calls'] != fit['evaluations']+1
                    or not compare(fit, forecast, dict(fit, reused_full_rejections=[]), forecast)['passed']):
                raise ValueError('sealed control did not pass: '+identity)
            staged[identity+'-reference'] = encoded(dict(fit=fit, forecast=forecast,
                compilation=preflight.artifact(identity, 'compilation.json'),
                artifact_sha256=preflight.rows[identity]['artifact_sha256']))
            for key in (task['input_key'], segment+'-training', segment+'-queries'):
                staged[key] = preflight.input(key, raw=True)
    inputs = dict(plan=PLAN)
    for key, raw in staged.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, raw)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=ADAPTER, tasks=rows,
        workers=2, threads=1, maximum_wall_s=1200., sources=deps)
    _write_equal(root/f'data/{ID}-inputs/definition.json', encoded(definition))
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .ilvis0_forecast import native_forecast
    from .ilvis0_solver_trust_v2 import fit_candidate
    from .ilvis0_training_forecast import fit_training
    from .ilvis0_wide_tangent import load, problem as widen

    identity, model = task['identity'], task['model']
    if (context.manifest['scope'] != SCOPE or identity not in CONTROLS
            or task['limits']['native_calls'] != parent.EVALUATIONS+1):
        raise ValueError('unchanged recorded control allowance required')
    reference = parent._json(context, identity+'-reference')
    base, directory, motion, compilation = parent.load_training(task, context)
    source = context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']
    kernel, compilation['wide'] = load(directory, expected_source_sha256=source)
    for name, build in compilation.items():
        if any(build[key] != reference['compilation'][name][key]
               for key in ('source_sha256', 'compiler', 'flags')):
            raise ValueError('compiled calculation differs from the sealed reference')
    context.save('compilation.json', compilation)
    problem = widen(base, kernel=kernel)
    fit = fit_training(problem, model, start=np.zeros(len(problem.bounds.active)),
        maximum_evaluations=parent.EVALUATIONS, reserve=context.charge,
        solver_provider=partial(fit_candidate, reuse_rejected_full=True))
    context.save('fit.json', fit)
    result = dict(identity=identity, model=model, passed=False, reference_converged=True,
        candidate_converged=fit['converged'], candidate_evaluations=fit['evaluations'],
        reference_evaluations=reference['fit']['evaluations'], forecast_native_calls=0,
        reused_full_rejections=len(fit['reused_full_rejections']),
        reference_sha256=reference['artifact_sha256'], scientific_decision='abstain')
    if fit['converged']:
        prediction = native_forecast(problem, fit['normalized_parameters'], model, **motion,
            maximum_interval_s=parent.MAX_INTERVAL, retain_training_difference=True, reserve=context.charge)
        forecast = dict(coordinates=prediction['coordinates'].tolist(), query_times_s=motion['times'].tolist(),
            training_epochs=task['training_epochs'], later_positions_used=False,
            training_coordinate_difference=prediction['training_coordinate_difference'].tolist())
        context.save('forecast.json', forecast)
        result.update(compare(reference['fit'], reference['forecast'], fit, forecast), forecast_native_calls=1)
    context.save('comparison.json', result)
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if set(study.tasks) != set(CONTROLS):
            raise ValueError('both frozen control identities are required')
        rows = []
        for identity in CONTROLS:
            envelope = study.envelope(identity)
            if f'artifacts/{identity}/comparison.json' in envelope['artifacts']:
                comparison = study.artifact(identity, 'comparison.json')
                calls = comparison['candidate_evaluations']+comparison['forecast_native_calls']
                if comparison != envelope['result'] or calls != envelope['charged']['native_calls']:
                    raise ValueError('comparison differs from the sealed outcome or charges')
            else:
                comparison = envelope['result']
                if comparison['passed']:
                    raise ValueError('passing outcome has no saved comparison')
            rows.append(comparison)
        result = dict(manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'], comparisons=rows,
            qualified=all(row['passed'] for row in rows), charged=study.summary['charged'])
    raw = encoded(result)
    _write_equal(root/RESULT, raw)
    return dict(qualified=result['qualified'], charged=result['charged'], result_sha256=digest(raw))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    print(json.dumps({'request': request, 'prepare': prepare, 'report': report}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
