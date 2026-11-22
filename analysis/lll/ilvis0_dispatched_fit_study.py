# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated fit comparison for model-declared tangent selection."""

from pathlib import Path


SCOPE = 'generated model-declared paired tangent fits; no observed or protected inputs'
PARENT = ('data/hybrid-paired-training-20261110',
          '98809b0d3c25647b59741cc36141cd0eb1c419174268decad11c2644de014848',
          '5d8b2f41448591120db2152ea84d80282817ca0a78080e96cd336b2a62156af8')


def recipe():
    from lll.ilvis0_hybrid_fit_study import recipe as base
    return dict(base(), version='model-declared-paired-fit-v1')


def tasks(settings=None):
    from lll.ilvis0_hybrid_fit_study import tasks as original
    return original(recipe() if settings is None else settings)


def parent_proof():
    return {'short_paired_fit': dict(manifest_sha256=PARENT[1],
                                     summary_sha256=PARENT[2],
                                     six_cases_passed=True)}


def qualification_sources(root):
    from lll.ilvis0_hybrid_fit_study import qualification_sources as prior
    from lll.studies.dependencies import source_closure
    from lll.studies.task_resume import qualification_sources as recovery_sources
    return sorted(set(prior(root)) | set(source_closure(root, [
        'analysis/lll/ilvis0_paired_fit_runtime.py',
        'analysis/lll/ilvis0_tangent_dispatch.py',
        'analysis/lll/ilvis0_dispatched_fit_study.py',
        'analysis/tests/test_ilvis0_tangent_dispatch.py',
        'analysis/tests/test_ilvis0_dispatched_fit_study.py',
        'docs/mixed-tangent-hybrid/MODEL_DISPATCH_FIT_PLAN.md',
        'analysis/tests/test_task_resume.py',
        *recovery_sources(root)])))


def required_tests():
    from lll.ilvis0_hybrid_fit_study import required_tests as prior
    from lll.studies.task_resume import REQUIRED_TESTS as recovery_tests
    return prior() + (
        'test_paired_runner_loads_declared_candidate_without_changing_reference',
        'test_model_dispatch_preserves_generated_fit_and_forecast[sphere_rotating-selective]',
        'test_model_dispatch_preserves_generated_fit_and_forecast[flat_still-wide]',
        'test_dispatch_study_keeps_six_bounded_generated_pairs',
        'test_dispatch_adapter_loads_from_frozen_file',
        'test_dispatch_study_refuses_preparation_without_qualification',
        'test_dispatch_study_requires_reboot_recovery_evidence',
    ) + recovery_tests


def prepare(root, *, qualification, identity='model-declared-paired-fit-20261115-v2'):
    if qualification is None:
        raise ValueError('source-bound qualification required before preparation')
    from lll import ilvis0_paired_fit_runtime as runtime
    from lll.studies.closed import ClosedStudy

    root = Path(root).resolve()
    parent = ClosedStudy(root, PARENT[0])
    try:
        if (len(parent.rows) != 6 or
                parent.completion['manifest_sha256'] != PARENT[1] or
                parent.completion['summary_sha256'] != PARENT[2] or
                not all(parent.envelope(name)['result']['passed']
                        for name in parent.tasks)):
            raise ValueError('complete passing short paired-fit parent required')
    finally:
        parent.close()
    return runtime.prepare(
        root, qualification=qualification, identity=identity,
        recipe=recipe, scope=SCOPE, sources=qualification_sources(root),
        required_tests=required_tests(), parent_proof=parent_proof(),
        adapter='analysis/lll/ilvis0_dispatched_fit_study.py', tasks=tasks)


def evaluate(task, context):
    from lll import ilvis0_paired_fit_runtime as runtime
    from lll.ilvis0_hybrid_fit_study import construction_limits, pair
    from lll.ilvis0_tangent_dispatch import load_for_model

    return runtime.evaluate(
        task, context, recipe=recipe, scope=SCOPE,
        parent_proof=parent_proof(), tasks=tasks,
        construction_limits=construction_limits, pair=pair,
        candidate_loader=load_for_model)


def inspect(root, prefix='data/model-declared-paired-fit-20261115-v2'):
    from lll import ilvis0_paired_fit_runtime as runtime
    from lll.ilvis0_hybrid_fit_study import construction_limits
    from lll.ilvis0_tangent_dispatch import method_for_model, VERSION
    from lll.studies.closed import ClosedStudy

    report = runtime.inspect(
        root, prefix, recipe=recipe, scope=SCOPE,
        parent_proof=parent_proof(), tasks=tasks,
        construction_limits=construction_limits)
    study = ClosedStudy(root, prefix)
    try:
        choices = []
        for task in tasks():
            identity = task['identity']
            if identity not in study.rows:
                continue
            reference = study.artifact(identity, 'wide-compilation.json')['tangent']
            candidate = study.artifact(identity, 'hybrid-compilation.json')['tangent']
            model = task['payload']['model']
            method = method_for_model(model)
            if (reference.get('dispatch_method') is not None or
                    candidate.get('dispatch_version') != VERSION or
                    candidate.get('dispatch_model') != model or
                    candidate.get('dispatch_method') != method):
                raise ValueError('saved model-declared tangent choice differs')
            choices.append(dict(identity=identity, model=model, method=method))
        report['dispatch_choices'] = choices
        report['dispatch_choices_verified'] = len(choices) == len(tasks())
        report['qualified'] = report['qualified'] and report['dispatch_choices_verified']
        return report
    finally:
        study.close()
