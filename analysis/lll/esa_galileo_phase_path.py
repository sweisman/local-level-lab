# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent-constellation carrier displacement on the sealed ESA 187 path."""

import argparse
from collections import defaultdict
from contextlib import closing
import gzip
import json
import math
from pathlib import Path
from statistics import median

from .esa_parallel_raw_receiver import (ID as MATCHED, RECEIVERS, FIRST, LAST,
    FIRST_SHARED, LAST_SHARED, INTERVALS, framed_window)
from .esa_raw_receiver_score import GEOMETRY, GEOMETRY_MANIFEST, MATCHED_MANIFEST
from .esa_rinex_window import FOLDER, WEEK, gps_seconds, read_header
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-galileo-phase-path-v1'
PLAN = FOLDER+'ESA_GALILEO_PHASE_PATH_PLAN.md'
RESULT = FOLDER+'esa-galileo-phase-path-result.json'
SCOPE = 'Galileo-only E1/E5b phase paths at the saved ESA 187 comparison times'
C, E1, E5B = 299792458., 1575420000., 1207140000.
GAMMA = (E1/E5B)**2
ORBIT_STEP = 300
PRODUCTS = {
    'orbit': ('ESA0MGNFIN_20231870000_01D_05M_ORB.SP3.gz',
              'b432894dada564aa6a677b4b488e744efb10a05a08fb182840123ca487308d30', 977601),
    'clock': ('ESA0MGNFIN_20231870000_01D_30S_CLK.CLK.gz',
              'eb736ad0c86877d0d62153034ab6b44eced10e89a7bd95ece693150ad84f66f2', 9470903),
}
TASK = dict(identity='two-galileo-519-step-paths', input_key='mosaic03', payload=dict(intervals=INTERVALS),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=INTERVALS, bound_steps=40*INTERVALS))


def _epoch(fields, step):
    week, seconds = gps_seconds(fields)
    if week != WEEK or seconds % step:
        raise ValueError('unexpected precise product time grid')
    return int(seconds)


def read_orbit(lines):
    first, second = next(lines), next(lines)
    if not first.startswith('#dP') or second.split()[1:4] != ['2269', '345600.00000000', '300.00000000']:
        raise ValueError('expected ESOC five-minute SP3-d position product')
    positions, clocks = defaultdict(dict), defaultdict(dict)
    gps_time = ended = False
    time = None
    for line in lines:
        if line.startswith('%c') and line.split()[3:4] == ['GPS']:
            gps_time = True
        if line.startswith('* '):
            time = _epoch(line.split()[1:], ORBIT_STEP)
        elif line.startswith('PE') and FIRST-1200 <= time <= LAST+1500:
            prn = int(line[2:4])
            xyz = tuple(float(line[i:i+14])*1000 for i in (4, 18, 32))
            clock = float(line[46:60])*1e-6
            if (not 1 <= prn <= 36 or time in positions[prn] or not 24e6 < math.hypot(*xyz) < 35e6
                    or not math.isfinite(clock)):
                raise ValueError('invalid Galileo SP3 satellite record')
            positions[prn][time] = xyz
            if abs(clock) < .1:
                clocks[prn][time] = clock
        elif line.strip() == 'EOF':
            ended = True
    if not gps_time or not ended or not positions:
        raise ValueError('complete GPS-time SP3-d product required')
    return positions, clocks


def read_clock(lines):
    first = next(lines)
    if first[:9].strip() != '3.02' or first[20:21] != 'C':
        raise ValueError('ESOC RINEX 3.02 clocks required')
    if not any(line[60:].strip() == 'END OF HEADER' for line in lines):
        raise ValueError('incomplete clock header')
    clocks = defaultdict(dict)
    for line in lines:
        if line.startswith('AS E'):
            fields = line.split()
            time = _epoch(fields[2:8], 30)
            if not FIRST-60 <= time <= LAST+60:
                continue
            prn, clock = int(fields[1][1:]), float(fields[9])
            if not 1 <= prn <= 36 or not abs(clock) < .1 or time in clocks[prn]:
                raise ValueError('invalid Galileo clock sample')
            clocks[prn][time] = clock
    return clocks


