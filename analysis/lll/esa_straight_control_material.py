# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare the four straight controls in the existing repeat-turn input format."""

import argparse
import hashlib
import json
import os
from pathlib import Path

from .airquantumgrav_inventory import METADATA
from .esa_repeat_turn_execution_v2 import CONTINUATION_INPUTS
from .esa_straight_control_windows import CLOCK_RESULT, query_clock
from .studies.artifacts import digest, encoded, safe_path


ID = 'esa-straight-control-material-v1'
SCOPE = 'ESA 187 four steady-course controls; training positions and later clock only'
BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_STRAIGHT_CONTROL_MATERIAL_PLAN.md'
REQUEST = BASE+'esa-straight-control-material-qualification.json'
REPORT = BASE+'esa-straight-control-material-tests.xml'
CLOCK_SHA = '78271d62699d9e58904f4726bd772e9661f1429ca9c777e174f88312d91a9c30'
WALL_S = 600.
REQUIRED = ('test_straight_material_scope_rejects_a_later_position_input_before_access',
            'test_straight_material_requires_exact_saved_clock_bytes',
            'test_control_query_clock_rejects_discontinuity_at_training_boundary')


def input_keys():
    return frozenset({'clock', *METADATA})


def task():
    return dict(identity=ID, payload={'recording': '187', 'windows': 4}, input_key='clock', native_kind='value',
                limits=dict(native_calls=0, packet_visits=0, bound_calls=0, bound_steps=0))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
        'analysis/tests/test_esa_straight_control_material.py', 'analysis/tests/test_esa_straight_control_windows.py'))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=REQUIRED,
            minimum_tests=len(REQUIRED))
    return sources


def prepare(root):
    from .studies.runtime import Definition

    sources = qualification(root, verify=True)
    if digest(safe_path(root, CLOCK_RESULT).read_bytes()) != CLOCK_SHA:
        raise ValueError('verified straight-control clock record required')
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
        sources=sorted(set(sources) | {REQUEST, REPORT}), inputs={'clock': CLOCK_RESULT, **METADATA},
        tasks=[task()], workers=1, threads=1, maximum_wall_s=WALL_S)
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=len(manifest['tasks']),
                manifest_sha256=digest((root/'data'/ID/'manifest.json').read_bytes()), launched=False)


def package_window(bound, earlier, later, edges, force, angles, *, reserve):
    import numpy as np
    from .airquantumgrav_geographic_controls import construct
    from .esa_motion_error_transfer import THRESHOLD_DEG_S
    from .esa_repeat_turn_inputs import TRAIN, packet_layout, query_indices
    from .esa_repeat_turn_material import array_hashes, package
    from .maneuver_error_roots import turn_exposure

    tags = query_clock(earlier, later)
    query = np.asarray([tag[1] for tag in tags])
    support = bound['inertial_support']
    if (query.tolist() != bound['query_times_s']
            or digest(encoded(earlier)) != bound['training_sha256']
            or digest(encoded(later)) != bound['scoring_clock_sha256']
            or len(edges) != support['clock_rows'] or edges[0] != support['first_time_s']
            or edges[-1] != support['last_time_s'] or np.max(np.diff(edges)) != support['maximum_gap_s']):
        raise ValueError('measurements or timing differ from the verified control clock')
    sample_times = edges[:-1]
    layout = packet_layout(sample_times, query, cut=TRAIN)
    converted = construct(dict(times=sample_times, specific_force_mps2=force, angular_rate_rads=angles),
                          method='linear_points', rate_hz=300, reserve=reserve)
    arrays = {key: converted[key] for key in ('dt', 'theta', 'dv')}
    times = query-sample_times[0]
    angular = turn_exposure(arrays['dt'], arrays['theta'], times, previous_time=0.,
                            threshold_deg_s=THRESHOLD_DEG_S)
    prefix = layout['training_packets']
    receipt = dict(window=bound['window'], **layout,
        training_receiver_sha256=bound['training_sha256'], scoring_clock_sha256=bound['scoring_clock_sha256'],
        query_source_indices=query_indices(bound['window']), query_times_s=times.tolist(),
        increment_hashes=array_hashes(arrays),
        training_prefix_hashes=array_hashes({key: value[:prefix] for key, value in arrays.items()}),
        angular_exposure_counts=dict(training=int(np.count_nonzero(angular[:TRAIN])),
                                     scoring=int(np.count_nonzero(angular[TRAIN:]))))
    return receipt, package(earlier, times, arrays, receipt)


