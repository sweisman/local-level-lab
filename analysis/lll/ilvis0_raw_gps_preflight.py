# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inventory satellite observations for the preselected ILVIS0 pilot candidates."""

import argparse
from collections import Counter
from contextlib import closing
import csv
import datetime as dt
import gzip
import io
import json
from pathlib import Path

import numpy as np

from . import gnss_position as gps
from . import trimble_observations as observations
from .ilvis0_receiver_overlap import WEEK_MS, _time_index
from .trimble_receiver import ReceiverStream, SurveyPages
from .studies.artifacts import atomic, digest, encoded


IDENTITY = 'ilvis0-raw-gps-preflight-v1-20261118'
PARENT = 'data/ilvis0-rt27-position-inventory-20261110-v2'
FOLDER = 'docs/ilvis0-measurement-contribution/'
BASELINE = 'docs/ilvis0-current-findings-20261015/current-stretches.csv'
METADATA = FOLDER+'matched-pilot-metadata.json'
ADAPTER = 'analysis/lll/ilvis0_raw_gps_preflight.py'
PLAN = FOLDER+'GPS_RECONSTRUCTION_PREFLIGHT_PLAN.md'
METHODS = ('l1_broadcast', 'dual_frequency')
MAX_BYTES, MAX_PACKETS, MAX_RECORDS, MAX_EPOCHS = 64_000_000, 200_000, 60_000, 20_000
GPS_EPOCH = dt.datetime(1980, 1, 6, tzinfo=dt.timezone.utc)


def tag(record):
    return record['gps_week']*WEEK_MS + round(record['gps_week_seconds']*1000)


def associate(records, wanted):
    matched, duplicates = {}, set()
    for record in records:
        timestamp = tag(record)
        if timestamp not in wanted or timestamp in duplicates:
            continue
        if timestamp in matched:
            del matched[timestamp]
            duplicates.add(timestamp)
        else:
            matched[timestamp] = record
    return matched, duplicates


def decode(raw, bounds, week):
    if not 0 < len(raw) <= MAX_BYTES:
        raise ValueError('bounded receiver byte stream required')
    first = bounds['prefix_bytes']
    end = len(raw)-bounds['tail_bytes']
    if not 0 <= first < end <= len(raw) or max(first, len(raw)-end) > 512:
        raise ValueError('previous checked receiver boundary differs')
    if (digest(raw[:first]) != bounds['prefix_sha256']
            or digest(raw[end:]) != bounds['tail_sha256']):
        raise ValueError('previous boundary hash differs')
    stream, pages = ReceiverStream(), SurveyPages()
    records, ephemerides, ionosphere = [], {}, {}
    binary_packets = initial_pages = 0
    seen_first, orphan = set(), {}
    for offset in range(first, end, 65536):
        for packet in stream.feed(raw[offset:min(end, offset+65536)]):
            if packet['kind'] != 'binary':
                continue
            binary_packets += 1
            if binary_packets > MAX_PACKETS:
                raise ValueError('receiver packet ceiling exceeded')
            payload = packet['payload']
            if packet['packet_type'] == 0x55 and payload:
                if payload[0] == 1:
                    sha = digest(payload)
                    if sha not in ephemerides:
                        ephemerides[sha] = observations.decode_gps_ephemeris(packet) | dict(payload_sha256=sha)
                elif payload[0] == 3:
                    sha = digest(payload)
                    if sha not in ionosphere:
                        ionosphere[sha] = gps.decode_ionosphere(payload)
            if packet['packet_type'] != 0x57 or not payload or payload[0] not in (0, 6):
                continue
            if len(payload) < 4:
                raise ValueError('truncated survey paging header')
            subtype, page, reply, flags = payload[:4]
            index, total = page >> 4, page & 15
            if subtype not in seen_first and index > 1:
                signature = (total, reply, flags)
                if index > total or flags & 12 or (subtype in orphan and
                        orphan[subtype] != (signature, index-1)):
                    raise ValueError('inconsistent initial survey fragment')
                orphan[subtype] = (signature, index)
                initial_pages += 1
                continue
            if subtype in orphan:
                signature, last = orphan.pop(subtype)
                if last != signature[0]:
                    raise ValueError('incomplete initial survey fragment before complete record')
            seen_first.add(subtype)
            packet['stream_offset'] += first
            record = pages.feed(packet)
            if record is not None:
                if len(records) == MAX_RECORDS:
                    raise ValueError('receiver measurement record ceiling exceeded')
                measurement = (observations.decode_rt17(record, week) if subtype == 0
                               else observations.decode_rt27(record))
                measurement.pop('encoded_payload_hex')
                measurement.update({key: record[key] for key in
                    ('payload_sha256', 'first_stream_offset')})
                records.append(measurement)
    stream.finish()
    return dict(records=records, ephemerides=list(ephemerides.values()),
                ionosphere=list(ionosphere.values()), binary_packets=binary_packets,
                initial_unassembled_survey_pages=initial_pages,
                tail_incomplete_survey_records=len(pages.pending))


