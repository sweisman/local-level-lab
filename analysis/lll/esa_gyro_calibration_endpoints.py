# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay each signed ESA sensor-calibration endpoint against fixed profiles."""
import argparse
from contextlib import closing
import fcntl
import gzip
import json
import math
import os
from pathlib import Path
import platform

from .compute_budget import environment
from .esa_doppler_force import DIRECTORY, FOLDER, MATRIX, MATRIX_SHA, WIDTHS
from .esa_doppler_force import REPORT as SCALAR
from .esa_gyro_direction_calibration import (
    EARLIER, EARLIER_SHA, MATCHED, MATCHED_SHA, TERMS, fixed_support, packet_inputs,
)
from .esa_gyro_direction_calibration import REPORT as BOUNDS
from .esa_gyro_force_direction import angles, midpoint_attitudes
from .esa_matched_gyro_direction import DISC_WITH_FIELD, GLOBE
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

PLAN = FOLDER+'ESA_GYRO_CALIBRATION_ENDPOINT_PLAN.md'
REPORT = FOLDER+'esa-gyro-calibration-endpoints-result.json'
BOUNDS_SHA = '518941335b83e252acd43ccc690e973903926420ae3d7b5e1c5ca02e1059c4c4'
SCALAR_SHA = 'd6a1c7e286c3e40e84c46887855bcc261fe9f1900a8029f1b2431593272d728b'


def direction_reversal(globe_best, disc_best, globe_allowance):
    """An explicit disc score beats every globe score in the covered range."""
    return disc_best < max(0.,globe_best-globe_allowance)


def rms(values):
    import numpy as np

    return float(np.linalg.norm(values)/math.sqrt(len(values)))


def evaluate(transported, force, supports, matched, scalar):
    import numpy as np

    results = []
    magnitudes = np.linalg.norm(force,axis=1)
    for width,pairs in supports.items():
        left = [p.earlier_weights@transported[p.earlier] for p in pairs]
        right = [p.later_weights@transported[p.later] for p in pairs]
        observed = angles(left,right)
        scalar_observed = np.array([p.earlier_weights@magnitudes[p.earlier] for p in pairs]
                                 +[p.later_weights@magnitudes[p.later] for p in pairs])
        for setting in matched['settings']:
            if setting['width_reports']!=width:
                continue
            scores = {}
            for shape,p in setting['by_shape'].items():
                differences = np.asarray(p['grid_pair_angles_rad'])-observed
                residual = np.sqrt(np.mean(differences**2,axis=1))
                index = int(np.argmin(residual))
                scores[shape] = dict(best_fraction=p['fractions'][index],rms_rad=float(residual[index]),
                   continuous_lower_rad=max(0.,float(residual[index])-p['continuity_allowance_rad']))
            source = setting['source']
            residuals = {}
            for law,blocks in scalar['rows'][str(width)]['required_force_mps2'][source].items():
                residuals[law] = {}
                for shape in (GLOBE,DISC_WITH_FIELD):
                    difference = scalar_observed-[block[shape] for block in blocks]
                    residuals[law][shape] = rms(difference[8:]-np.median(difference[:8]))
            results.append(dict(width_reports=width,source=source,scores=scores,
                profiled_disc_reversal=direction_reversal(scores[GLOBE]['rms_rad'],
                    scores[DISC_WITH_FIELD]['rms_rad'],setting['by_shape'][GLOBE]['continuity_allowance_rad']),
                scalar_offset_residual_mps2=residuals,
                pair_angles_rad=observed.tolist()))
    return results