def check_clock_samples(clocks, reference, used):
    times = range(math.floor(FIRST/300)*300, math.floor(LAST/300)*300+1, 300)
    differences = [abs(clocks[prn][time]-reference[prn][time]) for prn in sorted(used) for time in times]
    if not differences or max(differences) > 1e-12:
        raise ValueError('clock files disagree on the common Galileo GPS-time knots')
    return dict(checked=len(differences), maximum_difference_s=max(differences))


def galileo_signals(line, codes):
    from .esa_rinex_code import _real

    def field(name):
        if name not in codes:
            return None, 0
        start = 3+16*codes.index(name)
        text, lli = line[start:start+14].strip(), line[start+14:start+15].strip()
        if lli and lli not in '01234567':
            raise ValueError('invalid Galileo loss-of-lock flag')
        return _real(text) if text else None, int(lli or 0)

    return field('C1C')[0], field('L1C'), field('L7Q'), field('D1C')[0]


def carrier_change(first, second, *, doppler):
    if any(row[0] is None or not 1e6 < row[0] < 6e7 or any(v is None or flag for v, flag in row[1:3])
           for row in (first, second)):
        return None
    l1, l5 = (second[i][0]-first[i][0] for i in (1, 2))
    if doppler and (first[3] is None or second[3] is None or abs(l1+(first[3]+second[3])/2) > .7):
        return None
    a, b = C/E1*l1, C/E5B*l5
    return (GAMMA*a-b)/(GAMMA-1) if abs(a-b) <= .075 else None


def receiver_epoch_tables(context):
    output = {}
    for name, spec in RECEIVERS.items():
        raw = gzip.decompress(context.input_path(name).read_bytes())
        header, metadata = read_header(raw, expected_interval=spec['interval'], expected_systems=spec['systems'])
        _, _, output[name] = framed_window(raw[len(header):], 0, FIRST, LAST, spec['interval'],
            metadata['observation_types'], require_tail=False, selected_system='E',
            decode=galileo_signals, maximum_satellite=36)
    return output


def transmitter(orbit, clocks, receive, code):
    from .esa_final_orbit_replay import interpolate_orbit
    from .esa_relative_clock_replay import interpolate_clock

    raw = receive-code/C
    time = raw-interpolate_clock(clocks, raw)
    xyz = interpolate_orbit(orbit, time, step_s=ORBIT_STEP)
    before = interpolate_orbit(orbit, time-.5, step_s=ORBIT_STEP)
    after = interpolate_orbit(orbit, time+.5, step_s=ORBIT_STEP)
    relativistic = -2*math.fsum(p*(b-a) for p,a,b in zip(xyz, before, after, strict=True))/C**2
    return xyz, interpolate_clock(clocks, time)+relativistic


def atmosphere(anchor, positions):
    import numpy as np

    from . import gnss_position as gps

    latitude, longitude, height = gps.geodetic(anchor)
    delta = positions-anchor
    up = delta @ gps.local_rotation(latitude, longitude)[2]
    elevations = np.arcsin(np.clip(up/np.linalg.norm(delta, axis=1), -1., 1.))
    return [gps.troposphere(latitude, height, angle) if angle >= math.radians(5) else None
            for angle in elevations]


