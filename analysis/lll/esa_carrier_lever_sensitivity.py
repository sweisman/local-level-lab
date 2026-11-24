# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound the effect of a fixed antenna-to-IMU offset error on a saved ESA score."""

import argparse
from contextlib import closing
import io
import json
import math
from pathlib import Path


ID = 'esa-carrier-lever-sensitivity-v1'
SCOPE = 'ESA 187 anchored carrier score sensitivity to fixed antenna offset error'
FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_CARRIER_LEVER_SENSITIVITY_PLAN.md'
RESULT = FOLDER+'esa-carrier-lever-sensitivity-result.json'
IMU_PARENT = 'data/prediction-observed-development-continuation-v1-20261113'
SCORE_PARENT = 'data/esa-carrier-score-bound-v1'
PARENTS = {
    IMU_PARENT: ('2dbbd77362e7d21cad709f0a1001173ac99b44c3ea30e7021b6ce513de1e9788',
                 '1add15ded2e8c72e204dee11086833ebaea9b6c4c0a8e69d1fa82be4f2b5bc6d'),
    SCORE_PARENT: ('72596778c27d0f32d8d2b0efffda493d16e655c11e509586870b51db6f480a3b',
                   '6d9b144d6a3163d3027c713cac1edc1263a2ebe2838dc0f8abf9707e9a6c713e'),
}
SCORE_POINTS = 120
MAX_PACKETS = 37_000
ANGULAR_ALLOWANCE_RADS = math.radians(15.0411)/3600
TASK = dict(identity='anchored-fixed-offset', input_key='gyro', payload={},
            limits=dict(native_calls=0, packet_visits=0, bound_calls=2,
                        bound_steps=MAX_PACKETS+2*SCORE_POINTS))


def relative_rotations(edges, increments, anchor, targets):
    """Compose body increments over the requested partial and whole packets."""
    import numpy as np
    from scipy.spatial.transform import Rotation

    edges, increments, targets = (np.asarray(x, dtype=float) for x in (edges, increments, targets))
    if (edges.ndim != 1 or edges.size < 2 or increments.shape != (edges.size-1, 3)
            or targets.ndim != 1 or targets.size == 0
            or not all(np.isfinite(x).all() for x in (edges, increments, targets))
            or not edges[0] <= anchor < targets[0] <= targets[-1] <= edges[-1]
            or not (np.diff(edges) > 0).all() or not (np.diff(targets) > 0).all()):
        raise ValueError('finite, strictly ordered packet edges and score times required')
    durations = np.diff(edges)
    rotations = Rotation.from_rotvec(increments)
    index = int(np.searchsorted(edges, anchor, side='right')-1)
    cursor, current = anchor, Rotation.identity()
    at_targets = []
    for target in targets:
        while edges[index+1] <= target:
            if cursor == edges[index]:
                current = current*rotations[index]
            else:
                share = (edges[index+1]-cursor)/durations[index]
                current = current*Rotation.from_rotvec(share*increments[index])
            index += 1
            cursor = edges[index]
            if cursor == target:
                break
        if cursor < target:
            share = (target-cursor)/durations[index]
            current = current*Rotation.from_rotvec(share*increments[index])
            cursor = target
        at_targets.append(current.as_matrix())
    return np.array(at_targets)


def score_weights_ecef(positions, metric, taps):
    """Apply the transpose of the saved coordinate metric's position derivative."""
    import numpy as np

    from .gnss_position import local_rotation

    eccentricity_squared = (2-1/298.257223563)/298.257223563
    result = []
    for (latitude, longitude, height), tap in zip(positions, taps, strict=True):
        root = math.sqrt(1-eccentricity_squared*math.sin(latitude)**2)
        prime_vertical = 6378137/root
        north = prime_vertical*(1-eccentricity_squared)/root**2+height
        east = (prime_vertical+height)*math.cos(latitude)
        result.append((tap*metric/np.asarray([north, east, 1.]))@local_rotation(latitude, longitude))
    return np.array(result)


def score_bound(rotations, weights):
    """Upper-bound the anchored score change per metre for any fixed offset and pose."""
    import numpy as np

    weights = np.asarray(weights)
    delta = np.asarray(rotations)-np.eye(3)
    triangle = np.linalg.norm(weights, axis=1)@np.linalg.norm(delta, ord=2, axis=(1, 2))
    # The tensor sends a unit offset to a matrix of score coefficients for
    # the initial orientation Q. Its Frobenius norm is bounded by the tensor
    # operator norm. Every orthogonal Q has Frobenius norm sqrt(3).
    tensor = np.einsum('ti,tkj->ikj', weights, delta).reshape(9, 3)
    return float(min(triangle, math.sqrt(3)*np.linalg.norm(tensor, ord=2)))


