# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stage one fresh ESA software comparison using earlier positions and future times."""

import argparse
import gzip
import hashlib
import io
import itertools
import json
import os
from pathlib import Path

from .esa_dispatch_clock import HEADER, MAX_CLOCK_ROWS, RECORDS, WIDTH, receiver_window
from .esa_dispatch_window import PREDICTION, PRIOR, RESULT, TRAINING, preflight
from .esa_repeat_turn_inputs import LATENCY, MAX_GAP
from .studies.artifacts import digest, encoded, safe_path


ID = 'esa-dispatch-inputs-v2'
SCOPE = 'ESA 187 fresh paired solver input preparation; later receiver positions withheld'
BASE = 'docs/mixed-tangent-hybrid/'
CLOCK = BASE + 'esa-dispatch-clock-result.json'
CLOCK_SHA = '618956128c0946e4dc6c476f6f1605f64ac783872e3720ce43737abaf23a32fd'
REQUEST = BASE + 'esa-dispatch-inputs-v2-qualification.json'
REPORT = BASE + 'esa-dispatch-inputs-v2-tests.xml'
PLAN = BASE + 'OBSERVED_DISPATCH_INPUT_V2.md'
TEST = 'analysis/tests/test_esa_dispatch_clock.py'
REQUIRED = (
    'test_solver_inputs_do_not_decode_later_positions',
    'test_receiver_clock_reader_ignores_position_and_velocity_fields',
    'test_inertial_clock_reader_requires_uninterrupted_bracketing',
    'test_clock_selection_matches_after_json_round_trip',
)
MAX_BYTES = 32 * 1024**2
WALL_S = 300.


def training_and_times(stream, clock, *, total):
    from .airquantumgrav_receiver import records

    window = clock['selection']['window']
    tags, earlier = receiver_window(stream, first=window['first_index'], last=window['last_index'],
        total=total, sha256=clock['receiver_sha256'], training=TRAINING, stride=window['query_stride'])
    queries = tags[1:-1:window['query_stride']]
    if (len(queries) != TRAINING+PREDICTION or digest(encoded(tags)) != clock['receiver_clock_sha256']
            or digest(encoded(queries)) != clock['receiver_query_sha256']):
        raise ValueError('receiver input differs from the verified clock')
    training = list(records(earlier))
    if [(row['sequence'], row['time_s'], row['gps_week']) for row in training] != queries[:TRAINING]:
        raise ValueError('training positions do not follow the verified clock')
    return training, [tag[1] for tag in queries]


def task():
    return dict(identity=ID, input_key='clock', payload={'recording': '187'}, native_kind='value',
                limits=dict(native_calls=0, packet_visits=0, bound_calls=0, bound_steps=0))


def selection_matches(root, frozen):
    return encoded(preflight(root)) == encoded(frozen)


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    source = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (source, TEST, PLAN, PRIOR, RESULT))
    env = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=env, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=env, required_tests=REQUIRED,
            minimum_tests=len(REQUIRED))
    return sources


def prepare(root):
    from .airquantumgrav_inventory import METADATA
    from .studies.runtime import Definition

    sources = qualification(root, verify=True)
    if digest((root / CLOCK).read_bytes()) != CLOCK_SHA:
        raise ValueError('exact verified clock record required')
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
        sources=sorted(set(sources) | {REQUEST, REPORT}), inputs={'clock': CLOCK, **METADATA},
        tasks=[task()], workers=1, threads=1, maximum_wall_s=WALL_S)
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, limits=manifest['limits'], allocation=manifest['allocation'])


def inertial_samples(stream, source, check):
    """Decode exactly the rows already bracketed by the source clock check."""
    import numpy as np
    from .airquantumgrav import records

    support = source['inertial_support']
    first, last = support['first_index'], support['last_index']
    count = support['clock_rows']
    if not 0 <= first < last < RECORDS or not 2 <= count == last-first+1 <= MAX_CLOCK_ROWS:
        raise ValueError('bounded fixed inertial support required')
    start = os.fstat(stream.fileno())
    if (start.st_size != WIDTH*(RECORDS+1)
            or hashlib.file_digest(stream, 'sha256').hexdigest() != source['imu_sha256']):
        raise ValueError('inertial source size or hash differs')
    stream.seek(0)
    header = stream.read(WIDTH)
    if len(header) != WIDTH or header.decode('ascii').split() != HEADER.split():
        raise ValueError('documented fixed-width inertial header required')
    stream.seek(WIDTH*(first+1))

    def lines():
        for index in range(count):
            if index % 4096 == 0:
                check()
            raw = stream.read(WIDTH)
            if len(raw) != WIDTH or not raw.endswith(b'\n') or b'\n' in raw[:-1]:
                raise ValueError('unexpected inertial record boundary')
            yield raw

    rows = records(itertools.chain([header], lines()))
    sampled = np.fromiter(((r['gps_time_s'], *r['acceleration_mps2'], *r['angular_rate_rads']) for r in rows),
                          dtype=np.dtype((np.float64, 7)), count=count)
    end = os.fstat(stream.fileno())
    times = sampled[:, 0]
    gaps = np.diff(times)
    if ((start.st_size, start.st_mtime_ns, start.st_ctime_ns) != (end.st_size, end.st_mtime_ns, end.st_ctime_ns)
            or times[0] != support['first_time_s'] or times[-1] != support['last_time_s']
            or np.any(gaps <= 0.) or np.max(gaps) != support['maximum_gap_s']):
        raise ValueError('prepared inertial samples differ from the verified clock')
    return dict(times=times, specific_force_mps2=sampled[:, 1:4], angular_rate_rads=sampled[:, 4:])


