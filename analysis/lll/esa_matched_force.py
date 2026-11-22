# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare time-matched receiver and raw iMAR force on opened training supports."""

import argparse
from bisect import bisect_left
import hashlib
import itertools
import json
import math
import os
from pathlib import Path


BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_MATCHED_FORCE_PLAN.md'
FREEZE = BASE+'esa-matched-force-freeze.json'
RESULT = BASE+'esa-matched-force-result.json'
POSITION_SHA = '2dd9274b4ea68bb7b7c893bdd2b520e7a2638b4eb979ce2cadff38d81291996b'
WIDTH_REPORTS = 25
ORDERS = (2, 4)


def acceleration_kernel(times, *, center):
    """Return cubic coefficient operator and the exact second-derivative time kernel."""
    import numpy as np

    times = np.asarray(times, float)
    if (times.ndim != 1 or len(times) < 5 or not 0 < center < len(times)-1
            or not np.isfinite(times).all() or np.any(np.diff(times) <= 0.)):
        raise ValueError('ordered receiver support around the evaluation center required')
    time = times-times[center]
    scale = np.max(abs(time))
    design = np.polynomial.polynomial.polyvander(time/scale, 3)
    operator = np.linalg.pinv(design)/scale**np.arange(4)[:, None]
    # Summing the hinge functions follows by twice integrating acceleration
    # to get position. The second derivative weights remove initial x and v.
    kernel = np.maximum(time[None, :]-time[:, None], 0.) @ (2.*operator[2])
    if np.min(kernel) < -1e-10:
        raise ValueError('position derivative does not give a nonnegative averaging kernel')
    kernel = np.maximum(kernel, 0.)
    area = np.r_[0., np.cumsum((kernel[:-1]+kernel[1:])*np.diff(time)/2.)]
    if abs(area[-1]-1.) > 1e-10:
        raise ValueError('unit-mass acceleration kernel required')
    return operator, kernel, area


def sample_weights(times, knots, kernel, primitive):
    """Integrate the piecewise-linear kernel over each clipped sample hold."""
    import numpy as np

    times = np.asarray(times, float)
    if (times.ndim != 1 or len(times) < 2 or not np.isfinite(times).all()
            or np.any(np.diff(times) <= 0.) or times[0] > knots[0] or times[-1] < knots[-1]):
        raise ValueError('complete timed raw rate support required')
    clipped = np.clip(times, knots[0], knots[-1])
    index = np.clip(np.searchsorted(knots, clipped, side='right')-1, 0, len(knots)-2)
    duration = clipped-knots[index]
    slope = (kernel[index+1]-kernel[index])/(knots[index+1]-knots[index])
    cumulative = primitive[index]+kernel[index]*duration+.5*slope*duration**2
    weights = np.diff(cumulative)
    if np.min(weights) < -1e-12 or abs(weights.sum()-1.) > 1e-10:
        raise ValueError('sample weights do not preserve the receiver kernel mass')
    return np.maximum(weights, 0.)


def read_force(stream, header, *, lower, upper):
    import numpy as np
    from .airquantumgrav import records
    from .esa_component_preflight import MAX_DECODE_PER_WINDOW, RECORDS, WIDTH

    def line():
        raw = stream.read(WIDTH)
        if len(raw) != WIDTH or not raw.endswith(b'\n') or b'\n' in raw[:-1]:
            raise ValueError('unexpected fixed-width iMAR record boundary')
        return raw

    def timestamp(index):
        stream.seek(WIDTH*(index+1))
        time = float(line().split(maxsplit=1)[0])
        if not 0 <= time < 604800:
            raise ValueError('finite GPS seconds of week required')
        return time

    indexed = range(RECORDS)
    first, last = (bisect_left(indexed, bound, key=timestamp) for bound in (lower, upper))
    if not 0 <= first < last < RECORDS:
        raise ValueError('valid original raw force support required')
    if timestamp(first) > lower:
        first -= 1
    if not 0 <= first < last or last-first > MAX_DECODE_PER_WINDOW:
        raise ValueError('fixed observation allowance or original support exceeded')
    limit = timestamp(last)
    stream.seek(WIDTH*(first+1))
    decoded = records(itertools.chain((header,), (line() for _ in range(first, last))))
    samples = np.fromiter(((r['gps_time_s'], math.hypot(*r['acceleration_mps2'])) for r in decoded),
                          dtype=np.dtype((np.float64, 2)), count=last-first)
    time = np.r_[samples[:, 0], limit]
    if (not time[0] <= lower < time[1] or not time[-2] < upper <= time[-1]
            or np.any(np.diff(time) <= 0.) or np.any(np.diff(time) > .005)):
        raise ValueError('original raw timing support or continuity failed')
    return time, samples[:, 1]


