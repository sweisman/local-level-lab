# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score a sealed ESA development forecast against parallel PPP receivers."""

import gzip
import hashlib
import json
import math
from pathlib import Path
import platform

import numpy as np
import scipy

from .esa_parallel_gnss import build as verified_sources, earlier_lines, match_times
from .esa_ppp_acquisition import TARGETS


def position_at_time(row, target_time_s):
    """Move one reported PPP coordinate to a nearby time using its velocity."""
    phi = math.radians(float(row['latitude_deg']))
    lam = math.radians(float(row['longitude_deg']))
    h = float(row['height_m'])
    dt = float(row['time_s']) - float(target_time_s)
    velocity = tuple(float(row[key]) for key in
                     ('north_mps', 'east_mps', 'up_mps'))
    if (not all(map(math.isfinite, (phi, lam, h, dt, *velocity))) or
            abs(phi) >= math.pi/2):
        raise ValueError('finite nonpolar PPP position, velocity and time required')
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = f * (2 - f)
    q = 1 - e2 * math.sin(phi)**2
    meridional = a * (1 - e2) / q**1.5
    prime_vertical = a / math.sqrt(q)
    return (phi - velocity[0] * dt / (meridional + h),
            lam - velocity[1] * dt / ((prime_vertical + h) * math.cos(phi)),
            h - velocity[2] * dt)


def build(root):
    from .airquantumgrav_receiver import records
    from .esa_rolling_origin_400_conditioning import ID as condition_id
    from .esa_rolling_origin_400_conditioning_score import build as baseline_score
    from .esa_rolling_origin_400_score import PARENT, score_raw
    from .esa_rolling_origin_400_study import ID as fit_id
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    sources = verified_sources(root)
    source_path = root / 'docs/prediction-observed-development/PARALLEL_GNSS_RESULT.json'
    baseline_path = root / 'docs/prediction-observed-development/ROLLING_ORIGIN_400_CONDITIONAL_RESULT.json'
    if (sources != json.loads(source_path.read_text()) or
            baseline_score(root) != json.loads(baseline_path.read_text())):
        raise ValueError('unchanged source and sealed baseline reports required')
    fit = ClosedStudy(root, 'data/' + fit_id)
    conditioned = ClosedStudy(root, 'data/' + condition_id)
    parent = ClosedStudy(root, PARENT)
    try:
        origin = fit.input('parent_identity')
        if (origin['manifest_sha256'] != parent.completion['manifest_sha256'] or
                origin['summary_sha256'] != parent.completion['summary_sha256'] or
                conditioned.input('fit_identity') != dict(
                    prefix='data/' + fit_id,
                    manifest_sha256=fit.completion['manifest_sha256'],
                    summary_sha256=fit.completion['summary_sha256'])):
            raise ValueError('unchanged fit and conditioning lineage required')
        all_rows = json.loads(gzip.decompress(parent.input('training', raw=True)))
        targets = all_rows[400:520]
        if len(all_rows) != 800 or len(targets) != 120:
            raise ValueError('original 400/120 receiver window required')
        streams = [('air1', targets, sources['air1_source_sha256'])]
        base = root / 'data/external-imu-survey-20261018/esa-sample'
        for name in TARGETS:
            with (base / name).open() as stream:
                matched = match_times(targets, records(earlier_lines(
                    stream, last_training_s=targets[-1]['time_s'])))
            if [index for index, _ in matched] != list(range(120)):
                raise ValueError('all 120 later receiver times must match')
            source = next(item for item in sources['sources']
                          if item['filename'] == name)
            streams.append((name.split('_')[1], [row for _, row in matched],
                            source['source_sha256']))
        baseline = json.loads(baseline_path.read_text())
        results = []
        for law in ('increment', 'point'):
            if (fit.envelope(law)['result'].get('passed') is not True or
                    conditioned.envelope(law)['result'].get('passed') is not True):
                raise ValueError('both sealed fits and corrections must pass')
            raw = fit.artifact(law, 'forecast.json')
            saved = conditioned.artifact(law, 'conditional-forecast.json')
            times = np.asarray(raw['times_s'][400:520], dtype=float)
            actual = np.asarray([row['time_s'] for row in targets], dtype=float)
            if (saved['raw_coordinates'] != raw['coordinates'] or
                    saved['later_receiver_values_used'] or
                    saved['optimization_performed'] or
                    raw['prediction_receiver_positions_used'] or
                    len(saved['conditional_receiver_mean']) != 120 or
                    not np.allclose(times + fit.input('saved-input-binding')['time_origin_s'],
                                    actual, rtol=0, atol=1e-6)):
                raise ValueError('unchanged earlier-only forecast required')
            for receiver, rows, source_sha in streams:
                adjusted = [position_at_time(row, target['time_s'])
                            for row, target in zip(rows, targets)]
                scored = score_raw(saved['conditional_receiver_mean'], adjusted)
                if (receiver == 'air1' and scored !=
                        baseline['laws'][law]['score']['conditional']):
                    raise ValueError('original air1 forecast score not reproduced')
                metrics = scored['metrics']
                baseline_metrics = baseline['laws'][law]['score']['conditional']['metrics']
                results.append(dict(law=law, receiver=receiver,
                                    source_sha256=source_sha, epochs=120,
                                    metrics=metrics,
                                    horizontal_rms_difference_from_air1_m=(
                                        metrics['horizontal_rms_m'] -
                                        baseline_metrics['horizontal_rms_m']),
                                    height_rms_difference_from_air1_m=(
                                        metrics['vertical_rms_m'] -
                                        baseline_metrics['vertical_rms_m'])))
        return dict(version='esa-187-parallel-gnss-forecast-development-v1',
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    runtime=dict(python=platform.python_version(),
                                 numpy=np.__version__, scipy=scipy.__version__),
                    source_report_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
                    baseline_report_sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
                    fit_manifest_sha256=fit.completion['manifest_sha256'],
                    conditioning_manifest_sha256=conditioned.completion['manifest_sha256'],
                    results=results, later_receiver_epochs_scored=240,
                    protected_group_reads=0, new_fits=0, native_calculations=0,
                    independent_validation=False, confidence_calibrated=False,
                    scientific_decision='abstain')
    finally:
        parent.close()
        conditioned.close()
        fit.close()