def _utc_ms(value, leap_seconds):
    elapsed = dt.datetime.fromisoformat(value)-GPS_EPOCH
    return elapsed.days*86_400_000+(elapsed.seconds+leap_seconds)*1000+elapsed.microseconds/1000


def _selected_positions(compressed, task):
    positions = _time_index(list(csv.DictReader(io.StringIO(gzip.decompress(compressed).decode()))))
    weeks = {int(row['gps_week']) for row in positions.values()}
    if len(weeks) != 1:
        raise ValueError('one recorded GPS week required for the dated receiver stream')
    first, last = [_utc_ms(task[key], task['leap_seconds']) for key in ('start_utc', 'end_utc')]
    selected = {t: r for t, r in positions.items() if first <= t <= last}
    if not 1 <= len(selected) <= MAX_EPOCHS:
        raise ValueError('original selected receiver epoch count outside declared bounds')
    return weeks.pop(), selected


def _geometry(record, ephemerides, ionosphere, reference):
    state = np.r_[gps.ecef(*np.deg2rad([float(reference['latitude_deg']),
                                       float(reference['longitude_deg'])]),
                          float(reference['ellipsoid_height_m'])), 0.]
    result = {}
    for method in METHODS:
        if method == 'l1_broadcast' and ionosphere is None:
            result[method] = dict(ranges=None, rank=None, eligible=False, reason='ionosphere_context')
            continue
        selected, _ = gps.observations(record, ephemerides, method)
        design, _, used, _ = gps.range_system(state, selected, record['gps_week_seconds'],
                                             method, ionosphere)
        rank = int(np.linalg.matrix_rank(design)) if len(used) else 0
        eligible = len(used) >= 5 and rank == 4
        result[method] = dict(ranges=len(used), rank=rank, eligible=eligible,
                              reason='supported' if eligible else 'range_count_or_rank')
    return result


def evaluate(task, context):
    raw = gzip.decompress(context.input_path().read_bytes())
    position_bytes = context.input_path(task['position_key']).read_bytes()
    if digest(raw) != task['receiver_sha256'] or digest(position_bytes) != task['position_sha256']:
        raise ValueError('sealed receiver or position input differs')
    week, positioned = _selected_positions(position_bytes, task)
    result = dict(identity=task['identity'], segment_id=task['segment_id'],
                  source_sha256=task['source_sha256'], selected_epochs=len(positioned),
                  observed_fit_starts=0, imu_observations_used=False, scientific_decision='abstain')
    try:
        decoded = decode(raw, task['bounds'], week)
        if decoded['binary_packets'] != task['checked_packet_count']:
            raise ValueError('binary packet count differs from the recorded audit')
    except ValueError as error:
        artifact = context.save('coverage.json', dict(result, decode_status='unsupported',
            decode_reason=str(error), matched_unique=0, support={method: 0 for method in METHODS}))
        return dict(passed=True, decode_status='unsupported', report=artifact, **result)
    measurements = decoded.pop('records')
    ephemerides = decoded.pop('ephemerides')
    contexts = decoded.pop('ionosphere')
    coefficients = {tuple(item['alpha']+item['beta']) for item in contexts}
    ion = contexts[0] if len(coefficients) == 1 and all(
        item['leap_seconds'] == task['leap_seconds'] for item in contexts) else None
    matched, duplicates = associate(measurements, set(positioned))
    rows = []
    counts = Counter()
    for timestamp, reference in positioned.items():
        record = matched.get(timestamp)
        row = dict(gps_millisecond_tag=timestamp, record_status='matched' if record else
                   'duplicate' if timestamp in duplicates else 'missing',
                   payload_sha256=record['payload_sha256'] if record else None)
        if record is not None:
            geometry = _geometry(record, ephemerides, ion, reference)
            row.update(geometry)
            counts.update(method for method in METHODS if geometry[method]['eligible'])
        rows.append(row)
    table = context.save_bytes('epochs.json.gz', gzip.compress(encoded(rows), mtime=0))
    artifact = context.save('coverage.json', dict(result, **decoded, decode_status='checked',
        format_counts=dict(Counter(row['format'] for row in measurements)),
        ephemeris_payloads=len(ephemerides), ionosphere_context=ion is not None,
        matched_unique=len(matched), duplicate_epochs=len(duplicates),
        support={method: counts[method] for method in METHODS}, epoch_table=table))
    return dict(passed=True, decode_status='checked', report=artifact,
                eligible_l1=counts['l1_broadcast'], eligible_dual=counts['dual_frequency'], **result)


