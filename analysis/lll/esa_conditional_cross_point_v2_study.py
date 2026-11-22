# SPDX-License-Identifier: AGPL-3.0-or-later
"""Corrected time-grid replay of one fixed ESA conditional forecast."""

from pathlib import Path

from . import esa_conditional_cross_point_study as base

ID = 'esa-conditional-cross-point-development-v2'
FAILED = 'data/'+base.ID
SCOPE = base.SCOPE+'; native times supplied separately'
REQUEST = 'docs/prediction-observed-development/qualification/conditional-cross-point-v2-request.json'
REPORT = 'docs/prediction-observed-development/qualification/conditional-cross-point-v2-tests.xml'
FAILED_MANIFEST = '7298a7aadc5ff28c2f89173bbaef607a1101511ae9dfa4b75dacab97126e672d'
FAILED_SUMMARY = '2562f474c4355d7ffff1a1371521c554febadde7020cfcf9428d606beb98e156'


def tasks():
    return base.tasks()


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(Path(root).resolve(), base.sources(root)+[
        'analysis/lll/esa_conditional_cross_point_v2_study.py',
        'analysis/tests/test_esa_conditional_cross_point_v2_study.py',
        'docs/prediction-observed-development/CROSS_POINT_CONDITIONAL_V2_PLAN.md'])


def required_tests():
    return base.required_tests()+(
        'test_changed_forecast_time_grid_fails',
        'test_cross_point_v2_preserves_failed_task_and_limits',
        'test_cross_point_v2_requires_fresh_qualification')


def verify_failed_parent(root):
    from .studies.closed import ClosedStudy

    study = ClosedStudy(root, FAILED)
    try:
        result = study.envelope(tasks()[0]['identity'])['result']
        if (study.completion != dict(state='terminal',
                    manifest_sha256=FAILED_MANIFEST,
                    summary_sha256=FAILED_SUMMARY) or
                result.get('passed') is not False or
                result.get('reason') !=
                    'saved nominal route differs from native replay' or
                study.summary['charged']['native_calls'] != 450_000 or
                study.summary['total'] != study.summary['completed'] or
                study.summary['total'] != 1):
            raise ValueError('exact preserved technical failure required')
        return True
    finally:
        study.close()


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .studies.qualification import request

    env = environment()
    if env['numerical_environment'] != numerical_environment(workers=1, threads=1):
        raise ValueError('guarded one-thread qualification required')
    return request(Path(root).resolve(), sources=sources(root), environment=env,
                   output=REQUEST, report=REPORT)


def prepare(root, *, qualification=None):
    if qualification is None:
        raise ValueError('fresh source-bound qualification required')
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root = Path(root).resolve()
    base_path = safe_path(root, 'data/'+ID+'-inputs')
    if base_path.exists() or safe_path(root, 'data/'+ID).exists():
        raise ValueError('fresh corrected study identity required')
    env = environment()
    if env['numerical_environment'] != numerical_environment(workers=1, threads=1):
        raise ValueError('guarded one-thread allocation required')
    request, report = checked(root, qualification, sources=sources(root),
        environment=env, required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    verify_failed_parent(root)
    staged = base.parent_inputs(root)
    staged.update({'qualification-environment': encoded(env),
                   'qualification-request': request,
                   'qualification-report': report})
    if set(staged) != set(base.INPUT_KEYS):
        raise ValueError('same exact early-only input set required')
    base_path.mkdir(parents=True)
    inputs = {}
    for number, key in enumerate(base.INPUT_KEYS):
        path = base_path/f'input-{number:03d}'
        atomic(path, staged[key])
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE,
        adapter='analysis/lll/esa_conditional_cross_point_v2_study.py',
        sources=sources(root), inputs=inputs, tasks=tasks(),
        workers=1, threads=1, maximum_wall_s=3600.)
    atomic(base_path/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=1, allocation=manifest['allocation'])


def evaluate(task, context):
    return base.evaluate(task, context, scope=SCOPE)
