# SPDX-License-Identifier: AGPL-3.0-or-later
"""Propagate receiver velocity covariance into conditional motion proxies."""

import argparse
import json
import math
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from . import receiver_route_information as route
from .esa_gnss_covariance_audit import covariance_matrix
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded, safe_path
from .studies.dependencies import source_closure


PLAN = route.FOLDER + 'RECEIVER_MOTION_PRECISION_PLAN.md'
FREEZE = route.FOLDER + 'receiver-motion-precision-freeze.json'
RESULT = route.FOLDER + 'receiver-motion-precision-result.json'
SPANS = (30, 120)


def velocity_angles(velocity):
    """Course and flight-path angle, and their velocity Jacobians."""
    v = np.asarray(velocity, float)
    if v.ndim != 2 or v.shape[1] != 3 or not len(v) or not np.isfinite(v).all():
        raise ValueError('finite north, east and up velocities required')
    north, east, up = v.T
    speed = np.hypot(north, east)
    if np.any(speed <= 0):
        raise ValueError('nonzero horizontal speed required for course')
    square = speed**2 + up**2
    direction = np.column_stack((np.arctan2(east, north), np.arctan2(up, speed)))
    course = np.column_stack((-east / speed**2, north / speed**2, np.zeros(len(v))))
    flight_angle = np.column_stack((-up * north / (speed * square),
                                    -up * east / (speed * square), speed / square))
    return direction, np.stack((course, flight_angle), axis=1)


def slopes(times, angles, variance, *, span_seconds):
    """Centered linear slopes and uncertainty under stated time assumptions."""
    t, y, var = np.asarray(times, float), np.asarray(angles, float), np.asarray(variance, float)
    if (type(span_seconds) is not int or span_seconds % 2 or span_seconds < 2
            or t.ndim != 1 or len(t) <= span_seconds or y.shape != (len(t), 2)
            or var.shape != y.shape or not np.isfinite(t).all() or not np.isfinite(y).all()
            or not np.isfinite(var).all() or np.any(var < 0)
            or np.any(abs(np.diff(t) - 1.) > .02)):
        raise ValueError('complete one-second angles and nonnegative marginal variances required')
    length = span_seconds + 1
    blocks = sliding_window_view(t - t[0], length)
    centered = blocks - blocks.mean(axis=-1, keepdims=True)
    weights = centered / np.sum(centered**2, axis=-1, keepdims=True)
    angle_blocks = sliding_window_view(y, length, axis=0)
    sd_blocks = sliding_window_view(np.sqrt(var), length, axis=0)
    scaled = weights[:, None, :] * sd_blocks
    return dict(rates_rad_s=np.einsum('wn,wan->wa', weights, angle_blocks),
                independent_sd_rad_s=np.linalg.norm(scaled, axis=-1),
                arbitrary_correlation_sd_upper_rad_s=np.sum(abs(scaled), axis=-1))


def margin(gap_dph, *, motion_error_dph):
    """Exact distance after adding equal Euclidean RMS balls to both paths."""
    if (not math.isfinite(gap_dph) or gap_dph < 0. or not math.isfinite(motion_error_dph)
            or motion_error_dph < 0.):
        raise ValueError('finite nonnegative gap and error allowance required')
    return max(0., gap_dph - 2 * motion_error_dph)