def prepare(root):
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    root = Path(root).resolve()
    metadata = json.loads((root/METADATA).read_bytes())
    if digest((root/BASELINE).read_bytes()) != metadata['inputs'][BASELINE]:
        raise ValueError('pilot metadata is no longer bound to the selected segment table')
    eligible = {row['segment_id'] for row in metadata['rows'] if row['passes_checked_metadata']}
    with (root/BASELINE).open() as stream:
        segments = [row for row in csv.DictReader(stream) if row['segment_id'] in eligible]
    if len(segments) != len(eligible) or len(eligible) != 21 or metadata['pilot_selection_frozen']:
        raise ValueError('exact 21-source metadata inventory required')
    inputs, tasks = {'eligible_metadata': METADATA, 'segment_table': BASELINE}, []
    with closing(ClosedStudy(root, PARENT)) as study:
        if (study.summary['total'] != 53 or study.summary['completed'] != 53
                or sum(row['passed'] is True for row in study.rows.values()) != 52):
            raise ValueError('closed 53-source receiver inventory required')
        for segment in segments:
            identity = segment['task']
            prior = study.tasks[identity]
            audit = study.artifact(identity, 'summary.json')
            positions = study.artifact(identity, 'positions.csv.gz', raw=True)
            if not study.rows[identity]['passed'] or audit['source_sha256'] != segment['source_sha256']:
                raise ValueError('receiver inventory and pilot source disagree')
            receiver = study.manifest['inputs'][prior['input_key']]
            path = root/receiver['source']
            if not path.is_file() or digest(path.read_bytes()) != receiver['sha256']:
                raise ValueError('restore the frozen extracted receiver stream')
            position = f'data/{IDENTITY}-inputs/{identity}.csv.gz'
            if (root/position).is_file():
                if (root/position).read_bytes() != positions:
                    raise ValueError('saved preflight position input changed')
            else:
                atomic(root/position, positions)
            key, position_key = 'r_'+identity, 'p_'+identity
            inputs.update({key: receiver['source'], position_key: position})
            tasks.append(dict(identity=identity, input_key=key, position_key=position_key,
                bounds={name: audit[name] for name in ('prefix_bytes', 'prefix_sha256',
                                                     'tail_bytes', 'tail_sha256')},
                checked_packet_count=audit['checked_packet_count'],
                source_sha256=segment['source_sha256'], receiver_sha256=audit['stream_sha256'],
                position_sha256=digest(positions), leap_seconds=prior['leap_seconds'],
                **{name: segment[name] for name in ('segment_id', 'start_utc', 'end_utc')},
                limits=dict(native_calls=0, packet_visits=0, bound_calls=0, bound_steps=0)))
    sources = source_closure(root, (ADAPTER, PLAN, 'analysis/tests/test_ilvis0_raw_gps_preflight.py',
                                   'analysis/tests/test_trimble_observations.py'))
    definition = dict(id=IDENTITY, scope='satellite geometry coverage only; no fits',
                      adapter=ADAPTER, sources=sources, inputs=inputs, tasks=tasks,
                      workers=2, threads=1, maximum_wall_s=600.)
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+IDENTITY, allocation=manifest['allocation'],
                limits=manifest['limits'])


if __name__ == '__main__':
    from .ilvis0_control_shards import launch
    from .studies.validation_resume import _other_threads

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run'))
    args = parser.parse_args()
    root = Path.cwd()
    report = (prepare(root) if args.action == 'prepare'
              else launch(root/'data'/IDENTITY, reserved_threads=_other_threads(root, 2)))
    print(json.dumps(report, sort_keys=True))
