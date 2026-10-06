# SPDX-License-Identifier: AGPL-3.0-or-later
"""Resolve saved trajectory's model differences into horizontal and vertical rates."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'analysis'))

import numpy as np
from lll import models
from lll.calib import RAD2DPH
from lll.research_design import implementation_hash


def signal_budget(bins):
    weights = np.asarray(bins['dt'])
    if not np.isfinite(weights).all() or np.any(weights <= 0):
        raise ValueError('positive finite bin duration required')
    terms = np.stack(models.terms(bins['lat'], bins['h'], bins['v_n'], bins['v_e'],
                                  bins['lon_rate']), axis=-1)
    pairs = {}
    for i, a in enumerate(models.EXPECTED_K):
        for b in list(models.EXPECTED_K)[i + 1:]:
            signal = terms @ (np.asarray(models.EXPECTED_K[a]) - models.EXPECTED_K[b])
            total = float(np.sum(weights[:, None] * signal ** 2))
            mean = np.average(signal[:, 2], weights=weights)
            pairs[a + '_vs_' + b] = dict(
                horizontal_norm_fraction=float(np.sqrt(np.sum(weights[:, None] * signal[:, :2] ** 2) / total)) if total else None,
                horizontal_rms_dph=float(np.sqrt(np.average(np.sum(signal[:, :2] ** 2, axis=1), weights=weights)) * RAD2DPH),
                down_mean_dph=float(mean * RAD2DPH),
                down_sd_dph=float(np.sqrt(np.average((signal[:, 2] - mean) ** 2, weights=weights)) * RAD2DPH))
    earth = float(np.average(terms[:, 0, 0], weights=weights) * RAD2DPH)
    transport = float(np.average(terms[:, 0, 1], weights=weights) * RAD2DPH)
    return dict(pairs=pairs, mean_north_earth_rotation_dph=earth,
                mean_north_globe_transport_dph=transport, mean_north_sum_dph=earth + transport,
                mean_east_speed_mps=float(np.average(bins['v_e'], weights=weights)))


def review(directory):
    root = directory.resolve()
    campaign_path = root / 'campaign.json'
    campaign = json.loads(campaign_path.read_text())
    if implementation_hash() != campaign['implementation_hash']:
        raise ValueError('source differs from saved pilot')
    row = next(r for r in campaign['records'] if r['task_index'] == 1)
    path = root / 'diagnostics' / row['task_id'] / 'fit-input.npz'
    with np.load(path, allow_pickle=False) as data: result = signal_budget(dict(data))
    return dict(scope='duration-weighted predicted local-level rates from saved geometry, not measured IMU motion',
        implementation_hash=campaign['implementation_hash'], helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        input_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (campaign_path, path)},
        signal_budget=result, authorized_additional_attempts=0,
        limitations=['Raw model terms without nuisance projection or SVD; not an acceptance or power statistic.',
            'Ground coordinates and altitude assumptions unchanged; no wind or IMU truth used.',
            'Tray yaw turns preserve the vertical axis, so a nearly constant vertical difference can resemble bias.',
            'Cancellation depends on route direction and latitude; this case does not establish a general route guarantee.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review(args.directory)
    with args.output.open('x') as out: out.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result['signal_budget']))
