# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare carrier observations from the three receivers on ESA flight 187."""

import argparse
from contextlib import closing
import gzip
from itertools import combinations
import json
import math
from pathlib import Path
from statistics import median

from .esa_carrier_phase_support import GAMMA, L1_WAVELENGTH, L2_WAVELENGTH, _fields, phase_epochs
from .esa_rinex_window import WEEK, epoch_offsets, read_header
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-parallel-raw-receiver-v1'
FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER + 'ESA_PARALLEL_RAW_RECEIVER_WINDOW_PLAN.md'
RESULT = FOLDER + 'esa-parallel-raw-receiver-result.json'
SCOPE = 'ESA 187 matched raw GPS dual-band carrier receiver differences'
PARENT = 'esa-carrier-phase-continuous-v1'
PARENT_SHA = '93fcfc884ffe80067ae434f2d6a9abdb272337c732847a2541d620b768781d43'
FIRST, LAST, FIRST_LATER = 388214, 388735, 388615
FIRST_SHARED, LAST_SHARED = FIRST+1, LAST-1
INTERVALS = LAST_SHARED - FIRST_SHARED
TASK = dict(identity='519-common-carrier-intervals', input_key='air1', payload=dict(intervals=INTERVALS),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=INTERVALS, bound_steps=3*INTERVALS))
RECEIVERS = {
    'mosaic03': dict(file='SEPT1870.23O', size=684_326_587, interval=.2, systems='GESRCJ',
                    prefix_hash='492bc79b7ac3dde9a03a1901092af72495d61563e77e3a2e4fc842d3de366814',
                    probe_offset=81_350_000, cover_offset=81_500_000, cover_count=12*2**20),
    'pwrpak7': dict(file='NMPL20210019C_2023-07-06_19-23-46.23O', size=178_964_794, interval=1., systems='GREJC',
                    prefix_hash='486550a522e66fca94fd0233aa8236cfabd2674fd45847c1ff227d776bd473d2',
                    probe_offset=23_250_000, cover_offset=23_300_000, cover_count=7*2**19),
}
PAIRS = tuple(combinations(('air1', *RECEIVERS), 2))


def framed_window(raw, offset, first, last, interval, definitions, *, require_tail=True,
                  selected_system='G', decode=_fields, maximum_satellite=32):
    markers = epoch_offsets(raw, offset=offset)
    matches = [(row, following[0]) for row, following in zip(markers, markers[1:])
               if first <= row[2] <= last]
    if not require_tail and markers[-1][2] == last and raw.endswith(b'\n'):
        matches.append((markers[-1], offset+len(raw)))
    expected = [first+i*interval for i in range(round((last-first)/interval)+1)]
    if len(matches) != len(expected) or any(abs(row[2]-time) > 1e-8
                                            for (row, _), time in zip(matches, expected, strict=True)):
        raise ValueError('every expected epoch and its complete framing are required')
    integer_epochs, observed_systems = {}, set()
    for (begin, week, seconds, flag, count), end in matches:
        satellites = raw[begin-offset:end-offset].splitlines()[1:]
        if (week != WEEK or flag != 0 or count < 1 or len(satellites) != count
                or len({line[:3] for line in satellites}) != count):
            raise ValueError('complete normal epoch and unique satellite count required')
        observations = {}
        for line in satellites:
            system = line[:1].decode('ascii')
            if (system not in definitions or len(line) < 3 or not line[1:3].isdigit()
                    or len(line.rstrip()) > 3+16*len(definitions[system])):
                raise ValueError('unexpected satellite record in complete receiver epoch')
            observed_systems.add(system)
            if system == selected_system and seconds.is_integer():
                prn = int(line[1:3])
                if not 1 <= prn <= maximum_satellite:
                    raise ValueError('invalid recorded satellite')
                observations[prn] = decode(line.decode('ascii'), definitions[selected_system])
        if seconds.is_integer():
            integer_epochs[int(seconds)] = observations
    begin, end = matches[0][0][0], matches[-1][1]
    if set(integer_epochs) != set(range(first, last+1)):
        raise ValueError('every integer GPS epoch must be present exactly')
    return raw[begin-offset:end-offset], dict(epochs=len(matches), byte_start=begin,
        byte_end_exclusive=end, systems=sorted(observed_systems)), integer_epochs


