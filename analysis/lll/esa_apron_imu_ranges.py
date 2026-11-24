# SPDX-License-Identifier: AGPL-3.0-or-later
"""Match backed aircraft and museum carrier ranges during the iMAR overlap."""

import argparse
from contextlib import closing
import gzip
from itertools import islice, takewhile
import json
import math
from pathlib import Path

from . import esa_apron_carrier as apron
from . import esa_apron_imu_overlap as overlap
from . import esa_apron_nkar as comparison
from .studies.artifacts import digest, encoded


ID = 'esa-apron-imu-ranges-v2'
PREVIOUS_ID = 'esa-apron-imu-ranges-v1'
SCOPE = 'ESA 187 two-minute Nuuk apron common carrier range and inertial motion check'
PLAN = apron.FOLDER+'ESA_APRON_IMU_OVERLAP_PLAN.md'
CORRECTION = apron.FOLDER+'ESA_APRON_IMU_OVERLAP_ACCOUNTING_PLAN.md'
STOPPED = apron.FOLDER+'esa-apron-imu-ranges-v1-terminal.json'
RESULT = apron.FOLDER+'esa-apron-imu-ranges-result.json'
ACQUISITION_SHA = '6c2aa57cbf73b31b9dd0d7b5b76e6a5aa596d1b4bdc127411c3c2e52b4396ea3'
IMU = apron.source.LOCAL+'/187_rqh01.txt'
IMU_SHA = '7415a1ab77fe787bdd3c86e067ae0626adb181540eaeb69629f8a205c0d24ee6'
SECONDS = tuple(range(int(overlap.FIRST), int(overlap.LAST)+1))
INTERVALS = len(SECONDS)-1
AIR_PAIRS = INTERVALS * 2
MAX_IMU_ROWS = 75_000
TASK = dict(identity='apron-overlap', input_key='air', payload={}, limits=dict(
    native_calls=0, packet_visits=0, bound_calls=1+AIR_PAIRS+INTERVALS,
    bound_steps=1+MAX_IMU_ROWS+66*AIR_PAIRS+64*INTERVALS))


def reserve_setup(context):
    context.charge(bound_calls=1, bound_steps=1+MAX_IMU_ROWS)


def clock_offsets(body):
    fields = [line.split() for line in body.splitlines() if line.startswith(b'> ')]
    if not fields or any(len(row) != 10 for row in fields):
        raise ValueError('every epoch needs a recorded receiver clock offset')
    offsets = [float(row[9]) for row in fields]
    if (any(not math.isfinite(value) or abs(value) > .001 for value in offsets)
            or any(abs(right-left) > 2e-6 for left, right in zip(offsets, offsets[1:]))):
        raise ValueError('receiver clock offset or step exceeds the qualified limits')
    return offsets


def motion_summary(rows, *, start, end, rate_hz):
    from .esa_ground_rate_scale import summarize_scales

    selected = takewhile(lambda row: row['gps_time_s'] < end, rows)
    summary = summarize_scales(selected, windows={'overlap': (start, end)}, widths=(1,),
                               rate_hz=rate_hz)['overlap']['1']
    bins = summary['complete_bin_means']
    if ([row['index'] for row in bins] != list(range(end-start))
            or any(row['count'] > math.floor(1.05*rate_hz) for row in bins)
            or summary['omitted_partial_bins']):
        raise ValueError('complete one-second inertial bins are required')
    return summary


def _station_input(original, converter, prior):
    from .esa_nkar_score import station_geometry
    from .fixed_reference_rinex2 import observation_epochs, read_header
    from .rinex_archive_decode import decode_archive

    expected = prior['ground_provenance']
    if (original.name != 'nkar1870.23d.Z' or original.stat().st_size != expected['original']['bytes']
            or digest(original.read_bytes()) != expected['original']['sha256']
            or digest(converter.read_bytes()) != comparison.CONVERTER_SHA):
        raise ValueError('the verified station day and GSI decoder are required')
    with decode_archive(original, converter) as (stream, provenance):
        if any(provenance[key] != expected[key] for key in ('original', 'compact', 'expanded')):
            raise ValueError('the same expanded station day must reproduce')
        layout = read_header(stream)
        if encoded(layout) != encoded(prior['station_layout']):
            raise ValueError('the earlier qualified station layout must reproduce')
        epochs = []
        for index, row in enumerate(observation_epochs(stream, layout, retain_measurements=True), 1):
            if index > 40_000 or row['week'] != apron.source.WEEK:
                raise ValueError('station intake outside the fixed epoch and week allowance')
            if row['seconds'] > SECONDS[-1]:
                break
            if row['seconds'] >= SECONDS[0]:
                epochs.append(row)
    if [row['seconds'] for row in epochs] != list(SECONDS):
        raise ValueError('exact one-second museum observations required')
    if not layout.get('receiver_clock_applied') and any(row['receiver_offset_s'] for row in epochs):
        raise ValueError('museum clock offset correction would require separate qualification')
    antenna = station_geometry(layout).tolist()
    if antenna != prior['antenna_ecef_m']:
        raise ValueError('the surveyed station antenna position must reproduce')
    return dict(epochs=epochs, antenna_ecef_m=antenna, decoding=provenance)