def publish(root):
    from .studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    result = build(root)
    base = root / 'docs/prediction-observed-development'
    atomic(base / 'PARALLEL_GNSS_FORECAST_RESULT.json', encoded(result))
    rows = []
    for item in result['results']:
        metrics = item['metrics']
        rows.append('| {} | {} | {:.3f} | {:.3f} |'.format(
            item['law'], item['receiver'], metrics['horizontal_rms_m'],
            metrics['vertical_rms_m']))
    page = ('# Sealed ESA forecast against three receivers\n\n'
        'The unchanged early-only conditional forecast is scored against '
        'three PPP exports on the same 120 later times from opened recording '
        '187. The `air1` score is reproduced exactly before the other two '
        'streams are scored. Their positions are moved to the forecast epoch '
        'using reported velocity and the submillisecond timestamp offset.\n\n'
        '| Saved IMU error law | Receiver | Horizontal RMS (m) | Height RMS (m) |\n'
        '| --- | --- | ---: | ---: |\n' + '\n'.join(rows) + '\n\n'
        'This comparison was designed after the `air1` result was known. '
        'The three GNSS receivers share an antenna and may share processing '
        'errors. Similar scores would check receiver-specific sensitivity, '
        'not prove physical accuracy, calibrated coverage or an Earth-model '
        'decision. No protected flight or new fit was used.\n\n'
        '[Fixed method](PARALLEL_GNSS_FORECAST_PLAN.md) · '
        '[Detailed result](PARALLEL_GNSS_FORECAST_RESULT.json).\n')
    atomic(base / 'PARALLEL_GNSS_FORECAST_RESULT.md', page.encode())
    return result


if __name__ == '__main__':
    result = publish('.')
    print(json.dumps([(x['law'], x['receiver']) for x in result['results']]))
