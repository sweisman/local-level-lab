# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-only algebra and time-dependence check of ESA GNSS covariances."""

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np


LAGS = (1, 2, 5, 10)


def covariance_matrix(values):
    """Assemble NN, EE, HH, EN, NH, EH export values in NEU order."""
    value = np.asarray(values, dtype=float)
    if value.shape != (6,) or not np.isfinite(value).all():
        raise ValueError('six finite reported covariance values required')
    nn, ee, hh, en, nh, eh = value
    return np.array([[nn, en, nh], [en, ee, eh], [nh, eh, hh]])


def match_training(source_rows, sealed_rows):
    """Stop consuming the source immediately after the last sealed row."""
    sealed = list(sealed_rows)
    if (not sealed or any(sealed[i]['time_s'] >= sealed[i+1]['time_s']
                          for i in range(len(sealed)-1))):
        raise ValueError('ordered sealed training rows required')
    matched = []
    target = 0
    for row in source_rows:
        delta = row['time_s']-sealed[target]['time_s']
        if delta < -1e-6:
            continue
        if delta > 1e-6:
            raise ValueError('missing sealed training time in original source')
        expected = sealed[target]
        keys = ('sequence', 'gps_week', 'latitude_deg', 'longitude_deg',
                'height_m', 'north_mps', 'east_mps', 'up_mps')
        arrays = ('position_variance_m2', 'position_cross_covariance_m2')
        if (any(row[key] != expected[key] for key in keys) or
                any(row[key] != expected[key] for key in arrays)):
            raise ValueError('original source differs from sealed training report')
        matched.append(row)
        target += 1
        if target == len(sealed):
            return matched
    raise ValueError('original source ended before sealed training reports')


def _correlation(values, lag):
    left, right = values[:-lag], values[lag:]
    if len(left) < 2 or np.std(left) == 0 or np.std(right) == 0:
        return None
    return float(np.corrcoef(left, right)[0, 1])


