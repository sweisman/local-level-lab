# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check one sealed ESA IMU training fit against parallel PPP receivers."""

import gzip
import hashlib
import json
import math
from pathlib import Path
import platform

import numpy as np
import scipy

from .esa_parallel_gnss import (build as raw_comparison, earlier_lines,
                                match_times, relative_neu)
from .esa_parallel_gnss_time import axis_summary
from .esa_ppp_acquisition import TARGETS


def fit_residual_neu(coordinate, fit_time_s, observed):
    """Fitted minus observed position at the fit epoch, in local NEU metres."""
    if len(coordinate) != 3 or not math.isfinite(float(fit_time_s)):
        raise ValueError('three fitted coordinates and finite time required')
    fitted = dict(latitude_deg=math.degrees(coordinate[0]),
                  longitude_deg=math.degrees(coordinate[1]),
                  height_m=float(coordinate[2]))
    observed_minus_fitted = relative_neu(fitted, observed)
    dt = float(observed['time_s'] - fit_time_s)
    velocity = (observed['north_mps'], observed['east_mps'],
                observed['up_mps'])
    if not math.isfinite(dt) or not all(math.isfinite(float(v)) for v in velocity):
        raise ValueError('finite receiver time and velocity required')
    return tuple(float(v) * dt - difference
                 for v, difference in zip(velocity, observed_minus_fitted))


def build(root):
    from .airquantumgrav_receiver import records
    from .esa_rolling_origin_400_study import ID as fit_id
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    raw = raw_comparison(root)
    raw_path = root / 'docs/prediction-observed-development/PARALLEL_GNSS_RESULT.json'
    if raw != json.loads(raw_path.read_text()):
        raise ValueError('unchanged verified parallel receiver report required')
    time_path = root / 'docs/prediction-observed-development/PARALLEL_GNSS_TIME_RESULT.json'
    time_report = json.loads(time_path.read_text())
    time_source = root / 'analysis/lll/esa_parallel_gnss_time.py'
    if (time_report['source_sha256'] != hashlib.sha256(time_source.read_bytes()).hexdigest()
            or time_report['raw_report_sha256'] != hashlib.sha256(raw_path.read_bytes()).hexdigest()):
        raise ValueError('unchanged common-time method required')
    study = ClosedStudy(root, 'data/' + fit_id)
    try:
        training_input = study.input('training', raw=True)
        reference = json.loads(gzip.decompress(training_input))
        binding = study.input('saved-input-binding')
        if (len(reference) != 400 or
                hashlib.sha256(training_input).hexdigest() !=
                raw['air1_training_input_sha256']):
            raise ValueError('sealed 400-epoch training input required')
        streams = [('air1', reference, raw['air1_source_sha256'])]
        base = root / 'data/external-imu-survey-20261018/esa-sample'
        for name in TARGETS:
            with (base / name).open() as stream:
                matches = match_times(reference, records(earlier_lines(
                    stream, last_training_s=reference[-1]['time_s'])))
            if [index for index, _ in matches] != list(range(400)):
                raise ValueError('all 400 earlier receiver times must match')
            source = next(row for row in raw['sources'] if row['filename'] == name)
            streams.append((name.split('_')[1], [row for _, row in matches],
                            source['source_sha256']))
        reports = []
        for law in ('increment', 'point'):
            if not study.envelope(law)['result']['passed']:
                raise ValueError('sealed fit must pass numerical checks')
            forecast = study.artifact(law, 'forecast.json')
            fit = study.artifact(law, 'fit.json')
            coordinates = np.asarray(forecast['coordinates'][:400], dtype=float)
            times = np.asarray(forecast['times_s'][:400], dtype=float)
            difference = np.asarray(forecast['training_coordinate_difference'],
                                    dtype=float)
            if (coordinates.shape != (400, 3) or times.shape != (400,) or
                    difference.shape != (400, 3) or not np.isfinite(coordinates).all()
                    or not fit['converged'] or len(fit['active_parameters']) != 26
                    or forecast['training_epochs'] != 400
                    or forecast['prediction_epochs'] != 120
                    or forecast['prediction_receiver_positions_used']):
                raise ValueError('qualified saved training fit required')
            observed_times = np.asarray([row['time_s'] for row in reference])
            if not np.allclose(times + binding['time_origin_s'], observed_times,
                               rtol=0, atol=1e-6):
                raise ValueError('fit and sealed training times differ')
            observed_coord = np.asarray([
                [math.radians(row['latitude_deg']),
                 math.radians(row['longitude_deg']), row['height_m']]
                for row in reference])
            if not np.allclose(coordinates - observed_coord, difference,
                               rtol=0, atol=1e-8):
                raise ValueError('sealed training coordinate residual differs')
            for name, rows, source_sha in streams:
                residual = [fit_residual_neu(coordinates[i], observed_times[i], row)
                            for i, row in enumerate(rows)]
                reports.append(dict(law=law, receiver=name,
                                    receiver_source_sha256=source_sha,
                                    epochs=400, summary=axis_summary(residual)))
        return dict(version='esa-187-parallel-gnss-fit-training-v1',
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    runtime=dict(python=platform.python_version(),
                                 numpy=np.__version__, scipy=scipy.__version__),
                    training_input_sha256=raw['air1_training_input_sha256'],
                    fit_study_manifest_sha256=study.completion['manifest_sha256'],
                    fit_study_completion_sha256=hashlib.sha256(
                        study.read('completion.json', raw=True)).hexdigest(),
                    raw_report_sha256=hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                    common_time_report_sha256=hashlib.sha256(time_path.read_bytes()).hexdigest(),
                    rows=reports, saved_laws=['increment', 'point'],
                    later_receiver_reports_decoded=0, protected_group_reads=0,
                    new_fits=0, native_calculations=0,
                    absolute_accuracy_established=False,
                    scientific_decision='abstain')
    finally:
        study.close()


