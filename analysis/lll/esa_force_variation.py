# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate time-weighted force-vector variation from the common-support mismatch."""

import argparse
import hashlib
import json
import os
from pathlib import Path


BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_FORCE_VARIATION_PLAN.md'
FREEZE = BASE+'esa-force-variation-freeze.json'
RESULT = BASE+'esa-force-variation-result.json'
MATCHED_SHA = 'f27d59a5f3b44118e4ec6af66a905809b519c03283c33cfefac7dd987b168079'
BINS = (.1, 1.)


def variation(times, force, angular_speed, knots, kernel, primitive, *, width):
    """Time-weight both orders of averaging with exactly split held intervals."""
    import numpy as np
    from .esa_matched_force import sample_weights

    time, force, angular_speed, knots = (np.asarray(value, float) for value in (times, force, angular_speed, knots))
    if (time.ndim != 1 or len(time) < 2 or force.shape != (len(time)-1, 3)
            or angular_speed.shape != (len(time)-1,) or np.any(angular_speed < 0.)
            or not all(np.isfinite(value).all() for value in (force, angular_speed, time))
            or np.any(np.diff(time) <= 0.) or time[0] > knots[0] or time[-1] < knots[-1]
            or not np.isfinite(width) or width <= 0.):
        raise ValueError('complete logged vector support and positive bin duration required')
    interior = np.arange(1, int(np.ceil((knots[-1]-knots[0])/width)))*width+knots[0]
    edges = np.r_[knots[0], interior[interior < knots[-1]], knots[-1]]
    segments = np.unique(np.r_[edges, time[(time > knots[0]) & (time < knots[-1])]])
    selected = np.searchsorted(time, segments[:-1], side='right')-1
    bucket = np.searchsorted(edges, segments[:-1], side='right')-1
    weights = sample_weights(segments, knots, kernel, primitive)
    count = len(edges)-1
    total_mass = np.bincount(bucket, weights=weights, minlength=count)
    vectors = force[selected]
    weighted_magnitudes = weights*np.linalg.norm(vectors, axis=1)
    magnitude_per_bin = np.bincount(bucket, weights=weighted_magnitudes, minlength=count)
    vector_per_bin = np.column_stack([np.bincount(bucket, weights=weights*column, minlength=count)
                                      for column in vectors.T])
    angle_budget = np.bincount(bucket, weights=np.diff(segments)*angular_speed[selected], minlength=count)
    bounded_angle = np.minimum(angle_budget, np.pi/2)
    rotation_gap = float((2.*np.sin(bounded_angle/2.)**2)@magnitude_per_bin)
    raw = float(magnitude_per_bin.sum())
    binned = float(np.linalg.norm(vector_per_bin, axis=1).sum())
    if binned > raw+1e-10:
        raise ValueError('weighted vector averaging violated the triangle inequality')
    return dict(average_of_magnitudes_m_s2=raw, magnitude_after_bin_average_m_s2=binned,
        gap_m_s2=max(0., raw-binned), orientation_only_upper_gap_m_s2=rotation_gap,
        max_logged_turn_budget_deg=float(np.rad2deg(np.max(angle_budget))),
        positive_bins=int(np.count_nonzero(total_mass)))


