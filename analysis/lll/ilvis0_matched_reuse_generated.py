# SPDX-License-Identifier: AGPL-3.0-or-later
"""Qualify exact rejected-proposal reuse against sealed generated aircraft fits."""

import argparse
from contextlib import closing
from functools import partial
import json
import math
from pathlib import Path

from . import ilvis0_matched_trial_fits as reference, ilvis0_matched_wide as wide
from .ilvis0_control_shards import runtime_environment
from .ilvis0_solver_trust_v2 import fit_candidate
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-matched-reuse-generated-v1'
ARCHIVE = 'docs/ilvis0-matched-trial-fits-runtime'
PARENT_MANIFEST = 'bc3ebeecf401e2a65c95fd95beeef4629002850fafde45503e93ccafdf1b5148'
PARENT_SUMMARY = 'c275331ae6af8140e7174e84854bdbc33af0f5f9c6597fac87914a49b891d125'
FOLDER = wide.common.DOCS
PLAN = FOLDER+'MATCHED_REUSE_GENERATED_PLAN.md'
REQUEST = FOLDER+'matched-reuse-generated-qualification.json'
TEST_REPORT = FOLDER+'matched-reuse-generated-tests.xml'
RESULT = FOLDER+'matched-reuse-generated-result.json'
SCOPE = 'eight generated aircraft fit controls for exact rejected-proposal reuse'
RECOVERY = dict(max_attempts_per_task=2, max_technical_interruptions=2, maximum_wall_s=2400,
                minimum_free_bytes=1024**3, smoke_task_count=0)
TESTS = (
    'test_passing_references_require_both_stopping_and_forecast_agreement',
    'test_comparison_preserves_old_failures_and_rejects_material_cost_regression',
    'test_repeated_full_trial_reuses_only_an_identical_rejection[False]',
    'test_repeated_full_trial_reuses_only_an_identical_rejection[True]',
    'test_reuse_does_not_qualify_an_unfinished_physical_stop',
)


def assess(old, candidate, reference_forecast, candidate_forecast):
    import numpy as np

    from .ilvis0_precision_value import longitude_residual
    from .ilvis0_solver_position import physical_metric

    baseline = np.asarray(reference_forecast['coordinates'], float)
    predicted = np.asarray(candidate_forecast['coordinates'], float)
    cut = reference_forecast['training_epochs']
    if (baseline.ndim != 2 or baseline.shape != predicted.shape or baseline.shape[1] != 3
            or not 0 < cut < len(baseline) or candidate_forecast['training_epochs'] != cut
            or reference_forecast['later_positions_used'] or candidate_forecast['later_positions_used']
            or not np.isfinite(baseline).all() or not np.isfinite(predicted).all()):
        raise ValueError('finite matched training and forecast supports required')
    delta = predicted[cut:]-baseline[cut:]
    delta[:, 1] = longitude_residual(delta[:, 1])
    maximum = float(np.linalg.norm(delta*physical_metric(baseline[cut:]), axis=1).max())
    cost_change = (candidate['residual_sum_squares']-old['residual_sum_squares'])/max(
        1., candidate['residual_sum_squares'], old['residual_sum_squares'])
    initial_equal = math.isclose(candidate['initial_cost'], old['initial_cost'], rel_tol=1e-12, abs_tol=1e-10)
    same_pass = candidate['converged'] and abs(cost_change) <= 1e-8 and maximum <= .01
    passed = initial_equal and (same_pass if old['converged'] else cost_change <= 1e-8)
    return dict(passed=bool(passed), initial_cost_agrees=initial_equal, relative_cost_change=cost_change,
        maximum_later_position_change_m=maximum, reference_converged=old['converged'],
        candidate_converged=candidate['converged'], reference_evaluations=old['evaluations'],
        candidate_evaluations=candidate['evaluations'], reused_full_rejections=len(candidate['reused_full_rejections']))


