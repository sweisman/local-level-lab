# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify sealed proposal/support reservations without numerical execution."""
import hashlib
import json
from pathlib import Path


def check_case(root,record,*,steps,maximum_proposals,maximum_supports):
    root=Path(root).resolve();result=record['result'];artifacts=record['artifacts']
    if (type(maximum_proposals) is not int or type(maximum_supports) is not int
            or min(maximum_proposals,maximum_supports)<0 or result.get('passed') is not True):
        raise ValueError('passing case and finite nonnegative allowances required')
    names=sorted(n for n in artifacts if Path(n).name.startswith('reservation-'))
    if len(names)!=len(steps):raise ValueError('missing or extra reservation event')
    proposals=supports=0
    for ordinal,(name,step) in enumerate(zip(names,steps,strict=True),1):
        if (Path(name).name!=f'reservation-{ordinal:02d}.json' or len(step)!=2
                or any(type(v) is not int or v<0 for v in step)):
            raise ValueError('complete ordered reservation protocol required')
        path=(root/name).resolve()
        if not path.is_relative_to(root) or not path.is_file():raise ValueError('owned reservation artifact required')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=artifacts[name]:raise ValueError('reservation hash changed')
        counters=json.loads(raw);proposals+=step[0];supports+=step[1]
        if proposals>maximum_proposals or supports>maximum_supports:raise ValueError('reservation allowance exceeded')
        if (set(counters)!={'lp_proposals','exact_supports'}
                or any(type(v) is not int for v in counters.values())
                or counters['lp_proposals']!=proposals or counters['exact_supports']!=supports):
            raise ValueError('charged reservation sequence changed')
    if result.get('lp_proposals_reserved')!=proposals or result.get('exact_supports_reserved')!=supports:
        raise ValueError('result does not reconcile with charged reservations')
    return dict(identity=result['identity'],reservation_events=len(names),lp_proposals=proposals,
        exact_supports=supports,passed=True)
