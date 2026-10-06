# SPDX-License-Identifier: AGPL-3.0-or-later
"""Observable aircraft-motion exclusions, shared by turn reconstruction and design."""
import numpy as np


def maneuver_mask(kin, *, buffer_s=0., max_gap_s=5., max_turn_dps=.05,
                  max_bank_rate_dps=.05, max_vz_mps=1.5,min_speed_mps=100.,max_h_acc_m=100.):
    if not np.isfinite([buffer_s, max_gap_s]).all() or buffer_s < 0 or max_gap_s <= 0:
        raise ValueError('invalid maneuver buffer or coverage limit')
    if not np.isfinite([max_turn_dps,max_bank_rate_dps,max_vz_mps,min_speed_mps,max_h_acc_m]).all() or min(max_turn_dps,max_bank_rate_dps,max_vz_mps,min_speed_mps,max_h_acc_m) <= 0:
        raise ValueError('invalid aircraft-motion limits')
    if kin is None or len(kin['t']) < 3:
        return dict(version='aircraft-motion-mask-1', coverage=None, intervals=[], verified=False)
    t = np.asarray(kin['t'], float)
    if not np.isfinite(t).all() or np.any(np.diff(t) <= 0):
        raise ValueError('maneuver times must be finite and increasing')
    rate, speed = np.asarray(kin['psi_dot']), np.asarray(kin['speed'])
    bank = np.arctan(speed*rate/9.80665)
    bank_rate = np.gradient(bank, t)
    valid = np.isfinite(rate) & np.isfinite(speed) & np.isfinite(bank_rate)
    valid &= np.isfinite(kin.get('vz',np.zeros(len(t))))
    valid &= speed >= min_speed_mps
    accuracy=np.asarray(kin.get('h_acc',np.zeros(len(t))))
    valid &= np.isfinite(accuracy) & (accuracy<=max_h_acc_m)
    valid &= np.asarray(kin.get('bearing_ok', np.ones(len(t), bool)))
    moving = (np.abs(np.degrees(rate)) > max_turn_dps) | (np.abs(np.degrees(bank_rate)) > max_bank_rate_dps)
    moving |= np.abs(kin.get('vz', np.zeros(len(t)))) > max_vz_mps
    intervals = []
    for i in np.flatnonzero(~valid | moving):
        intervals.append(dict(start_s=float(t[max(0, i-1)]-buffer_s),
            end_s=float(t[min(len(t)-1, i+1)]+buffer_s),
            reason='aircraft maneuver' if valid[i] else 'unverified aircraft motion'))
    for a, b in zip(t[:-1], t[1:]):
        if b-a > max_gap_s:
            intervals.append(dict(start_s=float(a-buffer_s), end_s=float(b+buffer_s),
                                  reason='unverified aircraft motion'))
    # Merge only identical reasons, retaining explicit evidence for missing coverage.
    merged = []
    for item in sorted(intervals, key=lambda v: (v['reason'], v['start_s'])):
        if merged and item['reason'] == merged[-1]['reason'] and item['start_s'] <= merged[-1]['end_s']:
            merged[-1]['end_s'] = max(item['end_s'], merged[-1]['end_s'])
        else:
            merged.append(item.copy())
    return dict(version='aircraft-motion-mask-1', coverage=[float(t[0]), float(t[-1])],
                intervals=merged, verified=True, buffer_s=buffer_s, max_gap_s=max_gap_s)


def turn_motion_check(mask, start_s, end_s):
    if not np.isfinite([start_s,end_s]).all() or start_s > end_s:
        raise ValueError('invalid turn interval')
    if (mask is None or not mask.get('verified') or not mask.get('coverage') or
            start_s < mask['coverage'][0] or end_s > mask['coverage'][1]):
        return dict(safe=False, reason='unverified aircraft motion', evidence=[])
    hits = [v for v in mask['intervals'] if v['start_s'] <= end_s and v['end_s'] >= start_s]
    return dict(safe=not hits, reason=hits[0]['reason'] if hits else None, evidence=hits)
