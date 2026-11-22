# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound how ESA working sensor corrections can move the paired angles."""
import argparse
from contextlib import closing
from dataclasses import dataclass
import fcntl
import gzip
import io
import json
import math
import os
from pathlib import Path
import platform

from .compute_budget import environment
from .esa_doppler_force import CENTERS, DIRECTORY, FOLDER, MATRIX, MATRIX_SHA, WIDTHS
from .esa_doppler_force import matched_weights, rate_operator
from .esa_gyro_force_direction import angles, midpoint_attitudes
from .esa_matched_gyro_direction import EARLIER, EARLIER_SHA, REPORT as MATCHED
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

PLAN = FOLDER+'ESA_GYRO_DIRECTION_CALIBRATION_PLAN.md'
REPORT = FOLDER+'esa-gyro-direction-calibration-result.json'
MATCHED_SHA = 'fef1fdb49a1f1b3e7cd946cb391e7977145d6c3306675d4e2618235bae99f187'
TERMS = ('gyro_bias', 'gyro_gain', 'accel_bias', 'accel_gain')
BISECTION_STEPS = 32


@dataclass(frozen=True)
class Pair:
    earlier: slice
    later: slice
    earlier_weights: object
    later_weights: object
    earlier_norm: float
    later_norm: float


def angle_bounds(theta, force, dt, supports, limits):
    """Pair angle bounds for subtract-bias and divide-by-one-plus-gain corrections."""
    import numpy as np

    box = np.asarray(limits,float)
    if (box.shape != (4,3) or not np.isfinite(box).all()
            or np.any(box<0) or np.any(box[[1,3]]>=1)):
        raise ValueError('finite nonnegative per-axis limits and gains below one required')
    gyro_bias, gyro_gain, accel_bias, accel_gain = box
    angle_error = np.linalg.norm((abs(theta)*gyro_gain+dt[:,None]*gyro_bias)/(1.-gyro_gain),axis=1)
    force_error = np.linalg.norm((abs(force)*accel_gain+accel_bias)/(1.-accel_gain),axis=1)
    force_norm = np.linalg.norm(force,axis=1)
    prefix = np.r_[0.,np.cumsum(angle_error)]
    mid = prefix[:-1]+angle_error/2.
    output = []
    for pair in supports:
        anchor = min(pair.earlier.start,pair.later.start)
        endpoint = []
        for cut,weights,nominal in (
                (pair.earlier,pair.earlier_weights,pair.earlier_norm),
                (pair.later,pair.later_weights,pair.later_norm)):
            phase = np.minimum(math.pi,mid[cut]-prefix[anchor])
            error = float(weights@(force_error[cut]+2.*np.sin(phase/2.)*force_norm[cut]))
            # The angular cone from the origin to the vector error ball.
            endpoint.append(math.asin(error/nominal) if error<nominal else math.pi)
        output.append(min(math.pi,sum(endpoint)))
    return np.asarray(output)


def packet_inputs(matrix, end_time):
    import numpy as np

    origin = matrix.input('saved-input-binding')['time_origin_s']
    with np.load(io.BytesIO(matrix.input('interval',raw=True)),allow_pickle=False) as values:
        theta,dv,dt = (values[name] for name in ('theta','dv','dt'))
    if (len(dt)!=155868 or theta.shape!=dv.shape or dv.shape!=(len(dt),3)
            or not all(np.isfinite(v).all() for v in (theta,dv,dt))
            or np.any(dt<=0) or np.any(dt>.005)):
        raise ValueError('exact saved ESA increment and clock support required')
    time = origin+np.r_[0.,np.cumsum(dt)]
    end = np.searchsorted(time,end_time,side='left')
    if end<=0 or end>=len(time):
        raise ValueError('earlier analysis outside the sealed packet support')
    return time[:end+1],theta[:end],dv[:end]/dt[:end,None],dt[:end]


def fixed_support(width, times, packet_times, transported):
    import numpy as np

    ordinary = []
    for center in CENTERS:
        half = width//2
        t = times[center-half:center+half+1]
        r = t-times[center]
        _,kernel = rate_operator(r)
        start = np.searchsorted(packet_times,t[0],side='right')-1
        stop = np.searchsorted(packet_times,t[-1],side='left')
        if not 0<=start<stop<len(packet_times):
            raise ValueError('unsupported frozen force averaging window')
        keep = slice(start,stop)
        weights = matched_weights(packet_times[start:stop+1]-times[center],r,kernel)
        vector = weights@transported[keep]
        ordinary.append((keep,weights,vector))
    pairs = [Pair(left[0],right[0],left[1],right[1],np.linalg.norm(left[2]),np.linalg.norm(right[2]))
             for left,right in zip(ordinary[:8],ordinary[8:],strict=True)]
    observed = angles([row[2] for row in ordinary[:8]],[row[2] for row in ordinary[8:]])
    return pairs,observed