def audit_training(rows):
    """Report matrix validity and derivative contrast without a coverage test."""
    samples = list(rows)
    if len(samples) < max(LAGS)+4:
        raise ValueError('enough aligned earlier GNSS reports required')
    times = np.asarray([r['time_s'] for r in samples], dtype=float)
    lat = np.deg2rad([r['latitude_deg'] for r in samples])
    lon = np.unwrap(np.deg2rad([r['longitude_deg'] for r in samples]))
    h = np.asarray([r['height_m'] for r in samples], dtype=float)
    reported = np.asarray([[r['north_mps'], r['east_mps'], r['up_mps']]
                           for r in samples], dtype=float)
    if (not np.isfinite(times).all() or not np.isfinite(lat).all() or
            not np.isfinite(lon).all() or not np.isfinite(h).all() or
            not np.isfinite(reported).all() or
            np.any(np.diff(times) <= 0) or np.any(np.abs(lat) >= np.pi/2)):
        raise ValueError('finite increasing nonpolar training reports required')

    matrices = {}
    for label, diag_key, cross_key in (
            ('position', 'position_variance_m2', 'position_cross_covariance_m2'),
            ('velocity', 'velocity_covariance_export', None)):
        values = [r[diag_key] if cross_key is None else
                  r[diag_key]+r[cross_key] for r in samples]
        matrix = np.asarray([covariance_matrix(v) for v in values])
        eigen = np.linalg.eigvalsh(matrix)
        diag = np.diagonal(matrix, axis1=1, axis2=2)
        scale = np.maximum(1.0, np.max(np.abs(matrix), axis=(1, 2)))
        matrices[label] = dict(
            negative_diagonal_epochs=int(np.count_nonzero(np.any(diag < 0, axis=1))),
            negative_eigenvalue_epochs=int(np.count_nonzero(
                np.any(eigen < -1e-10*scale[:, None], axis=1))),
            smallest_eigenvalue=float(np.min(eigen)),
            diagonal_root_median=np.median(
                np.sqrt(np.maximum(diag, 0.0)), axis=0).tolist())

    a = 6378137.0
    f = 1/298.257223563
    e2 = f*(2-f)
    q = 1-e2*np.sin(lat)**2
    meridional = a*(1-e2)/q**1.5
    prime_vertical = a/np.sqrt(q)
    derivative = np.column_stack((
        (meridional+h)*np.gradient(lat, times),
        (prime_vertical+h)*np.cos(lat)*np.gradient(lon, times),
        np.gradient(h, times)))
    difference = derivative[1:-1]-reported[1:-1]
    correlations = {axis: {str(lag): _correlation(difference[:, i], lag)
                           for lag in LAGS}
                    for i, axis in enumerate(('north', 'east', 'up'))}
    return dict(training_reports=len(samples), interior_epochs=len(difference),
                position_negative_diagonal_epochs=matrices['position']['negative_diagonal_epochs'],
                position_negative_eigenvalue_epochs=matrices['position']['negative_eigenvalue_epochs'],
                position_smallest_eigenvalue=matrices['position']['smallest_eigenvalue'],
                position_diagonal_root_median=matrices['position']['diagonal_root_median'],
                velocity_negative_diagonal_epochs=matrices['velocity']['negative_diagonal_epochs'],
                velocity_negative_eigenvalue_epochs=matrices['velocity']['negative_eigenvalue_epochs'],
                velocity_smallest_eigenvalue=matrices['velocity']['smallest_eigenvalue'],
                velocity_diagonal_root_median=matrices['velocity']['diagonal_root_median'],
                contrast_mean_mps=np.mean(difference, axis=0).tolist(),
                contrast_rms_mps=np.sqrt(np.mean(difference**2, axis=0)).tolist(),
                contrast_p95_absolute_mps=np.quantile(
                    np.abs(difference), .95, axis=0).tolist(),
                contrast_lag_correlations=correlations,
                covariance_units_from_export_header=True,
                cross_time_covariance_available=False,
                position_velocity_cross_covariance_available=False,
                empirical_coverage_calibrated=False)


def build(root):
    from .airquantumgrav_receiver import records
    from .esa_rolling_origin_400_study import ID as FIT_ID
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    source_report = json.loads((root /
        'docs/external-imu-data/esa-gnss-report.json').read_text())
    source_name = source_report['source_file']
    if source_name != '187_air1_ppp_2Hz_final.txt':
        raise ValueError('documented ESA development export required')
    source = root / 'data/external-imu-survey-20261018/esa-sample' / source_name
    digest = hashlib.sha256()
    with source.open('rb') as stream:
        while chunk := stream.read(1024*1024):
            digest.update(chunk)
    source_sha = digest.hexdigest()
    if source_sha != source_report['sha256']:
        raise ValueError('ESA GNSS source hash differs from published inventory')
    fit = ClosedStudy(root, 'data/' + FIT_ID)
    try:
        if (fit.completion.get('state') != 'complete' or
                fit.summary.get('completed') != 2 or
                fit.summary.get('passed') is not True):
            raise ValueError('sealed passing 400/120 training input required')
        raw = fit.input('training', raw=True)
        sealed = json.loads(gzip.decompress(raw))
        if len(sealed) != 400:
            raise ValueError('exact 400-report earlier input required')
        with source.open() as stream:
            matched = match_training(records(stream), sealed)
        result = audit_training(matched)
        prior_path = (root /
            'docs/prediction-observed-development/GNSS_VELOCITY_CONSISTENCY.json')
        prior = json.loads(prior_path.read_text())
        if (prior['fit_manifest_sha256'] != fit.completion['manifest_sha256'] or
                prior['training_input_sha256'] != hashlib.sha256(raw).hexdigest()):
            raise ValueError('earlier consistency report identity differs')
        earlier = prior['diagnostic']
        for current, old in ((result['contrast_mean_mps'], earlier['mean_difference_mps']),
                             (result['contrast_rms_mps'], earlier['rms_difference_mps']),
                             (result['contrast_p95_absolute_mps'],
                              earlier['p95_absolute_difference_mps'])):
            if not np.allclose(current, old, rtol=1e-10, atol=1e-10):
                raise ValueError('saved position-velocity contrast not reproduced')
        return dict(version='esa-gnss-training-covariance-audit-v1',
                    source_file=source_name, source_original_sha256=source_sha,
                    source_report_sha256=hashlib.sha256((root /
                        'docs/external-imu-data/esa-gnss-report.json').read_bytes()).hexdigest(),
                    fit_manifest_sha256=fit.completion['manifest_sha256'],
                    training_input_sha256=hashlib.sha256(raw).hexdigest(),
                    prior_consistency_sha256=hashlib.sha256(prior_path.read_bytes()).hexdigest(),
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    diagnostic=result, source_originals_hashed=1,
                    training_source_reports_decoded=len(matched),
                    later_receiver_reports_decoded=0,
                    protected_group_reads=0, imu_samples_used=0,
                    new_model_fits=0, independent_motion_evidence=False,
                    scientific_decision='abstain')
    finally:
        fit.close()


