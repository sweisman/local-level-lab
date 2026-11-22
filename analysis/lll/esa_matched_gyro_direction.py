# SPDX-License-Identifier: AGPL-3.0-or-later
"""Profile the retained gyro field for matched-shape force direction scores."""
import argparse
from contextlib import closing
from dataclasses import dataclass
import fcntl
import gzip
import json
import os
from pathlib import Path
import platform

from .compute_budget import environment
from .esa_doppler_force import (
    BASE, CENTERS, DIRECTORY, FOLDER, GRAVITY, MATCH_SHA, MATRIX, MATRIX_SHA,
    VELOCITY_SHA, WIDTHS, _quadrature_rule, paths, rate_operator,
)
from .esa_gyro_force_direction import REPORT as EARLIER
from .esa_gyro_force_direction import REMOVED, angles, models
from .ilvis0_force_motion_triplets import force_in_fixed_frame
from .ilvis0_receiver_force import DISC_WITH_FIELD, evaluate_batch
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

GLOBE = 'sphere_rotating'
PLAN = FOLDER+'ESA_MATCHED_GYRO_DIRECTION_PLAN.md'
REPORT = FOLDER+'esa-matched-gyro-direction-result.json'
EARLIER_SHA = 'c665a24211ab849b998b6ffb17aa209be84bd4ecc8ea8117f2fd06729a76282b'
FRACTIONS = 41


class FieldFrame:
    """Ordered rotations through a piecewise-constant field in fixed axes."""

    def __init__(self, times, axes, fraction):
        import numpy as np
        from scipy.spatial.transform import Rotation

        self.times = np.asarray(times,float)
        self.body_rate = np.asarray(axes,float)*fraction
        dt = np.diff(self.times)
        if (self.times.ndim != 1 or len(dt) < 1 or np.any(dt <= 0)
                or self.body_rate.shape != (len(dt),3) or not 0 <= fraction <= 1
                or not np.isfinite(dt).all() or not np.isfinite(self.body_rate).all()):
            raise ValueError('finite ordered piecewise field required')
        deltas = Rotation.from_rotvec(self.body_rate*dt[:,None])
        cumulative = [Rotation.identity()]
        for delta in deltas:
            cumulative.append(cumulative[-1]*delta)
        self.prefix = Rotation.concatenate(cumulative)

    def at(self, query):
        import numpy as np
        from scipy.spatial.transform import Rotation

        query = np.asarray(query,float)
        if (query.ndim != 1 or not np.isfinite(query).all() or
                np.any(query < self.times[0]) or np.any(query > self.times[-1])):
            raise ValueError('force evaluation must be inside the sampled field path')
        index = np.minimum(np.searchsorted(self.times,query,side='right')-1,len(self.times)-2)
        elapsed = query-self.times[index]
        return self.prefix[index]*Rotation.from_rotvec(elapsed[:,None]*self.body_rate[index])


@dataclass(frozen=True)
class Support:
    times: object
    weights: object
    forces: object
    start: float

    def average(self, frame):
        return self.weights@frame.at(self.times).apply(self.forces)

    def rate_bound(self, angular_rate, anchor):
        import numpy as np

        return angular_rate*float(self.weights@(np.linalg.norm(self.forces,axis=1)*(self.times-anchor)))


def background_axes(positions, model):
    import numpy as np

    latitude = positions[:,0]
    field = models.OMEGA_E*np.column_stack((np.cos(latitude),np.zeros(len(latitude)),-np.sin(latitude)))
    return force_in_fixed_frame(field,positions,model=model)


def support(relative,kernel,center,rates,elapsed,model):
    import numpy as np

    nodes, quadrature = _quadrature_rule()
    half = np.diff(relative)[:,None]/2.
    grids = ((relative[:-1]+relative[1:])[:,None]/2.+half*nodes).ravel()
    weights = (half*quadrature*kernel[:,None]).ravel()
    poly = np.polynomial.polynomial
    pos = center+poly.polyval(grids,poly.polyint(rates)).T
    vel = poly.polyval(grids,rates).T
    acc = poly.polyval(grids,poly.polyder(rates)).T
    local = evaluate_batch(pos, vel, acc, model=model, background_rate_rads=models.OMEGA_E,
        gravity_mps2=np.full(len(pos), GRAVITY), disc_radius_m=models.WGS84_A)['specific_force_ned_mps2']
    return Support(grids+elapsed,weights,force_in_fixed_frame(local,pos,model=model),relative[0]+elapsed)