def evaluate(work, context):
    from .airquantumgrav_inventory import IMU_NAME, RECEIVER_PATH, validate_context
    from .airquantumgrav_packet_slice import held_measurements
    from .esa_component_preflight import RECORDS, WIDTH
    from .esa_repeat_turn_inputs import MAX_PER_WINDOW, PAD, read_receiver
    from .esa_repeat_turn_material import MAX_BYTES
    from .ilvis0_control_shards import _check_continue

    inputs = set(context.manifest['inputs'])
    declared = {name: value for name, value in work.items() if name not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or declared != task()
            or inputs not in (input_keys(), input_keys() | CONTINUATION_INPUTS)):
        raise ValueError('only the exact training and clock task is allowed')
    clock_raw = context.input_path('clock').read_bytes()
    if digest(clock_raw) != CLOCK_SHA:
        raise ValueError('unchanged verified straight-control clock required')
    clock = json.loads(clock_raw)
    raw = {key: context.input_path(key).read_bytes() for key in METADATA}
    if {key: digest(value) for key, value in raw.items()} != clock['metadata_sha256']:
        raise ValueError('frozen recording-187 source metadata changed')
    source = validate_context(**{key: json.loads(value) for key, value in raw.items()})
    if source != clock['source']:
        raise ValueError('unchanged opened development source required')
    directory = context.root.parent
    if directory.name == ID+'-recovery':
        directory = directory.parent
    if directory.name != 'data':
        raise ValueError('standard study directory required')
    root = directory.parent
    check = lambda: _check_continue(context.root, context.manifest)
    check()
    windows = [bound['window'] for bound in clock['windows']]
    earlier, later = read_receiver(safe_path(root, RECEIVER_PATH), windows,
        sha=source['receiver_sha256'], named_reports=source['expected_receiver_epochs'])
    imu_path = str(Path(METADATA['inspection']).with_name(IMU_NAME))
    receipts, bytes_written, constructed = [], 0, 0

    def reserve(*, constructed_intervals):
        nonlocal constructed
        check()
        constructed += constructed_intervals
        if not 0 < constructed_intervals < MAX_PER_WINDOW or constructed > 4*MAX_PER_WINDOW:
            raise ValueError('bounded control increment construction required')

    with safe_path(root, imu_path).open('rb') as stream:
        start = os.fstat(stream.fileno())
        if (start.st_size != WIDTH*(RECORDS+1)
                or hashlib.file_digest(stream, 'sha256').hexdigest() != source['imu_source_sha256']):
            raise ValueError('verified original control recording required')
        stream.seek(0)
        header = stream.read(WIDTH)
        for bound, rows, tags in zip(clock['windows'], earlier, later, strict=True):
            check()
            times = bound['query_times_s']
            edges, force, angles = held_measurements(stream, header, row_bytes=WIDTH, row_count=RECORDS,
                maximum_samples=MAX_PER_WINDOW, lower=times[0]-PAD, upper=times[-1]+PAD)
            binding, files = package_window(bound, rows, tags, edges, force, angles, reserve=reserve)
            bytes_written += sum(len(raw) for raw in files.values())
            if bytes_written > MAX_BYTES:
                raise ValueError('control package exceeds the original material size limit')
            index = bound['window']['first_index']
            for name, raw in files.items():
                context.save_bytes(f'{index}/{name}', raw)
            receipts.append(dict(binding, files={name: digest(raw) for name, raw in files.items()}))
        end = os.fstat(stream.fileno())
        if (start.st_size, start.st_mtime_ns, start.st_ctime_ns) != (end.st_size, end.st_mtime_ns, end.st_ctime_ns):
            raise ValueError('recording changed during control preparation')
    if len(receipts) != 4 or constructed != sum(row['forecast_packets'] for row in receipts):
        raise ValueError('complete input bundle and construction accounting required')
    context.save('bundle.json', dict(clock_sha256=CLOCK_SHA, windows=receipts, bytes_written=bytes_written))
    check()
    return dict(passed=True, windows=4, material_files=12, constructed_intervals=constructed,
                later_receiver_positions_decoded=0, protected_reads=0, scientific_decision='abstain')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = prepare(root) if action == 'prepare' else qualification(root, verify=False)
    print(json.dumps(result, sort_keys=True))
