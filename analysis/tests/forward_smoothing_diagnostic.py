# SPDX-License-Identifier: AGPL-3.0-or-later
"""Research-only matched forward-reference filtering; no uncertainty or eligibility policy."""
import numpy as np
from lll.attitude import course_rate, unit
from lll.models import G0

WINDOW_SECONDS = 30.


def matched_filter(t, values, valid, window_seconds=WINDOW_SECONDS):
    """Apply the same centered Hann kernel only inside complete, regular, valid runs."""
    t = np.asarray(t, float)
    values = np.asarray(values, float)
    valid = np.asarray(valid, bool) & np.isfinite(values).all(axis=1)
    filtered = np.full_like(values, np.nan)
    keep = np.zeros(len(t), bool)
    if len(t) < 3:
        return filtered, keep
    step = float(np.median(np.diff(t)))
    if step <= 0 or window_seconds <= 0:
        raise ValueError('positive timestamps and filter duration required')
    half = max(1, int(np.ceil(window_seconds / step / 2)))
    width = 2*half+1
    kernel = np.hanning(width)
    kernel /= kernel.sum()
    cuts = np.r_[0, np.flatnonzero(abs(np.diff(t)-step) > .05*step)+1, len(t)]
    for left, right in zip(cuts[:-1], cuts[1:]):
        # Invalid observations are boundaries, never filled or bridged.
        good = valid[left:right]
        starts = np.flatnonzero(good & ~np.r_[False, good[:-1]])+left
        ends = np.flatnonzero(good & ~np.r_[good[1:], False])+left+1
        for start, end in zip(starts, ends):
            if end-start < width:
                continue
            target = slice(start+half, end-half)
            for column in range(values.shape[1]):
                filtered[target, column] = np.convolve(values[start:end, column], kernel, mode='valid')
            keep[target] = True
    return filtered, keep


def diagnose(gyro_t, gyro, gps_t, speed, course, up):
    """Direction/quality only. This cannot supply a science fit's forward uncertainty."""
    gps_t = np.asarray(gps_t, float)
    gyro_t = np.asarray(gyro_t, float)
    gyro = np.asarray(gyro, float)
    speed, course = np.asarray(speed, float), np.asarray(course, float)
    proxy = np.full(len(gps_t), np.nan)
    if len(gps_t) < 3 or len(gyro_t) < 3:
        return dict(available=False, reason='too little GPS or gyro', diagnostic_only=True)
    if not np.isfinite(gps_t).all() or not np.isfinite(gyro_t).all() or np.any(np.diff(gps_t) <= 0) or np.any(np.diff(gyro_t) <= 0):
        raise ValueError('finite increasing GPS and gyro timestamps required')
    if not np.isfinite(gyro).all():
        return dict(available=False, reason='nonfinite gyro', diagnostic_only=True)
    step = np.median(np.diff(gps_t))
    cuts = np.r_[0, np.flatnonzero(abs(np.diff(gps_t)-step) > .05*step)+1, len(gps_t)]
    for left, right in zip(cuts[:-1], cuts[1:]):
        if right-left < 7:
            continue
        sl = slice(left, right)
        bank = np.arctan(speed[sl]*course_rate(gps_t[sl], course[sl])/G0)
        proxy[sl] = np.gradient(bank, gps_t[sl])
        # The five-second course difference needs support at both edges.
        proxy[left:left+3] = np.nan
        proxy[right-3:right] = np.nan
    lo, hi = np.searchsorted(gyro_t, gps_t-.5), np.searchsorted(gyro_t, gps_t+.5)
    cs = np.vstack([np.zeros(3), np.cumsum(gyro, axis=0)])
    averaged = (cs[hi]-cs[lo])/np.maximum(hi-lo, 1)[:, None]
    normal = unit(up)
    horizontal = averaged-(averaged @ normal)[:, None]*normal
    # A gap inside a GPS-aligned gyro averaging bin must not be smoothed over.
    supported = (hi > lo) & (gps_t-.5 >= gyro_t[0]) & (gps_t+.5 <= gyro_t[-1])
    for gap in np.flatnonzero(np.diff(gyro_t) > 3*np.median(np.diff(gyro_t))):
        supported &= ~((gps_t+.5 >= gyro_t[gap]) & (gps_t-.5 <= gyro_t[gap+1]))
    values, valid = matched_filter(gps_t, np.column_stack([proxy, horizontal]),
                                    supported)
    br, gh = values[valid, 0], values[valid, 1:]
    energy = float(br @ br)
    if energy < 1e-4:
        return dict(available=False, reason='insufficient filtered bank energy', bank_energy=energy,
                    samples=int(valid.sum()), diagnostic_only=True, window_seconds=WINDOW_SECONDS)
    axis = np.sum(gh*br[:, None], axis=0)/energy
    gain = float(np.linalg.norm(axis))
    residual = gh-br[:, None]*axis
    explained = float(1-np.sum(residual**2)/max(np.sum(gh**2), 1e-30))
    available = gain >= .1 and explained >= .05
    return dict(available=available, gain=gain, r2=explained, bank_energy=energy,
                axis=None if gain == 0 else (axis/gain).tolist(), samples=int(valid.sum()),
                diagnostic_only=True, window_seconds=WINDOW_SECONDS,
                uncertainty_available=False, accepted_for_science=False)
