# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-input consistency check for ESA GNSS positions and velocities."""

import gzip
import hashlib
import json
from pathlib import Path


def diagnose(times_s, latitude_deg, longitude_deg, height_m,
             reported_neu_mps):
    """Compare centered position derivatives with GNSS-reported NEU velocity."""
    import numpy as np

    t = np.asarray(times_s, dtype=float)
    lat = np.radians(np.asarray(latitude_deg, dtype=float))
    lon = np.radians(np.asarray(longitude_deg, dtype=float))
    h = np.asarray(height_m, dtype=float)
    v = np.asarray(reported_neu_mps, dtype=float)
    if (t.ndim != 1 or len(t) < 5 or
            lat.shape != t.shape or lon.shape != t.shape or
            h.shape != t.shape or v.shape != (len(t), 3) or
            not np.all(np.isfinite(t)) or not np.all(np.isfinite(lat)) or
            not np.all(np.isfinite(lon)) or not np.all(np.isfinite(h)) or
            not np.all(np.isfinite(v)) or
            np.any(np.diff(t) <= 0) or
            np.any(np.abs(lat) >= np.pi/2)):
        raise ValueError('finite aligned increasing nonpolar receiver samples required')
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = f * (2 - f)
    q = 1 - e2 * np.sin(lat)**2
    meridional = a * (1 - e2) / q**1.5
    prime_vertical = a / np.sqrt(q)
    derivative = np.column_stack((
        (meridional + h) * np.gradient(lat, t),
        (prime_vertical + h) * np.cos(lat) * np.gradient(lon, t),
        np.gradient(h, t),
    ))
    difference = derivative[1:-1] - v[1:-1]
    return dict(interior_epochs=len(difference),
                first_and_last_derivative_epochs_excluded=True,
                axis_order=['north', 'east', 'up'],
                mean_difference_mps=np.mean(difference, axis=0).tolist(),
                rms_difference_mps=np.sqrt(np.mean(difference**2, axis=0)).tolist(),
                p95_absolute_difference_mps=np.quantile(
                    np.abs(difference), .95, axis=0).tolist(),
                minimum_dt_s=float(np.min(np.diff(t))),
                maximum_dt_s=float(np.max(np.diff(t))),
                covariance_calibrated=False,
                velocity_independent_of_position_proven=False)


def sealed_fit_ready(completion, summary):
    return (completion.get('state') == 'complete' and
            summary.get('completed') == 2 and
            summary.get('total') == 2 and
            summary.get('passed') is True)


def build(root):
    from .esa_rolling_origin_400_study import ID as FIT_ID
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    fit = ClosedStudy(root, 'data/' + FIT_ID)
    try:
        if not sealed_fit_ready(fit.completion, fit.summary):
            raise ValueError('sealed passing 400/120 fit required')
        raw = fit.input('training', raw=True)
        rows = json.loads(gzip.decompress(raw))
        if len(rows) != 400:
            raise ValueError('exact sealed earlier-only 400-report input required')
        report = diagnose(
            [r['time_s'] for r in rows],
            [r['latitude_deg'] for r in rows],
            [r['longitude_deg'] for r in rows],
            [r['height_m'] for r in rows],
            [[r['north_mps'], r['east_mps'], r['up_mps']] for r in rows])
        return dict(version='esa-gnss-velocity-training-consistency-v1',
                    fit_manifest_sha256=fit.completion['manifest_sha256'],
                    fit_summary_sha256=fit.completion['summary_sha256'],
                    training_input_sha256=hashlib.sha256(raw).hexdigest(),
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    training_receiver_reports=400,
                    later_receiver_reports_read=0,
                    original_reads=0, protected_reads=0, new_model_fits=0,
                    diagnostic=report,
                    independent_motion_evidence=False,
                    scientific_decision='abstain')
    finally:
        fit.close()


def publish(root):
    from .studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    result = build(root)
    base = root / 'docs/prediction-observed-development'
    atomic(base / 'GNSS_VELOCITY_CONSISTENCY.json', encoded(result))
    d = result['diagnostic']
    axes = ('north', 'east', 'up')
    rows = [f'| {name} | {d["mean_difference_mps"][i]:.4f} | '
            f'{d["rms_difference_mps"][i]:.4f} | '
            f'{d["p95_absolute_difference_mps"][i]:.4f} |'
            for i, name in enumerate(axes)]
    page = ('# GNSS position and velocity consistency\n\n'
        'On the already sealed first 400 ESA development receiver reports, '
        'the reported GNSS velocity is compared with the centered time '
        'derivative of the reported positions. The derivative uses actual '
        'time tags and WGS84 distance scales. The two endpoint derivatives '
        'are excluded; no later receiver reports were read.\n\n'
        '| Axis | Mean difference (m/s) | RMS difference (m/s) | '
        '95th percentile absolute difference (m/s) |\n'
        '| --- | ---: | ---: | ---: |\n' + '\n'.join(rows) + '\n\n'
        'This checks internal consistency, not independent accuracy. Position '
        'and velocity come from the same GNSS-only PPP solution, and their '
        'cross-time dependence and reported uncertainty are not calibrated '
        'here. The check cannot establish the aircraft motion-error range or '
        'qualify the observed forecast. No Earth-model decision follows.\n\n'
        '[Method and chronology](GNSS_VELOCITY_CONSISTENCY_PLAN.md) · '
        '[Detailed result](GNSS_VELOCITY_CONSISTENCY.json).\n')
    atomic(base / 'GNSS_VELOCITY_CONSISTENCY.md', page.encode())
    return result


if __name__ == '__main__':
    print(json.dumps(publish('.')['diagnostic'], sort_keys=True))