def box_summary(theta, force, dt, pairs, box, limit_deg):
    import numpy as np

    def evaluate(scale):
        bound = np.rad2deg(angle_bounds(theta,force,dt,pairs,box*scale))
        return float(np.linalg.norm(bound)/math.sqrt(len(bound))),bound
    full,full_pairs = evaluate(1.)
    lower,upper = 0.,1.
    probes = 1
    if full < limit_deg:
        lower = 1.
    else:
        for _ in range(BISECTION_STEPS):
            mid = (upper+lower)/2.
            score,_ = evaluate(mid)
            probes += 1
            if score < limit_deg:
                lower = mid
            else:
                upper = mid
    return dict(full_box_rms_upper_deg=full,full_pair_angle_upper_deg=full_pairs.tolist(),
                full_box_certifies_preference=full<limit_deg,
                certified_common_fraction_of_working_box=lower,evaluations=probes)


def compare(matrix, reference, matched):
    import numpy as np

    rows = json.loads(gzip.decompress(matrix.input('training',raw=True)))
    times = np.asarray([r['time_s'] for r in rows],float)
    if len(times)!=400 or np.any(np.diff(times)<=0):
        raise ValueError('same earlier receiver clock required')
    recipe = matrix.input('recipe')
    limits = recipe['limits']
    working = np.asarray([[limits[term+'_'+axis] for axis in 'xyz'] for term in TERMS])
    packet_times,theta,force,dt = packet_inputs(matrix,times[-1])
    transported = midpoint_attitudes(theta).apply(force)
    results = []
    for width, earlier in zip(WIDTHS,reference['settings'],strict=True):
        pairs,observed = fixed_support(width,times,packet_times,transported)
        if (earlier['width_reports']!=width or not np.allclose(
                np.rad2deg(observed),earlier['measured_pair_angles_deg'],rtol=0,atol=1e-10)):
            raise ValueError('nominal earlier measured angles did not reproduce')
        gaps = [r['minimum_shape_error_gap_deg'] for r in matched['settings'] if r['width_reports']==width]
        if len(gaps)!=3 or min(gaps)<=0:
            raise ValueError('complete positive shape margins required')
        threshold = min(gaps)/2.
        masks = dict(joint=np.ones((4,1)))
        masks.update({term:np.eye(4)[i,:,None] for i,term in enumerate(TERMS)})
        results.append(dict(width_reports=width,threshold_deg=threshold,terms={
            term:box_summary(theta,force,dt,pairs,working*mask,threshold) for term,mask in masks.items()}))
    evaluations = sum(row['evaluations'] for width in results for row in width['terms'].values())
    if evaluations>350:
        raise ValueError('finite bound budget exceeded')
    return dict(widths=results,working_limits={term:values.tolist() for term,values in zip(TERMS,working)},
                integrated_packet_intervals=len(dt),bound_evaluations=evaluations,
                usable_as_device_specification=False,new_fits=0,reserved_reads=0,
                receiver_error_bounded=False,scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('freeze','run'))
    args = parser.parse_args()
    threads = environment(threads=1)
    if any(os.environ.get(key)!=value for key,value in threads.items()):
        raise ValueError('one numerical thread required')
    import numpy as np
    import scipy

    root = Path.cwd()
    folder = root/DIRECTORY
    reference = json.loads((root/EARLIER).read_bytes())['result']
    matched = json.loads((root/MATCHED).read_bytes())['result']
    if digest(encoded(reference))!=EARLIER_SHA or digest(encoded(matched))!=MATCHED_SHA:
        raise ValueError('sealed angle profile sources differ')
    with (folder/'direction-calibration.lock').open('a') as lock, closing(ClosedStudy(root,MATRIX)) as matrix:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (matrix.completion['manifest_sha256']!=MATRIX_SHA
                or matrix.input('parent_identity')['source_id']!='esa-99f1530c3eda4318'):
            raise ValueError('same opened ESA development window required')
        sources = [Path(__file__),root/PLAN,root/'analysis/tests/test_esa_gyro_direction_calibration.py']
        sources.extend(root/'analysis/lll'/name for name in (
            'esa_doppler_force.py','esa_gyro_force_direction.py','esa_matched_gyro_direction.py',
            'ilvis0_forward.py','compute_budget.py','studies/artifacts.py','studies/closed.py'))
        finish = encoded(dict(inputs=dict(matrix=MATRIX_SHA,direction=EARLIER_SHA,matched=MATCHED_SHA),
            sources={str(p.relative_to(root)):digest(p.read_bytes()) for p in sources},
            environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                os=platform.system(),arch=platform.machine(),threads=threads),
            max_intervals=155868,max_bound_evaluations=350,max_new_fits=0,observed_groups=['187']))
        binding = folder/'direction-calibration-freeze.json'
        if args.action=='freeze' and not binding.exists():
            atomic(binding,finish)
        if binding.read_bytes()!=finish:
            raise ValueError('gyro direction calibration freeze differs')
        if args.action=='freeze':
            print(digest(finish))
            return
        result_path = root/REPORT
        if not result_path.exists():
            result = compare(matrix,reference,matched)
            atomic(result_path,encoded(dict(freeze=json.loads(finish),freeze_sha256=digest(finish),
                result=result,result_sha256=digest(encoded(result)))))
        saved = json.loads(result_path.read_bytes())
        if (saved['freeze_sha256']!=digest(finish) or digest(encoded(saved['freeze']))!=digest(finish)
                or digest(encoded(saved['result']))!=saved['result_sha256']):
            raise ValueError('sealed direction calibration comparison differs')
        print(f'{saved["result"]["bound_evaluations"]} evaluations, SHA-256 {saved["result_sha256"]}')


if __name__=='__main__':
    main()