def _describe(rows, prior):
    t = [row['time_s'] for row in rows]
    velocity = [[row[key] for key in ('north_mps', 'east_mps', 'up_mps')] for row in rows]
    angles, jacobian = velocity_angles(velocity)
    angles = np.unwrap(angles, axis=0)
    covariance = np.asarray([covariance_matrix(row['velocity_covariance_export']) for row in rows])
    if np.min(np.linalg.eigvalsh(covariance)) < -1e-10:
        raise ValueError('reported velocity covariance is not positive semidefinite')
    variance = np.einsum('nai,nij,naj->na', jacobian, covariance, jacobian)
    if np.any(variance < 0.):
        raise ValueError('reported covariance does not support this direction')
    summary = {}
    for span in SPANS:
        sample = slopes(t, angles, variance, span_seconds=span)
        rates, independent, upper = (np.rad2deg(sample[key])*3600. for key in
            ('rates_rad_s', 'independent_sd_rad_s', 'arbitrary_correlation_sd_upper_rad_s'))
        summary[str(span)] = dict(epochs=len(rates), median_rate_sd_independent_dph=np.median(
            independent, axis=0).tolist(), median_rate_sd_upper_dph=np.median(upper, axis=0).tolist(),
            maximum_rate_sd_upper_dph=np.max(upper, axis=0).tolist(),
            rate_rms_dph=np.sqrt(np.mean(rates**2, axis=0)).tolist())
    budgets = {}
    for pair, value in prior['geometry']['None'].items():
        gap = value['rms_dph']
        critical = gap / 2.
        if margin(gap, motion_error_dph=critical) != 0.:
            raise ValueError('critical model-pair contact budget must close')
        budgets[pair] = dict(constant_bias_profiled_gap_dph=gap,
                             per_model_motion_rms_at_contact_dph=critical)
    return dict(angle_order=['course', 'flight_path_angle'],
        median_reported_angle_sd_deg=np.rad2deg(np.median(np.sqrt(variance), axis=0)).tolist(),
        slopes=summary, rate_budgets=budgets, empirical_body_motion_bound_established=False,
        scientific_decision='abstain')


def run(root, action):
    paths = (route.FREEZE, route.RESULT, route.SELECTION, route.INVENTORY, route.LEDGER)
    hashes = {path: (root / path).read_bytes() for path in paths}
    prior, result, selection, inventory, ledger = (json.loads(hashes[path]) for path in paths)
    windows = selection['plan']['windows']
    group = next(row for row in ledger['groups'] if row['group_id'] == route.GROUP)
    source = safe_path(root, route.SOURCE)
    if (result['freeze_sha256'] != digest(hashes[route.FREEZE])
            or any(prior['inputs'][path] != digest(hashes[path]) for path in paths[2:])
            or group['role'] != 'development' or source.name != inventory['source_file']
            or prior['receiver_source_sha256'] != inventory['sha256']
            or len(windows) != 3 or set(result['training_windows']) != {w['window_id'] for w in windows}
            or any(w['group_id'] != route.GROUP or w['future_first_index'] <= w['training_last_index']
                   for w in windows)):
        raise ValueError('unchanged development-only source, geometry and training windows required')
    own = Path(__file__).relative_to(root).as_posix()
    config = encoded(dict(inputs={p: digest(b) for p, b in hashes.items()},
        sources={p: digest((root / p).read_bytes()) for p in source_closure(
            root, (own, PLAN, 'analysis/tests/test_receiver_motion_precision.py'))},
        source_sha256=inventory['sha256'], source_row_limit=64080, source_passes=1,
        max_decoded_reports=2400, spans_s=SPANS, threads=1, fits=0,
        later_rows_decoded=0, protected_reads=0, environment=runtime_environment()))
    if action == 'freeze':
        _write_equal(root / FREEZE, config)
        return dict(freeze_sha256=digest(config))
    if (root / FREEZE).read_bytes() != config:
        raise ValueError('same fixed diagnostic inputs required')
    decoded = route._read_queries(source, windows, inventory['sha256'], inventory['epochs'])
    by_window = {key: _describe(rows, result['training_windows'][key]) for key, rows in decoded.items()}
    payload = encoded(dict(freeze_sha256=digest(config), windows=by_window, decoded_reports=2400,
        protected_reads=0, imu_reads=0, later_rows_decoded=0, fits=0, scientific_decision='abstain'))
    _write_equal(root / RESULT, payload)
    return dict(sha256=digest(payload), windows=len(by_window))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