def compare(matrix, inputs):
    import numpy as np

    rows = json.loads(gzip.decompress(matrix.input('training',raw=True)))
    times = np.asarray([r['time_s'] for r in rows],float)
    if len(times)!=400 or np.any(np.diff(times)<=0):
        raise ValueError('same earlier receiver support required')
    packet_time,theta,force,dt = packet_inputs(matrix,times[-1])
    frames = midpoint_attitudes(theta)
    nominal = frames.apply(force)
    supports = {}
    for width,prior in zip(WIDTHS,inputs['direction']['settings'],strict=True):
        supports[width],observed = fixed_support(width,times,packet_time,nominal)
        if prior['width_reports']!=width or not np.allclose(
                np.rad2deg(observed),prior['measured_pair_angles_deg'],atol=1e-10,rtol=0):
            raise ValueError('nominal measured direction did not replay')
    cases = [dict(label='nominal',settings=evaluate(nominal,force,supports,inputs['matched'],inputs['scalar']))]
    for i,term in enumerate(TERMS):
        for axis,axis_name in enumerate('xyz'):
            for sign in (-1,1):
                changed = np.zeros((4,3))
                changed[i,axis] = sign*inputs['bounds']['working_limits'][term][axis]
                gyro_bias,gyro_gain,accel_bias,accel_gain = changed
                if i<2:
                    transport = midpoint_attitudes((theta-dt[:,None]*gyro_bias)/(1.+gyro_gain))
                else:
                    transport = frames
                raw_force = (force-accel_bias)/(1.+accel_gain)
                settings = evaluate(transport.apply(raw_force),raw_force,supports,inputs['matched'],inputs['scalar'])
                cases.append(dict(label=f'{term}_{axis_name}_{sign:+d}',term=term,axis=axis_name,
                                  signed_correction=float(changed[i,axis]),settings=settings))
    return dict(cases=cases,replays=len(cases),intervals_per_replay=len(dt),new_fits=0,
                reserved_reads=0,earlier_full_position_fit_checked=False,
                scientific_decision='abstain')


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
    bindings = dict(direction=(EARLIER,EARLIER_SHA),matched=(MATCHED,MATCHED_SHA),
                    bounds=(BOUNDS,BOUNDS_SHA),scalar=(SCALAR,SCALAR_SHA))
    inputs = {key:json.loads((root/name).read_bytes())['result'] for key,(name,_) in bindings.items()}
    if any(digest(encoded(inputs[key]))!=expected for key,(_,expected) in bindings.items()):
        raise ValueError('sealed direction, scalar or calibration sources differ')
    with (folder/'direction-endpoints.lock').open('a') as lock, closing(ClosedStudy(root,MATRIX)) as matrix:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (matrix.completion['manifest_sha256']!=MATRIX_SHA
                or matrix.input('parent_identity')['source_id']!='esa-99f1530c3eda4318'):
            raise ValueError('same opened ESA development cut required')
        sources = [Path(__file__),root/PLAN,root/'analysis/tests/test_esa_gyro_calibration_endpoints.py']
        sources.extend(root/'analysis/lll'/name for name in (
            'esa_gyro_direction_calibration.py','esa_gyro_force_direction.py',
            'esa_doppler_force.py','esa_matched_gyro_direction.py',
            'compute_budget.py','studies/artifacts.py','studies/closed.py'))
        freeze = encoded(dict(inputs={key:ref[1] for key,ref in bindings.items()}|dict(matrix=MATRIX_SHA),
            sources={str(p.relative_to(root)):digest(p.read_bytes()) for p in sources},
            environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                os=platform.system(),arch=platform.machine(),threads=threads),
            max_replays=25,max_intervals_per_replay=155868,max_new_fits=0,observed_groups=['187']))
        binding = folder/'direction-endpoints-freeze.json'
        if args.action=='freeze' and not binding.exists():
            atomic(binding,freeze)
        if binding.read_bytes()!=freeze:
            raise ValueError('direction endpoint freeze differs')
        if args.action=='freeze':
            print(digest(freeze))
            return
        output = root/REPORT
        if not output.exists():
            result = compare(matrix,inputs)
            atomic(output,encoded(dict(freeze=json.loads(freeze),freeze_sha256=digest(freeze),
                result=result,result_sha256=digest(encoded(result)))))
        saved = json.loads(output.read_bytes())
        if (saved['freeze_sha256']!=digest(freeze) or digest(encoded(saved['freeze']))!=digest(freeze)
                or digest(encoded(saved['result']))!=saved['result_sha256']):
            raise ValueError('sealed endpoint comparisons differ')
        print(f'{saved["result"]["replays"]} replays, SHA-256 {saved["result_sha256"]}')


if __name__=='__main__':
    main()
