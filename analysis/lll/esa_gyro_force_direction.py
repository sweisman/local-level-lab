# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare force-direction changes in sensor and candidate common frames."""
import argparse
from contextlib import closing
import fcntl
import gzip
import io
import json
import math
import os
from pathlib import Path
import platform

from . import models
from .compute_budget import environment
from .esa_doppler_force import (
    BASE, CENTERS, DIRECTORY, FOLDER, GRAVITY, MATCH_SHA, MATRIX, MATRIX_SHA,
    VELOCITY_FREEZE, VELOCITY_SHA, WIDTHS, _quadrature_rule, matched_weights, paths, rate_operator,
)
from .ilvis0_force_motion_triplets import force_in_fixed_frame
from .ilvis0_receiver_force import MODELS, evaluate_batch
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

PLAN = FOLDER+'ESA_GYRO_FORCE_DIRECTION_PLAN.md'
REPORT = FOLDER+'esa-gyro-force-direction-result.json'
ROTATING, STILL, FLAT = MODELS
REMOVED = 'sphere_rotating_full_rate_removed'


def midpoint_attitudes(increments):
    """Map each interval's midpoint body axes to the starting body axes."""
    import numpy as np
    from scipy.spatial.transform import Rotation

    theta = np.asarray(increments, float)
    if theta.ndim != 2 or theta.shape[1] != 3 or not np.all(np.isfinite(theta)) or not len(theta):
        raise ValueError('complete three-axis increments required')
    delta = Rotation.from_rotvec(theta).as_quat().tolist()
    prefix = np.empty((len(theta), 4))
    x, y, z, w = 0., 0., 0., 1.
    for i, (a, b, c, d) in enumerate(delta):
        prefix[i] = (x, y, z, w)
        x, y, z, w = (w*a+x*d+y*c-z*b, w*b-x*c+y*d+z*a,
                      w*c+x*b-y*a+z*d, w*d-x*a-y*b-z*c)
    return Rotation.from_quat(prefix)*Rotation.from_rotvec(theta/2)


def angles(first, second):
    """Stable angles between vectors, unchanged by a common proper rotation."""
    import numpy as np

    a, b = np.asarray(first, float), np.asarray(second, float)
    if (a.shape != b.shape or a.ndim != 2 or a.shape[1] != 3
            or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b))
            or np.any(np.linalg.norm(a, axis=1) == 0) or np.any(np.linalg.norm(b, axis=1) == 0)):
        raise ValueError('finite paired nonzero force vectors required')
    return np.arctan2(np.linalg.norm(np.cross(a, b), axis=1), np.einsum('ij,ij->i', a,b))


def common_force(force, positions, elapsed, model, retained):
    import numpy as np
    from scipy.spatial.transform import Rotation

    fixed = force_in_fixed_frame(force, positions, model=model)
    if model == ROTATING and retained:
        return Rotation.from_euler('z', np.asarray(elapsed)[:,None]*models.OMEGA_E).apply(fixed)
    return fixed


def predictions(relative, kernel, origin, rates, center_elapsed):
    import numpy as np

    nodes, weights = _quadrature_rule()
    half_width = np.diff(relative)[:,None]/2
    grid = ((relative[:-1]+relative[1:])[:,None]/2+half_width*nodes).ravel()
    weights = (half_width*weights*kernel[:,None]).ravel()
    polynomial = np.polynomial.polynomial
    position = origin+polynomial.polyval(grid, polynomial.polyint(rates)).T
    velocity = polynomial.polyval(grid, rates).T
    acceleration = polynomial.polyval(grid, polynomial.polyder(rates)).T
    result = {}
    for model in MODELS:
        field = models.OMEGA_E if model == ROTATING else 0.
        required = evaluate_batch(position, velocity, acceleration, model=model, background_rate_rads=field,
            gravity_mps2=np.full(len(position), GRAVITY), disc_radius_m=models.WGS84_A)['specific_force_ned_mps2']
        result[model] = weights@common_force(required, position, grid+center_elapsed, model, True)
        if model == ROTATING:
            result[REMOVED] = weights@common_force(required, position, grid+center_elapsed, model, False)
    return result


def log_vectors(matrix, last_time):
    import numpy as np

    origin = matrix.input('saved-input-binding')['time_origin_s']
    with np.load(io.BytesIO(matrix.input('interval',raw=True)), allow_pickle=False) as archive:
        theta, dv, dt = (archive[key] for key in ('theta','dv','dt'))
    if (dt.shape != (155868,) or theta.shape != dv.shape or dv.shape != (len(dt),3)
            or not all(np.all(np.isfinite(v)) for v in (dt,dv,theta))
            or np.any(dt<=0) or np.any(dt>.005)):
        raise ValueError('unaltered inertial increments and valid clock required')
    times = origin+np.r_[0.,np.cumsum(dt)]
    end = np.searchsorted(times,last_time,side='left')
    if end >= len(times):
        raise ValueError('inertial support ends before the earlier window')
    frames = midpoint_attitudes(theta[:end])
    return times[:end+1], frames.apply(dv[:end]/dt[:end,None])


