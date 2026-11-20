# SPDX-License-Identifier: AGPL-3.0-or-later
"""Earlier-only comparison of three ESA-187 PPP receiver exports."""

import gzip
import hashlib
import json
import math
from pathlib import Path
import re

import numpy as np

from .esa_ppp_acquisition import TARGETS, verify_complete


MATCH_TOLERANCE_S = 0.002
MIN_MATCHES = 300


def earlier_lines(lines, *, last_training_s, tolerance_s=MATCH_TOLERANCE_S):
    """Pass the source header and earlier rows without decoding later values."""
    if not math.isfinite(last_training_s) or tolerance_s <= 0:
        raise ValueError('finite earlier cutoff and positive tolerance required')
    for line in lines:
        parts = line.split()
        if len(parts) == 30 and re.fullmatch(r'\d{8}', parts[0]):
            if float(parts[26]) > last_training_s + tolerance_s:
                return
        yield line


def match_times(targets, source_rows, *, tolerance_s=MATCH_TOLERANCE_S):
    """Match ordered epochs by GPS time only, without interpolation or reuse."""
    expected = list(targets)
    if (not expected or tolerance_s <= 0 or
            any(expected[i]['time_s'] >= expected[i+1]['time_s']
                for i in range(len(expected)-1))):
        raise ValueError('ordered earlier time targets required')
    index = 0
    matched = []
    for row in source_rows:
        time = row['time_s']
        if not math.isfinite(time):
            raise ValueError('finite source time required')
        while (index < len(expected) and
               time > expected[index]['time_s'] + tolerance_s):
            index += 1
        if index == len(expected):
            break
        if abs(time-expected[index]['time_s']) <= tolerance_s:
            matched.append((index, row))
            index += 1
            if index == len(expected):
                break
    return matched


def relative_neu(reference, other):
    """Small coordinate separation in the reference's local NEU axes."""
    values = [reference[key] for key in ('latitude_deg', 'longitude_deg', 'height_m')]
    values += [other[key] for key in ('latitude_deg', 'longitude_deg', 'height_m')]
    if (not all(math.isfinite(float(v)) for v in values) or
            any(abs(float(p)) >= 90 for p in (values[0], values[3])) or
            any(abs(float(l)) > 180 for l in (values[1], values[4]))):
        raise ValueError('finite nonpolar receiver coordinates required')
    phi = math.radians(values[0])
    dphi = math.radians(values[3]-values[0])
    dlon = math.radians((values[4]-values[1]+180) % 360-180)
    height = float(values[2])
    a = 6378137.0
    f = 1/298.257223563
    e2 = f*(2-f)
    q = 1-e2*math.sin(phi)**2
    meridional = a*(1-e2)/q**1.5
    prime_vertical = a/math.sqrt(q)
    return ((meridional+height)*dphi,
            (prime_vertical+height)*math.cos(phi)*dlon,
            float(values[5]-values[2]))


def _axis_summary(values):
    matrix = np.asarray(values, dtype=float)
    mean = np.mean(matrix, axis=0)
    return dict(mean=mean.tolist(),
                rms=np.sqrt(np.mean(matrix**2, axis=0)).tolist(),
                centered_rms=np.sqrt(np.mean((matrix-mean)**2, axis=0)).tolist(),
                p95_absolute=np.quantile(np.abs(matrix), .95, axis=0).tolist())


def summarize(reference, matched):
    indices = [index for index, _ in matched]
    if len(indices) < MIN_MATCHES:
        return dict(matched_epochs=len(indices), usable=False,
                    reason='fewer than 300 exact-time training matches',
                    matched_training_indices=indices,
                    paired_values=None)
    times = [row['time_s']-reference[index]['time_s']
             for index, row in matched]
    time_motion = [abs(row['time_s']-reference[index]['time_s']) * max(
        math.hypot(row['north_mps'], row['east_mps']),
        math.hypot(reference[index]['north_mps'],
                   reference[index]['east_mps']))
        for index, row in matched]
    position = [relative_neu(reference[index], row)
                for index, row in matched]
    velocity = [[row[k]-reference[index][k]
                 for k in ('north_mps', 'east_mps', 'up_mps')]
                for index, row in matched]
    return dict(matched_epochs=len(indices), usable=True,
                matched_training_indices=indices,
                paired_values=dict(
                    position_difference_neu_m=_axis_summary(position),
                    velocity_difference_neu_mps=_axis_summary(velocity),
                    time_difference_s=dict(min=float(min(times)),
                                           mean=float(np.mean(times)),
                                           max=float(max(times)),
                                           maximum_absolute=float(max(map(abs, times)))),
                    maximum_time_offset_motion_m=float(max(time_motion))))


