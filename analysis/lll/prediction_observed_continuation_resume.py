# SPDX-License-Identifier: AGPL-3.0-or-later
"""Idempotent, evidence-checked resume for the finite ESA development task."""

import argparse
import json
from pathlib import Path


def resume(root):
    from . import ilvis0_control_shards as runner
    from .prediction_observed_continuation_study import IDENTITY, task
    from .studies.closed import ClosedStudy
    from .studies.recovery import inspect
    from .studies.task_resume import (
        close_original, prepare_campaign, resume_campaign)
    from .studies.validation_resume import _other_threads

    root = Path(root).resolve()
    parent_name = 'data/'+IDENTITY
    parent = root/parent_name
    output = root/'data'/(IDENTITY+'-recovery')
    qualification = ('docs/prediction-observed-development/qualification/'
                     'continuation-recovery-request.json')
    if output.exists():
        return resume_campaign(root, output)
    if not parent.is_dir():
        raise ValueError('prepared frozen observed continuation required')
    already_closed = (parent/'completion.json').exists()
    if already_closed:
        closed = ClosedStudy(root, parent_name)
        try:
            if closed.manifest['tasks'][0]['identity'] != task(smoke=False)['identity']:
                raise ValueError('changed observed continuation identity')
            if closed.completion['state'] == 'complete':
                return dict(state='complete', completed=closed.summary['completed'],
                            passed=closed.summary['passed'], new_starts=0)
            if (closed.completion['state'] != 'terminal' or
                    closed.rows[task(smoke=False)['identity']]['status'] != 'interrupted'):
                return dict(state='terminal_completed_failure',
                            completed=closed.summary['completed'], new_starts=0)
        finally:
            closed.close()
    else:
        advice = inspect(root, parent_name)
        if advice['state'] == 'owned':
            return dict(state='owned', new_starts=0,
                        owned_lease=advice['owned_lease'])
        manifest = runner.verify(parent)
        if (len(manifest['tasks']) != 1 or
                manifest['tasks'][0]['identity'] != task(smoke=False)['identity'] or
                manifest['allocation']['workers'] != 1 or
                manifest['allocation']['threads'] != 1):
            raise ValueError('unchanged one-task frozen continuation required')
        if advice['state'] == 'uncharged_work_available' and not advice['interrupted_identities']:
            if runner.merge(parent)['charged_identities'] != 0:
                raise ValueError('uncharged status conflicts with journal')
            return runner.launch(parent, reserved_threads=_other_threads(root, 1))
        if advice['state'] not in ('no_uncharged_work', 'deadline_exhausted'):
            raise ValueError('recovery state requires manual diagnosis: '+advice['state'])
        close_original(root, parent_name, qualification_request=qualification)
        closed = ClosedStudy(root, parent_name)
        try:
            if closed.completion['state'] == 'complete':
                return dict(state='complete', completed=1,
                            passed=closed.summary['passed'], new_starts=0)
            row = closed.rows[task(smoke=False)['identity']]
            if row['status'] != 'interrupted':
                return dict(state='terminal_completed_failure',
                            completed=closed.summary['completed'], new_starts=0)
        finally:
            closed.close()
    prepare_campaign(
        root, parent_name, output,
        qualification_request=qualification,
        max_attempts_per_task=2, max_technical_interruptions=2,
        maximum_wall_s=14_400, minimum_free_bytes=20*1024**3,
        smoke_task_count=0)
    return resume_campaign(root, output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    print(json.dumps(resume(args.root), sort_keys=True))


if __name__ == '__main__':
    main()
