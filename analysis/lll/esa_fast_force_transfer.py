# SPDX-License-Identifier: AGPL-3.0-or-later
"""Earlier-to-later score transfer using measured force variation on ESA 187."""

import argparse
from contextlib import closing
import gzip
import hashlib
import json
import math
import os
from pathlib import Path


BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_FAST_FORCE_TRANSFER_PLAN.md'
FREEZE = BASE+'esa-fast-force-transfer-v2-freeze.json'
PRIOR_FAILURE = BASE+'esa-fast-force-transfer-failure.json'
EARLIER = BASE+'esa-fast-force-transfer-earlier.json'
RESULT = BASE+'esa-fast-force-transfer-result.json'
ARMS = ('constant', 'during_interval', 'decaying')
MAXIMUM_ROWS = 40000
BIN_S = .1
DECAY_S = 15.
REFERENCE_FLOOR_M_S2 = .001
BLOCK = 30


def weights(fast_force, spacing, *, reference):
    import numpy as np

    fast, spacing = (np.asarray(x, float) for x in (fast_force, spacing))
    if (fast.ndim != 1 or fast.shape != spacing.shape or not len(fast)
            or not all(np.isfinite(x).all() for x in (fast, spacing))
            or np.any(fast < 0.) or np.any(spacing <= 0.) or not math.isfinite(reference) or reference <= 0.):
        raise ValueError('finite measured force variation and positive timing and reference required')
    fraction = -np.expm1(-spacing/DECAY_S)
    memory = np.empty(len(fast))
    value = 0.
    for i, (target, step) in enumerate(zip(fast/reference, fraction, strict=True)):
        value += step*(target-value)
        memory[i] = value
    return dict(constant=np.ones(len(fast)), during_interval=1.+fast/reference, decaying=1.+memory)


def score(innovations, multipliers, *, scale=None):
    import numpy as np

    z, weight = (np.asarray(x, float) for x in (innovations, multipliers))
    if (z.ndim != 2 or z.shape[1] != 3 or not z.size or weight.shape != (len(z),)
            or not all(np.isfinite(x).all() for x in (z, weight)) or np.any(weight <= 0.)):
        raise ValueError('complete three-component innovations and positive variance multipliers required')
    quadratic = float(np.sum(z**2/weight[:, None]))
    scale = quadratic/z.size if scale is None else scale
    if not math.isfinite(scale) or scale <= 0. or not math.isfinite(quadratic):
        raise ValueError('positive finite variance scale and finite score required')
    # All arms share the original innovation transformation and Gaussian
    # constant. Omitting these terms preserves each matched score contrast.
    return dict(variance_scale=float(scale), mean_standardized_error=quadratic/(z.size*scale),
                reduced_negative_log_score=.5*(quadratic/scale + z.size*math.log(scale)
                                              + 3.*float(np.log(weight).sum())))


def interval_gap(timestamps, force, speed, *, span):
    import numpy as np
    from .esa_force_variation import variation

    if not math.isfinite(span) or span <= 0.:
        raise ValueError('positive receiver interval required')
    value = variation(timestamps, force, speed, np.array([0., span]), np.full(2, 1./span),
                      np.array([0., 1.]), width=BIN_S)
    return dict(fast_force_gap_m_s2=value['gap_m_s2'],
                orientation_only_upper_gap_m_s2=value['orientation_only_upper_gap_m_s2'])


def inertial_support(source, inspection, times):
    import numpy as np
    from .airquantumgrav_packet_slice import held_measurements
    from .esa_component_preflight import RECORDS, WIDTH

    with source.open('rb') as stream:
        before = os.fstat(stream.fileno())
        if (inspection['records'] != RECORDS or before.st_size != WIDTH*(RECORDS+1)
                or hashlib.file_digest(stream, 'sha256').hexdigest() != inspection['source_sha256']):
            raise ValueError('opened original iMAR source differs')
        stream.seek(0)
        header = stream.read(WIDTH)
        timestamp, force, gyro = held_measurements(stream, header, row_bytes=WIDTH, row_count=RECORDS,
            maximum_samples=MAXIMUM_ROWS, lower=times[0], upper=times[-1])
        after = os.fstat(stream.fileno())
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('original IMU changed during verified reads')
    speed = np.linalg.norm(gyro, axis=1)
    details = []
    for left, right in zip(times[:-1], times[1:], strict=True):
        first = np.searchsorted(timestamp, left, side='right')-1
        last = np.searchsorted(timestamp, right, side='left')
        span = right-left
        if not 0 <= first < last < len(timestamp) or span <= 0.:
            raise ValueError('unbracketed original receiver interval')
        details.append(interval_gap(timestamp[first:last+1]-left, force[first:last], speed[first:last], span=span))
    return len(force), details