def publish(root):
    from .studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    result = build(root)
    base = root / 'docs/prediction-observed-development'
    atomic(base / 'GNSS_COVARIANCE_AUDIT.json', encoded(result))
    d = result['diagnostic']
    lines = []
    for i, axis in enumerate(('north', 'east', 'up')):
        lag = d['contrast_lag_correlations'][axis]
        lines.append('| {} | {:.4f} | {:.4f} | {:.4f} | {:.3f} | {:.3f} |'.format(
            axis, d['contrast_rms_mps'][i],
            d['position_diagonal_root_median'][i],
            d['velocity_diagonal_root_median'][i],
            lag['1'], lag['10']))
    page = ('# GNSS covariance and time-dependence audit\n\n'
        'The original GNSS-only PPP export was hash-verified and matched to '
        'all 400 sealed earlier receiver reports. Parsing stopped before the '
        'withheld reports. Its printed north/east/up covariance fields were '
        'assembled as matrices without changing the sealed fit input.\n\n'
        f"Position matrices with a negative eigenvalue: {d['position_negative_eigenvalue_epochs']}/400. "
        f"Velocity matrices: {d['velocity_negative_eigenvalue_epochs']}/400. "
        'A valid matrix is not proof that its reported uncertainty covers '
        'actual receiver error.\n\n'
        '| Axis | Position-derivative minus velocity RMS (m/s) | '
        'Median reported position SD (m) | '
        'Median reported velocity SD (m/s) | Lag 1 | Lag 10 |\n'
        '| --- | ---: | ---: | ---: | ---: | ---: |\n' + '\n'.join(lines) + '\n\n'
        'The export header labels position covariance in m² and velocity '
        'covariance in m²/s², so the printed square roots have m and m/s '
        'units respectively. Their empirical coverage is unverified. '
        'The position and velocity '
        'come from the same PPP solution. A small difference between them '
        'does not establish that either reported uncertainty is conservative. '
        'Their missing cross-time and '
        'cross-field covariance prevents a valid normalized significance '
        'test or an aircraft motion-error bound. This check does not qualify '
        'forecast coverage or an Earth-model decision.\n\n'
        '[Fixed method](GNSS_COVARIANCE_AUDIT_PLAN.md) · '
        '[Detailed result](GNSS_COVARIANCE_AUDIT.json).\n')
    atomic(base / 'GNSS_COVARIANCE_AUDIT.md', page.encode())
    return result


if __name__ == '__main__':
    outcome = publish('.')
    print(json.dumps({k: outcome['diagnostic'][k] for k in (
        'position_negative_eigenvalue_epochs',
        'velocity_negative_eigenvalue_epochs')}, sort_keys=True))
