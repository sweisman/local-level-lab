# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bind fixed repeat-turn inputs while decoding only later receiver clock tags."""

import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path


BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_REPEAT_TURN_INPUT_PLAN.md'
FREEZE = BASE+'esa-repeat-turn-input-freeze.json'
RESULT = BASE+'esa-repeat-turn-input-result.json'
INVENTORY_SHA = '880551800b37372ee18d9aa55a6e1bbeedd684604ae26a847d1fcbe5dc603d16'
RECIPE_SHA = '08f9b2cb07549f470560a1bb6e6007b4143a6fd566131c5023ae53bd89092be6'
TRAIN, LATER = 400, 120
PAD, LATENCY, MAX_GAP = .05, .01, .005
MAX_PER_WINDOW = 157000


def query_indices(window):
    first, last = window['first_index'], window['last_index']
    boundary = first+2*TRAIN
    if (window['training_last_index'] != boundary-1 or window['scoring_first_index'] != boundary
            or last != boundary+2*LATER-1):
        raise ValueError('exact original repeat-turn boundaries required')
    return list(range(first+1, boundary, 2)), list(range(boundary+1, last+1, 2))


def clock_tag(fields):
    if len(fields) != 30 or len(fields[0]) != 8 or not fields[0].isdigit() or not fields[27].isdigit():
        raise ValueError('original receiver clock and sequence fields required')
    stamp = float(fields[26])
    if not 0. <= stamp < 604800.:
        raise ValueError('finite single-week receiver clock required')
    return int(fields[0]), stamp, int(fields[27])


def read_receiver(path, windows, *, sha, named_reports):
    from .airquantumgrav_receiver import records

    earlier, later = {}, {}
    for slot, window in enumerate(windows):
        training, scoring = query_indices(window)
        earlier.update(dict.fromkeys(training, slot))
        later.update(dict.fromkeys(scoring, slot))
    if len(earlier) != len(windows)*TRAIN or len(later) != len(windows)*LATER or earlier.keys() & later.keys():
        raise ValueError('separate exact training and scoring indices required')
    clocks = [[] for _ in windows]
    full = [[] for _ in windows]
    count = 0
    source = hashlib.sha256()

    def lines():
        nonlocal count
        with path.open('rb') as stream:
            for line in stream:
                source.update(line)
                head = line.split(maxsplit=1)[:1]
                if head and len(head[0]) == 8 and head[0].isdigit():
                    index = count
                    count += 1
                    if count > named_reports:
                        raise ValueError('original receiver report budget exceeded')
                    if index in later:
                        clocks[later[index]].append(clock_tag(line.split()))
                    if index in earlier:
                        yield line
                elif count == 0:
                    yield line

    for index, row in zip(sorted(earlier), records(lines()), strict=True):
        full[earlier[index]].append(row)
    if (count != named_reports or source.hexdigest() != sha
            or any(len(block) != LATER for block in clocks) or any(len(block) != TRAIN for block in full)):
        raise ValueError('original receiver hash, report count or selected coverage differs')
    return full, clocks


def packet_layout(raw_time, query, *, cut):
    import numpy as np

    time, query = (np.asarray(a, float) for a in (raw_time, query))
    if (time.ndim != 1 or query.ndim != 1 or not 0 < cut < len(query) or len(time) < 2
            or not all(np.isfinite(a).all() for a in (time, query))
            or np.any(np.diff(time) <= 0.) or np.any(np.diff(time) > MAX_GAP) or np.any(np.diff(query) <= 0.)):
        raise ValueError('complete original support and ordered forecast queries required')
    if query[0]-LATENCY < time[0] or query[-1]+LATENCY > time[-1]:
        raise ValueError('original support must bracket the complete latency allowance')
    index = int(np.searchsorted(time, query[cut-1]+LATENCY))
    if time[index] >= query[cut]:
        raise ValueError('training packet support overlaps the first scoring epoch')
    return dict(training_packets=index, forecast_packets=len(time)-1,
                raw_first_s=float(time[0]), raw_last_s=float(time[-1]), training_raw_end_s=float(time[index]),
                first_query_margin_s=float(query[0]-time[0]), last_query_margin_s=float(time[-1]-query[-1]))


def bind_window(window, rows, clocks, times, force, angles, *, reserve):
    import numpy as np
    from .airquantumgrav_error_policy import build
    from .airquantumgrav_geographic_controls import construct
    from .esa_motion_error_transfer import THRESHOLD_DEG_S
    from .maneuver_error_roots import turn_exposure
    from .studies.artifacts import digest, encoded

    tags = [(r['sequence'], r['time_s'], r['gps_week']) for r in rows]+clocks
    query = np.asarray([stamp for _, stamp, _ in tags])
    if (len({week for _, _, week in tags}) != 1 or np.any(abs(np.diff(query)-1.) > .02)
            or any(b[0] != a[0]+2 for a,b in zip(tags[:-1],tags[1:],strict=True))):
        raise ValueError('complete one-second receiver window with strict native sequence required')
    layout = packet_layout(times, query, cut=TRAIN)
    origin = times[0]
    material = construct(dict(times=times, angular_rate_rads=angles, specific_force_mps2=force),
                         method='linear_points', rate_hz=300, reserve=reserve)
    dt, theta, dv = (material[k] for k in ('dt', 'theta', 'dv'))
    exposure = turn_exposure(dt, theta, query-origin, previous_time=0., threshold_deg_s=THRESHOLD_DEG_S)
    weight = build(rows, policy_id='reported-short-v1')

    def hashes(items):
        return {key: digest(np.asarray(value, dtype='<f8').tobytes()) for key, value in items.items()}

    arrays = dict(dt=dt, theta=theta, dv=dv)
    return dict(window=window, **layout, query_source_indices=query_indices(window), query_times_s=(query-origin).tolist(),
        training_receiver_sha256=digest(encoded(rows)), scoring_clock_sha256=digest(encoded(clocks)),
        weight_configuration=weight.configuration, weight_training_sha256=weight.source_sha256,
        raw_hashes=hashes(dict(time=times, force=force, rate=angles)), increment_hashes=hashes(arrays),
        training_prefix_hashes=hashes({name: val[:layout['training_packets']] for name,val in arrays.items()}),
        packet_min_dt_s=float(dt.min()), packet_max_dt_s=float(dt.max()),
        angular_exposure_counts=dict(training=int(np.count_nonzero(exposure[:TRAIN])),
            scoring=int(np.count_nonzero(exposure[TRAIN:])), turn_block=int(np.count_nonzero(exposure[TRAIN+30:TRAIN+60]))))