def phase(study, cut, receiver, recorded, source, inspection, *, earlier):
    import numpy as np
    from .esa_innovation_transfer import window

    errors = window(study, cut, receiver, recorded)
    times = np.asarray([r['time_s'] for r in receiver[cut-1:cut+120]])
    if len(times) != 121:
        raise ValueError('exact original forecast time interval required')
    decoded, exposure = inertial_support(source, inspection, times)
    fast = np.asarray([r['fast_force_gap_m_s2'] for r in exposure])
    reference = max(REFERENCE_FLOOR_M_S2, float(np.median(fast))) if earlier is None else earlier['reference_m_s2']
    multiplier = weights(fast, np.diff(times), reference=reference)
    results = {}
    for law, (innovation, physical) in errors.items():
        scores = {arm: score(innovation, multiplier[arm], scale=(
            None if earlier is None else earlier['by_sensor_law'][law]['scores'][arm]['variance_scale'])) for arm in ARMS}
        blocks = []
        for i in range(0, len(fast), BLOCK):
            part = slice(i, i+BLOCK)
            blocks.append(dict(first_report=i+1, last_report=i+BLOCK,
                mean_force_gap_m_s2=float(np.mean(fast[part])),
                innovation_energy_ordered=np.sum(innovation[part]**2, axis=0).tolist(),
                position_energy_neu_m2=np.sum(physical[part]**2, axis=0).tolist()))
        results[law] = dict(scores=scores, blocks=blocks)
    return dict(cut=cut, reference_m_s2=reference, intervals=exposure, imu_samples=decoded,
                by_sensor_law=results)


def run(root, action):
    from . import esa_innovation_transfer as sealed
    from . import esa_native_rolling_transfer as original
    from .airquantumgrav_inventory import IMU_NAME, METADATA, validate_context
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure

    raw = {name: (root/path).read_bytes() for name, path in METADATA.items()}
    metadata = {name: json.loads(value) for name, value in raw.items()}
    validate_context(**metadata)
    source = safe_path(root, str(Path(METADATA['inspection']).with_name(IMU_NAME)))
    with closing(ClosedStudy(root, 'data/'+original.ID)) as study:
        if (study.completion['manifest_sha256'] != sealed.SOURCE_SHA or study.completion['state'] != 'complete'
                or set(study.rows) != {task['identity'] for task in original.tasks()}
                or any(not row['passed'] for row in study.rows.values())):
            raise ValueError('complete and exact archival forecasts required')
        sources = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_esa_fast_force_transfer.py')
        freeze = encoded(dict(source=study.completion, environment=runtime_environment(),
            prior_technical_failure_sha256=digest((root/PRIOR_FAILURE).read_bytes()),
            metadata_hashes={name:digest(data) for name, data in raw.items()},
            sources={name:digest((root/name).read_bytes()) for name in source_closure(root, sources)},
            archived_score_hashes=(sealed.EARLY_SCORE_SHA, sealed.LATE_SCORE_SHA), arms=ARMS,
            decay_s=DECAY_S, bin_s=BIN_S, reference_floor_m_s2=REFERENCE_FLOOR_M_S2,
            imu_rows_per_phase=MAXIMUM_ROWS, variation_evaluations_per_phase=120, scores_per_phase=6,
            receiver_reports_per_block=BLOCK, optimizer_starts=0, native_calls=0, protected_reads=0))
        if action == 'freeze':
            _write_equal(root/FREEZE, freeze)
            return dict(freeze_sha256=digest(freeze))
        if (root/FREEZE).read_bytes() != freeze:
            raise ValueError('frozen force-error transfer inputs or policy changed')
        if action == 'earlier':
            recorded = (root/original.EARLIER_REPORT).read_bytes()
            if digest(recorded) != sealed.EARLY_SCORE_SHA:
                raise ValueError('sealed earlier score changed')
            receiver = json.loads(gzip.decompress(study.input('400-training', raw=True)))
            value = phase(study, 200, receiver, json.loads(recorded), source, metadata['inspection'], earlier=None)
            report = dict(**value, later_opened=False)
            target = EARLIER
        else:
            earlier_bytes = (root/EARLIER).read_bytes()
            earlier = json.loads(earlier_bytes)
            recorded = (root/original.REPORT).read_bytes()
            if (earlier['freeze_sha256'] != digest(freeze) or earlier['later_opened'] is not False
                    or digest(recorded) != sealed.LATE_SCORE_SHA):
                raise ValueError('verified earlier scales and later score required')
            with closing(ClosedStudy(root, original.LATER_SOURCE, store=study.store)) as parent:
                if parent.completion['manifest_sha256'] != original.LATER_SOURCE_SHA:
                    raise ValueError('sealed later receiver source changed')
                receiver = json.loads(gzip.decompress(parent.input('training', raw=True)))
            value = phase(study, 400, receiver, json.loads(recorded), source, metadata['inspection'], earlier=earlier)
            report = dict(**value, earlier_sha256=digest(earlier_bytes), later_opened=True)
            target = RESULT
    payload = encoded(dict(**report, freeze_sha256=digest(freeze), optimizer_starts=0, native_calls=0,
                           protected_reads=0, scientific_decision='abstain'))
    _write_equal(root/target, payload)
    return dict(sha256=digest(payload), scores=6, forecast_cut=value['cut'], imu_samples=value['imu_samples'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'earlier', 'compare'))
    print(json.dumps(run(Path.cwd(), parser.parse_args().action), sort_keys=True))