def phase_changes(first, second, allowed=None):
    prns = first.keys() & second.keys()
    result = {}
    for prn in sorted(prns if allowed is None else prns & allowed):
        a, b = first[prn], second[prn]
        signals = [a['l1'], b['l1'], a['l2'].get('2W'), b['l2'].get('2W')]
        if any(value is None or value[1] for value in signals):
            continue
        l1 = L1_WAVELENGTH * (signals[1][0]-signals[0][0])
        l2 = L2_WAVELENGTH * (signals[3][0]-signals[2][0])
        result[prn] = (GAMMA*l1-l2)/(GAMMA-1)
    return result


def pair_difference(first, second, common=None):
    names = sorted(first.keys() & second.keys() if common is None else common)
    if len(names) < 5:
        return dict(satellites=names, reason='insufficient common dual-band observations')
    raw = [first[prn]-second[prn] for prn in names]
    clock = median(raw)
    return dict(satellites=names, clock_difference_m=clock,
                signed_differences_m=[value-clock for value in raw])


def _write_equal(path, raw):
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('changed existing sealed file: '+path.name)
    else:
        atomic(path, raw)


def seal_receiver(source, name, spec, base):
    offset, count = spec['cover_offset'], spec['cover_count']
    probe_start, probe_count = spec['probe_offset'], 2**18
    prefix = (source/f'lll-esa187-{name}-header.rnx').read_bytes()
    probe = (source/f'lll-esa187-{name}-{probe_start}-{probe_count}.rnx').read_bytes()
    cover = (source/f'lll-esa187-{name}-{offset}-{count}.rnx').read_bytes()
    if (len(prefix) != 65536 or digest(prefix) != spec['prefix_hash']
            or len(probe) != probe_count or len(cover) != count):
        raise ValueError('catalog preflight prefix and exact requested lengths required')
    length = probe_start+probe_count-offset
    if not 4096 <= length <= min(len(cover), len(probe)) or probe[-length:] != cover[:length]:
        raise ValueError('the independent archive ranges must overlap exactly')
    header, metadata = read_header(prefix, expected_interval=spec['interval'], expected_systems=spec['systems'])
    trimmed, inventory, _ = framed_window(cover, offset, FIRST, LAST, spec['interval'],
                                          metadata['observation_types'])
    if not {'L1C', 'L2W'} <= set(metadata['observation_types']['G']):
        raise ValueError('common GPS L1C and L2W observations required')
    combined = header+trimmed
    _write_equal(base/(name+'.rnx.gz'), gzip.compress(combined, mtime=0))
    return dict(file=spec['file'], source_size=spec['size'], interval_s=spec['interval'],
        prefix_sha256=digest(prefix), header_sha256=digest(header), header_bytes=len(header),
        locating_range=dict(offset=probe_start, length=probe_count, sha256=digest(probe)),
        cover_range=dict(offset=offset, length=count, sha256=digest(cover)), overlap_bytes=length,
        retained_uncompressed_sha256=digest(combined), retained_uncompressed_bytes=len(combined),
        **inventory)