def publish(root):
    from .studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    result = build(root)
    base = root / 'docs/prediction-observed-development'
    atomic(base / 'PARALLEL_GNSS_FIT_RESULT.json', encoded(result))
    rows = []
    for row in result['rows']:
        rms = '/'.join(f'{x:.3f}' for x in row['summary']['rms'])
        rows.append(f'| {row["law"]} | {row["receiver"]} | {rms} |')
    page = ('# One fitted trajectory, three GNSS receivers\n\n'
        'The two sealed ESA IMU fits used only the first 400 `air1` positions. '
        'Their unchanged, pre-conditioning trajectories are compared here with `air1` '
        'and two other PPP exports at the same earlier times. The other '
        'receivers were adjusted to the `air1` epoch using their reported '
        'velocity and submillisecond time offset. No later receiver report, '
        'protected flight, new fit or IMU packet was used.\n\n'
        '| Saved error law | Receiver | Fitted-minus-receiver north/east/up RMS (m) |\n'
        '| --- | --- | ---: |\n' + '\n'.join(rows) + '\n\n'
        'The fitted trajectory misses each receiver by roughly 0.8 m north '
        'and 1.0 m east RMS, while the receivers differ from one another by '
        'centimetres. These are **training** residuals from the raw fitted '
        'trajectory, not predictions on unused times; the separate early-only '
        'conditioning step changes the later forecast. '
        'The receivers share an antenna and may share PPP errors. Close '
        'agreement cannot establish absolute accuracy, a prediction-error '
        'law or an Earth-model decision.\n\n'
        '[Fixed method](PARALLEL_GNSS_FIT_PLAN.md) · '
        '[Detailed result](PARALLEL_GNSS_FIT_RESULT.json).\n')
    atomic(base / 'PARALLEL_GNSS_FIT_RESULT.md', page.encode())
    return result


if __name__ == '__main__':
    result = publish('.')
    print(json.dumps([(x['law'], x['receiver'], x['epochs'])
                      for x in result['rows']]))
