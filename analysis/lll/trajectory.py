# SPDX-License-Identifier: AGPL-3.0-or-later
"""Development-only replay of observed positions with explicit latent-path assumptions."""
import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator

from . import models
from .inference_policy import digest

TRACK_VERSION = 'observed-trajectory-replay-1'
SMOOTH_TRACK_VERSION = 'observed-trajectory-replay-2'


def smooth_track_spec(spec):
    """Explicit alternative latent path; keep all observation/support/provenance fields."""
    TrackReplay(spec)
    content = {k: v for k, v in spec.items() if k != 'trajectory_hash'}
    content.update(version=SMOOTH_TRACK_VERSION, curve_model='cubic_natural',
        interpolation='Natural C2 cubic within short observed intervals only; no provider estimates or long-gap bridging; development latent-path assumption')
    return {**content, 'trajectory_hash': digest(content)}


def track_spec(case, mode='simulated_high_rate'):
    if mode not in ('observed_fixes', 'simulated_high_rate'):
        raise ValueError('unknown trajectory observation mode')
    if case.get('status') != 'prepared_geometry_only':
        raise ValueError('track blocked by observed coverage')
    window = case['candidate_window']
    content = dict(version=TRACK_VERSION, mode=mode, track_id=case['id'],
        source_sha256=case['source_sha256'], rows=case['rows'],
        start_s=window['start_s'], end_s=window['end_s'], max_interval_s=90.,
        altitude_assumption='reported altitude treated as geometric height; actual reference unknown',
        clock_assumption='synthetic clock; source timezone does not align a real IMU',
        interpolation='PCHIP within short observed intervals only; no provider estimates or long-gap bridging')
    return {**content, 'trajectory_hash': digest(content)}


class TrackReplay:
    def __init__(self, spec):
        if spec.get('version') not in (TRACK_VERSION, SMOOTH_TRACK_VERSION) or spec.get('mode') not in ('observed_fixes', 'simulated_high_rate'):
            raise ValueError('unsupported trajectory input')
        smooth = spec['version'] == SMOOTH_TRACK_VERSION
        if (smooth and spec.get('curve_model') != 'cubic_natural') or (not smooth and 'curve_model' in spec):
            raise ValueError('trajectory curve model must match its explicit version')
        if spec.get('trajectory_hash') != digest({k: v for k, v in spec.items() if k != 'trajectory_hash'}):
            raise ValueError('trajectory hash mismatch')
        self.spec, self.duration = spec, float(spec['end_s']-spec['start_s'])
        self.rows = spec['rows']
        times = np.asarray([r['t_s'] for r in self.rows], float)
        if len(times) < 2 or not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
            raise ValueError('trajectory requires increasing unique timestamps')
        if not np.isfinite([spec['start_s'],spec['end_s']]).all() or self.duration <= 0 or not 0 < spec['max_interval_s'] <= 90:
            raise ValueError('invalid trajectory support limits')
        blocks, current = [], []
        for row in self.rows:
            if row.get('is_provider_estimate'):
                if len(current) >= 2: blocks.append(current)
                current = []
                continue
            if current and row['t_s']-current[-1]['t_s'] > spec['max_interval_s']:
                if len(current) >= 2: blocks.append(current)
                current = []
            current.append(row)
        if len(current) >= 2: blocks.append(current)
        if not blocks: raise ValueError('no usable observed intervals')
        self.blocks = []
        for rows in blocks:
            t = np.array([r['t_s']-spec['start_s'] for r in rows], float)
            lat = np.radians([r['latitude_deg'] for r in rows])
            lon = np.unwrap(np.radians([r['longitude_deg'] for r in rows]))
            height = np.array([r.get('reported_altitude_m') for r in rows], float)
            if not np.isfinite(lat).all() or not np.isfinite(lon).all() or not np.isfinite(height).all():
                raise ValueError('replay requires finite positions and declared reported-height assumption')
            if np.any(np.abs(lat)>np.pi/2.): raise ValueError('invalid replay latitude')
            curves = [CubicSpline(t, a, bc_type='natural', extrapolate=False) if smooth
                      else PchipInterpolator(t, a, extrapolate=False) for a in (lat, lon, height)]
            self.blocks.append((t[0], t[-1], curves))

    def support(self, t):
        t = np.asarray(t)
        return (t>=0) & (t<=self.duration) & np.logical_or.reduce([(t >= a) & (t <= b) for a, b, _ in self.blocks])

    def sample(self, t):
        t = np.asarray(t, float)
        lat, lon, h, dn, de, vz = [np.full(len(t), np.nan) for _ in range(6)]
        for a, b, curves in self.blocks:
            keep = (t >= a) & (t <= b)
            for out, curve in zip((lat, lon, h), curves): out[keep] = curve(t[keep])
            for out, curve in zip((dn, de, vz), curves): out[keep] = curve.derivative()(t[keep])
        rm, rn = models.radii(lat)
        vn, ve = dn*(rm+h), de*(rn+h)*np.cos(lat)
        speed, psi = np.hypot(vn, ve), np.arctan2(ve, vn)
        # Differentiate independently within each supported block; never across a hole.
        rate = np.full(len(t), np.nan)
        for a, b, _ in self.blocks:
            keep = np.flatnonzero((t >= a) & (t <= b))
            if len(keep) >= 2: rate[keep] = np.gradient(np.unwrap(psi[keep]), t[keep])
        return dict(lat=lat, lon=lon, h=h, v_n=vn, v_e=ve, vz=vz, speed=speed, psi=psi, psi_dot=rate)

    def observed_gnss(self, flight_start, clock_ns, utc_ms):
        rows = [r for r in self.rows if self.spec['start_s'] <= r['t_s'] <= self.spec['end_s']
                and not r.get('is_provider_estimate')]
        t_ns = clock_ns+np.round((flight_start+np.array([r['t_s']-self.spec['start_s'] for r in rows]))*1e9).astype(np.int64)
        def values(key): return np.array([r.get(key) for r in rows], float)
        n = len(rows)
        return dict(t_ns=t_ns, utc_ms=utc_ms+(t_ns-clock_ns)//10**6,
            lat=values('latitude_deg'), lon=values('longitude_deg'), alt_m=values('reported_altitude_m'),
            speed_mps=values('ground_speed_mps'), bearing_deg=values('ground_course_deg'),
            **{key: np.full(n, np.nan) for key in ('h_acc_m','v_acc_m','speed_acc_mps','bearing_acc_deg')},
            sats_used=np.full(n, -1, np.int64))