def evaluate(work, context):
    from .airquantumgrav_inventory import IMU_NAME, METADATA, RECEIVER_PATH, validate_context
    from .ilvis0_control_shards import _check_continue

    declared = {name: value for name, value in work.items() if name not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != task() or set(context.manifest['inputs']) != {
            'clock', *METADATA}:
        raise ValueError('exact development input preparation task required')
    raw = context.input_path('clock').read_bytes()
    if digest(raw) != CLOCK_SHA:
        raise ValueError('unchanged verified clock required')
    clock = json.loads(raw)
    metadata = {key: context.input_path(key).read_bytes() for key in METADATA}
    if {key: digest(value) for key, value in metadata.items()} != clock['metadata_sha256']:
        raise ValueError('original development metadata changed')
    source = validate_context(**{key: json.loads(value) for key, value in metadata.items()})
    root = context.root.parent.parent
    if (not context.root.parent.name == 'data' or source['group_id'] != clock['development_group']
            or source['receiver_sha256'] != clock['receiver_sha256']
            or source['imu_source_sha256'] != clock['imu_sha256']
            or not selection_matches(root, clock['selection'])):
        raise ValueError('exact frozen recording-187 source and selection required')

    import numpy as np
    from .airquantumgrav_error_policy import build, policies
    from .airquantumgrav_geographic_controls import construct

    check = lambda: _check_continue(context.root, context.manifest)
    check()
    with safe_path(root, RECEIVER_PATH).open('rb') as stream:
        training, queries = training_and_times(stream, clock, total=source['expected_receiver_epochs'])
    imu = str(Path(METADATA['inspection']).with_name(IMU_NAME))
    with safe_path(root, imu).open('rb') as stream:
        sampled = inertial_samples(stream, clock, check)
    reserved = 0

    def reserve(*, constructed_intervals):
        nonlocal reserved
        check()
        if reserved or not 0 < constructed_intervals < MAX_CLOCK_ROWS:
            raise ValueError('one bounded interval construction required')
        reserved = constructed_intervals

    material = construct(sampled, method='linear_points', rate_hz=300, reserve=reserve)
    origin = float(sampled['times'][0])
    times = np.asarray(queries)-origin
    ends = np.cumsum(material['dt'])
    if (times[0]-LATENCY < 0 or times[-1]+LATENCY > ends[-1] or len(ends) != reserved
            or np.any(material['dt'] > MAX_GAP)):
        raise ValueError('prepared intervals do not cover the complete latency allowance')
    prefix = int(np.searchsorted(ends, times[TRAINING-1]+LATENCY))+1
    if ends[prefix-1] >= times[TRAINING]:
        raise ValueError('training interval overlaps the first future query')
    archive = io.BytesIO()
    np.savez_compressed(archive, **{name: material[name] for name in ('dt', 'theta', 'dv')})
    payload = dict(interval=archive.getvalue(), training=gzip.compress(encoded(training), mtime=0),
        queries=encoded(dict(times_s=times.tolist(), time_origin_gps_sow_s=origin)),
        weights=encoded({name: build(training, policy_id=name).configuration for name in policies()}))
    check()
    if sum(map(len, payload.values())) > MAX_BYTES:
        raise ValueError('prepared inputs exceed the bounded artifact size')
    for name, data in payload.items():
        context.save_bytes(name, data)
    return dict(passed=True, development_group=source['group_id'], training_positions=len(training),
                forecast_times=PREDICTION, forecast_positions_decoded=0, protected_reads=0,
                native_packets=len(ends), training_prefix_packets=prefix, scientific_decision='abstain')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = prepare(root) if action == 'prepare' else qualification(root, verify=False)
    print(json.dumps(result, sort_keys=True))
