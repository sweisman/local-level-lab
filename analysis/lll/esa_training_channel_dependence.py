# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cross-channel rate contrasts from the sealed ESA training interval."""

import argparse
import hashlib
import io
import json
import math
from pathlib import Path


def contrast_correlations(values):
    """Return same-time correlations; zero-variance channels are undefined."""
    import numpy as np
    array = np.asarray(values, dtype=float)
    if (array.ndim != 2 or array.shape[1] != 6 or len(array) < 3 or
            not np.all(np.isfinite(array))):
        raise ValueError('at least three finite six-channel contrasts required')
    centered = array - np.mean(array, axis=0)
    products = centered.T @ centered
    variances = np.diag(products)
    result = []
    for i in range(6):
        row = []
        for j in range(6):
            if variances[i] <= 0 or variances[j] <= 0:
                row.append(None)
            else:
                value = float(products[i, j] / math.sqrt(
                    float(variances[i] * variances[j])))
                row.append(max(-1., min(1., value)))
        result.append(row)
    return result


def strongest_pair(correlations, *, cross_sensor):
    if (len(correlations) != 6 or any(len(row) != 6 for row in correlations)):
        raise ValueError('six-channel correlation matrix required')
    pairs = ((i, j) for i in range(3) for j in
             (range(3, 6) if cross_sensor else range(i+1, 3)))
    available = [(i, j, correlations[i][j]) for i, j in pairs
                 if correlations[i][j] is not None]
    if not available:
        return None
    i, j, value = max(available, key=lambda pair: abs(pair[2]))
    return dict(first_channel=('gyro_x', 'gyro_y', 'gyro_z',
                               'force_x', 'force_y', 'force_z')[i],
                second_channel=('gyro_x', 'gyro_y', 'gyro_z',
                                'force_x', 'force_y', 'force_z')[j],
                correlation=value)


def build(root):
    import numpy as np
    from .rate_variation import contrasts, training_prefix
    from .studies.artifacts import digest
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    study = ClosedStudy(root, 'data/esa-training-rate-variation-20261024')
    try:
        source_names = [study.prefix + '/source-freeze/' + name
                        for name in study.manifest['sources']]
        if (study.completion['state'] != 'complete' or
                study.summary['completed'] != 1 or
                set(study.tasks) != {'logged-rates'} or
                set(study.rows) != {'logged-rates'} or
                any(study.catalog['paths'].get(alias, {}).get('sha256') != sha
                    for alias, sha in zip(source_names,
                        study.manifest['sources'].values(), strict=True))):
            raise ValueError('sealed earlier-only rate study and sources required')
        study.store.verify(names=source_names)
        result = study.envelope('logged-rates')['result']
        source = study.artifact('logged-rates', 'variation.json')
        if (result['passed'] is not True or
                result['training_samples'] != 239864 or
                result['original_reads'] != 0 or
                result['protected_reads'] != 0 or
                source['points'] != result['training_samples']):
            raise ValueError('complete saved training-rate outcome required')
        recipe = study.input('recipe')
        layout = study.input('query-layout')
        raw = study.input('interval', raw=True)
        if (recipe['strides'] != [1, 3, 30, 300] or
                recipe['training_epochs'] != 800 or
                recipe['prediction_epochs'] != 400 or
                len(raw) > recipe['maximum_input_bytes']):
            raise ValueError('bounded saved interval required')
        with np.load(io.BytesIO(raw), allow_pickle=False) as archive:
            times = np.array(archive['raw_time_s'], dtype=float, copy=True)
            rates = np.array(archive['angular_rate_rads'], dtype=float, copy=True)
            force = np.array(archive['acceleration_mps2'], dtype=float, copy=True)
        if (rates.shape != (len(times), 3) or
                force.shape != (len(times), 3) or
                len(times) != result['input_samples']):
            raise ValueError('unchanged six-channel saved input required')
        cutoff = (layout['time_origin_gps_sow_s'] +
                  layout['times_s'][recipe['training_epochs']-1])
        times, values = training_prefix(times,
            np.column_stack((rates, force)), last_training_time_s=cutoff,
            maximum_points=recipe['maximum_input_samples'])
        if (digest(times.astype('<f8').tobytes()) != source['used_times_sha256'] or
                digest(values.astype('<f8').tobytes()) != source['used_values_sha256']):
            raise ValueError('training prefix differs from sealed source')
        rows = []
        for stride in recipe['strides']:
            result = contrasts(times, values, stride=stride,
                maximum_points=recipe['maximum_input_samples'],
                maximum_gap_s=recipe['maximum_gap_s'])
            original = next(row for row in source['contrasts']
                            if row['stride'] == stride)
            if (result['count'] != original['count'] or
                    not np.allclose(np.sqrt(np.mean(
                        result['values']**2, axis=0)),
                        original['rms_native_units'], rtol=1e-12, atol=1e-12)):
                raise ValueError('contrast differs from sealed source')
            matrix = contrast_correlations(result['values'])
            rows.append(dict(stride=stride, count=result['count'],
                median_span_s=float(np.median(result['separation_s'])),
                correlations=matrix,
                strongest_gyro_pair=strongest_pair(matrix, cross_sensor=False),
                strongest_gyro_force_pair=strongest_pair(matrix, cross_sensor=True)))
        return dict(version='esa-training-channel-dependence-v1',
            parent='data/esa-training-rate-variation-20261024',
            parent_manifest_sha256=study.completion['manifest_sha256'],
            parent_summary_sha256=study.completion['summary_sha256'],
            frozen_sources_verified=len(source_names),
            source_input_sha256=digest(raw),
            reporter_sha256=hashlib.sha256((root /
                'analysis/lll/esa_training_channel_dependence.py').read_bytes()).hexdigest(),
            training_samples=len(times), rows=rows,
            original_reads=0, protected_reads=0, native_calls=0,
            fitted_parameters=0, isolated_sensor_noise_estimated=False,
            error_law_calibrated=False, scientific_decision='abstain')
    finally:
        study.close()