def prepare(root, original, converter):
    from .esa_ground_rate_scale import _sha
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the existing finite study')
    receipt = (root/overlap.REPORT).read_bytes()
    station = (root/comparison.STATION).read_bytes()
    if digest(receipt) != ACQUISITION_SHA or digest(station) != comparison.STATION_SHA:
        raise ValueError('the sealed aircraft acquisition and earlier station result are required')
    receipt_data = json.loads(receipt)
    air = receipt_data['retained_source']
    if digest(gzip.decompress((root/air).read_bytes())) != receipt_data['retained_sha256']:
        raise ValueError('decoded aircraft observation hash changed')
    if _sha(root/IMU) != IMU_SHA:
        raise ValueError('expected original iMAR file required')
    inputs = dict(plan=PLAN, aircraft_receipt=overlap.REPORT, station_receipt=comparison.STATION,
                  air=air, imu=IMU)
    station_input = f'data/{ID}-inputs/station.json'
    _write_equal(root/station_input, encoded(_station_input(original, converter, json.loads(station))))
    inputs['station'] = station_input
    with closing(ClosedStudy(root, 'data/'+apron.ID)) as study:
        saved = json.loads((root/apron.RESULT).read_bytes())
        if (digest((root/apron.RESULT).read_bytes()) != comparison.APRON_SHA
                or study.completion != saved['completion']
                or study.envelope(apron.TASK['identity'])['charged'] != apron.TASK['limits']):
            raise ValueError('the original completed apron study is required')
        for key in ('tie', 'navigation', 'orbit', 'clock'):
            path = f'data/{ID}-inputs/{key}'
            _write_equal(root/path, study.input(key, raw=True))
            inputs[key] = path
    return _freeze(root, inputs)


def _freeze(root, inputs):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, CORRECTION, 'analysis/tests/test_esa_apron_imu_ranges.py'))
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=60)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def prepare_corrected(root):
    from .esa_ground_rate_scale import _sha
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy

    prefix = 'data/'+PREVIOUS_ID
    with closing(ClosedStudy(root, prefix)) as previous:
        envelope = previous.envelope(TASK['identity'])
        if (previous.completion['state'] != 'terminal' or len(previous.rows) != 1
                or any(envelope['charged'].values()) or any(previous.summary['charged'].values())
                or envelope['result']['reason'] != 'one complete finite operation reservation required'):
            raise ValueError('the original zero-work accounting stop is required')
        inputs = {name: prefix+'/'+data['path'] for name, data in previous.manifest['inputs'].items()}
        if (previous.manifest['inputs']['imu']['sha256'] != IMU_SHA
                or any(_sha(root/inputs[key]) != expected['sha256']
                       for key, expected in previous.manifest['inputs'].items())):
            raise ValueError('all original sealed inputs must match')
        _write_equal(root/STOPPED, encoded(dict(completion=previous.completion, terminal_result=envelope)))
    imu_prefix = f'data/{ID}-inputs/imu-prefix.txt'
    with (root/inputs['imu']).open('rb') as stream:
        lines = list(islice(stream, MAX_IMU_ROWS+1))
    if len(lines) != MAX_IMU_ROWS+1 or not lines[-1].endswith(b'\n'):
        raise ValueError('the full charged prefix including its header is required')
    _write_equal(root/imu_prefix, b''.join(lines))
    inputs.update(imu=imu_prefix, correction=CORRECTION, stopped=STOPPED)
    return _freeze(root, inputs)