def run(root, action):
    from . import esa_innovation_transfer as sealed
    from . import esa_native_rolling_transfer as prior
    from .airquantumgrav_inventory import IMU_NAME, METADATA, RECEIVER_PATH, validate_context
    from .airquantumgrav_packet_slice import held_measurements
    from .esa_component_preflight import RECORDS, WIDTH
    from .esa_repeat_turns import RESULT as INVENTORY
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure

    raw = {name: (root/path).read_bytes() for name,path in METADATA.items()}
    values = {name:json.loads(byte) for name,byte in raw.items()}
    context = validate_context(**values)
    selected = (root/INVENTORY).read_bytes()
    inventory = json.loads(selected)
    windows = [w for s in inventory['segments'] for w in s['disjoint_supports']]
    if (digest(selected) != INVENTORY_SHA or inventory['fit_authorized'] is not False
            or len(windows) != 4 or context['expected_receiver_epochs'] != 64080
            or values['inspection']['records'] != RECORDS):
        raise ValueError('exact opened repeat-turn inventory required')
    with closing(ClosedStudy(root, 'data/'+prior.ID)) as study:
        recipe = study.input('400-recipe', raw=True)
        if study.completion['manifest_sha256'] != sealed.SOURCE_SHA or digest(recipe) != RECIPE_SHA:
            raise ValueError('exact previously checked 400/120 recipe required')
    raw_recipe = json.loads(recipe)
    if (raw_recipe['limits']['time_offset'] != LATENCY or raw_recipe['maximum_interval_s'] != MAX_GAP
            or raw_recipe['clock'] != 'header_elapsed' or set(raw_recipe['noise_by_law']) != set(prior.LAWS)):
        raise ValueError('prepared inputs must match both original forecast descriptions')
    sources = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_esa_repeat_turn_inputs.py')
    freeze = encoded(dict(environment=runtime_environment(), inventory_sha256=INVENTORY_SHA, prior_recipe_sha256=RECIPE_SHA,
        metadata_hashes={name:digest(byte) for name,byte in raw.items()}, sources={name:digest((root/name).read_bytes())
            for name in source_closure(root,sources)}, windows=windows, pad_s=PAD, latency_s=LATENCY, maximum_gap_s=MAX_GAP,
        maximum_raw_points=4*MAX_PER_WINDOW, maximum_constructed_intervals=4*MAX_PER_WINDOW,
        receiver_weight_sets=4, source_passes_per_original=1, raw_scoring_positions=0, optimizer_starts=0, protected_reads=0))
    if action == 'freeze':
        _write_equal(root/FREEZE, freeze)
        return dict(freeze_sha256=digest(freeze))
    if (root/FREEZE).read_bytes() != freeze:
        raise ValueError('frozen repeat-turn input policy or sources changed')
    earlier, later = read_receiver(safe_path(root, RECEIVER_PATH), windows, sha=context['receiver_sha256'],
                                   named_reports=context['expected_receiver_epochs'])
    original = safe_path(root, str(Path(METADATA['inspection']).with_name(IMU_NAME)))
    results, decoded, constructed = [], 0, 0

    def reserve(*, constructed_intervals):
        nonlocal constructed
        constructed += constructed_intervals
        if constructed > 4*MAX_PER_WINDOW:
            raise ValueError('constructed interval limit exceeded')

    with original.open('rb') as stream:
        start = os.fstat(stream.fileno())
        if start.st_size != WIDTH*(RECORDS+1) or hashlib.file_digest(stream, 'sha256').hexdigest() != context['imu_source_sha256']:
            raise ValueError('opened original raw source differs')
        stream.seek(0)
        header = stream.read(WIDTH)
        for window, rows, clocks in zip(windows, earlier, later, strict=True):
            times, force, angles = held_measurements(stream, header, row_bytes=WIDTH, row_count=RECORDS,
                maximum_samples=MAX_PER_WINDOW, lower=rows[0]['time_s']-PAD, upper=clocks[-1][1]+PAD)
            decoded += len(force)
            results.append(bind_window(window, rows, clocks, times[:-1], force, angles, reserve=reserve))
        stop = os.fstat(stream.fileno())
        if (start.st_size,start.st_ctime_ns,start.st_mtime_ns) != (stop.st_size,stop.st_ctime_ns,stop.st_mtime_ns):
            raise ValueError('original raw source changed during verified reads')
    report = encoded(dict(freeze_sha256=digest(freeze), windows=results, decoded_imu_samples=decoded,
        constructed_intervals=constructed, earlier_receiver_rows=4*TRAIN, later_clock_tags=4*LATER,
        scoring_positions_decoded=0, optimizer_starts=0, protected_reads=0, fit_authorized=False))
    _write_equal(root/RESULT, report)
    return dict(sha256=digest(report), windows=len(results), decoded_imu_samples=decoded, constructed_intervals=constructed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(json.dumps(run(Path.cwd(), parser.parse_args().action), sort_keys=True))