def compare(matrix, velocity, indices):
    import numpy as np

    times, coord, rate_paths = paths(matrix, velocity, indices)
    imu_epochs, force_vectors = log_vectors(matrix, times[-1])
    results = []
    for width in WIDTHS:
        assigned = {source:{m:[] for m in (*MODELS,REMOVED)} for source in rate_paths}
        observed = []
        for center in CENTERS:
            half = width//2
            cut = slice(center-half,center+half+1)
            t = times[cut]
            rel = t-times[center]
            operator,kernel = rate_operator(rel)
            first = np.searchsorted(imu_epochs,t[0],side='right')-1
            last = np.searchsorted(imu_epochs,t[-1],side='left')
            if not 0<=first<last<len(imu_epochs):
                raise ValueError('recorded inertial support does not bracket the fixed stencil')
            weights = matched_weights(imu_epochs[first:last+1]-times[center],rel,kernel)
            observed.append(weights@force_vectors[first:last])
            for source,rates in rate_paths.items():
                prediction = predictions(rel,kernel,coord[center],operator@rates[cut],times[center]-times[0])
                for model,value in prediction.items():
                    assigned[source][model].append(value)
        measured = np.rad2deg(angles(observed[:8],observed[8:]))
        comparison = {}
        for source,by_model in assigned.items():
            comparison[source] = {}
            for model,vectors in by_model.items():
                predicted = np.rad2deg(angles(vectors[:8],vectors[8:]))
                residual = measured-predicted
                comparison[source][model] = dict(pair_angles_deg=predicted.tolist(),
                    signed_angle_residuals_deg=residual.tolist(),
                    rms_deg=float(np.linalg.norm(residual)/math.sqrt(len(residual))))
        results.append(dict(width_reports=width,measured_pair_angles_deg=measured.tolist(),
                            by_receiver=comparison))
    return dict(settings=results,centers_s=times[list(CENTERS)].tolist(),
                gyro_intervals=len(force_vectors),candidate_vector_averages=288,
                alternate_frame_averages=96, new_fits=0, original_reads=0, reserved_reads=0,
                assumed_gyro_gain_bias_corrections='none', absolute_accuracy_calibrated=False,
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
    velocity = json.loads(gzip.decompress((folder/'velocity.json.gz').read_bytes()))
    matching = json.loads((root/(BASE+'comparison.json')).read_bytes())
    if (velocity['velocity_sha256']!=VELOCITY_SHA or digest(encoded(velocity['velocity']))!=VELOCITY_SHA
            or velocity['freeze_sha256']!=VELOCITY_FREEZE
            or digest((folder/'freeze.json').read_bytes())!=VELOCITY_FREEZE
            or matching['result_sha256']!=MATCH_SHA or digest(encoded(matching['result']))!=MATCH_SHA):
        raise ValueError('exact previously sealed receiver sources required')
    with (folder/'direction.lock').open('a') as lock, closing(ClosedStudy(root,MATRIX)) as matrix:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (matrix.completion['manifest_sha256']!=MATRIX_SHA
                or matrix.input('parent_identity')['source_id']!='esa-99f1530c3eda4318'):
            raise ValueError('unchanged earlier development cut required')
        sources = [Path(__file__),root/PLAN,root/'analysis/tests/test_esa_gyro_force_direction.py']
        sources.extend(root/'analysis/lll'/name for name in (
            'esa_doppler_force.py','esa_doppler_comparison.py','esa_rinex_code_comparison.py',
            'ilvis0_receiver_force.py','ilvis0_force_motion_triplets.py','ilvis0_channel_controls.py',
            'gnss_position.py','models.py','compute_budget.py','studies/artifacts.py','studies/closed.py'))
        freeze = encoded(dict(
            inputs=dict(matrix=MATRIX_SHA,velocity=VELOCITY_SHA,match=MATCH_SHA),
            sources={str(p.relative_to(root)):digest(p.read_bytes()) for p in sources},
            environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                os=platform.system(),arch=platform.machine(),threads=threads),
            maximum_gyro_intervals=155868,maximum_candidate_averages=288,
            maximum_alternate_frames=96,maximum_new_fits=0,observed_groups=['187']))
        binding = folder/'direction-freeze.json'
        if args.action=='freeze' and not binding.exists():
            atomic(binding,freeze)
        if binding.read_bytes()!=freeze:
            raise ValueError('gyro-force direction freeze differs')
        if args.action=='freeze':
            print(digest(freeze))
            return
        output = root/REPORT
        if not output.exists():
            result = compare(matrix,velocity['velocity'],matching['result']['matched_code_indices'][:400])
            atomic(output,encoded(dict(freeze=json.loads(freeze),freeze_sha256=digest(freeze),
                result=result,result_sha256=digest(encoded(result)))))
        saved = json.loads(output.read_bytes())
        if (saved['freeze_sha256']!=digest(freeze) or digest(encoded(saved['freeze']))!=digest(freeze)
                or digest(encoded(saved['result']))!=saved['result_sha256']):
            raise ValueError('sealed direction comparison differs')
        print(f'{len(saved["result"]["settings"])} widths, SHA-256 {saved["result_sha256"]}')


if __name__=='__main__':
    main()
