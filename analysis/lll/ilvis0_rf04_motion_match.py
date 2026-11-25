# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare RF04 and Group 4 on a preselected NASA stretch."""

import argparse
from contextlib import closing
from datetime import timedelta
import gzip
import json
from pathlib import Path

from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_ncar_rf04 import ATTITUDE, START, utc_string
from .ilvis0_paired_gyro_clock import CLOCKS, MAX_PACKETS, PacketRates
from .studies.artifacts import ArchiveStore, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'ilvis0-rf04-motion-match-v1'
FOLDER = 'docs/ilvis0-measurement-contribution/'
PLAN = FOLDER + 'RF04_MOTION_MATCH_PLAN.md'
RESULT = FOLDER + 'rf04-motion-match-result.json'
INTAKE = 'data/ilvis0-rf04-intake/rf04-motion-intake.json'
INTAKE_SHA = '50233f4fa317ad9b354f034bc994c8d766ef552b4a4b19e9ed7b4c8815ef1654'
SEGMENT = '2791235ca0b11b1ef4386e21'
SOURCE_SHA = '02459608f57b1b266e25daefcd9e5190515e1a046c0f633474604d1877a3ac75'
SOURCE = 'data/ilvis0-ready/12fbcbce3c7f52a3eae7/decoded/ILVIS0_applanix_55846_610_LVIS.013.gz'
SCOPE = 'Compare separate receiver tracks and whole-second attitude changes for IceBridge RF04'
TEST = 'analysis/tests/test_ilvis0_rf04_motion_match.py'
TESTS = ('test_rf04_motion_composes_whole_packets_in_physical_order',
         'test_rf04_receiver_match_keeps_missing_seconds_and_separate_height_datums')
