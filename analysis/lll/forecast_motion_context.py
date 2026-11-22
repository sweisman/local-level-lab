# SPDX-License-Identifier: AGPL-3.0-or-later
"""Observable motion and receiver-quality summaries for the ESA score blocks."""

import argparse
from contextlib import closing
import gzip
import io
import json
from pathlib import Path


FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_FORECAST_MOTION_PLAN.md'
FREEZE = FOLDER+'esa-forecast-motion-freeze.json'
RESULT = FOLDER+'esa-forecast-motion-result.json'
EARLIER_SHA = '26f565650b0e6d052c9c25f7fcfa940ac601c0a0dd65370493d072b4857a9972'
LATER_SHA = 'c6be5d40ed9cd9092c9b1f16e441dd31a28d6306d1d7a5bc908c6042e7e792ea'


def receiver_motion(times, velocity):
    import numpy as np

    times, velocity = np.asarray(times,float), np.asarray(velocity,float)
    if (times.ndim != 1 or len(times) < 2 or velocity.shape != (len(times),3)
            or np.any(np.diff(times)<=0) or not np.isfinite(times).all()
            or not np.isfinite(velocity).all() or np.any(np.linalg.norm(velocity[:,:2],axis=1)==0)):
        raise ValueError('aligned ordered receiver velocity and times required')
    course = np.unwrap(np.arctan2(velocity[:,1], velocity[:,0]))
    accel = np.diff(velocity,axis=0)/np.diff(times)[:,None]
    return dict(net_course_change_deg=float(np.rad2deg(course[-1]-course[0])),
        total_course_change_deg=float(np.rad2deg(np.sum(np.abs(np.diff(course))))),
        mean_speed_mps=float(np.mean(np.linalg.norm(velocity[:,:2],axis=1))),
        horizontal_acceleration_rms_m_s2=float(np.sqrt(np.mean(np.sum(accel[:,:2]**2,axis=1)))),
        mean_up_velocity_mps=float(np.mean(velocity[:,2])))


def inertial_motion(dt, angle, delta_velocity):
    import numpy as np

    dt, angle, delta_velocity = (np.asarray(v,float) for v in (dt,angle,delta_velocity))
    if (dt.ndim != 1 or not len(dt) or angle.shape != (len(dt),3)
            or delta_velocity.shape != angle.shape or np.any(dt<=0)
            or any(not np.isfinite(v).all() for v in (dt,angle,delta_velocity))):
        raise ValueError('complete finite, timed inertial increments required')
    rate = np.linalg.norm(angle,axis=1)/dt
    force = np.linalg.norm(delta_velocity,axis=1)/dt
    mean = np.average(force,weights=dt)
    return dict(angular_rate_rms_deg_s=float(np.rad2deg(np.sqrt(np.average(rate**2,weights=dt)))),
        specific_force_magnitude_sd_m_s2=float(np.sqrt(np.average((force-mean)**2,weights=dt))))


def context(study, cut, receiver, data, score):
    import numpy as np
    from .esa_native_rolling_transfer import matched_window
    from .studies.artifacts import digest, encoded

    times = np.asarray(study.input(f'{cut}-forecast_times'))
    origin = study.input(f'{cut}-saved-input-binding')['time_origin_s']
    training = json.loads(gzip.decompress(study.input(f'{cut}-training',raw=True)))
    held = matched_window(receiver, training, times, origin=origin)
    if len(held)!=120 or digest(encoded(held))!=score['held_receiver_sha256']:
        raise ValueError('same archived 120 scored epochs required')
    with np.load(io.BytesIO(study.input(f'{cut}-interval',raw=True)),allow_pickle=False) as original:
        dt, angle, dv = (original[name] for name in ('dt','theta','dv'))
    ends = np.cumsum(dt)
    if ends[-1]<times[-1]:
        raise ValueError('inertial packets do not cover last fixed query')
    output = []
    for index in range(4):
        start, stop = index*30, (index+1)*30
        rows = held[start:stop]
        prefix = (training[-1] if index==0 else held[start-1])
        movement = [prefix, *rows]
        v = [[r['north_mps'],r['east_mps'],r['up_mps']] for r in movement]
        block = receiver_motion(times[cut+start-1:cut+stop],v)
        segment = slice(int(np.searchsorted(ends,times[cut+start-1],side='right')),
                        int(np.searchsorted(ends,times[cut+stop-1],side='right')))
        block.update(inertial_motion(dt[segment],angle[segment],dv[segment]))
        block.update(block=index+1, innovation_east_energy_share=
                       data['innovations']['block_energy_shares'][index][1],
            position_east_energy_share=data['physical_errors']['block_energy_shares'][index][1],
            median_pdop=float(np.median([r['pdop'] for r in rows])),
            median_satellites=float(np.median([r['satellites'] for r in rows])),
            median_reported_east_sd_m=float(np.median(np.sqrt(
                       [r['position_variance_m2'][1] for r in rows]))))
        output.append(block)
    return output


def run(root, action):
    from . import esa_innovation_transfer as innovations
    from . import esa_native_rolling_transfer as prior
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure

    with closing(ClosedStudy(root,'data/'+prior.ID)) as study:
        if study.completion['manifest_sha256']!=innovations.SOURCE_SHA or study.completion['state']!='complete':
            raise ValueError('exact original two-cut replay required')
        current = Path(__file__).relative_to(root).as_posix()
        frozen = encoded(dict(study_completion=study.completion, earlier=EARLIER_SHA, later=LATER_SHA,
            sources={name:digest((root/name).read_bytes()) for name in source_closure(
                root,(current,PLAN,'analysis/tests/test_forecast_motion_context.py'))},
            environment=runtime_environment(), blocks_per_cut=4, rows_per_block=30,
            protected_reads=0, optimizer_starts=0, native_calls=0))
        if action=='freeze':
            _write_equal(root/FREEZE,frozen)
            return dict(freeze_sha256=digest(frozen))
        if (root/FREEZE).read_bytes()!=frozen:
            raise ValueError('frozen motion checks changed')
        distinct = [(200,prior.EARLIER_REPORT,innovations.EARLY,EARLIER_SHA,innovations.EARLY_SCORE_SHA),
                    (400,prior.REPORT,innovations.RESULT,LATER_SHA,innovations.LATE_SCORE_SHA)]
        output = {}
        for cut,score_path,diagnosis,expected,score_hash in distinct:
            raw = (root/diagnosis).read_bytes()
            score = (root/score_path).read_bytes()
            if digest(raw)!=expected or digest(score)!=score_hash:
                raise ValueError('original sealed motion and score boundaries required')
            if cut==200:
                receiver=json.loads(gzip.decompress(study.input('400-training',raw=True)))
            else:
                with closing(ClosedStudy(root,prior.LATER_SOURCE,store=study.store)) as parent:
                    if parent.completion['manifest_sha256']!=prior.LATER_SOURCE_SHA:
                        raise ValueError('exact development scoring receiver source required')
                    receiver=json.loads(gzip.decompress(parent.input('training',raw=True)))
            output[str(cut)]=context(study,cut,receiver,json.loads(raw)['details']['increment'],json.loads(score))
    report=encoded(dict(freeze_sha256=digest(frozen),windows=output,
        protected_reads=0,optimizer_starts=0,native_calls=0,scientific_decision='abstain'))
    _write_equal(root/RESULT,report)
    return dict(sha256=digest(report),blocks=sum(len(window) for window in output.values()))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('freeze','replay'))
    print(json.dumps(run(Path.cwd(),parser.parse_args().action),sort_keys=True))
