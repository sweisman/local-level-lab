# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check a common GPS receiver error on two saved NASA force histories."""

from contextlib import closing
import json
from pathlib import Path


ID = 'ilvis0-shared-force-witness-v2-20261120'
ORIGINAL = 'ilvis0-shared-force-witness-v1-20261120'
ORIGINAL_SHA = '92d83904fbc8c2bb5cd246b2f561e09ae3db6d8cf5e2a9a6474f6b4bfec18d98'
SCOPE = 'One shared receiver-error proposal on positive saved IMU8 force deficits'
PLAN = 'docs/ilvis0-measurement-contribution/SHARED_FORCE_WITNESS_V2_PLAN.md'
WINDOWS = {'8': 608, '21': 383}
PER_WINDOW = 8
STEPS = 64
MAX_GRADIENTS = 64
PROPOSAL_MARGIN = .00001


def tasks():
    return [dict(identity='imu8', input_key='imu8', payload=dict(imu_type='8'),
                 limits=dict(native_calls=0, packet_visits=0, bound_calls=3,
                             bound_steps=PER_WINDOW*WINDOWS['8']+MAX_GRADIENTS+STEPS))]


def evaluate(task, context):
    import numpy as np
    from scipy.sparse import csr_matrix

    from . import ilvis0_matched_force_average as average
    from . import ilvis0_matched_force_covariance as covariance
    from .ilvis0_error_model import Spec
    from .ilvis0_shared_force_witness import project_witness
    from .ilvis0_solver_position import physical_metric

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if declared not in tasks() or context.manifest['scope'] != SCOPE:
        raise ValueError('exact archived gyro-free witness tasks required')
    material = json.loads(context.input_path().read_bytes())
    imu = task['payload']['imu_type']
    times, tags, coordinates = (np.asarray(material[key]) for key in ('times', 'tags', 'coordinates'))
    windows = material['windows']
    models = average.MATCHED_MODELS
    if (imu != material['imu_type'] or len(windows) != WINDOWS[imu] or coordinates.shape != (len(times), 3)
            or len(tags) != len(times) or not np.isfinite(coordinates).all() or np.any(np.diff(tags) <= 0)
            or len(models)*len(average.support.CLOCKS) != PER_WINDOW or set(material['gains']) != set(models)):
        raise ValueError('full matched GPS and accelerometer window history required')
    metric = physical_metric(coordinates)
    shared = np.diag(np.square(covariance.SHARED_SIGMA))
    law = Spec(np.diag(np.square(covariance.WHITE_SIGMA)), ((covariance.TAU_S, shared),),
               shared, shared, times[0], times[-1]-times[0])
    columns, values, boundaries, sigma, deficit, layout, active = [], [], [0], [], [], [], []
    context.charge(bound_calls=1, bound_steps=MAX_GRADIENTS)
    for window in windows:
        first, last, target = window['first'], window['last'], window['target']
        stop = last+1
        train = stop <= material['cut']
        if (not 0 <= first <= target <= last < len(times) or stop-first != window['sample_count']
                or first < material['cut'] < stop or train != (window['side'] == 'training')):
            raise ValueError('window differs from its saved contiguous split')
        support = slice(first, stop)
        weights = average.quadratic_weights((tags[support]-tags[target])/1000.)
        local = coordinates[support].copy()
        local[:, 1] = np.unwrap(local[:, 1])
        jet = weights @ local
        for clock in average.support.CLOCKS:
            clock_row = window['clocks'][clock]
            interval = clock_row['interval']
            for model in models:
                low = clock_row['acceleration_lower_mps2']/(1.+material['gains'][model])
                high = clock_row['prediction_upper_mps2'][model]
                gap = low-np.nextafter(high, np.inf)
                deficit.append(gap)
                layout.append((model, clock, window['side'], int(tags[target]), interval, support, weights, low))
                if gap <= 0.:
                    continue
                if len(active) >= MAX_GRADIENTS:
                    raise ValueError('finite active proposal gradient allowance exceeded')
                gradient = covariance.mean_gradient(jet, interval, model=model, background_rate_rads=average.rate(model),
                    gravity_mps2=average.GRAVITY, disc_radius_m=average.RADIUS)
                row = (weights.T @ gradient)/metric[support]
                columns.extend(range(3*first, 3*stop))
                values.extend(row.ravel())
                boundaries.append(len(values))
                sigma.append(clock_row['sigma_mps2'][model])
                active.append(len(deficit)-1)
    if not active:
        raise ValueError('at least one positive saved IMU8 deficit required')
    matrix = csr_matrix((values, columns, boundaries), shape=(len(active), 3*len(times)))
    proposal = np.asarray(deficit)[active]+PROPOSAL_MARGIN
    context.charge(bound_calls=1, bound_steps=STEPS)
    witness = project_witness(times, law, matrix, proposal, sigma, maximum_steps=STEPS)
    correction = witness.pop('error_m').reshape((-1, 3))
    context.save('receiver-error.json', dict(times_s=times.tolist(), axes=['north', 'east', 'up'],
                 correction_m=correction.tolist(), projected_rows=active,
                 projected=matrix.dot(correction.ravel()).tolist(), **witness))
    adjusted = coordinates + correction/metric
    rows = []
    time_offset = average.support.TIME_OFFSET_S
    context.charge(bound_calls=1, bound_steps=PER_WINDOW*len(windows))
    for before, (model, clock, side, tag, interval, support, weights, low) in zip(deficit, layout, strict=True):
        local = adjusted[support].copy()
        local[:, 1] = np.unwrap(local[:, 1])
        predicted_lo, predicted_hi = average.bound_average(weights @ local, interval,
            offset_bounds_s=(-time_offset, time_offset), subdivisions=average.SUBDIVISIONS,
            model=model, background_rate_rads=average.rate(model), gravity_mps2=average.GRAVITY,
            disc_radius_m=average.RADIUS)
        rows.append(dict(model=model, clock=clock, side=side, gps_tag=tag, initial_deficit_mps2=float(before),
            reconstructed_deficit_mps2=float(low-np.nextafter(predicted_hi, np.inf)),
            reconstructed_stronger_deficit_mps2=float(low-np.nextafter(predicted_lo, np.inf))))
    context.save('inequalities.json', rows)
    return dict(passed=True, imu_type=imu, inequalities=len(rows), proposal_gradients=len(active),
                initial_violations=sum(bool(row['initial_deficit_mps2'] > 0.) for row in rows),
                remaining_violations=sum(bool(row['reconstructed_deficit_mps2'] > 0.) for row in rows),
                remaining_stronger=sum(bool(row['reconstructed_stronger_deficit_mps2'] > 0.) for row in rows),
                largest_position_correction_m=float(np.max(np.linalg.norm(correction, axis=1))),
                **witness, fit_starts=0, gyro_observations_used=False, scientific_decision='abstain')