def receiver_average(knots, kernel, fit, reference, *, order):
    import numpy as np
    from .esa_receiver_acceleration import GRAVITY
    from .ilvis0_receiver_force import evaluate
    from .models import OMEGA_E, WGS84_A

    nodes, weights = np.polynomial.legendre.leggauss(order)
    half = np.diff(knots)[:, None]/2.
    grid = ((knots[:-1]+knots[1:])[:, None]/2.+half*nodes).ravel()
    weights = (half*weights).ravel()*np.interp(grid, knots, kernel)
    values = np.polynomial.polynomial.polyval(grid, fit).T+reference
    rate = np.polynomial.polynomial.polyval(grid, np.polynomial.polynomial.polyder(fit)).T
    acceleration = np.polynomial.polynomial.polyval(grid, np.polynomial.polynomial.polyder(fit, 2)).T
    norms = [np.linalg.norm(evaluate(p, v, a, model='sphere_rotating', background_rate_rads=OMEGA_E,
                                     gravity_mps2=GRAVITY, disc_radius_m=WGS84_A)['specific_force_ned_mps2'])
             for p, v, a in zip(values, rate, acceleration, strict=True)]
    return float(weights@norms)


def compare(rows, prior, imu_times, magnitudes):
    import numpy as np
    from .esa_receiver_acceleration import GROUP_SIZE
    from .esa_receiver_acceleration import GRAVITY
    from .ilvis0_receiver_force import evaluate
    from .models import OMEGA_E, WGS84_A

    time = np.asarray([r['time_s'] for r in rows])
    coordinates = np.asarray([[r['latitude_deg'], r['longitude_deg'], r['height_m']] for r in rows])
    coordinates[:, :2] = np.deg2rad(coordinates[:, :2])
    coordinates[:, 1] = np.unwrap(coordinates[:, 1])
    result = []
    for mid, previous in zip(range(GROUP_SIZE//2, len(rows), GROUP_SIZE), prior, strict=True):
        if time[mid] != previous['center_time_s'] or rows[mid]['sequence'] != previous['center_sequence']:
            raise ValueError('changed sealed receiver center')
        half = WIDTH_REPORTS//2
        block = slice(mid-half, mid+half+1)
        center = time[mid]
        absolute = time[block]
        relative = absolute-center
        operator, kernel, area = acceleration_kernel(relative, center=half)
        reference = coordinates[mid]
        fit = operator@(coordinates[block]-reference)
        position, velocity, acceleration = reference+fit[0], fit[1], 2.*fit[2]
        nominal = evaluate(position, velocity, acceleration, model='sphere_rotating',
                           background_rate_rads=OMEGA_E, gravity_mps2=GRAVITY, disc_radius_m=WGS84_A)
        baseline = previous['stencils'][str(WIDTH_REPORTS)]
        old = baseline['force_magnitude_m_s2']
        if abs(np.linalg.norm(nominal['specific_force_ned_mps2'])-old) > 1e-9:
            raise ValueError('cubic receiver fit does not reproduce sealed center')
        first = np.searchsorted(imu_times, absolute[0], side='right')-1
        last = np.searchsorted(imu_times, absolute[-1], side='left')
        if not 0 <= first < last < len(imu_times):
            raise ValueError('IMU does not bracket receiver support')
        observed = float(sample_weights(imu_times[first:last+1]-center, relative, kernel, area)@magnitudes[first:last])
        estimates = [receiver_average(relative, kernel, fit, reference, order=order) for order in ORDERS]
        quad_difference = abs(estimates[1]-estimates[0])
        if quad_difference > 1e-8:
            raise ValueError('receiver magnitude quadrature did not converge at fixed orders')
        result.append(dict(center_time_s=float(center), center_sequence=rows[mid]['sequence'],
            support_s=absolute[[0,-1]].tolist(), imu_samples=int(last-first), receiver_center_m_s2=old,
            receiver_matched_m_s2=estimates[1], receiver_quadrature_difference_m_s2=quad_difference,
            raw_imu_matched_m_s2=observed, logged_minus_receiver_m_s2=observed-estimates[1]))
    return result


def transfer_offsets(differences):
    import numpy as np

    offsets = {}
    for label, values in differences.items():
        pool = np.concatenate([v for name, v in differences.items() if name != label])
        offset = float(np.median(pool))
        residual = np.asarray(values)-offset
        offsets[label] = dict(offset_m_s2=offset, other_training_values=len(pool), evaluation_values=len(values),
            residual_rms_m_s2=float(np.sqrt(np.mean(residual**2))), residual_median_m_s2=float(np.median(residual)))
    return offsets


def run(root, action):
    from .airquantumgrav_inventory import IMU_NAME, METADATA, validate_context
    from .esa_component_preflight import MAX_DECODE_PER_WINDOW, RECORDS, WIDTH
    from .esa_position_acceleration import RESULT as POSITION_RESULT
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .receiver_route_information import SELECTION, SOURCE, _read_queries
    from .studies.artifacts import digest, encoded, safe_path
    from .studies.dependencies import source_closure

    raw = {key: (root/name).read_bytes() for key, name in METADATA.items()}
    metadata = {key: json.loads(value) for key, value in raw.items()}
    context = validate_context(**metadata)
    selection = (root/SELECTION).read_bytes()
    plan = json.loads(selection)['plan']
    windows = plan['windows']
    inventory = metadata['receiver_report']
    prior_bytes = (root/POSITION_RESULT).read_bytes()
    prior = json.loads(prior_bytes)['windows']
    if (digest(prior_bytes) != POSITION_SHA or plan['fit_authorized'] is not False
            or plan['confirmation_authorized'] is not False or inventory['epochs'] != 64080
            or len(windows) != 3 or set(prior) != {w['window_id'] for w in windows}
            or any(w['group_id'] != context['group_id'] or w['receiver_source_sha256'] != context['receiver_sha256']
                   for w in windows) or metadata['inspection']['records'] != RECORDS):
        raise ValueError('exact authorized recording, receiver fit and three training supports required')
    sources = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_esa_matched_force.py')
    freeze = encoded(dict(environment=runtime_environment(), selection_sha256=digest(selection),
        position_result_sha256=POSITION_SHA, metadata_hashes={name:digest(data) for name, data in raw.items()},
        sources={name:digest((root/name).read_bytes()) for name in source_closure(root, sources)},
        width=WIDTH_REPORTS, quadrature_orders=ORDERS, source_hash_passes=1, expected_receiver_queries=2400,
        maximum_imu_rows=3*MAX_DECODE_PER_WINDOW, expected_kernels=96, scalar_offsets=3,
        fit_starts=0, later_queries=0, protected_reads=0))
    if action == 'freeze':
        _write_equal(root/FREEZE, freeze)
        return dict(freeze_sha256=digest(freeze))
    if (root/FREEZE).read_bytes() != freeze:
        raise ValueError('matched force inputs or frozen definition changed')
    selected = _read_queries(safe_path(root, SOURCE), windows, context['receiver_sha256'], inventory['epochs'])
    original = safe_path(root, str(Path(METADATA['inspection']).with_name(IMU_NAME)))
    decoded, results = 0, {}
    with original.open('rb') as stream:
        start = os.fstat(stream.fileno())
        if start.st_size != WIDTH*(RECORDS+1) or hashlib.file_digest(stream, 'sha256').hexdigest() != context['imu_source_sha256']:
            raise ValueError('opened original IMU source differs')
        stream.seek(0)
        header = stream.read(WIDTH)
        for name, rows in selected.items():
            times, magnitudes = read_force(stream, header, lower=rows[0]['time_s'], upper=rows[-1]['time_s'])
            decoded += len(magnitudes)
            results[name] = compare(rows, prior[name], times, magnitudes)
        end = os.fstat(stream.fileno())
        if (start.st_size, start.st_mtime_ns, start.st_ctime_ns) != (end.st_size, end.st_mtime_ns, end.st_ctime_ns):
            raise ValueError('original IMU changed during verified reads')
    if sum(map(len, results.values())) != 96:
        raise ValueError('incomplete frozen center coverage')
    offsets = transfer_offsets({name: [row['logged_minus_receiver_m_s2'] for row in rows] for name, rows in results.items()})
    report = encoded(dict(freeze_sha256=digest(freeze), windows=results, imu_rows_decoded=decoded, receiver_queries=2400,
                          offset_transfer=offsets, fit_starts=0, later_queries=0, protected_reads=0, scientific_decision='abstain'))
    _write_equal(root/RESULT, report)
    return dict(sha256=digest(report), training_windows=len(results), centers=96)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(json.dumps(run(Path.cwd(), parser.parse_args().action), sort_keys=True))