def profile(observed, supports, vectors, fractions, rate):
    """Bound the best score between tested fractions for the declared field."""
    import numpy as np

    count = len(observed)
    if (vectors.shape != (len(fractions),2*count,3) or len(supports) != 2*count
            or len(fractions) < 2 or fractions[0] != 0. or fractions[-1] != 1.
            or np.any(np.diff(fractions) <= 0)):
        raise ValueError('complete fixed matched pairs and fraction grid required')
    predictions = np.asarray([angles(row[:count],row[count:]) for row in vectors])
    scores = np.sqrt(np.mean((predictions-observed)**2,axis=1))
    nearest = np.max(np.diff(fractions))/2.
    minimum_norm = np.min(np.linalg.norm(vectors,axis=2),axis=0)
    pair_bounds = []
    for i in range(count):
        indices = (i,i+count)
        anchor = min(supports[j].start for j in indices)
        slope = 0.
        for j in indices:
            change = supports[j].rate_bound(rate,anchor)
            lower_norm = minimum_norm[j]-change*nearest
            if lower_norm <= 0:
                raise ValueError('continuous bound cannot keep the force vectors nonzero')
            slope += change/lower_norm
        pair_bounds.append(slope)
    allowance = float(nearest*np.sqrt(np.mean(np.square(pair_bounds)))+1e-12)
    best = int(np.argmin(scores))
    return dict(fractions=fractions.tolist(),grid_rms_rad=scores.tolist(),
                grid_pair_angles_rad=predictions.tolist(),
                grid_best_fraction=float(fractions[best]),grid_best_rms_rad=float(scores[best]),
                continuity_allowance_rad=allowance,
                continuous_lower_rms_rad=max(0.,float(scores[best])-allowance))


def profile_all_pairs(observed_deg, supports, vectors, fractions, rate):
    """Bound the all-pairs RMS over field strength with the same pairwise proof."""
    import numpy as np

    measured, vectors, fractions = (np.asarray(value, float) for value in (observed_deg, vectors, fractions))
    first, second = np.triu_indices(len(supports), k=1)
    if (not len(first) or measured.shape != first.shape or vectors.shape != (len(fractions), len(supports), 3)
            or not np.isfinite(measured).all() or np.any((measured < 0.) | (measured > 180.))
            or not np.isfinite(rate) or rate < 0.):
        raise ValueError('one finite angle per unordered support pair and bounded field rate required')
    indices = np.r_[first, second]
    result = profile(np.deg2rad(measured), [supports[i] for i in indices], vectors[:, indices], fractions, rate)
    for name, value in tuple(result.items()):
        if name.endswith('_rad'):
            result[name.removesuffix('_rad')+'_deg'] = np.rad2deg(value).tolist()
            del result[name]
    return result