def prepare(root):
    from .studies.artifacts import atomic
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing common force witness freeze')
    with closing(ClosedStudy(root, 'data/'+ORIGINAL)) as prior:
        stopped = prior.envelope('imu8')['result']
        charged = prior.rows['imu8']['charged']
        if (prior.completion['manifest_sha256'] != ORIGINAL_SHA
                or prior.completion['state'] != 'terminal' or not prior.rows['imu21']['passed']
                or stopped.get('error_type') != 'BudgetStopped'
                or stopped.get('reason') != 'original cooperative deadline exhausted'
                or charged != dict(bound_calls=1, bound_steps=4864, native_calls=0, packet_visits=0)):
            raise ValueError('original IMU8 gradient timeout and sealed IMU21 result required')
        material = prior.input('imu8', raw=True)
    base.mkdir(parents=True)
    path = base/'imu8.json'
    atomic(path, material)
    inputs = {'plan': PLAN, 'imu8': path.relative_to(root).as_posix()}
    adapter = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=tasks(),
        workers=1, threads=1, maximum_wall_s=120., sources=source_closure(root, [adapter, PLAN])), root).prepare(root)
    print(json.dumps(dict(study=ID, limits=manifest['limits']), sort_keys=True))


if __name__ == '__main__':
    prepare(Path.cwd())
