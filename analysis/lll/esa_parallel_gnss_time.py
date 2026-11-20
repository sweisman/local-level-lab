# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exploratory common-time comparison of ESA-187 PPP receiver streams."""

import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from .esa_parallel_gnss import (build as raw_comparison, earlier_lines,
                                match_times, relative_neu)
from .esa_ppp_acquisition import TARGETS


def corrected_neu(reference, other):
    """Return raw and local first-order time-adjusted position differences."""
    raw = relative_neu(reference, other)
    dt = float(other['time_s'] - reference['time_s'])
    velocity = (other['north_mps'], other['east_mps'], other['up_mps'])
    if not math.isfinite(dt) or not all(math.isfinite(float(v)) for v in velocity):
        raise ValueError('finite time and reported velocity required')
    return raw, tuple(value - float(rate) * dt
                      for value, rate in zip(raw, velocity))


def axis_summary(values):
    array = np.asarray(values, dtype=float)
    if array.ndim != 2 or array.shape[1] != 3 or not len(array):
        raise ValueError('nonempty north/east/up differences required')
    mean = np.mean(array, axis=0)
    centered = array - mean
    lag = []
    for axis in range(3):
        earlier = array[:-1, axis]
        later = array[1:, axis]
        if (len(earlier) < 2 or np.std(earlier) == 0 or
                np.std(later) == 0):
            lag.append(None)
        else:
            lag.append(float(np.corrcoef(earlier, later)[0, 1]))
    return dict(mean=mean.tolist(),
                rms=np.sqrt(np.mean(array**2, axis=0)).tolist(),
                centered_rms=np.sqrt(np.mean(centered**2, axis=0)).tolist(),
                p95_absolute=np.quantile(np.abs(array), .95, axis=0).tolist(),
                lag_one_correlation=lag)


def build(root):
    from .airquantumgrav_receiver import records
    from .esa_rolling_origin_400_study import ID as fit_id
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    raw_result = raw_comparison(root)
    raw_path = root / 'docs/prediction-observed-development/PARALLEL_GNSS_RESULT.json'
    saved = json.loads(raw_path.read_text())
    if (saved != raw_result or
            hashlib.sha256((root / 'analysis/lll/esa_parallel_gnss.py').read_bytes()).hexdigest()
            != '2a2ff3d74521ca191094374880a9d00b078bc08943be0ef24a96819a5629c980'):
        raise ValueError('unchanged verified raw comparison required')
    fit = ClosedStudy(root, 'data/' + fit_id)
    try:
        raw_training = fit.input('training', raw=True)
        reference = json.loads(gzip.decompress(raw_training))
        if (len(reference) != 400 or
                hashlib.sha256(raw_training).hexdigest() !=
                saved['air1_training_input_sha256']):
            raise ValueError('verified 400-epoch training input required')
        base = root / 'data/external-imu-survey-20261018/esa-sample'
        summaries = []
        for name in TARGETS:
            with (base / name).open() as stream:
                matched = match_times(reference, records(earlier_lines(
                    stream, last_training_s=reference[-1]['time_s'])))
            prior = next(x for x in saved['sources'] if x['filename'] == name)
            indices = [index for index, _ in matched]
            if (not prior['usable'] or indices != prior['matched_training_indices']
                    or len(indices) > 400):
                raise ValueError('original matched training epochs changed')
            pairs = [corrected_neu(reference[index], row)
                     for index, row in matched]
            raw_summary = axis_summary([raw for raw, _ in pairs])
            if not np.allclose(raw_summary['rms'],
                               prior['paired_values']['position_difference_neu_m']['rms'],
                               rtol=0, atol=1e-10):
                raise ValueError('raw receiver comparison changed')
            summaries.append(dict(filename=name, matched_epochs=len(indices),
                                  raw=raw_summary,
                                  time_adjusted=axis_summary(
                                      [adjusted for _, adjusted in pairs])))
        return dict(version='esa-187-parallel-gnss-common-time-v1',
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    raw_report_sha256=hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                    training_input_sha256=saved['air1_training_input_sha256'],
                    sources=summaries, training_epochs=400,
                    later_receiver_reports_decoded=0, protected_group_reads=0,
                    imu_samples_used=0, earth_model_fits=0,
                    correction='other PPP velocity times signed offset',
                    absolute_accuracy_established=False,
                    scientific_decision='abstain')
    finally:
        fit.close()


def publish(root):
    from .studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    result = build(root)
    base = root / 'docs/prediction-observed-development'
    atomic(base / 'PARALLEL_GNSS_TIME_RESULT.json', encoded(result))
    rows = []
    for source in result['sources']:
        raw = source['raw']['rms']
        adjusted = source['time_adjusted']['rms']
        rows.append('| {} | {} | {} | {} |'.format(
            source['filename'].split('_')[1], source['matched_epochs'],
            '/'.join(f'{x:.3f}' for x in raw),
            '/'.join(f'{x:.3f}' for x in adjusted)))
    lag_values = [value for source in result['sources']
                  for value in source['time_adjusted']['lag_one_correlation']
                  if value is not None]
    page = ('# Parallel receiver positions at one common time\n\n'
        'This exploratory comparison removes the position shift expected '
        'from each submillisecond timestamp difference using that export’s '
        'reported velocity. It uses only the 400 earlier training epochs of '
        'the opened ESA flight. No later reports, protected flights or IMU '
        'samples were examined.\n\n'
        '| Other export | Matched times | Raw north/east/up RMS (m) | '
        'Time-adjusted north/east/up RMS (m) |\n'
        '| --- | ---: | ---: | ---: |\n' + '\n'.join(rows) + '\n\n'
        'The adjustment is a local first-order approximation. The receivers '
        'share an antenna and may share PPP processing errors. The adjusted '
        'differences also persist across seconds: their per-axis lag-one '
        f'correlations range from {min(lag_values):.2f} to {max(lag_values):.2f}. '
        'The remaining '
        'differences measure relative agreement; they cannot prove absolute '
        'accuracy, qualify the full prediction-error law or decide an Earth '
        'model.\n\n'
        '[Fixed method](PARALLEL_GNSS_TIME_PLAN.md) · '
        '[Detailed result](PARALLEL_GNSS_TIME_RESULT.json).\n')
    atomic(base / 'PARALLEL_GNSS_TIME_RESULT.md', page.encode())
    return result


if __name__ == '__main__':
    result = publish('.')
    print(json.dumps([(x['filename'], x['matched_epochs'])
                      for x in result['sources']]))