def publish(root):
    from .studies.artifacts import atomic, encoded
    root = Path(root).resolve()
    result = build(root)
    base = root / 'docs/prediction-observed-development'
    atomic(base / 'RECORDED_CHANNEL_DEPENDENCE.json', encoded(result))
    rows = []
    for row in result['rows']:
        pair = row['strongest_gyro_force_pair']
        name = ('unavailable' if pair is None else
                pair['first_channel'] + ' / ' + pair['second_channel'])
        value = ('unavailable' if pair is None else
                 '{:.3f}'.format(pair['correlation']))
        rows.append('| {:.4f} | {} | {} | {} |'.format(
            row['median_span_s'], row['count'], name, value))
    page = ('# Do recorded IMU channels change together?\n\n'
        'This saved-data check uses the first 13.33 minutes of ESA development '
        'recording 187. It reads the same sealed training samples used by the '
        '[rate-variation study](../esa-training-rate-variation/README.md). '
        'No new fit, original file or reserved flight group is opened.\n\n'
        'Each row takes disjoint groups of three samples, removes a straight '
        'line at their actual timestamps, then compares the six resulting '
        'channel changes. The table shows the strongest same-time pairing '
        'between a gyroscope and an accelerometer axis.\n\n'
        '| Sample span (s) | Groups | Axis pair | Correlation |\n'
        '| ---: | ---: | --- | ---: |\n' + '\n'.join(rows) + '\n\n'
        'A shared change can reflect aircraft motion or vibration. No shared '
        'change would not prove sensor noise: motion can affect axes at '
        'different times or leave one channel nearly unchanged. This check '
        'does not separate sensor bias, sensor noise, aircraft motion or '
        'receiver error and does not calibrate prediction uncertainty.\n\n'
        '[All six-axis correlations and source hashes]'
        '(RECORDED_CHANNEL_DEPENDENCE.json) · '
        '[Next qualification](OBSERVED_ERROR_PLAN.md).\n')
    atomic(base / 'RECORDED_CHANNEL_DEPENDENCE.md', page.encode())
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    result = publish(args.root)
    print(json.dumps([dict(stride=row['stride'], count=row['count'],
        pair=row['strongest_gyro_force_pair']) for row in result['rows']],
        sort_keys=True))


if __name__ == '__main__':
    main()
