# SPDX-License-Identifier: AGPL-3.0-or-later
"""Idempotent, finite recovery for the ESA 400/120 development fit."""

import json
from pathlib import Path

from . import ilvis0_control_shards as runner
from .esa_rolling_origin_400_study import ID,SCOPE
from .studies import task_resume
from .studies.artifacts import atomic,digest,encoded
from .studies.qualification import checked,request

SELF='analysis/lll/esa_rolling_origin_400_recovery.py'
PARENT='data/'+ID
CONTINUATION=PARENT+'-continuation'
POLICY=('docs/prediction-observed-development/qualification/'
        'rolling-origin-400-recovery-policy.json')
REQUEST=('docs/prediction-observed-development/qualification/'
         'rolling-origin-400-recovery-request.json')
REPORT=('docs/prediction-observed-development/qualification/'
        'rolling-origin-400-recovery-tests.xml')
VERSION='esa-rolling-origin-400-recovery-v1'


def request_qualification(root):
    root=Path(root).resolve()
    return request(root,sources=task_resume.qualification_sources(root),
                   environment=runner.runtime_environment(),
                   output=REQUEST,report=REPORT)


def _qualification(root):
    raw,report=checked(root,REQUEST,
        sources=task_resume.qualification_sources(root),
        environment=runner.runtime_environment(),
        required_tests=task_resume.REQUIRED_TESTS,
        minimum_tests=len(task_resume.REQUIRED_TESTS))
    return digest(raw),digest(report)


def freeze(root):
    root=Path(root).resolve();target=root/POLICY
    if target.exists() or (root/PARENT/'start.json').exists():
        raise ValueError('fresh recovery policy required before first launch')
    manifest=runner.verify(root/PARENT)
    if (manifest['scope']!=SCOPE or len(manifest['tasks'])!=2 or
            manifest['accounting_format']!='sqlite-v1' or
            manifest['allocation']['workers']!=2 or
            manifest['allocation']['threads']!=1):
        raise ValueError('prepared recoverable two-fit parent required')
    request_sha,report_sha=_qualification(root)
    policy=dict(version=VERSION,parent=PARENT,
        parent_manifest_sha256=runner._sha(root/PARENT/'manifest.json'),
        recovery_source_sha256=runner._sha(root/SELF),
        qualification_request_sha256=request_sha,
        qualification_report_sha256=report_sha,
        qualification_request=REQUEST,
        max_attempts_per_task=2,max_technical_interruptions=2,
        maximum_wall_s=14400,minimum_free_bytes=10*1024**3,
        continuation=CONTINUATION,
        completed_numerical_failures_retried=False)
    atomic(target,encoded(policy))
    return dict(state='frozen',parent=PARENT,
                policy_sha256=digest(encoded(policy)))


def _policy(root):
    policy=json.loads((root/POLICY).read_bytes())
    request_sha,report_sha=_qualification(root)
    if (policy.get('version')!=VERSION or policy.get('parent')!=PARENT or
            policy.get('continuation')!=CONTINUATION or
            policy.get('parent_manifest_sha256')!=runner._sha(
                root/PARENT/'manifest.json') or
            policy.get('recovery_source_sha256')!=runner._sha(root/SELF) or
            policy.get('qualification_request_sha256')!=request_sha or
            policy.get('qualification_report_sha256')!=report_sha or
            policy.get('qualification_request')!=REQUEST or
            policy.get('max_attempts_per_task')!=2 or
            policy.get('max_technical_interruptions')!=2 or
            policy.get('maximum_wall_s')!=14400 or
            policy.get('minimum_free_bytes')!=10*1024**3 or
            policy.get('completed_numerical_failures_retried') is not False):
        raise ValueError('frozen rolling-origin recovery policy changed')
    return policy


def resume(root):
    from .studies.recovery import inspect
    from .studies.validation_resume import _other_threads

    root=Path(root).resolve();policy=_policy(root);path=root/PARENT
    manifest=runner.verify(path)
    if manifest['environment']!=runner.runtime_environment():
        raise ValueError('original numerical environment changed')
    if not (path/'completion.json').exists():
        advice=inspect(root,PARENT)
        if advice['state']=='owned':
            return dict(state='owned',parent=PARENT)
        if (advice['state']=='uncharged_work_available' and
                not advice['interrupted_identities']):
            runner.launch(path,reserved_threads=_other_threads(
                root,manifest['allocation']['workers']))
        else:
            if advice['state'] not in ('uncharged_work_available',
                                      'no_uncharged_work',
                                      'deadline_exhausted'):
                raise ValueError('original study not safe to close or resume')
            task_resume.close_original(root,PARENT,
                                       qualification_request=REQUEST)
    summary=runner.verify_completion(path)
    if summary['state']=='complete':
        return dict(state='complete',parent=PARENT,
                    completed=summary['completed'],passed=summary['passed'])
    if summary['state']!='terminal':
        raise ValueError('verified original completion required')
    merged=runner.merge(path)
    if (merged['completed']==merged['total'] and
            all(row['status']=='complete' for row in merged['results'])):
        return dict(state='terminal_numerical',parent=PARENT,
                    completed=merged['completed'])
    target=root/policy['continuation']
    if not target.exists():
        task_resume.prepare_campaign(root,PARENT,target,
            qualification_request=REQUEST,
            max_attempts_per_task=policy['max_attempts_per_task'],
            max_technical_interruptions=policy['max_technical_interruptions'],
            maximum_wall_s=policy['maximum_wall_s'],
            minimum_free_bytes=policy['minimum_free_bytes'])
    return task_resume.resume_campaign(root,target,launch=True)


def verify_policy(root):
    from .studies.recovery import inspect
    root=Path(root).resolve();policy=_policy(root)
    manifest=runner.verify(root/PARENT)
    if manifest['environment']!=runner.runtime_environment():
        raise ValueError('original numerical environment changed')
    advice=inspect(root,PARENT)
    return dict(state=advice['state'],parent=PARENT,
                parent_manifest_sha256=policy['parent_manifest_sha256'],
                continuation=CONTINUATION)


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','freeze','verify','resume'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv);root=Path(args.root).resolve()
    result=(request_qualification(root) if args.action=='request' else
            freeze(root) if args.action=='freeze' else
            verify_policy(root) if args.action=='verify' else resume(root))
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
