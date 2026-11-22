# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conditional receiver-only rate contrast for the fixed ESA training windows."""

import argparse
import hashlib
from itertools import combinations, product
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import norm

from . import ilvis0_observation as observation, models
from .airquantumgrav_receiver import records
from .esa_full_receiver_consistency import INVENTORY, SOURCE
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_field import profile_constant_gyro_offset
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded, safe_path
from .studies.dependencies import source_closure


FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER + 'RECEIVER_ROUTE_INFORMATION_PLAN.md'
FREEZE = FOLDER + 'receiver-route-information-freeze.json'
RESULT = FOLDER + 'receiver-route-information-result.json'
SELECTION = 'docs/esa-short-block-development/selection.json'
LEDGER = 'docs/analysis-provenance/ledger.json'
LIMITS = (0., 1., 3., 10., 20., None)
GROUP = 'esa-99f1530c3eda4318'
MODEL_ORDER = ('sphere_rotating', 'sphere_still', 'flat_still')


def bounded_pair(first, second, *, limit_dph):
    """Minimum separation when the two candidates have separate offsets."""
    a, b = np.asarray(first, float), np.asarray(second, float)
    if (a.ndim != 2 or a.shape[1:] != (3,) or a.shape != b.shape or not len(a)
            or not np.isfinite(a).all() or not np.isfinite(b).all()
            or (limit_dph is not None and (not math.isfinite(limit_dph) or limit_dph < 0.0))):
        raise ValueError('complete matched body-rate histories and valid per-model offset needed')
    if limit_dph not in (None, 0.0):
        fit = profile_constant_gyro_offset(a, b, limit_dph=2 * limit_dph)
        return dict(rms_dph=math.degrees(math.sqrt(fit['weighted_mean_square_rads2']))*3600.,
                    bias_difference_dph=fit['offset_dph'].tolist())
    difference = a - b
    offset = difference.mean(axis=0) if limit_dph is None else np.zeros(3)
    error = difference - offset
    return dict(rms_dph=math.degrees(float(np.linalg.norm(error)) / math.sqrt(len(a)))*3600.,
                bias_difference_dph=(np.rad2deg(offset)*3600).tolist())


def receiver_terms(rows):
    """Convert observed velocities to the declared geodetic rate templates."""
    a = np.asarray([[r[k] for k in ('time_s', 'latitude_deg', 'height_m', 'north_mps', 'east_mps')]
                    for r in rows], float)
    if (a.ndim != 2 or len(a) < 3 or not np.isfinite(a).all()
            or np.any(abs(np.diff(a[:, 0]) - 1.0) > 0.02) or np.any(abs(a[:, 1]) >= 85.0)):
        raise ValueError('complete one-second finite nonpolar receiver reports required')
    time, latitude, height, north, east = a.T
    lat = np.deg2rad(latitude)
    m, n = models.radii(lat)
    speed = np.hypot(north, east)
    if np.any(speed <= 0.) or np.any(m + height <= 0.) or np.any(n + height <= 0.):
        raise ValueError('moving receiver support and positive coordinate metric required')
    pd = north / (m + height)
    ld = east / ((n + height) * np.cos(lat))
    return dict(time=time, course=np.arctan2(east, north), speed=speed, latitude=latitude,
        globe=np.column_stack((np.cos(lat)*ld, -pd, -np.sin(lat)*ld)),
        rotation=models.earth_rate_sphere(lat),
        disc=np.column_stack((np.zeros(len(a)), np.zeros(len(a)), -ld)))


def _screen(rows):
    body = receiver_terms(rows)
    course = body['course']
    angles = product(observation.POLICY['crab_envelope_deg'],
                     observation.POLICY['attitude_envelope_deg'],
                     observation.POLICY['attitude_envelope_deg'])
    pair_list = list(combinations(range(3), 2))
    result = {str(b): {} for b in LIMITS}
    for crab, roll, pitch in angles:
        yaw = course + np.deg2rad(crab)
        c, s = np.cos(yaw), np.sin(yaw)
        zero, one = np.zeros(len(c)), np.ones(len(c))
        heading = np.column_stack((c, s, zero, -s, c, zero, zero, zero, one)).reshape(-1, 3, 3)
        roll_pitch = observation.installation.rotation([roll, pitch, 0]).T
        frame = np.einsum('ij,njk->nik', roll_pitch, heading)
        profiles = [np.einsum('nij,nj->ni', frame, v) for v in
                    (body['rotation'] + body['globe'], body['globe'], body['disc'])]
        for i, j in pair_list:
            key = MODEL_ORDER[i] + '/' + MODEL_ORDER[j]
            for limit in LIMITS:
                entry = bounded_pair(profiles[i], profiles[j], limit_dph=limit)
                old = result[str(limit)].get(key)
                if old is None or entry['rms_dph'] < old['rms_dph']:
                    result[str(limit)][key] = dict(entry, crab_deg=crab, roll_deg=roll, pitch_deg=pitch,
                        white_axis_sd_at_80pct_power_dph=entry['rms_dph'] * math.sqrt(len(rows))
                        / (norm.isf(.01) + norm.ppf(.8)))
    return dict(geometry=result, median_ground_speed_mps=float(np.median(body['speed'])),
                latitude_deg=[float(body['latitude'].min()), float(body['latitude'].max())],
                course_span_deg=math.degrees(float(np.ptp(np.unwrap(course)))),
                reported_epochs=len(rows), scientific_decision='abstain')


