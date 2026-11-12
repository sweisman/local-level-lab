# SPDX-License-Identifier: AGPL-3.0-or-later
"""Idempotent recovery entry point for the frozen independent-seed method check.

The shared study runtime verifies leases, source/input hashes, charges and
sealed results. This small wrapper chooses its existing recovery stages; it
does not change a scientific task or retry a sealed result.
"""

import argparse
import json
from pathlib import Path

from lll.studies.recovery import inspect
from lll.studies.task_resume import (close_original, prepare_campaign,
                                     resume_campaign)


ORIGINAL = 'data/bounded-nonlinear-independent-seeds-v2'
CONTINUATION = 'data/bounded-nonlinear-independent-seeds-v2-continuation'
QUALIFICATION = 'docs/bounded-calibration-prediction/qualification/recovery-request.json'
TOTAL = 48


def resume(project):
    """Return current ownership or continue only verified unfinished work."""
    project = Path(project).resolve()
    advice = inspect(project, ORIGINAL)
    state = advice['state']
    if state == 'owned':
        return {'state': 'owned', 'action': 'none'}
    if state == 'stop_requested':
        return {'state': 'stop_requested', 'action': 'none'}
    if state != 'closed':
        if state not in ('uncharged_work_available', 'no_uncharged_work',
                         'deadline_exhausted', 'cohort_unavailable'):
            raise ValueError('unrecognized original recovery state: ' + state)
        close_original(project, ORIGINAL, qualification_request=QUALIFICATION)
        advice = inspect(project, ORIGINAL)
        if advice['state'] != 'closed':
            raise ValueError('original study did not close')
    completed = advice['completed']
    if type(completed) is not int or not 0 <= completed <= TOTAL:
        raise ValueError('invalid original completion count')
    if completed == TOTAL:
        return {'state': 'original_complete', 'completed': TOTAL,
                'action': 'report'}
    output = project / CONTINUATION
    if not output.exists():
        prepare_campaign(project, ORIGINAL, output,
                         qualification_request=QUALIFICATION,
                         max_attempts_per_task=3,
                         max_technical_interruptions=24,
                         maximum_wall_s=18000,
                         minimum_free_bytes=5 * 1024**3)
    return resume_campaign(project, output, launch=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default='.')
    args = parser.parse_args(argv)
    print(json.dumps(resume(args.project), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