def tasks():
    selected = {row['identity'] for row in reference.tasks()}
    return [dict(row, input_key=row['identity'], limits=dict(row['limits'], bound_calls=1, bound_steps=1))
            for row in wide.tasks() if row['identity'] in selected]


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
        'analysis/lll/ilvis0_native.c', 'analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/test_ilvis0_repeated_full_trial.py', 'analysis/tests/test_ilvis0_matched_reuse_generated.py'))


def request(root):
    from .studies.qualification import request as bind

    return bind(root, sources=sources(root), environment=runtime_environment(),
                output=REQUEST, report=TEST_REPORT)


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS as RECOVERY_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('retain the existing generated reuse study')
    deps, environment = sources(root), runtime_environment()
    qualification, tests = checked(root, REQUEST, sources=deps, environment=environment,
                                    required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_report = checked(root, wide.common.RECOVERY,
        sources=qualification_sources(root), environment=environment,
        required_tests=RECOVERY_TESTS, minimum_tests=len(RECOVERY_TESTS))
    rows = tasks()
    staged = dict(recipe=encoded(wide.recipe()), recovery_policy=encoded(RECOVERY),
        software_request=qualification, software_tests=tests, recovery=recovery, recovery_tests=recovery_report)
    with closing(ClosedStudy(root, ARCHIVE)) as seal:
        completion = seal.completion
        if ((completion['manifest_sha256'], completion['summary_sha256']) != (PARENT_MANIFEST, PARENT_SUMMARY)
                or seal.manifest['environment'] != environment or not seal.summary['passed']
                or len(rows) != 8 or set(seal.rows) != {row['identity'] for row in rows}
                or seal.input('recipe', raw=True) != staged['recipe']):
            raise ValueError('exact eight generated reference controls required')
        for row in rows:
            identity = row['identity']
            if seal.tasks[identity]['payload'] != row['payload']:
                raise ValueError('generated control recipe changed')
            staged[identity] = encoded(dict(fit=seal.artifact(identity, 'fit.json'),
                forecast=seal.artifact(identity, 'forecast.json'),
                reference_sha256=seal.rows[identity]['artifact_sha256']))
        staged['reference_completion'] = encoded(completion)
    inputs = dict(plan=PLAN)
    for key, raw in staged.items():
        location = 'data/'+ID+'-inputs/'+key
        atomic(root/location, raw)
        inputs[key] = location
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=adapter, tasks=rows,
        workers=4, threads=1, maximum_wall_s=1200., sources=deps)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or declared not in tasks()
            or context.input_path('recipe').read_bytes() != encoded(wide.recipe())):
        raise ValueError('the declared generated control and recipe are required')
    earlier = json.loads(context.input_path().read_bytes())
    run = wide.evaluate_fit(task['payload'], context,
                           solver_provider=partial(fit_candidate, reuse_rejected_full=True))
    context.charge(bound_calls=1, bound_steps=1)
    fit, forecast = (json.loads((context.directory/f'{name}.json').read_bytes())
                     for name in ('fit', 'forecast'))
    comparison = assess(earlier['fit'], fit, earlier['forecast'], forecast)
    result = dict(run, **{key: value for key, value in comparison.items() if key != 'passed'})
    result['passed'] = run['passed'] and comparison['passed']
    result['reference_sha256'] = earlier['reference_sha256']
    context.save('comparison.json', result)
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if len(study.rows) != 8 or study.summary['charged']['bound_calls'] != 8:
            raise ValueError('the eight completed comparisons are required')
        rows = [study.artifact(identity, 'comparison.json') for identity in study.rows]
        verified = sum(row['passed'] for row in rows)
        result = dict(manifest_sha256=study.completion['manifest_sha256'], summary_sha256=study.completion['summary_sha256'],
            comparisons=rows, qualified=verified == len(rows), charged=study.summary['charged'],
            verified=verified, scientific_decision='abstain')
    path = root/RESULT
    raw = encoded(result)
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved generated fit report differs')
    return dict(verified=verified, result_sha256=digest(raw), charged=result['charged'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    args = parser.parse_args()
    result = {'request': request, 'prepare': prepare, 'report': report}[args.action](Path.cwd())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