def step_inputs(tables, start, orbit, clocks, reference):
    import numpy as np

    signals = {name: (epochs[start], epochs[start+1]) for name, epochs in tables.items()}
    common = sorted(set.intersection(*(set(epoch) for pair in signals.values() for epoch in pair)))
    paired, exclusions = {}, {}
    for prn in common:
        phases = [carrier_change(a[prn], b[prn], doppler=name == 'pwrpak7')
                  for name, (a,b) in signals.items()]
        if None in phases:
            exclusions[prn] = 'phase continuity or Doppler support'
            continue
        try:
            positions = [tuple(transmitter(orbit[prn], clocks[prn], start+side, epoch[prn][0])
                         for side, epoch in enumerate(pair)) for pair in signals.values()]
        except (KeyError, ValueError):
            exclusions[prn] = 'precise orbit or clock support'
            continue
        if any(atmosphere(anchor, np.asarray([record[0]]))[0] is None
               for pair in positions for anchor, record in zip(reference, pair, strict=True)):
            exclusions[prn] = 'common elevation mask'
            continue
        paired[prn] = (phases, positions)
    if len(paired) >= 5:
        common_clock = median(phases[0]-phases[1] for phases, _ in paired.values())
        for prn, (phases, _) in list(paired.items()):
            if abs(phases[0]-phases[1]-common_clock) > .075:
                del paired[prn]
                exclusions[prn] = 'between-receiver phase continuity'
    return paired, dict(initial_common=common, accepted=list(paired), excluded=exclusions)


def displacement(center, step):
    import numpy as np

    from .esa_carrier_phase_later import recover_metre_change

    data, measured = zip(*step, strict=True)
    a, b = zip(*data, strict=True)
    first, clock_a = map(np.asarray, zip(*a, strict=True))
    last, clock_b = map(np.asarray, zip(*b, strict=True))
    trop_a = atmosphere(center, first)

    def solve(trop_b):
        if None in trop_a or None in trop_b:
            raise ValueError('path leaves the common elevation mask')
        result = recover_metre_change(center, first, last, clock_a, clock_b,
                                      np.asarray(trop_a), np.asarray(trop_b), np.asarray(measured))
        if result['status'] != 'converged':
            raise ValueError(result['reason'])
        return result

    preliminary = solve(atmosphere(center, last))
    return solve(atmosphere(center+preliminary['displacement_ecef_m'], last))


def prepare(root, source):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing Galileo study must be preserved')
    staged = {}
    for role, (_, sha, size) in PRODUCTS.items():
        payload = (source/f'lll-esa187-galileo-{role}.gz').read_bytes()
        if len(payload) != size or digest(payload) != sha:
            raise ValueError('exact public ESOC product required')
        staged[role] = payload
    with closing(ClosedStudy(root, 'data/'+MATCHED)) as matched, closing(
            ClosedStudy(root, 'data/'+GEOMETRY, store=matched.store)) as geometry:
        if (matched.completion['manifest_sha256'] != MATCHED_MANIFEST
                or geometry.completion['manifest_sha256'] != GEOMETRY_MANIFEST
                or not matched.summary['passed'] or not geometry.summary['passed']):
            raise ValueError('exact archived receiver excerpts and GPS shape score required')
        for name in RECEIVERS:
            staged[name] = matched.input(name, raw=True)
        for name in ('track', 'shape', 'operator', 'baseline'):
            staged[name] = geometry.input(name, raw=True)
    inputs = dict(plan=PLAN)
    for name, raw in staged.items():
        path = 'data/'+ID+'-inputs/'+name
        atomic(root/path, raw)
        inputs[name] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=adapter, tasks=[TASK],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_galileo_phase_path.py']),
        workers=1, threads=1, maximum_wall_s=120.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    import numpy as np

    from . import gnss_position as gps
    from .esa_carrier_satellite_influence import ecef_track

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the frozen two-receiver Galileo task is required')
    with gzip.open(context.input_path('orbit'), 'rt', encoding='ascii') as stream:
        orbit, sp3_clocks = read_orbit(iter(stream))
    with gzip.open(context.input_path('clock'), 'rt', encoding='ascii') as stream:
        clocks = read_clock(iter(stream))
    tables = receiver_epoch_tables(context)
    track = json.loads(context.input_path('track').read_bytes())['positions']
    original = ecef_track(track)[::2]
    if [row['seconds'] for row in track[::2]] != list(range(FIRST_SHARED, LAST_SHARED+1)):
        raise ValueError('the original GPS support and one earlier anchor are required')
    names = tuple(tables)
    centers = {name: original[0].copy() for name in names}
    positions = {name: [track[0]['position']] for name in names}
    records, used = [], set()
    failure = None
    for index, second in enumerate(range(FIRST_SHARED, LAST_SHARED)):
        context.charge(bound_calls=1, bound_steps=40)
        paired, support = step_inputs(tables, second, orbit, clocks, original[index:index+2])
        records.append(dict(seconds=second, **support))
        if len(paired) < 5:
            failure = dict(seconds=second, reason='fewer than five supported Galileo satellites')
            break
        try:
            checks = check_clock_samples(clocks, sp3_clocks, set(paired)) if set(paired)-used else None
            steps = {name: displacement(centers[name], [(state[side], phase[side])
                     for phase, state in paired.values()]) for side, name in enumerate(names)}
        except (ValueError, KeyError) as error:
            failure = dict(seconds=second, reason=str(error))
            break
        used.update(paired)
        records[-1].update(solutions=steps, clock_check=checks)
        for name in names:
            centers[name] += np.asarray(steps[name]['displacement_ecef_m'])
            positions[name].append(list(gps.geodetic(centers[name])))
    context.save_bytes('galileo-paths.json', encoded(dict(paths=positions, records=records, failure=failure,
        clocks=check_clock_samples(clocks, sp3_clocks, used) if used else None)))
    return dict(passed=failure is None, failure=failure, completed_intervals=min(map(len, positions.values()))-1,
                scientific_decision='abstain')


