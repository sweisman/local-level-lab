# SPDX-License-Identifier: AGPL-3.0-or-later
"""Restore and continue only the untouched IMU21 task from the archived preflight."""

import argparse
from contextlib import closing
import json
from pathlib import Path
import time

from .studies import task_resume
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy
from .studies.source_versions import read_source
from .studies.task_continuation import plan_closed_parent


ARCHIVE = 'docs/ilvis0-matched-observed-preflight-runtime'
RECEIPT_SHA = '77d0ce69687dfde8ec155db415d3c8f9c6842a5b01620557f62952ddb26a386d'
MANIFEST = '4e48c0e5ac089d4cf79327d2f2efebde33fedb55d61bdf8d455f8eb14203488b'
SUMMARY = '6b40f5efcc675a980e096dd69b0c87e0f94429f73b057ee295d5dc993f80224d'
WORKSPACE = 'data/ilvis0-matched-unstarted-disc-recovery'
ORIGINAL = 'data/sealed-original'
CAMPAIGN = 'data/continuation'
QUALIFICATION = 'docs/prediction-group-transfer/observed-fixed-timing-recovery-request.json'
IDENTITY = '2791235ca0b11b1ef4386e21-flat_still'
WALL_S = 3900
MINIMUM_FREE_BYTES = 1024**3


def _write_equal(root, path, raw):
    target = safe_path(root, path)
    if not target.exists():
        atomic(target, raw)
    if target.read_bytes() != raw:
        raise ValueError('restored evidence differs: '+path)


def _plan(manifest, summary, completion):
    plan = plan_closed_parent(manifest, summary, completion)
    if (completion['manifest_sha256'] != MANIFEST or completion['summary_sha256'] != SUMMARY
            or plan['completed'] != 7 or plan['completed_failures'] != 1
            or plan['prior_interrupted_identities'] or plan['never_started'] != 1
            or [task['identity'] for task in plan['tasks']] != [IDENTITY]
            or plan['tasks'][0]['limits']['native_calls'] != 31):
        raise ValueError('only the single never-started IMU21 task can continue')
    return plan


def restore(root, workspace):
    workspace.mkdir(parents=True, exist_ok=True)
    with closing(ClosedStudy(root, ARCHIVE)) as study:
        plan = _plan(study.manifest, study.summary, study.completion)
        receipt = study.read('evidence-receipt.json', RECEIPT_SHA)
        hashes = receipt['artifacts']
        for name, sha in hashes.items():
            _write_equal(workspace, ORIGINAL+'/'+name, study.read(name, sha, raw=True))
        for source, sha in study.manifest['sources'].items():
            _write_equal(workspace, source, study.read('source-freeze/'+source, sha, raw=True))
        for key, record in study.manifest['inputs'].items():
            _write_equal(workspace, record['source'], study.input(key, raw=True))
        qualification = study.input('recovery')
        for source, sha in qualification['sources'].items():
            if source not in study.manifest['sources']:
                _write_equal(workspace, source, read_source(root, source, sha))
        _write_equal(workspace, QUALIFICATION, study.input('recovery', raw=True))
        _write_equal(workspace, qualification['report'], study.input('recovery_tests', raw=True))
        for shard in range(study.manifest['allocation']['workers']):
            _write_equal(workspace, f'{ORIGINAL}/shards/{shard:03d}/worker.lock', b'')
    status = workspace/'analysis/status.py'
    if not status.exists():
        status.symlink_to(root/'analysis/status.py')
    if status.resolve() != (root/'analysis/status.py').resolve():
        raise ValueError('use the canonical analysis status command')
    for path, raw in (('analysis/study-status.lock', b''), ('analysis/study-status.json', encoded(dict(studies=[])))):
        target = workspace/path
        if not target.exists():
            atomic(target, raw)
    return plan


def prepare(root):
    workspace = root/WORKSPACE
    plan = restore(root, workspace)
    campaign = workspace/CAMPAIGN
    if not campaign.exists():
        task_resume.prepare_campaign(workspace, ORIGINAL, campaign, qualification_request=QUALIFICATION,
            max_attempts_per_task=2, max_technical_interruptions=1, maximum_wall_s=WALL_S,
            minimum_free_bytes=MINIMUM_FREE_BYTES)
    advice = task_resume.resume_campaign(workspace, campaign, launch=False)
    stage = campaign/'stage-000'
    if not stage.is_dir() and advice.get('next_stage') == 0 and advice.get('next_stage_tasks') == 1:
        saved, policy, manifest = task_resume._frozen(workspace, campaign)
        fields = ('completed', 'completed_failures', 'prior_interrupted_identities',
                  'never_started', 'tasks', 'parent_manifest_sha256')
        if any(saved[key] != plan[key] for key in fields):
            raise ValueError('continuation contains a different task')
        clock = policy['deadline_unix']-time.time()-1
        if clock <= 0:
            raise ValueError('the frozen continuation window has ended')
        stage = task_resume._new_stage(workspace, campaign, 0, plan['tasks'], manifest, policy, clock)
        task_resume._register_stage(root, stage)
        advice = task_resume.resume_campaign(workspace, campaign, launch=False)
    return dict(advice, identity=IDENTITY, first_stage=stage.relative_to(root).as_posix(),
                original_completed=7, original_failed=1)


def resume(root):
    workspace = root/WORKSPACE
    campaign = workspace/CAMPAIGN
    if not (campaign/'stage-000/manifest.json').is_file():
        raise ValueError('prepare and verify the untouched task before running')
    for stage in sorted(campaign.glob('stage-*')):
        if (stage/'manifest.json').is_file():
            task_resume._register_stage(root, stage)
    outcome = task_resume.resume_campaign(workspace, campaign)
    for stage in sorted(campaign.glob('stage-*')):
        if (stage/'manifest.json').is_file():
            task_resume._register_stage(root, stage)
    return outcome


def check(root):
    workspace = root/WORKSPACE
    return task_resume.resume_campaign(workspace, workspace/CAMPAIGN, launch=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'check', 'resume'))
    args = parser.parse_args()
    result = {'prepare': prepare, 'check': check, 'resume': resume}[args.action](Path.cwd().resolve())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