def compare(rows, prior, imu_times, acceleration, angular_rate):
    import numpy as np
    from .esa_matched_force import WIDTH_REPORTS, acceleration_kernel
    from .esa_receiver_acceleration import GROUP_SIZE

    time = np.asarray([r['time_s'] for r in rows])
    angular_speed = np.linalg.norm(angular_rate, axis=1)
    result = []
    for mid, previous in zip(range(GROUP_SIZE//2, len(rows), GROUP_SIZE), prior, strict=True):
        half = WIDTH_REPORTS//2
        center = time[mid]
        support = time[mid-half:mid+half+1]
        if (center != previous['center_time_s'] or rows[mid]['sequence'] != previous['center_sequence']
                or support[[0,-1]].tolist() != previous['support_s']):
            raise ValueError('changed frozen receiver support')
        relative = support-center
        _, kernel, integral = acceleration_kernel(relative, center=half)
        first = np.searchsorted(imu_times, support[0], side='right')-1
        last = np.searchsorted(imu_times, support[-1], side='left')
        if not 0 <= first < last < len(imu_times) or last-first != previous['imu_samples']:
            raise ValueError('raw support does not reproduce the prior sample count')
        now = imu_times[first:last+1]-center
        force, gyro = acceleration[first:last], angular_speed[first:last]
        cases = {str(width): variation(now, force, gyro, relative, kernel, integral, width=width) for width in BINS}
        expected = previous['raw_imu_matched_m_s2']
        if any(abs(row['average_of_magnitudes_m_s2']-expected) > 1e-9 for row in cases.values()):
            raise ValueError('original matched magnitude does not reproduce')
        receiver = previous['receiver_matched_m_s2']
        for row in cases.values():
            row['binned_minus_receiver_m_s2'] = row['magnitude_after_bin_average_m_s2']-receiver
        result.append(dict(center_time_s=float(center), center_sequence=previous['center_sequence'],
            raw_minus_receiver_m_s2=previous['logged_minus_receiver_m_s2'], cases=cases))
    return result


def run(root, action):
    from .airquantumgrav_inventory import IMU_NAME, METADATA, validate_context
    from .airquantumgrav_packet_slice import held_measurements
    from .esa_component_preflight import MAX_DECODE_PER_WINDOW, RECORDS, WIDTH
    from .esa_matched_force import RESULT as MATCHED_RESULT, transfer_offsets
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
    windows, receiver = plan['windows'], metadata['receiver_report']
    prior_bytes = (root/MATCHED_RESULT).read_bytes()
    prior = json.loads(prior_bytes)
    if (digest(prior_bytes) != MATCHED_SHA or plan['fit_authorized'] is not False
            or plan['confirmation_authorized'] is not False or len(windows) != 3 or receiver['epochs'] != 64080
            or set(prior['windows']) != {w['window_id'] for w in windows}
            or any(w['group_id'] != context['group_id'] or w['receiver_source_sha256'] != context['receiver_sha256']
                   for w in windows) or metadata['inspection']['records'] != RECORDS):
        raise ValueError('exact development record, matched result and three earlier supports required')
    sources = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_esa_force_variation.py')
    freeze = encoded(dict(environment=runtime_environment(), selection_sha256=digest(selection),
        matched_result_sha256=MATCHED_SHA, metadata_hashes={name:digest(data) for name, data in raw.items()},
        sources={name:digest((root/name).read_bytes()) for name in source_closure(root, sources)},
        widths_s=BINS, source_hash_passes=1, expected_receiver_queries=2400, maximum_imu_rows=3*MAX_DECODE_PER_WINDOW,
        expected_supports=96, variation_calculations=192, scalar_offsets=6, fit_starts=0, later_queries=0, protected_reads=0))
    if action == 'freeze':
        _write_equal(root/FREEZE, freeze)
        return dict(freeze_sha256=digest(freeze))
    if (root/FREEZE).read_bytes() != freeze:
        raise ValueError('force variation inputs or numerical definition changed')
    selected = _read_queries(safe_path(root, SOURCE), windows, context['receiver_sha256'], receiver['epochs'])
    original = safe_path(root, str(Path(METADATA['inspection']).with_name(IMU_NAME)))
    decoded, results = 0, {}
    with original.open('rb') as stream:
        start = os.fstat(stream.fileno())
        if start.st_size != WIDTH*(RECORDS+1) or hashlib.file_digest(stream, 'sha256').hexdigest() != context['imu_source_sha256']:
            raise ValueError('opened original IMU source differs')
        stream.seek(0)
        header = stream.read(WIDTH)
        for name, rows in selected.items():
            times, force, gyro = held_measurements(stream, header, row_bytes=WIDTH, row_count=RECORDS,
                maximum_samples=MAX_DECODE_PER_WINDOW, lower=rows[0]['time_s'], upper=rows[-1]['time_s'])
            decoded += len(force)
            results[name] = compare(rows, prior['windows'][name], times, force, gyro)
        end = os.fstat(stream.fileno())
        if (start.st_size, start.st_mtime_ns, start.st_ctime_ns) != (end.st_size, end.st_mtime_ns, end.st_ctime_ns):
            raise ValueError('original IMU changed during verified reads')
    if sum(map(len, results.values())) != 96 or decoded != prior['imu_rows_decoded']:
        raise ValueError('frozen support coverage or decoded sample count differs')
    offsets = {str(width): transfer_offsets({name: [row['cases'][str(width)]['binned_minus_receiver_m_s2'] for row in cases]
                                             for name, cases in results.items()}) for width in BINS}
    report = encoded(dict(freeze_sha256=digest(freeze), windows=results, imu_rows_decoded=decoded, receiver_queries=2400,
                          offset_transfer=offsets, fit_starts=0, later_queries=0, protected_reads=0, scientific_decision='abstain'))
    _write_equal(root/RESULT, report)
    return dict(sha256=digest(report), centers=96, variation_calculations=192)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(json.dumps(run(Path.cwd(), parser.parse_args().action), sort_keys=True))