REQUEST, XML = (f'data/{ID}-inputs/{name}' for name in ('qualification.json', 'tests.xml'))
EPOCHS = 443
WIDTHS = (1, 5, 10)
SHIFTS = (0., -.08, .08)
TASK = dict(identity='rf04', input_key='layout', payload={}, limits=dict(
    native_calls=0, packet_visits=0, bound_calls=3+len(CLOCKS)*len(SHIFTS)*len(WIDTHS),
    bound_steps=2*MAX_PACKETS+EPOCHS+len(CLOCKS)*len(SHIFTS)*sum((EPOCHS-1)//w for w in WIDTHS)))


def prefix_rotations(angles):
    import numpy as np
    from scipy.spatial.transform import Rotation

    rotations = np.empty((len(angles)+1, 4))
    current = Rotation.identity()
    rotations[0] = current.as_quat()
    for index, increment in enumerate(Rotation.from_rotvec(angles), 1):
        current = current*increment
        rotations[index] = current.as_quat()
    return Rotation.from_quat(rotations)


def packet_windows(prefix, ends, periods, starts, width):
    import numpy as np

    packets = PacketRates(ends, periods, np.zeros((len(ends), 3)))
    first, last, covered = packets.bounds(starts, width)
    return prefix[first].inv()*prefix[last], covered


def receiver_match(rows, start, times, gps):
    import math

    paired = []
    for time, (lat, lon, height) in zip(times, gps, strict=True):
        dt = time-start
        index = round(dt)
        if not 0 <= index < len(rows) or abs(dt-index) > 1e-7:
            continue
        rf = rows[index]
        ncar_lat, ncar_lon = map(math.radians, (rf['GGLAT'], rf['GGLON']))
        hav = math.sin((lat-ncar_lat)/2)**2 + math.cos(lat)*math.cos(ncar_lat)*math.sin((lon-ncar_lon)/2)**2
        distance = 2*6_371_000*math.asin(math.sqrt(min(1., hav)))
        paired.append(dict(index_s=index, horizontal_m=distance, height_offset_m=float(height-rf['GGALT'])))
    if len(paired) < 2 or len({row['index_s'] for row in paired}) != len(paired):
        raise ValueError('unique matching GPS report times are required')
    first = paired[0]['height_offset_m']
    return [dict(row, height_change_difference_m=row['height_offset_m']-first) for row in paired]


def qualification(root, *, check=False):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .ilvis0_remaining_prediction_layouts import CONTEXT, POPULATION
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the fixed RF04 comparison')
    sources = qualification(root, check=True)
    if digest((root/INTAKE).read_bytes()) != INTAKE_SHA:
        raise ValueError('the verified RF04 excerpt is required')
    with closing(ArchiveStore(root)) as store:
        pop, contexts = store.read(POPULATION), store.read(CONTEXT)
    choice, = (row for row in json.loads(gzip.decompress(pop))['selected'] if row['segment']['segment_id'] == SEGMENT)
    record, = (row for row in json.loads(contexts)['results'] if row['task_id'] == choice['task'])
    segment = choice['segment']
    source = safe_path(root, SOURCE)
    if (Path(choice['source_path']).name != source.name or segment['imu_type'] != 21
            or (segment['start_s'], segment['end_s']) != (302740., 303182.)
            or record['inspection']['source_sha256'] != SOURCE_SHA or not 0 < source.stat().st_size < 32*1024**2):
        raise ValueError('the selected original IMU21 recording is required')
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    layout = dict(segment=segment, context=record, selection_sha256=digest(pop), context_sha256=digest(contexts))
    files = dict(plan=PLAN, rf04=INTAKE, applanix=SOURCE, qualification=REQUEST, tests=XML)
    for name, raw in dict(layout=encoded(layout), recovery=recovery, recovery_tests=tests,
                          recovery_policy=encoded(RECOVERY_POLICY)).items():
        path = f'data/{ID}-inputs/{name}'
        _write_equal(root/path, raw)
        files[name] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=files,
                      sources=sources, tasks=[TASK], workers=1, threads=1, maximum_wall_s=90)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def _stats(series):
    import numpy as np

    return dict(median=float(np.median(series)), p95=float(np.quantile(series, .95)),
                rms=float(np.sqrt(np.mean(np.square(series)))), maximum=float(np.max(series)))


def evaluate(task, context):
    import numpy as np
    from scipy.spatial.transform import Rotation

    from .ilvis0_segments import extract_segment

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the fixed RF04 comparison is required')
    saved = json.loads(context.input_path('layout').read_bytes())
    region = saved['segment']
    rf04 = json.loads(context.input_path('rf04').read_bytes())
    rows = rf04['rows']
    if [row['utc'] for row in rows] != [utc_string(START+timedelta(seconds=i)) for i in range(EPOCHS)]:
        raise ValueError('complete and ordered RF04 seconds are required')
    context.charge(bound_calls=1, bound_steps=MAX_PACKETS)
    raw, times, gps, provenance = extract_segment(context.input_path('applanix'), saved['context'], region)
    if len(raw) > MAX_PACKETS or provenance['group1_observations_used'] or provenance['source_sha256'] != SOURCE_SHA:
        raise ValueError('the original bounded Group-4 stream is required')
    context.charge(bound_calls=1, bound_steps=EPOCHS)
    positions = receiver_match(rows, region['start_s'], times+provenance['first_interval_start_utc_s'], gps)
    reference = Rotation.from_euler('ZYX', [[row[key] for key in reversed(ATTITUDE)] for row in rows], degrees=True)
    context.charge(bound_calls=1, bound_steps=MAX_PACKETS)
    prefix = prefix_rotations(raw[:, 9:12])
    stamps, periods = (raw[:, 1]-region['start_s'], raw[:, 2])
    clocks = dict(header_elapsed=(stamps, periods), nominal_200Hz=(stamps[0]-periods[0]+.005*np.arange(1, len(raw)+1),
                                                                  np.full(len(raw), .005)))
    comparisons = []
    for clock in CLOCKS:
        for shift in SHIFTS:
            for width in WIDTHS:
                starts = np.arange(0, EPOCHS-width, width)
                context.charge(bound_calls=1, bound_steps=len(starts))
                actual, coverage = packet_windows(prefix, *clocks[clock], starts+shift, width)
                good = coverage >= width-.015-1e-8
                expected = reference[starts].inv()*reference[starts+width]
                comparisons.append(dict(clock=clock, shift_s=shift, window_s=width, windows=int(good.sum()),
                    omitted=int((~good).sum()), uncovered_max_s=float(np.max(width-coverage)),
                    rotation_difference_deg=_stats(np.rad2deg((expected[good].inv()*actual[good]).magnitude())),
                    rf04_rotation_deg=_stats(np.rad2deg(expected[good].magnitude())),
                    group4_rotation_deg=_stats(np.rad2deg(actual[good].magnitude()))))
    context.save('matched-receiver.json', positions)
    return dict(passed=True, scientific_decision='abstain', independent_peak_rate_upper_bound_established=False,
                new_fits=0, reserved_reads=0, source=provenance, rf04_sha256=rf04['sha256'],
                matched_receiver_seconds=len(positions),
                horizontal_separation_m=_stats([row['horizontal_m'] for row in positions]),
                relative_height_difference_m=_stats([abs(row['height_change_difference_m']) for row in positions]),
                comparisons=comparisons)


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        env = study.envelope(TASK['identity'])
        if env['charged'] != TASK['limits'] or not env['result']['passed']:
            raise ValueError('complete finite motion check required')
        value = dict(env['result'], completion=study.completion, charged=env['charged'])
    _write_equal(root/RESULT, encoded(value))
    return {k: v for k, v in value.items() if k not in ('source', 'comparisons')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = {'request': qualification, 'prepare': prepare, 'report': report}[parser.parse_args().action]
    print(json.dumps(action(Path.cwd()), sort_keys=True))
