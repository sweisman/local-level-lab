# SPDX-License-Identifier: AGPL-3.0-or-later
"""Continuous isolated X-bias sensitivity of the sealed ESA direction comparison."""
import argparse
from contextlib import closing
import fcntl
import gzip
import json
import os
from pathlib import Path
import platform

from .compute_budget import environment
from .esa_doppler_force import DIRECTORY, FOLDER, MATRIX, MATRIX_SHA, WIDTHS
from .esa_ground_x_bias import GROUND, GROUND_SHA, ground_profile
from .esa_ground_x_bias import REPORT as GROUND_RESULT
from .esa_gyro_calibration_endpoints import REPORT as ENDPOINTS
from .esa_gyro_direction_calibration import (
    MATCHED, MATCHED_SHA, REPORT as BOUNDS, fixed_support, packet_inputs,
)
from .esa_gyro_force_direction import angles, midpoint_attitudes
from .esa_matched_gyro_direction import DISC_WITH_FIELD, GLOBE
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

PLAN = FOLDER+'ESA_X_BIAS_DIRECTION_PROFILE_PLAN.md'
REPORT = FOLDER+'esa-x-bias-direction-profile-result.json'
ENDPOINT_SHA = '4851787a9963f17a694b9a670a3c192c77881c563b62ef3c2104cad6f3bff4da'
GROUND_RESULT_SHA = '307135028e6a04b1a87a435ec73ab3932b240fe0bcc52231b95f6433f24d4c66'
BOUNDS_SHA = '518941335b83e252acd43ccc690e973903926420ae3d7b5e1c5ca02e1059c4c4'
GRID_SIZE = 401


def direction_slope(base, response, limit):
    """Upper bound on the direction derivative of each base - bias * response."""
    import numpy as np

    aa = np.asarray(base,float)
    cc = np.asarray(response,float)
    denominator = np.einsum('ij,ij->i',cc,cc)
    dot = np.einsum('ij,ij->i',aa,cc)
    t = np.clip(np.divide(dot,denominator,out=np.zeros_like(dot),where=denominator>0),-limit,limit)
    residual = aa-t[:,None]*cc
    minimum = np.einsum('ij,ij->i',residual,residual)
    if np.any(minimum<=0):
        raise ValueError('force mean can vanish within the bias interval')
    return np.linalg.norm(np.cross(aa,cc),axis=1)/minimum


def run_ranges(edges,cells):
    """Merge adjacent certified cells into closed intervals."""
    ranges = []
    for i,passed in enumerate(cells):
        if passed:
            left,right = float(edges[i]),float(edges[i+1])
            if ranges and ranges[-1][1]==left:
                ranges[-1][1] = right
            else:
                ranges.append([left,right])
    return ranges


def data_angles(frames,force,dt,times,packet_times,grid):
    import numpy as np

    raw = frames.apply(force)
    unit_x = frames.apply(np.tile([1.,0.,0.],(len(dt),1)))
    result = {}
    for width in WIDTHS:
        pairs,_ = fixed_support(width,times,packet_times,raw)
        start = np.asarray([p.earlier_weights@raw[p.earlier] for p in pairs])
        end = np.asarray([p.later_weights@raw[p.later] for p in pairs])
        start_x = np.asarray([p.earlier_weights@unit_x[p.earlier] for p in pairs])
        end_x = np.asarray([p.later_weights@unit_x[p.later] for p in pairs])
        measured = np.asarray([angles(start-bias*start_x,end-bias*end_x) for bias in grid])
        slope = direction_slope(start,start_x,grid[-1])+direction_slope(end,end_x,grid[-1])
        result[width] = (measured,float(np.sqrt(np.mean(slope*slope))))
    return result


