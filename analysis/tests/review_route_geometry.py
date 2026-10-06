# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cheap assumed-route screening of observable criteria; no flights, fits or SVDs."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis'))

import numpy as np
from lll.policy import heading_diversity
from lll.trajectory import TrackReplay,smooth_track_spec


def review():
    core=ROOT/'docs/core-pipeline-20261006'
    proposal=json.loads((core/'proposal.json').read_text())
    cases=[]
    for item in proposal['config']['replay_inputs']:
        if item['mode']!='simulated_high_rate': continue
        path=Path(item['path'])
        if path.parent!=Path('trajectories') or path.suffix!='.json':
            raise ValueError('only explicit documented trajectory inputs are allowed')
        original=json.loads((core/path).read_text())
        spec=smooth_track_spec(original); replay=TrackReplay(spec)
        t=np.arange(0.,replay.duration,1.)
        values=replay.sample(t)
        keep=replay.support(t)&np.isfinite(values['psi'])
        angles=np.sort(np.degrees(values['psi'][keep])%360)
        span=float(360-np.max(np.diff(np.r_[angles,angles[0]+360])))
        heading=heading_diversity({'psi':values['psi'][keep],'dt':np.ones(keep.sum())})
        cases.append(dict(track_id=spec['track_id'],curve_model=spec['curve_model'],
            trajectory_hash=spec['trajectory_hash'],duration_minutes=replay.duration/60,
            optimistic_supported_minutes=float(keep.sum()/60),
            sampled_assumed_heading_span_deg=span,optimistic_heading_diversity=heading,
            heading_span_below_required_separation=span<heading['min_separation_deg']))
    return dict(scope='geometry-only one-second sampling, optimistic retention; no IMU or complete preprocessing',
        cases=cases,authorized_attempts=0,
        interpretation='All supported seconds counted before motion/accelerometer/watchdog/bin losses. A pass is not eligibility or identifiability; narrow sampled heading spans flag poor proposed windows. No gate, threshold or observations changed.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=review()
    with args.output.open('x') as out:
        out.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({**result,'cases':[{k:v for k,v in c.items() if k!='optimistic_heading_diversity'}
                                     for c in result['cases']]},allow_nan=False))