def _read_queries(source, windows, expected_hash, row_count):
    indexed = {index: window['window_id'] for window in windows for index in
               range(window['training_first_index'], window['training_last_index'] + 1, 2)}
    if len(indexed) != 2400 or max(indexed) >= row_count:
        raise ValueError('three disjoint 800-query training supports required')
    selected = {window['window_id']: [] for window in windows}
    identities = iter(sorted(indexed))
    file_hash = hashlib.sha256()
    count = 0

    def lines():
        nonlocal count
        with source.open('rb') as stream:
            for line in stream:
                file_hash.update(line)
                prefix = line.split(maxsplit=1)[:1]
                if prefix and len(prefix[0]) == 8 and prefix[0].isdigit():
                    index = count
                    count += 1
                    if count > row_count:
                        raise ValueError('source row allowance exceeded')
                    if index in indexed:
                        yield line
                elif count == 0:
                    yield line

    for index, row in zip(identities, records(lines()), strict=True):
        selected[indexed[index]].append(row)
    if count != row_count or file_hash.hexdigest() != expected_hash or any(len(v) != 800 for v in selected.values()):
        raise ValueError('receiver source SHA-256, denominator or query count differs')
    return selected


def run(root, action):
    raw = {name: (root / name).read_bytes() for name in (SELECTION, INVENTORY, LEDGER)}
    selection, inventory, provenance = (json.loads(raw[name]) for name in (SELECTION, INVENTORY, LEDGER))
    groups = {row['group_id']: row['role'] for row in provenance['groups']}
    plan = selection['plan']
    windows = plan['windows']
    source = safe_path(root, SOURCE)
    if (plan['version'] != 'esa-development-short-block-v1' or len(windows) != 3
            or plan['fit_authorized'] is not False or plan['confirmation_authorized'] is not False
            or groups.get(GROUP) != 'development' or source.name != inventory['source_file']
            or inventory['epochs'] != 64080 or any(row['group_id'] != GROUP
                or row['receiver_source_sha256'] != inventory['sha256']
                or row['training_reports'] != 800 or row['query_stride'] != 2
                or row['training_last_index'] - row['training_first_index'] != 1598
                or row['future_first_index'] <= row['training_last_index'] for row in windows)):
        raise ValueError('preselected recording 187 development training queries required')
    own = Path(__file__).relative_to(root).as_posix()
    config = encoded(dict(inputs={p: digest(b) for p, b in raw.items()},
        sources={p: digest((root / p).read_bytes()) for p in source_closure(
            root, (own, PLAN, 'analysis/tests/test_receiver_route_information.py'))},
        receiver_source_sha256=inventory['sha256'], receiver_passes=1, max_source_rows=64080,
        max_decoded_rows=2400, offset_limits_dph=LIMITS, comparisons=1458, threads=1,
        fits=0, protected_reads=0, environment=runtime_environment()))
    if action == 'freeze':
        _write_equal(root / FREEZE, config)
        return dict(freeze_sha256=digest(config))
    if (root / FREEZE).read_bytes() != config:
        raise ValueError('same frozen geometry check required')
    queries = _read_queries(source, windows, inventory['sha256'], inventory['epochs'])
    result = {key: _screen(rows) for key, rows in queries.items()}
    output = encoded(dict(freeze_sha256=digest(config), training_windows=result,
        decoded_rows=sum(len(rows) for rows in queries.values()), receiver_passes=1,
        fits=0, imu_reads=0, future_rows_decoded=0, protected_reads=0, scientific_decision='abstain'))
    _write_equal(root / RESULT, output)
    return dict(sha256=digest(output), training_windows=len(result), decoded_rows=2400)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