def compare(matrix, velocity, indices, earlier):
    import numpy as np

    frac = np.linspace(0.,1.,FRACTIONS)
    times, coordinates, rate_paths = paths(matrix,velocity,indices)
    elapsed = times-times[0]
    frames = {}
    maximum_rate = models.OMEGA_E*(1.+1e-14)
    for model in (GLOBE,DISC_WITH_FIELD):
        axes = background_axes(coordinates,model)
        steps = (axes[:-1]+axes[1:])/2.
        if np.max(np.linalg.norm(steps,axis=1)) > maximum_rate:
            raise ValueError('field magnitude exceeds the analytic allowance')
        frames[model] = [FieldFrame(elapsed,steps,q) for q in frac]
    reports = []
    for width, reference in zip(WIDTHS,earlier['settings'],strict=True):
        if reference['width_reports'] != width:
            raise ValueError('earlier force direction support changed')
        observed = np.deg2rad(reference['measured_pair_angles_deg'])
        for source,rates in rate_paths.items():
            result = {}
            for model in frames:
                supports = []
                for center in CENTERS:
                    half = width//2
                    sl = slice(center-half,center+half+1)
                    relative = times[sl]-times[center]
                    operator,kernel = rate_operator(relative)
                    supports.append(support(relative,kernel,coordinates[center],
                                           operator@rates[sl],elapsed[center],model))
                vectors = np.asarray([[s.average(frame) for s in supports] for frame in frames[model]])
                result[model] = profile(observed,supports,vectors,frac,maximum_rate)
            baseline = reference['by_receiver'][source]
            for axis, model in ((0,REMOVED),(-1,GLOBE)):
                actual = np.rad2deg(result[GLOBE]['grid_pair_angles_rad'][axis])
                if not np.allclose(actual,baseline[model]['pair_angles_deg'],rtol=0,atol=1e-10):
                    raise ValueError('earlier globe field endpoints did not replay')
            margin = result[DISC_WITH_FIELD]['continuous_lower_rms_rad']-result[GLOBE]['grid_best_rms_rad']
            reports.append(dict(width_reports=width,source=source,by_shape=result,
                minimum_shape_error_gap_deg=float(np.rad2deg(margin)), fixed_field_globe_closer=margin>0))
    return dict(settings=reports,new_fits=0,new_inertial_reads=0,reserved_reads=0,
                retained_fraction_profiled_separately=True,scientific_decision='abstain')


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
    earlier = json.loads((root/EARLIER).read_bytes())
    if (digest(encoded(velocity['velocity']))!=VELOCITY_SHA
            or digest(encoded(matching['result']))!=MATCH_SHA
            or digest(encoded(earlier['result']))!=EARLIER_SHA):
        raise ValueError('exact sealed observation and direction comparison inputs required')
    with (folder/'matched-direction.lock').open('a') as lock, closing(ClosedStudy(root,MATRIX)) as matrix:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (matrix.completion['manifest_sha256']!=MATRIX_SHA
                or matrix.input('parent_identity')['source_id']!='esa-99f1530c3eda4318'):
            raise ValueError('same earlier ESA development cut required')
        sources = [Path(__file__),root/PLAN,root/'analysis/tests/test_esa_matched_gyro_direction.py']
        sources.extend(root/'analysis/lll'/name for name in (
            'esa_gyro_force_direction.py','esa_doppler_force.py','esa_rinex_code_comparison.py',
            'ilvis0_receiver_force.py','ilvis0_force_motion_triplets.py','ilvis0_channel_controls.py',
            'models.py','gnss_position.py','compute_budget.py','studies/artifacts.py','studies/closed.py'))
        freeze = encoded(dict(
            inputs=dict(matrix=MATRIX_SHA,velocity=VELOCITY_SHA,match=MATCH_SHA,earlier=EARLIER_SHA),
            sources={str(p.relative_to(root)):digest(p.read_bytes()) for p in sources},
            environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                os=platform.system(),arch=platform.machine(),threads=threads),
            maximum_vector_supports=192,maximum_averages=192*FRACTIONS,
            maximum_new_fits=0,observed_groups=['187']))
        binding = folder/'matched-direction-freeze.json'
        if args.action=='freeze' and not binding.exists():
            atomic(binding,freeze)
        if binding.read_bytes()!=freeze:
            raise ValueError('matched gyro field freeze differs')
        if args.action=='freeze':
            print(digest(freeze))
            return
        output = root/REPORT
        if not output.exists():
            result = compare(matrix,velocity['velocity'],matching['result']['matched_code_indices'][:400],earlier['result'])
            atomic(output,encoded(dict(freeze=json.loads(freeze),freeze_sha256=digest(freeze),
                result=result,result_sha256=digest(encoded(result)))))
        saved = json.loads(output.read_bytes())
        if (saved['freeze_sha256']!=digest(freeze) or digest(encoded(saved['freeze']))!=digest(freeze)
                or digest(encoded(saved['result']))!=saved['result_sha256']):
            raise ValueError('sealed matched direction comparison differs')
        print(f'{len(saved["result"]["settings"])} settings, SHA-256 {saved["result_sha256"]}')


if __name__=='__main__':
    main()