def prepare(root):
    import numpy as np

    from .esa_carrier_score_bound import score_grid
    from .esa_rinex_code_comparison import coordinates
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('preserve the original finite offset sensitivity study')
    parents = {}
    with closing(ClosedStudy(root, SCORE_PARENT)) as study:
        parents[SCORE_PARENT] = verify_parent(study)
        score, anchor, path, metric = map(study.input, ('score', 'anchor', 'path', 'metric'))
        times, taps = score_grid(score, anchor)
        start = float(anchor['time_s'])
        path_times = [start, *(row['seconds'] for row in path)]
        path_positions = np.array([coordinates([anchor])[0], *(row['position'] for row in path)])
        if (len(times) != SCORE_POINTS or len(path_times) != 2*SCORE_POINTS+1
                or not start < times[0] < times[-1] <= path_times[-1]
                or not np.all(np.diff(path_times) > 0)
                or np.any(abs(np.diff(path_positions[:, 1])) > np.pi)):
            raise ValueError('original half-second path and supported score times required')
        positions = np.array([np.interp(times, path_times, axis) for axis in path_positions.T]).T
        fixed = dict(start_gps_s=start, score_times_gps_s=times, taps=taps.tolist(),
                     metric=metric, positions=positions.tolist(), original_gap_exact=score['gap'])
    with closing(ClosedStudy(root, IMU_PARENT)) as study:
        parents[IMU_PARENT] = verify_parent(study)
        binding = study.input('saved-input-binding')
        if (binding['source_id'] != 'esa-99f1530c3eda4318'
                or binding['original_reads'] != 0 or binding['protected_reads'] != 0):
            raise ValueError('sealed ESA 187 development material required')
        interval = study.input('interval', raw=True)
        with np.load(io.BytesIO(interval), allow_pickle=False) as archive:
            edges = archive['raw_time_s']
            first = int(np.searchsorted(edges, start, side='right')-1)
            stop = int(np.searchsorted(edges, times[-1]))
            if not 0 <= first < stop < len(edges) or stop-first > MAX_PACKETS:
                raise ValueError('sealed intervals do not cover the exact times within allowance')
            sample_edges = edges[first:stop+1]
            increments = archive['theta'][first:stop]
            dt = archive['dt'][first:stop]
            if (not np.allclose(np.diff(sample_edges), dt, atol=2e-9, rtol=0)
                    or not np.all((dt > 0) & (dt < .005))):
                raise ValueError('logged packet time gaps or interval disagreement')
        fixed.update(imu_interval_sha256=digest(interval), first_packet_index=first,
                     stop_packet_index_exclusive=stop, source_id=binding['source_id'], parents=parents)
    buffer = io.BytesIO()
    np.savez(buffer, edges=sample_edges, increments=increments)
    inputs = {'plan': PLAN}
    for key, payload in {'gyro': buffer.getvalue(), 'fixed': encoded(fixed)}.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, payload)
        inputs[key] = name
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, 'analysis/tests/test_esa_carrier_lever_sensitivity.py'))
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                                     tasks=[TASK], workers=1, threads=1, maximum_wall_s=60), root).prepare(root)['limits']


def verify_parent(study):
    completion = study.completion
    if (completion['state'] != 'complete' or len(study.rows) != 1
            or (completion['manifest_sha256'], completion['summary_sha256']) != PARENTS[study.prefix]):
        raise ValueError('exact closed parent study required')
    study.envelope(next(iter(study.rows)))
    return completion


def evaluate(task, context):
    from fractions import Fraction

    import numpy as np
    from scipy.spatial.transform import Rotation

    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('frozen anchored offset sensitivity required')
    context.charge(bound_calls=1, bound_steps=MAX_PACKETS)
    fixed = json.loads(context.input_path('fixed').read_bytes())
    times, start = np.asarray(fixed['score_times_gps_s']), fixed['start_gps_s']
    with np.load(context.input_path('gyro'), allow_pickle=False) as saved:
        edges, increments = saved['edges'], saved['increments']
    if len(increments) > MAX_PACKETS or len(times) != SCORE_POINTS:
        raise ValueError('frozen analysis limits exceeded')
    rotations = relative_rotations(edges, increments, start, times)
    context.charge(bound_calls=1, bound_steps=2*SCORE_POINTS)
    weights = score_weights_ecef(fixed['positions'], np.array(fixed['metric']), fixed['taps'])
    upper = score_bound(rotations, weights)
    angular_extra = float(np.linalg.norm(weights, axis=1)@(
        2*np.sin(ANGULAR_ALLOWANCE_RADS*(times-start)/2)))
    gap = float(Fraction(fixed['original_gap_exact']))
    if not 0 < upper < math.inf or not 0 < gap < math.inf:
        raise ValueError('finite positive sensitivity and original gap required')
    return dict(passed=True, scientific_decision='abstain', packets=len(increments),
        score_points=len(times), start_gps_s=start, stop_gps_s=float(times[-1]), original_score_gap=gap,
        peak_relative_angle_deg=float(np.degrees(max(Rotation.from_matrix(rotations).magnitude()))),
        nominal_score_bound_per_m=upper, one_field_rate_score_bound_per_m=upper+angular_extra,
        nominal_minimum_offset_m=gap/upper, one_field_rate_minimum_offset_m=gap/(upper+angular_extra),
        one_field_rate_allowance_rads=ANGULAR_ALLOWANCE_RADS,
        score_gap_fraction_for_10cm=.1*upper/gap, score_gap_fraction_for_10cm_with_allowance=.1*(upper+angular_extra)/gap,
        original_reads=0, protected_reads=0, new_fits=0)


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import encoded
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('complete result and charges required')
        result = dict(envelope['result'], charged=envelope['charged'], completion=study.completion,
                      inputs=study.manifest['inputs'], parent_completions=study.input('fixed')['parents'])
    _write_equal(root/RESULT, encoded(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    action = parser.parse_args().action
    print(json.dumps({'prepare': prepare, 'report': report}[action](Path.cwd()), sort_keys=True))