def _air_input(raw):
    import numpy as np

    from .esa_carrier_phase_support import phase_epochs
    from .esa_precise_gps_support import read_orbit_positions
    from .esa_relative_clock_replay import _clock_records
    from .esa_rinex_code import read_navigation
    from .gnss_position import ecef, local_rotation

    source = gzip.decompress(raw('air'))
    header, _ = apron.source.read_header(source)
    declared = [line[:6].strip() for line in header.splitlines()
                if line[60:].strip() == b'RCV CLOCK OFFS APPL']
    if declared not in ([], [b'0']):
        raise ValueError('only the unapplied receiver clock convention is qualified')
    offsets = clock_offsets(source[len(header):])
    epochs = list(phase_epochs(source, first=overlap.FIRST, last=overlap.LAST))
    if len(offsets) != len(epochs):
        raise ValueError('one clock offset per aircraft epoch required')
    stop = json.loads(raw('tie'))['ground_stops'][0]
    ref = stop['airport_reference']
    lat, lon = map(math.radians, (ref['latitude_deg'], ref['longitude_deg']))
    rotation = local_rotation(lat, lon)
    nominal = ecef(lat, lon, ref['height_m'])+rotation.T@np.asarray(stop['antenna_neu_from_reference_m'])

    def product(name):
        return gzip.decompress(raw(name)).decode('ascii')

    nav, atmosphere = read_navigation(product('navigation'))
    return epochs, offsets, nominal, (nav, atmosphere, read_orbit_positions(product('orbit')),
                                      _clock_records(product('clock')))


def evaluate(task, context):
    import numpy as np

    from .airquantumgrav import records
    from .esa_nkar_score import final_range_model, reference_pair

    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('the frozen overlap comparison is required')
    reserve_setup(context)

    def raw(key):
        return context.input_path(key).read_bytes()

    with context.input_path('imu').open('rb') as stream:
        motion = motion_summary(islice(records(stream), MAX_IMU_ROWS), start=SECONDS[0],
                                end=SECONDS[-1], rate_hz=300)
    context.save('ground-motion.json', motion)
    epochs, offsets, nominal, products = _air_input(raw)
    pairs, unmodeled = apron.calculate_residuals(epochs, offsets, final_range_model(*products, nominal),
                                                lambda: context.charge(bound_calls=1, bound_steps=66))
    station = json.loads(raw('station'))
    ground_rows = station['epochs']
    model = final_range_model(*products, np.asarray(station['antenna_ecef_m']))
    matched, unmatched = [], []
    for air, first, last in zip(apron.one_second_ranges(pairs), ground_rows[:-1], ground_rows[1:], strict=True):
        context.charge(bound_calls=1, bound_steps=64)
        pair = comparison.matched_residuals(air, reference_pair(first, last, sorted(air), model))
        if pair is None:
            unmatched.append(first['seconds'])
        else:
            matched.append(dict(gps_s=first['seconds'], **pair))
    context.save('matched-ranges.json', matched)
    minute_statistics = []
    for start in (SECONDS[0], SECONDS[0]+60):
        rows = [row for row in matched if start <= row['gps_s'] < start+60]
        minute_statistics.append(comparison.pooled_statistics(rows) if rows else None)
    return dict(passed=True, aircraft_error_cap_established=False, scientific_decision='abstain',
                first_gps_s=SECONDS[0], last_gps_s=SECONDS[-1], unmatched_starts_gps_s=unmatched,
                unmodeled_prns=sorted(unmodeled), minutes=minute_statistics,
                receiver_clock_offset_s=[min(offsets), max(offsets)],
                aircraft_ranges=apron.rms_steps(pairs), matched=comparison.pooled_statistics(matched),
                imu_samples=motion['selected_samples'], imu_rate_spread_deg_per_hour=motion['spread_xyz_deg_per_hour'],
                original_downloads=0, new_fits=0, protected_reads=0)


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('the verified complete overlap check is required')
        summary = dict(envelope['result'], completion=study.completion,
                       inputs=study.manifest['inputs'], charged=envelope['charged'])
        result = dict(summary, motion=study.artifact(TASK['identity'], 'ground-motion.json'),
                      ranges=study.artifact(TASK['identity'], 'matched-ranges.json'))
    _write_equal(root/RESULT, encoded(result))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'prepare-corrected', 'report'))
    parser.add_argument('--original', type=Path)
    parser.add_argument('--converter', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare' and (args.original is None or args.converter is None):
        parser.error('prepare requires --original and --converter')
    if args.action == 'prepare':
        result = prepare(Path.cwd(), args.original, args.converter)
    else:
        result = {'prepare-corrected': prepare_corrected, 'report': report}[args.action](Path.cwd())
    print(json.dumps(result, sort_keys=True))