def prepare(root, source):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('the existing comparison must be preserved')
    base = root/'data'/(ID+'-inputs')
    receipt = {name: seal_receiver(source, name, spec, base) for name, spec in RECEIVERS.items()}
    _write_equal(base/'ranges.json', encoded(receipt))
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if parent.completion['manifest_sha256'] != PARENT_SHA or not parent.summary['passed']:
            raise ValueError('the sealed AIR1 carrier path is required')
        for name in ('rinex', 'clock', 'continuity'):
            _write_equal(base/name, parent.input(name, raw=True))
    names = dict(air1='rinex', clock='clock', continuity='continuity', ranges='ranges.json')
    names.update({name: name+'.rnx.gz' for name in RECEIVERS})
    inputs = dict(plan=PLAN, **{name: (base/path).relative_to(root).as_posix() for name, path in names.items()})
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=adapter, tasks=[TASK],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_parallel_raw_receiver.py']),
        workers=1, threads=1, maximum_wall_s=60.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact paired raw receiver task required')
    def load(name):
        return json.loads(context.input_path(name).read_bytes())

    receipt = load('ranges')
    clock_index = load('clock')['result']['pair_index']
    support = load('continuity')['result']['per_pair']
    air = list(phase_epochs(gzip.decompress(context.input_path('air1').read_bytes())))
    indices = {row['seconds']: i for i, row in enumerate(air)}
    observations = {}
    for name, spec in RECEIVERS.items():
        data = gzip.decompress(context.input_path(name).read_bytes())
        if digest(data) != receipt[name]['retained_uncompressed_sha256']:
            raise ValueError('original exact receiver excerpt required')
        header, metadata = read_header(data, expected_interval=spec['interval'], expected_systems=spec['systems'])
        _, inventory, observations[name] = framed_window(data[len(header):], 0, FIRST, LAST,
            spec['interval'], metadata['observation_types'], require_tail=False)
        if inventory['epochs'] != receipt[name]['epochs']:
            raise ValueError('retained receiver count differs')
    archive = []
    for second in range(FIRST_SHARED, LAST_SHARED):
        context.charge(bound_calls=1, bound_steps=3)
        start, end = indices[second], indices[second+1]
        if end-start != 2:
            raise ValueError('the AIR1 grid must supply two half-second steps per comparison')
        row = dict(first_gps_seconds=second, last_gps_seconds=second+1,
                   portion='later' if second >= FIRST_LATER-1 else 'earlier')
        if start <= clock_index < end:
            archive.append(dict(row, skipped='archived AIR1 receiver clock step'))
            continue
        a, middle, b = [air[index]['satellites'] for index in range(start, end+1)]
        allowed = set(support[start]['accepted_prns']) & set(support[start+1]['accepted_prns'])
        # Use the same L2 channel at the intermediate point in the archived AIR1 screen.
        allowed &= phase_changes(a, middle, allowed).keys() & phase_changes(middle, b, allowed).keys()
        changes = dict(air1=phase_changes(a, b, allowed))
        changes.update({name: phase_changes(epochs[second], epochs[second+1])
                        for name, epochs in observations.items()})
        common = set.intersection(*(set(result) for result in changes.values()))
        paired = {'-'.join((first, last)): pair_difference(changes[first], changes[last], common)
                  for first, last in PAIRS}
        archive.append(dict(row, support={name: sorted(values) for name, values in changes.items()}, pairs=paired))
    if len(archive) != INTERVALS or sum('skipped' in row for row in archive) != 1:
        raise ValueError('all intervals and the original one-second clock omission must be recorded')
    context.save_bytes('carrier-differences.json', encoded(archive))
    return dict(passed=True, intervals=len(archive), scientific_decision='abstain')


def summarize(archive):
    result = {}
    for portion in ('earlier', 'later'):
        result[portion] = {}
        for pair in PAIRS:
            key = '-'.join(pair)
            records = [r['pairs'][key] for r in archive if r['portion'] == portion and 'pairs' in r]
            passing = [r['signed_differences_m'] for r in records if 'signed_differences_m' in r]
            values = [abs(v) for r in passing for v in r]
            if not values:
                raise ValueError('at least one usable paired receiver record required')
            rms = [math.sqrt(math.fsum(v*v for v in r)/len(r)) for r in passing]
            result[portion][key] = dict(usable_intervals=len(passing), omitted_intervals=len(records)-len(passing),
                observations=len(values), minimum_satellites=min(map(len, passing)),
                median_interval_rms_m=median(rms), rms_m=math.sqrt(math.fsum(v*v for v in values)/len(values)),
                p95_abs_m=sorted(values)[math.ceil(.95*len(values))-1], max_abs_m=max(values))
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.summary['charged']['bound_calls'] != INTERVALS:
            raise ValueError('complete matched receiver study required')
        records = study.artifact(TASK['identity'], 'carrier-differences.json')
        result = dict(manifest_sha256=study.completion['manifest_sha256'], ranges=study.input('ranges'),
            intervals=INTERVALS, clock_skips=[row['first_gps_seconds'] for row in records if 'skipped' in row],
            results=summarize(records), scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(result))
    print(encoded(result).decode(), end='')


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
