# SPDX-License-Identifier: AGPL-3.0-or-later
"""Package verified repeat-turn measurements for training-only forecast tasks."""

import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path


BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_REPEAT_TURN_MATERIAL_PLAN.md'
FREEZE = BASE+'esa-repeat-turn-material-freeze.json'
RECEIPT = BASE+'esa-repeat-turn-material-result.json'
STAGE = 'data/esa-repeat-turn-forecast-inputs-v1'
INPUT_SHA = '78e4d5bcd0ee1a27776afaff06ec1eeaf0692cbd4a1b1eee0f649ab19fe740df'
SCORING_REQUEST_SHA = 'c50c6c91622c168648c2f8f7a9a1603f2a9477186abae3b4c3431d60c9c98175'
MAX_BYTES = 48*1024**2
FILES = ('training.json.gz', 'forecast-times.json', 'interval.npz')


def array_hashes(items):
    import numpy as np
    from .studies.artifacts import digest

    return {name: digest(np.asarray(value, dtype='<f8').tobytes()) for name, value in items.items()}


def package(rows, times, arrays, receipt):
    import numpy as np
    from .esa_repeat_turn_inputs import LATENCY, MAX_GAP, TRAIN, LATER
    from .studies.artifacts import digest, encoded

    encoded_rows = encoded(rows)
    if len(rows) != TRAIN or digest(encoded_rows) != receipt['training_receiver_sha256']:
        raise ValueError('exact earlier receiver positions required')
    times = np.asarray(times, dtype=float)
    if (times.shape != (TRAIN+LATER,) or times.tolist() != receipt['query_times_s']
            or not np.array_equal(np.asarray([row['time_s'] for row in rows])-receipt['raw_first_s'], times[:TRAIN])
            or not np.isfinite(times).all() or np.any(np.diff(times) <= 0.)):
        raise ValueError('exact earlier and later query clock required')
    count, total = (receipt[name] for name in ('training_packets', 'forecast_packets'))
    if (set(arrays) != {'dt', 'theta', 'dv'} or not 0 < count < total
            or array_hashes(arrays) != receipt['increment_hashes']
            or array_hashes({key: array[:count] for key, array in arrays.items()}) != receipt['training_prefix_hashes']):
        raise ValueError('full and prefix inertial hashes must match the preflight')
    dt = arrays['dt']
    if (dt.shape != (total,) or arrays['theta'].shape != (total,3) or arrays['dv'].shape != (total,3)
            or not all(np.isfinite(a).all() for a in arrays.values()) or np.any(dt <= 0.) or np.any(dt > MAX_GAP)):
        raise ValueError('complete finite supported increments required')
    ends = np.cumsum(dt)
    if (times[0]-LATENCY < 0. or times[-1]+LATENCY > ends[-1]
            or count != np.searchsorted(ends, times[TRAIN-1]+LATENCY, side='left')+1):
        raise ValueError('latency support and original forecast-engine prefix must match')
    buffer = io.BytesIO()
    np.savez_compressed(buffer, dt=dt, theta=arrays['theta'], dv=arrays['dv'])
    return {'training.json.gz': gzip.compress(encoded_rows, mtime=0),
            'forecast-times.json': encoded(times.tolist()), 'interval.npz': buffer.getvalue()}


def verify(root):
    from .studies.artifacts import digest, safe_path

    receipt_bytes = (root/RECEIPT).read_bytes()
    receipt = json.loads(receipt_bytes)
    if (receipt['freeze_sha256'] != digest((root/FREEZE).read_bytes()) or len(receipt['windows']) != 4
            or receipt['input_preflight_sha256'] != INPUT_SHA or receipt['scoring_positions_decoded'] != 0
            or receipt['optimizer_starts'] != 0):
        raise ValueError('exact training-only material receipt required')
    total = 0
    for window in receipt['windows']:
        if set(window['files']) != set(FILES):
            raise ValueError('unexpected or missing forecast input artifact')
        for filename, detail in window['files'].items():
            path = safe_path(root, f"{STAGE}/{window['first_index']}/{filename}")
            total += detail['size_bytes']
            if (total > MAX_BYTES or path.stat().st_size != detail['size_bytes']
                    or digest(path.read_bytes()) != detail['sha256']):
                raise ValueError('staged forecast material hash or size changed')
    if total != receipt['staged_bytes']:
        raise ValueError('staged file accounting differs from receipt')
    return dict(sha256=digest(receipt_bytes), windows=4, verified_files=4*len(FILES), staged_bytes=total)