def report(root):
    import numpy as np

    from .airquantumgrav_geographic_report import error_metrics
    from .esa_changing_drift_transfer import _chart
    from .esa_fit_adjusted_forecast_report import position_errors_neu
    from .innovations_snapshot import restore
    from .esa_carrier_phase_later import CUT

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.summary['charged']['bound_calls'] != INTERVALS:
            raise ValueError('both complete continuous Galileo paths are required')
        saved = study.artifact(TASK['identity'], 'galileo-paths.json')
        shape, snapshot, baseline = study.input('shape'), study.input('operator', raw=True), study.input('baseline')
        reference = [row['position'] for row in study.input('track')['positions'][::2]]
        manifest = study.completion['manifest_sha256']
    origin = np.asarray(reference[0])
    base = _chart(reference, origin)
    operator = restore(snapshot, expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)
    direction = np.r_[np.zeros(3*CUT), shape['direction']]
    reference_score = baseline['carrier_signed_midpoint']
    results = {}
    for name, path in saved['paths'].items():
        error = position_errors_neu(path, reference)
        change = float(direction @ operator.whiten((_chart(path, origin)-base).ravel()))
        results[name] = dict(earlier=error_metrics(error[:CUT].tolist()), later=error_metrics(error[CUT:].tolist()),
                             score=reference_score+change, score_change_from_gps=change)
    a, b = (saved['paths'][name] for name in RECEIVERS)
    relative = position_errors_neu(a, b)
    output = dict(manifest_sha256=manifest, gps_reference_score=reference_score, receivers=results,
        relative_earlier=error_metrics(relative[:CUT].tolist()), relative_later=error_metrics(relative[CUT:].tolist()),
        intervals=INTERVALS, minimum_satellites=min(len(row['accepted']) for row in saved['records']),
        maximum_condition=max(r['condition'] for row in saved['records'] for r in row['solutions'].values()),
        clock_samples=saved['clocks'], scientific_decision='abstain')
    destination = root/RESULT
    raw = encoded(output)
    if not destination.exists():
        atomic(destination, raw)
    if destination.read_bytes() != raw:
        raise ValueError('existing Galileo report differs')
    print(raw.decode(), end='')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    parser.add_argument('--download-directory', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        if args.download_directory is None:
            parser.error('prepare requires --download-directory')
        prepare(Path.cwd(), args.download_directory)
    else:
        report(Path.cwd())