def build(root):
    from .airquantumgrav_receiver import records
    from .esa_gnss_covariance_audit import build as verified_air1
    from .esa_rolling_origin_400_study import ID as FIT_ID
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    air1_audit = verified_air1(root)
    fit = ClosedStudy(root, 'data/' + FIT_ID)
    try:
        raw = fit.input('training', raw=True)
        reference = json.loads(gzip.decompress(raw))
        if (len(reference) != 400 or
                hashlib.sha256(raw).hexdigest() !=
                air1_audit['training_input_sha256']):
            raise ValueError('verified sealed air1 training input required')
        base = root / 'data/external-imu-survey-20261018/esa-sample'
        outputs = []
        for name in TARGETS:
            target = base / name
            receipt_path = base / (name+'.receipt.json')
            receipt = json.loads(receipt_path.read_text())
            digest = verify_complete(target, TARGETS[name], receipt)
            with target.open() as stream:
                candidates = records(earlier_lines(
                    stream, last_training_s=reference[-1]['time_s']))
                matched = match_times(reference, candidates)
            result = summarize(reference, matched)
            outputs.append(dict(filename=name,
                                source_sha256=digest,
                                receipt_sha256=hashlib.sha256(
                                    receipt_path.read_bytes()).hexdigest(),
                                expected_cadence_hz=5 if 'mosaic03' in name else 1,
                                **result))
        return dict(version='esa-187-parallel-gnss-training-v1',
                    air1_source_sha256=air1_audit['source_original_sha256'],
                    air1_training_input_sha256=air1_audit['training_input_sha256'],
                    air1_audit_source_sha256=air1_audit['source_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    training_receiver_epochs=len(reference),
                    tolerance_s=MATCH_TOLERANCE_S,
                    minimum_matches=MIN_MATCHES,
                    sources=outputs,
                    later_receiver_reports_decoded=0,
                    protected_group_reads=0,
                    imu_samples_used=0, earth_model_fits=0,
                    shared_antenna=True,
                    receiver_hardware_distinct_per_campaign_paper=True,
                    common_processing_possible=True,
                    absolute_accuracy_established=False,
                    scientific_decision='abstain')
    finally:
        fit.close()


def publish(root):
    from .studies.artifacts import atomic, encoded

    root = Path(root).resolve()
    result = build(root)
    base = root / 'docs/prediction-observed-development'
    atomic(base / 'PARALLEL_GNSS_RESULT.json', encoded(result))
    rows = []
    for source in result['sources']:
        if source['usable']:
            values = source['paired_values']
            pos = values['position_difference_neu_m']['rms']
            vel = values['velocity_difference_neu_mps']['rms']
            largest_dt = values['time_difference_s']['maximum_absolute']
            rows.append('| {} | {} | {:.4f} | {:.3f} | {} | {} |'.format(
                source['filename'].split('_')[1], source['matched_epochs'],
                largest_dt, values['maximum_time_offset_motion_m'],
                '/'.join(f'{x:.3f}' for x in pos),
                '/'.join(f'{x:.3f}' for x in vel)))
        else:
            rows.append('| {} | {} | — | — | — | — |'.format(
                source['filename'].split('_')[1], source['matched_epochs']))
    page = ('# Parallel GNSS receivers on the opened ESA flight\n\n'
        'Two additional PPP exports from recording 187 were downloaded with '
        'verified sizes, hashes and resumable receipts. The source campaign '
        'reports three physical GNSS receivers sharing one aircraft antenna. '
        'This check compares only the 400 earlier `air1` training times; '
        'no withheld report or protected flight was analyzed.\n\n'
        '| Other export | Matched earlier epochs | Largest time offset (s) | '
        'Maximum motion during time offset (m) | '
        'North/east/up position RMS difference (m) | '
        'North/east/up velocity RMS difference (m/s) |\n'
        '| --- | ---: | ---: | ---: | ---: | ---: |\n' + '\n'.join(rows) + '\n\n'
        'Matches require timestamps within 2 ms and use no interpolation. '
        'The motion column bounds the apparent displacement from each time '
        'offset using reported speed; it has not been subtracted. '
        'The detailed result also gives signed means and variation after '
        'subtracting a constant offset. The separate receiver hardware gives '
        'a real cross-check, but the antenna is shared and PPP processing may '
        'have common errors. Pairwise disagreement can expose error; agreement '
        'does not prove absolute accuracy or calibrate the IMU error law. '
        'No Earth-model decision follows.\n\n'
        '[Fixed method](PARALLEL_GNSS_PLAN.md) · '
        '[Detailed result](PARALLEL_GNSS_RESULT.json) · '
        '[Campaign instrumentation](https://essd.copernicus.org/articles/17/1667/2025/essd-17-1667-2025.html).\n')
    atomic(base / 'PARALLEL_GNSS_RESULT.md', page.encode())
    return result


if __name__ == '__main__':
    result = publish('.')
    print(json.dumps([(s['filename'], s['matched_epochs'], s['usable'])
                      for s in result['sources']]))
