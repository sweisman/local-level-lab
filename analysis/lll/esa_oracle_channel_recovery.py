# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reboot-safe finite entry point for four generated channel controls."""

import argparse
import json
from pathlib import Path

from .esa_study_recovery import (PolicySpec,freeze,request_qualification,
                                 resume,verify_policy)
from .esa_oracle_channel_study import ID,SCOPE,DIRECTORY


SPEC=PolicySpec(
    parent='data/'+ID,continuation='data/'+ID+'-continuation',
    policy=DIRECTORY+'oracle-channel-recovery-policy.json',
    request=DIRECTORY+'oracle-channel-recovery-request.json',
    report=DIRECTORY+'oracle-channel-recovery-tests.xml',
    wrapper='analysis/lll/esa_oracle_channel_recovery.py',
    scope=SCOPE,task_count=4,workers=2,maximum_wall_s=3600)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','freeze','verify','resume'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv);root=Path(args.root).resolve()
    result=(request_qualification(root,SPEC) if args.action=='request' else
            freeze(root,SPEC) if args.action=='freeze' else
            verify_policy(root,SPEC) if args.action=='verify' else
            resume(root,SPEC))
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