def compare(matrix,matched,endpoints,ground,ground_result,calibration):
    import numpy as np

    calls = 0
    previous = json.loads(gzip.decompress(matrix.input('training',raw=True)))
    times = np.asarray([row['time_s'] for row in previous],float)
    if len(times)!=400 or np.any(np.diff(times)<=0):
        raise ValueError('same earlier receiver clock required')
    limit = calibration['working_limits']['accel_bias'][0]
    if limit!=.1:
        raise ValueError('same isolated X-axis working allowance required')
    t,theta,force,dt = packet_inputs(matrix,times[-1])
    grid = np.linspace(-limit,limit,GRID_SIZE)
    directions = data_angles(midpoint_attitudes(theta),force,dt,times,t,grid)
    for index,label in ((0,'accel_bias_x_-1'),(GRID_SIZE//2,'nominal'),(-1,'accel_bias_x_+1')):
        prior = next(case for case in endpoints['cases'] if case['label']==label)
        for row in prior['settings']:
            if not np.allclose(directions[row['width_reports']][0][index],
                row['pair_angles_rad'],atol=1e-12,rtol=0):
                raise ValueError('angle response did not reproduce the sealed endpoint results')
    globe,disc = np.ones(GRID_SIZE-1,bool),np.ones(GRID_SIZE-1,bool)
    settings = []
    for row in matched['settings']:
        width,source = row['width_reports'],row['source']
        observed,slope = directions[width]
        upper,lower = {},{}
        for name in (GLOBE,DISC_WITH_FIELD):
            profile = row['by_shape'][name]
            predictions = np.asarray(profile['grid_pair_angles_rad'],float)
            distance = predictions[None,:,:]-observed[:,None,:]
            upper[name] = np.min(np.sqrt(np.mean(distance**2,axis=2)),axis=1)
            lower[name] = np.maximum(0.,upper[name]-profile['continuity_allowance_rad'])
        edges_g = lower[DISC_WITH_FIELD]-upper[GLOBE]
        edges_d = lower[GLOBE]-upper[DISC_WITH_FIELD]
        dx = np.diff(grid)
        cert_g = np.minimum(edges_g[:-1],edges_g[1:]) > slope*dx+1e-12
        cert_d = np.minimum(edges_d[:-1],edges_d[1:]) > slope*dx+1e-12
        if np.any(cert_g&cert_d):
            raise ValueError('inconsistent directional intervals')
        globe &= cert_g
        disc &= cert_d
        settings.append(dict(width_reports=width,source=source,
            globe_ranges_mps2=run_ranges(grid,cert_g),disc_ranges_mps2=run_ranges(grid,cert_d),
            slope_bound_deg_per_mps2=float(np.rad2deg(slope)),
            globe_upper_deg=np.rad2deg(upper[GLOBE]).tolist(),
            disc_upper_deg=np.rad2deg(upper[DISC_WITH_FIELD]).tolist()))
    globe_ranges = run_ranges(grid,globe)
    disc_ranges = run_ranges(grid,disc)
    lo,hi = next(bounds for bounds in globe_ranges if bounds[0]<=0.<=bounds[1])
    boundary = None
    if 0.<hi<limit:
        calls = 1
        stops = [np.asarray(row['minute_means_body_m_s2']) for row in ground['ground']['stops']]
        if [len(rows) for rows in stops]!=[45,30]:
            raise ValueError('same sealed ground minute means required')
        limits = calibration['working_limits']
        ground_case = ground_profile(stops,limits['accel_bias'],limits['accel_gain'],hi)
        boundary = dict(fixed_x_bias_mps2=hi,fit=ground_case,
            nominal=ground_result['sets']['shared']['nominal'],
            earlier_unconstrained=ground_result['sets']['shared']['free'])
    return dict(bias_grid_mps2=grid.tolist(),settings=settings,common_globe_ranges_mps2=globe_ranges,
        common_disc_ranges_mps2=disc_ranges,common_globe_interval_through_zero_mps2=[lo,hi],
        ground_check=boundary,ground_programs=calls,integrated_packet_intervals=len(dt),
        new_fits=0,reserved_reads=0,scientific_decision='abstain')


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
    bindings = dict(matched=(MATCHED,MATCHED_SHA),endpoints=(ENDPOINTS,ENDPOINT_SHA),
                    ground_result=(GROUND_RESULT,GROUND_RESULT_SHA),calibration=(BOUNDS,BOUNDS_SHA))
    inputs = {key:json.loads((root/name).read_bytes())['result'] for key,(name,_) in bindings.items()}
    ground = (root/GROUND).read_bytes()
    if (digest(ground)!=GROUND_SHA or
            any(digest(encoded(inputs[key]))!=expected for key,(_,expected) in bindings.items())):
        raise ValueError('exact existing direction and ground inputs required')
    with (folder/'x-bias-profile.lock').open('a') as lock, closing(ClosedStudy(root,MATRIX)) as matrix:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (matrix.completion['manifest_sha256']!=MATRIX_SHA
                or matrix.input('parent_identity')['source_id']!='esa-99f1530c3eda4318'):
            raise ValueError('same sealed earlier ESA study required')
        sources = [Path(__file__),root/PLAN,root/'analysis/tests/test_esa_x_bias_direction_profile.py']
        sources.extend(root/'analysis/lll'/name for name in (
            'esa_ground_x_bias.py','esa_gyro_direction_calibration.py','esa_gyro_force_direction.py',
            'esa_doppler_force.py','compute_budget.py','studies/artifacts.py','studies/closed.py'))
        freeze = encoded(dict(inputs={k:v[1] for k,v in bindings.items()}|dict(matrix=MATRIX_SHA,ground=GROUND_SHA),
            sources={str(p.relative_to(root)):digest(p.read_bytes()) for p in sources},
            environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                os=platform.system(),arch=platform.machine(),threads=threads),
            max_inertial_intervals=155868,max_bias_grid=GRID_SIZE,max_ground_programs=1,max_fits=0))
        binding = folder/'x-bias-profile-freeze.json'
        if args.action=='freeze' and not binding.exists():
            atomic(binding,freeze)
        if binding.read_bytes()!=freeze:
            raise ValueError('isolated bias profile freeze differs')
        if args.action=='freeze':
            print(digest(freeze))
            return
        path = root/REPORT
        if not path.exists():
            result = compare(matrix,ground=json.loads(ground),**inputs)
            atomic(path,encoded(dict(freeze=json.loads(freeze),freeze_sha256=digest(freeze),
                result=result,result_sha256=digest(encoded(result)))))
        saved = json.loads(path.read_bytes())
        if (saved['freeze_sha256']!=digest(freeze) or digest(encoded(saved['freeze']))!=digest(freeze)
                or digest(encoded(saved['result']))!=saved['result_sha256']):
            raise ValueError('sealed continuous bias profile differs')
        print(f'{len(saved["result"]["settings"])} settings, SHA-256 {saved["result_sha256"]}')


if __name__=='__main__':
    main()
