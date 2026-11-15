# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared finite, idempotent recovery for a source-frozen ESA study."""

from dataclasses import dataclass
import json
from pathlib import Path

from . import ilvis0_control_shards as runner
from .studies import task_resume
from .studies.artifacts import atomic, digest, encoded
from .studies.qualification import checked, request


SELF = 'analysis/lll/esa_study_recovery.py'
VERSION = 'esa-study-technical-recovery-v1'


@dataclass(frozen=True)
class PolicySpec:
    parent: str
    continuation: str
    policy: str
    request: str
    report: str
    wrapper: str
    scope: str
    task_count: int
    workers: int
    maximum_wall_s: int
    max_attempts_per_task: int = 2
    max_technical_interruptions: int = 2
    minimum_free_bytes: int = 10*1024**3


def _check_spec(spec):
    if (not isinstance(spec, PolicySpec) or
            not spec.parent.startswith('data/') or
            spec.continuation != spec.parent+'-continuation' or
            not spec.policy.startswith('docs/') or
            not spec.request.startswith('docs/') or
            not spec.report.startswith('docs/') or
            not spec.wrapper.startswith('analysis/lll/') or
            not spec.scope or spec.task_count < 1 or
            not 1 <= spec.workers <= 4 or
            spec.maximum_wall_s <= 0 or
            spec.max_attempts_per_task < 2 or
            spec.max_technical_interruptions < 0 or
            spec.minimum_free_bytes < 0):
        raise ValueError('complete finite ESA recovery policy required')
    return spec


def request_qualification(root, spec):
    spec = _check_spec(spec)
    root = Path(root).resolve()
    return request(root, sources=task_resume.qualification_sources(root),
                   environment=runner.runtime_environment(),
                   output=spec.request, report=spec.report)


def _qualification(root, spec):
    raw, report = checked(
        root, spec.request, sources=task_resume.qualification_sources(root),
        environment=runner.runtime_environment(),
        required_tests=task_resume.REQUIRED_TESTS,
        minimum_tests=len(task_resume.REQUIRED_TESTS))
    return digest(raw), digest(report)


def freeze(root, spec):
    spec = _check_spec(spec)
    root = Path(root).resolve()
    study = root/spec.parent
    target = root/spec.policy
    if target.exists() or (study/'start.json').exists():
        raise ValueError('fresh recovery policy required before first launch')
    manifest = runner.verify(study)
    if (manifest['scope'] != spec.scope or
            len(manifest['tasks']) != spec.task_count or
            manifest['accounting_format'] != 'sqlite-v1' or
            manifest['allocation']['workers'] != spec.workers or
            manifest['allocation']['threads'] != 1):
        raise ValueError('prepared matching recoverable parent required')
    request_sha, report_sha = _qualification(root, spec)
    policy = dict(version=VERSION, parent=spec.parent,
        continuation=spec.continuation,
        parent_manifest_sha256=runner._sha(study/'manifest.json'),
        shared_source_sha256=runner._sha(root/SELF),
        wrapper_source_sha256=runner._sha(root/spec.wrapper),
        qualification_request_sha256=request_sha,
        qualification_report_sha256=report_sha,
        qualification_request=spec.request,
        max_attempts_per_task=spec.max_attempts_per_task,
        max_technical_interruptions=spec.max_technical_interruptions,
        maximum_wall_s=spec.maximum_wall_s,
        minimum_free_bytes=spec.minimum_free_bytes,
        completed_numerical_failures_retried=False)
    atomic(target, encoded(policy))
    return dict(state='frozen', parent=spec.parent,
                policy_sha256=digest(encoded(policy)))


def _policy(root, spec):
    spec = _check_spec(spec)
    policy = json.loads((root/spec.policy).read_bytes())
    request_sha, report_sha = _qualification(root, spec)
    expected = dict(version=VERSION, parent=spec.parent,
        continuation=spec.continuation,
        parent_manifest_sha256=runner._sha(root/spec.parent/'manifest.json'),
        shared_source_sha256=runner._sha(root/SELF),
        wrapper_source_sha256=runner._sha(root/spec.wrapper),
        qualification_request_sha256=request_sha,
        qualification_report_sha256=report_sha,
        qualification_request=spec.request,
        max_attempts_per_task=spec.max_attempts_per_task,
        max_technical_interruptions=spec.max_technical_interruptions,
        maximum_wall_s=spec.maximum_wall_s,
        minimum_free_bytes=spec.minimum_free_bytes,
        completed_numerical_failures_retried=False)
    if policy != expected:
        raise ValueError('frozen ESA recovery policy changed')
    return policy


def verify_policy(root, spec):
    from .studies.recovery import inspect
    root = Path(root).resolve()
    policy = _policy(root, spec)
    manifest = runner.verify(root/spec.parent)
    if manifest['environment'] != runner.runtime_environment():
        raise ValueError('original numerical environment changed')
    advice = inspect(root, spec.parent)
    return dict(state=advice['state'], parent=spec.parent,
                parent_manifest_sha256=policy['parent_manifest_sha256'],
                continuation=spec.continuation)


def resume(root, spec):
    """Run only uncharged original work or separately charged recovery tasks."""
    from .studies.recovery import inspect
    from .studies.validation_resume import _other_threads

    root = Path(root).resolve()
    policy = _policy(root, spec)
    study = root/spec.parent
    manifest = runner.verify(study)
    if manifest['environment'] != runner.runtime_environment():
        raise ValueError('original numerical environment changed')
    if not (study/'completion.json').exists():
        advice = inspect(root, spec.parent)
        if advice['state'] == 'owned':
            return dict(state='owned', parent=spec.parent)
        if (advice['state'] == 'uncharged_work_available' and
                not advice['interrupted_identities']):
            runner.launch(study, reserved_threads=_other_threads(
                root, manifest['allocation']['workers']))
        else:
            if advice['state'] not in ('uncharged_work_available',
                                       'no_uncharged_work',
                                       'deadline_exhausted'):
                raise ValueError('original study not safe to close or resume')
            task_resume.close_original(root, spec.parent,
                                       qualification_request=spec.request)
    summary = runner.verify_completion(study)
    if summary['state'] == 'complete':
        return dict(state='complete', parent=spec.parent,
                    completed=summary['completed'], passed=summary['passed'])
    if summary['state'] != 'terminal':
        raise ValueError('verified original completion required')
    merged = runner.merge(study)
    if (merged['completed'] == merged['total'] and
            all(row['status'] == 'complete' for row in merged['results'])):
        return dict(state='terminal_numerical', parent=spec.parent,
                    completed=merged['completed'])
    target = root/policy['continuation']
    if not target.exists():
        task_resume.prepare_campaign(
            root, spec.parent, target,
            qualification_request=spec.request,
            max_attempts_per_task=policy['max_attempts_per_task'],
            max_technical_interruptions=policy['max_technical_interruptions'],
            maximum_wall_s=policy['maximum_wall_s'],
            minimum_free_bytes=policy['minimum_free_bytes'])
    return task_resume.resume_campaign(root, target, launch=True)
