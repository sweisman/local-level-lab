# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reusable, hash-bound task recovery policy frozen before a study starts.

The original allowance and any continuation have separate charge ledgers.
Completed numerical failures are sealed, never retried. The generic task
continuation engine supplies the reboot/worker-interruption checks.
"""

import json
from pathlib import Path

from . import task_resume
from .artifacts import atomic, digest, encoded
from .qualification import checked, request
from .. import ilvis0_control_shards as runner


VERSION = 'original-task-recovery-policy-v1'
SELF = 'analysis/lll/studies/original_recovery_policy.py'


def _relative(root, name):
    path = Path(name)
    if path.is_absolute() or not (root/path).resolve().is_relative_to(root):
        raise ValueError('project-relative recovery path required')
    return path.as_posix()


def request_qualification(root, *, output, report):
    root = Path(root).resolve()
    return request(root, sources=task_resume.qualification_sources(root),
                   environment=runner.runtime_environment(),
                   output=output, report=report)


def _qualification(root, qualification_request):
    raw, report = checked(
        root, qualification_request,
        sources=task_resume.qualification_sources(root),
        environment=runner.runtime_environment(),
        required_tests=task_resume.REQUIRED_TESTS,
        minimum_tests=len(task_resume.REQUIRED_TESTS))
    return digest(raw), digest(report)


def freeze(root, *, parent, policy_path, continuation,
           qualification_request, max_attempts_per_task=2,
           max_technical_interruptions=2, maximum_wall_s=7200,
           minimum_free_bytes=10*1024**3):
    root = Path(root).resolve()
    parent = _relative(root, parent)
    continuation = _relative(root, continuation)
    policy_path = _relative(root, policy_path)
    qualification_request = _relative(root, qualification_request)
    if (parent == continuation or parent == policy_path or
            (root/policy_path).exists() or
            (root/(policy_path+'.freeze.json')).exists() or
            (root/parent/'start.json').exists() or
            type(max_attempts_per_task) is not int or
            max_attempts_per_task < 2 or
            type(max_technical_interruptions) is not int or
            max_technical_interruptions < 0 or
            type(maximum_wall_s) is not int or maximum_wall_s <= 0 or
            type(minimum_free_bytes) is not int or minimum_free_bytes < 0):
        raise ValueError('fresh finite recovery policy required before launch')
    manifest = runner.verify(root/parent)
    allocation = manifest['allocation']
    if (not manifest['tasks'] or manifest['accounting_format'] != 'sqlite-v1' or
            allocation['threads'] != 1 or allocation['workers'] > 4 or
            manifest['environment'] != runner.runtime_environment()):
        raise ValueError('prepared recoverable numerical parent required')
    request_sha, report_sha = _qualification(root, qualification_request)
    policy = dict(version=VERSION, parent=parent,
                  parent_manifest_sha256=runner._sha(root/parent/'manifest.json'),
                  recovery_source_sha256=runner._sha(root/SELF),
                  qualification_request=qualification_request,
                  qualification_request_sha256=request_sha,
                  qualification_report_sha256=report_sha,
                  continuation=continuation,
                  max_attempts_per_task=max_attempts_per_task,
                  max_technical_interruptions=max_technical_interruptions,
                  maximum_wall_s=maximum_wall_s,
                  minimum_free_bytes=minimum_free_bytes,
                  completed_numerical_failures_retried=False)
    atomic(root/policy_path, encoded(policy))
    atomic(root/(policy_path+'.freeze.json'), encoded(dict(
        version=VERSION, policy_sha256=digest(encoded(policy)))))
    return dict(state='frozen', parent=parent,
                policy_sha256=digest(encoded(policy)))


def _policy(root, policy_path):
    policy_path = _relative(root, policy_path)
    raw = (root/policy_path).read_bytes()
    receipt = json.loads((root/(policy_path+'.freeze.json')).read_bytes())
    if (receipt.get('version') != VERSION or
            receipt.get('policy_sha256') != digest(raw)):
        raise ValueError('frozen task recovery policy changed')
    policy = json.loads(raw)
    request_sha, report_sha = _qualification(
        root, _relative(root, policy['qualification_request']))
    parent = _relative(root, policy['parent'])
    continuation = _relative(root, policy['continuation'])
    if (policy.get('version') != VERSION or
            policy.get('parent_manifest_sha256') !=
                runner._sha(root/parent/'manifest.json') or
            policy.get('recovery_source_sha256') != runner._sha(root/SELF) or
            policy.get('qualification_request_sha256') != request_sha or
            policy.get('qualification_report_sha256') != report_sha or
            policy.get('completed_numerical_failures_retried') is not False or
            type(policy.get('max_attempts_per_task')) is not int or
            policy['max_attempts_per_task'] < 2 or
            type(policy.get('max_technical_interruptions')) is not int or
            policy['max_technical_interruptions'] < 0 or
            type(policy.get('maximum_wall_s')) is not int or
            policy['maximum_wall_s'] <= 0 or
            type(policy.get('minimum_free_bytes')) is not int or
            policy['minimum_free_bytes'] < 0 or
            parent == continuation):
        raise ValueError('frozen task recovery policy changed')
    return policy


def resume(root, policy_path):
    from .recovery import inspect
    from .validation_resume import _other_threads

    root = Path(root).resolve()
    policy = _policy(root, policy_path)
    parent = policy['parent']
    path = root/parent
    manifest = runner.verify(path)
    if manifest['environment'] != runner.runtime_environment():
        raise ValueError('original numerical environment changed')
    if not (path/'completion.json').exists():
        advice = inspect(root, parent)
        if advice['state'] == 'owned':
            return dict(state='owned', parent=parent)
        if (advice['state'] == 'uncharged_work_available' and
                not advice['interrupted_identities']):
            runner.launch(path, reserved_threads=_other_threads(
                root, manifest['allocation']['workers']))
        else:
            if advice['state'] not in ('uncharged_work_available',
                                      'no_uncharged_work',
                                      'deadline_exhausted'):
                raise ValueError('original study cannot safely resume')
            task_resume.close_original(
                root, parent,
                qualification_request=policy['qualification_request'])
    summary = runner.verify_completion(path)
    if summary['state'] == 'complete':
        return dict(state='complete', parent=parent,
                    completed=summary['completed'], passed=summary['passed'])
    if summary['state'] != 'terminal':
        raise ValueError('verified original completion required')
    merged = runner.merge(path)
    if (merged['completed'] == merged['total'] and
            all(row['status'] == 'complete' for row in merged['results'])):
        return dict(state='terminal_numerical', parent=parent,
                    completed=merged['completed'])
    continuation = root/policy['continuation']
    if not continuation.exists():
        task_resume.prepare_campaign(
            root, parent, continuation,
            qualification_request=policy['qualification_request'],
            max_attempts_per_task=policy['max_attempts_per_task'],
            max_technical_interruptions=policy['max_technical_interruptions'],
            maximum_wall_s=policy['maximum_wall_s'],
            minimum_free_bytes=policy['minimum_free_bytes'])
    return task_resume.resume_campaign(root, continuation, launch=True)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    requested = actions.add_parser('request')
    requested.add_argument('--output', required=True)
    requested.add_argument('--report', required=True)
    frozen = actions.add_parser('freeze')
    frozen.add_argument('--parent', required=True)
    frozen.add_argument('--policy', required=True)
    frozen.add_argument('--continuation', required=True)
    frozen.add_argument('--qualification-request', required=True)
    frozen.add_argument('--maximum-wall-s', required=True, type=int)
    frozen.add_argument('--minimum-free-bytes', required=True, type=int)
    resumed = actions.add_parser('resume')
    resumed.add_argument('--policy', required=True)
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.action == 'request':
        result = request_qualification(root, output=args.output,
                                       report=args.report)
    elif args.action == 'freeze':
        result = freeze(root, parent=args.parent, policy_path=args.policy,
                        continuation=args.continuation,
                        qualification_request=args.qualification_request,
                        maximum_wall_s=args.maximum_wall_s,
                        minimum_free_bytes=args.minimum_free_bytes)
    else:
        result = resume(root, args.policy)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
