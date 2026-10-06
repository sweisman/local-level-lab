# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare saved GPS bank proxies with assumed replay roll; no flights or science fits."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'analysis'))

import numpy as np
from lll.attitude import course_rate
from lll.format import read_session
from lll.models import G0
from lll.trajectory import TrackReplay


def bank_proxy(t, speed, course):
    return np.gradient(np.arctan(speed * course_rate(t, course) / G0), t)


def compare(proxy, reference, valid):
    valid = valid & np.isfinite(proxy) & np.isfinite(reference)
    x, y = proxy[valid], reference[valid]
    energy = float(x @ x)
    if not len(x) or energy <= 0 or float(y @ y) <= 0:
        return dict(available=False, samples=len(x))
    gain = float(x @ y / energy)
    return dict(available=True, samples=len(x), gain=gain,
                explained_fraction=float(1 - ((y-gain*x) @ (y-gain*x)) / (y @ y)),
                proxy_energy=energy, reference_energy=float(y @ y))


def knot_bank_jumps(replay):
    """One-sided bank limits at interpolation knots, using small within-block differences."""
    result = []
    eps = 1e-3
    for start, end, curves in replay.blocks:
        for knot in curves[0].x[1:-1]:
            if not 0 < knot < replay.duration:
                continue
            local = knot + np.array([-eps, -eps/2, eps/2, eps])
            if local[0] < start or local[-1] > end:
                continue
            path = replay.sample(local)
            bank = np.arctan(path['speed'] * path['psi_dot'] / G0)
            result.append(dict(t_s=float(knot), jump_deg=float(np.degrees(bank[-1]-bank[0]))))
    return result


def audit(directory):
    source = directory / 'campaign.json'
    campaign = json.loads(source.read_text())
    row = campaign['records'][0]
    saved = directory / 'diagnostics' / row['task_id']
    session = read_session(saved / 'session.zip')
    flight = session.phase('flight')
    gyro = np.load(saved / 'turn-input.npz', allow_pickle=False)
    t = np.round(gyro['t'] - flight['start_ns']/1e9, 8)
    replay = TrackReplay(row['design']['simulator']['trajectory_input'])
    path = replay.sample(t)
    bank = np.arctan(path['speed'] * path['psi_dot'] / G0)
    # Scalar bank rotation only: this is not an injected gyro, recovered orientation,
    # full Euler-rate model, or substitute for measured forward-axis uncertainty.
    roll = np.r_[np.diff(bank)/np.diff(t), 0.]
    roll[:-1][np.diff(t) > 1.5/row['design']['simulator']['fs']] = 0.
    gn = session.slice('gnss', flight['start_ns'], flight['end_ns'])
    gt = np.round(gn['t_ns']/1e9-flight['start_ns']/1e9, 8)
    lo, hi = np.searchsorted(t, gt-.5), np.searchsorted(t, gt+.5)
    cs = np.r_[0., np.cumsum(np.nan_to_num(roll))]
    average = (cs[hi]-cs[lo])/np.maximum(hi-lo, 1)
    valid = (hi > lo) & (gt > t[0]+5) & (gt < t[-1]-5)
    # Exclude GPS gap edges from both comparisons; no differentiation across a hole.
    for gap in np.flatnonzero(np.diff(gt) > 1.5):
        valid &= ~((gt >= gt[gap]-5) & (gt <= gt[gap+1]+5))
    measured = bank_proxy(gt, gn['speed_mps'], gn['bearing_deg'])
    ideal = replay.sample(gt)
    noiseless = bank_proxy(gt, ideal['speed'], np.degrees(ideal['psi']))
    jumps = knot_bank_jumps(replay)
    near = np.zeros(len(gt), dtype=bool)
    for entry in jumps:
        near |= abs(gt-entry['t_s']) <= 1.
    return dict(scope='saved-data and assumed-path scalar roll diagnostic; no synthesis, science fit, SVD or search',
                campaign_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                task_id=row['task_id'], trajectory_hash=replay.spec['trajectory_hash'],
                saved_gps_proxy=compare(measured, average, valid),
                assumed_noise_free_gps_proxy=compare(noiseless, average, valid),
                interpolation_knot_count=len(jumps),
                max_absolute_bank_jump_deg=max(abs(v['jump_deg']) for v in jumps),
                bank_jumps_over_one_degree=sum(abs(v['jump_deg']) > 1 for v in jumps),
                knot_neighborhood_reference_energy_fraction=float(np.sum(average[valid & near]**2)/np.sum(average[valid]**2)),
                knot_bank_jumps=jumps,
                interpretation='Position PCHIP is C1; acceleration, coordinated bank and roll can jump at knots. Noise-free proxy checks interpolation compatibility only, not actual aircraft motion or a usable IMU reference.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.directory)
    with args.output.open('x') as out:
        out.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'knot_bank_jumps'}, allow_nan=False))