def run(root, action):
    from .airquantumgrav_geographic_controls import construct
    from .airquantumgrav_inventory import IMU_NAME, METADATA, RECEIVER_PATH, validate_context
    from .airquantumgrav_packet_slice import held_measurements
    from .esa_component_preflight import RECORDS, WIDTH
    from .esa_repeat_turn_inputs import MAX_PER_WINDOW, PAD, RESULT as INPUT, RECIPE_SHA, read_receiver
    from .esa_repeat_turn_scoring import qualification
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded, safe_path
    from .studies.dependencies import source_closure

    if action == 'verify':
        return verify(root)
    scoring = qualification(root, 'verify')
    input_bytes = (root/INPUT).read_bytes()
    frozen = json.loads(input_bytes)
    data = {name: (root/path).read_bytes() for name,path in METADATA.items()}
    values = {name:json.loads(raw) for name,raw in data.items()}
    source = validate_context(**values)
    if (digest(input_bytes) != INPUT_SHA or scoring['request_sha256'] != SCORING_REQUEST_SHA
            or len(frozen['windows']) != 4 or frozen['scoring_positions_decoded'] != 0
            or frozen['fit_authorized'] is not False or values['inspection']['records'] != RECORDS):
        raise ValueError('exact staged-data preflight and fixed scoring qualification required')
    own = Path(__file__).relative_to(root).as_posix()
    paths = source_closure(root, (own, PLAN, 'analysis/tests/test_esa_repeat_turn_material.py'))
    freeze = encoded(dict(environment=runtime_environment(), source_hashes={name:digest((root/name).read_bytes()) for name in paths},
        input_preflight_sha256=INPUT_SHA, prior_forecast_recipe_sha256=RECIPE_SHA, scoring_software=scoring,
        source_metadata_hashes={name:digest(raw) for name, raw in data.items()},
        maximum_decoded_imu=4*MAX_PER_WINDOW, maximum_constructed_intervals=4*MAX_PER_WINDOW,
        maximum_material_bytes=MAX_BYTES, maximum_source_passes=1, optimizer_starts=0, native_calls=0,
        raw_scoring_positions=0, protected_reads=0))
    if action == 'freeze':
        _write_equal(root/FREEZE, freeze)
        return dict(freeze_sha256=digest(freeze))
    if (root/FREEZE).read_bytes() != freeze:
        raise ValueError('frozen material preparation inputs or definition changed')
    if (root/RECEIPT).exists():
        return verify(root)
    windows = [entry['window'] for entry in frozen['windows']]
    training, clocks = read_receiver(safe_path(root, RECEIVER_PATH), windows, sha=source['receiver_sha256'],
                                     named_reports=source['expected_receiver_epochs'])
    original = safe_path(root, str(Path(METADATA['inspection']).with_name(IMU_NAME)))
    staged_count, decoded, constructed = 0, 0, 0
    entries = []

    def reserve(*, constructed_intervals):
        nonlocal constructed
        constructed += constructed_intervals
        if constructed > 4*MAX_PER_WINDOW:
            raise ValueError('constructed interval allowance exceeded')

    with original.open('rb') as stream:
        start = os.fstat(stream.fileno())
        if start.st_size != WIDTH*(RECORDS+1) or hashlib.file_digest(stream, 'sha256').hexdigest() != source['imu_source_sha256']:
            raise ValueError('verified original IMU required')
        stream.seek(0)
        header = stream.read(WIDTH)
        for entry, rows, tags in zip(frozen['windows'], training, clocks, strict=True):
            if digest(encoded(tags)) != entry['scoring_clock_sha256']:
                raise ValueError('later clock fields differ from the bound preflight')
            full_time, force, angles = held_measurements(stream, header, row_bytes=WIDTH, row_count=RECORDS,
                maximum_samples=MAX_PER_WINDOW, lower=rows[0]['time_s']-PAD, upper=tags[-1][1]+PAD)
            time = full_time[:-1]
            decoded += len(time)
            if array_hashes(dict(time=time, force=force, rate=angles)) != entry['raw_hashes']:
                raise ValueError('raw series differ from the bound preflight')
            values = construct(dict(times=time, angular_rate_rads=angles, specific_force_mps2=force),
                               method='linear_points', rate_hz=300, reserve=reserve)
            queries = [row['time_s']-time[0] for row in rows]+[tag[1]-time[0] for tag in tags]
            contents = package(rows, queries, {key: values[key] for key in ('dt', 'theta', 'dv')}, entry)
            files = {name:dict(sha256=digest(payload), size_bytes=len(payload)) for name,payload in contents.items()}
            staged_count += sum(detail['size_bytes'] for detail in files.values())
            if staged_count > MAX_BYTES:
                raise ValueError('staged artifacts exceed the sealed disk allowance')
            index = entry['window']['first_index']
            for filename, payload in contents.items():
                _write_equal(safe_path(root, f'{STAGE}/{index}/{filename}'), payload)
            entries.append(dict(first_index=index, time_origin_s=entry['raw_first_s'],
                full_packets=entry['forecast_packets'], training_packets=entry['training_packets'], files=files))
        end = os.fstat(stream.fileno())
        if (start.st_size,start.st_mtime_ns,start.st_ctime_ns) != (end.st_size,end.st_mtime_ns,end.st_ctime_ns):
            raise ValueError('original IMU changed while staging')
    if decoded != frozen['decoded_imu_samples'] or constructed != frozen['constructed_intervals']:
        raise ValueError('prepared material count differs from preflight')
    report = encoded(dict(freeze_sha256=digest(freeze), input_preflight_sha256=INPUT_SHA, windows=entries,
        decoded_samples=decoded, constructed_intervals=constructed, staged_bytes=staged_count,
        training_positions=1600, scoring_times=480, scoring_positions_decoded=0,
        optimizer_starts=0, native_calls=0, fit_authorized=False))
    _write_equal(root/RECEIPT, report)
    return verify(root)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'stage', 'verify'))
    print(json.dumps(run(Path.cwd(), parser.parse_args().action), sort_keys=True))
