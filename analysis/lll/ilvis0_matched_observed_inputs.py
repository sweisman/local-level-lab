# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare frozen recorded packets and separate training and scoring inputs."""

import argparse
from contextlib import closing
import fcntl
import gzip
import io
import json
from pathlib import Path

import numpy as np

from .ilvis0_control_shards import runtime_environment
from .ilvis0_gps_force_comparison import ONBOARD, _matching_positions
from .ilvis0_gps_reconstruction_pilot import FOLDER, METHODS, SELECTION
from .ilvis0_matched_observed_layout import CONTEXT, OUTPUT as LAYOUT, POPULATION
from .ilvis0_matched_training import matched_limits
from .ilvis0_receiver_overlap import WEEK_MS
from .ilvis0_segments import extract_segment
from .studies.artifacts import ArchiveStore, atomic, digest, encoded, safe_path


ID = 'ilvis0-matched-observed-inputs-v1-20261118'
PLAN = FOLDER+'MATCHED_OBSERVED_PREFLIGHT_PLAN.md'
SOURCE = 'analysis/lll/ilvis0_matched_observed_inputs.py'
TEST = 'analysis/tests/test_ilvis0_matched_observed_inputs.py'
GPS_RECEIPT = FOLDER+'gps-reconstruction-pilot-receipt.json'
FREEZE = FOLDER+'matched-observed-inputs-freeze.json'
RECEIPT = FOLDER+'matched-observed-inputs-receipt.json'
CLOCKS = ('nominal_200Hz', 'header_elapsed')
TRACKS = (ONBOARD, *METHODS)
MAX_PACKETS = 150_000
MAX_SOURCE_BYTES = 300_000_000
MAX_INTERVAL = .0075


def clock_support(values, times, *, cut, time_offset_s):
    """Check complete perturbation timing support and derive each training prefix."""
    packet = np.asarray(values, dtype=float)
    query = np.asarray(times, dtype=float)
    if (packet.ndim != 2 or packet.shape[1] != 15 or not 2 <= len(packet) <= MAX_PACKETS
            or query.ndim != 1 or type(cut) is not int or not 0 < cut < len(query)
            or not np.isfinite(packet).all() or not np.isfinite(query).all()
            or not np.isfinite(time_offset_s) or time_offset_s < 0.
            or np.any(np.diff(query) <= 0.) or np.any(np.diff(query) > 2.)
            or np.any(np.diff(packet[:, 0]) <= 0.) or packet[0, 0] < 0.
            or np.any(abs(np.diff(packet[:, 1])-packet[1:, 2]) > 1e-8)
            or np.any(packet[:, 2] < .0025) or np.any(packet[:, 2] > MAX_INTERVAL)):
        raise ValueError('complete and ordered packet and receiver supports required')
    raw = packet[:, 3:9]
    if (np.any(packet[:, 0] != np.rint(packet[:, 0])) or np.any(raw != np.rint(raw))
            or np.any(raw < -(2**31)) or np.any(raw >= 2**31)):
        raise ValueError('unaltered integer packet offsets and signed counts required')
    ends = (np.cumsum(np.full(len(packet), .005)), np.cumsum(packet[:, 2]))
    result = {}
    for name, end in zip(CLOCKS, ends, strict=True):
        margin = min(query[0]-time_offset_s, end[-1]-query[-1]-time_offset_s)
        if margin < 0.:
            raise ValueError(f'{name} lacks complete time-offset support')
        prefix = int(np.searchsorted(end, query[cut-1]+time_offset_s, side='left'))+1
        result[name] = dict(training_packets=prefix, forecast_packets=len(packet),
                            supported_epochs=len(query),
                            minimum_timing_margin_s=float(margin),
                            duration_s=float(end[-1]))
    return result


def _write_equal(path, raw):
    if path.is_file():
        if path.read_bytes() != raw:
            raise ValueError(f'published preparation artifact differs: {path.name}')
    else:
        atomic(path, raw)


def _fixed_inputs(root):
    layout_bytes = (root/LAYOUT).read_bytes()
    layout = json.loads(layout_bytes)
    selected = json.loads((root/SELECTION).read_bytes())
    cases = layout['layouts']
    if (layout['inputs'][SELECTION] != digest((root/SELECTION).read_bytes())
            or len(cases) != 2 or len({row['group_id'] for row in cases}) != 2
            or [row['segment_id'] for row in cases] !=
               [row['segment_id'] for row in selected['selected']]
            or sum(row['exact_common_training_epochs'] for row in cases) != 740
            or sum(row['exact_common_prediction_epochs'] for row in cases) != 371):
        raise ValueError('unchanged two-recording selection and cut required')
    return layout, selected


def configuration(root):
    from .studies.dependencies import source_closure

    layout, _ = _fixed_inputs(root)
    return dict(plan_sha256=digest((root/PLAN).read_bytes()), environment=runtime_environment(),
        sources={name: digest((root/name).read_bytes())
                 for name in source_closure(root, (SOURCE, TEST, PLAN))},
        inputs={name: digest((root/name).read_bytes()) for name in (LAYOUT, SELECTION, GPS_RECEIPT)},
        archive_inputs={name: layout['inputs'][name] for name in (CONTEXT, POPULATION)},
        original_sources={row['source_task']: row['source_sha256'] for row in layout['layouts']},
        time_offset_s=matched_limits(1.)['time_offset'], clocks=CLOCKS, threads=1,
        maximum_original_reads=2, maximum_decoded_packets_per_recording=MAX_PACKETS,
        position_solves=0, imu_fit_starts=0)


def _recipes(root, layout):
    with closing(ArchiveStore(root)) as store:
        catalog = store.catalog()
        payloads = {name: store._read(name, catalog) for name in (CONTEXT, POPULATION)}
    if any(digest(raw) != layout['inputs'][name] for name, raw in payloads.items()):
        raise ValueError('sealed archive selection or timing context changed')
    population = json.loads(gzip.decompress(payloads[POPULATION]))
    sources = {row['segment']['segment_id']: row for row in population['selected']}
    contexts = {row['task_id']: row for row in json.loads(payloads[CONTEXT])['results']}
    return sources, contexts


def _receiver_material(geometry, source, saved, times):
    segment = source['segment']
    offset_ms = round(geometry['gps_minus_utc_s']*1000)
    original = [round(row['time_s']*1000) for row in segment['receiver_fixes']]
    joined = {(tag-offset_ms) % WEEK_MS: tag for tag in saved}
    if len(joined) != len(saved) or not set(original) <= set(joined):
        raise ValueError('raw receiver epoch cannot be joined exactly across GPS processing streams')
    tags = [joined[key] for key in original]
    tracks = {name: np.array([saved[tag][name] for tag in tags], dtype=float) for name in TRACKS}
    if any(array.shape != (len(times), 3) or not np.isfinite(array).all()
           or np.any(abs(np.diff(array[:, 1])) >= np.pi) for array in tracks.values()):
        raise ValueError('finite aligned receiver coordinate chart required')
    cut = geometry['training_epochs']
    if (len(tags) != geometry['exact_common_receiver_epochs']
            or cut != geometry['exact_common_training_epochs']
            or len(tags)-cut != geometry['exact_common_prediction_epochs']):
        raise ValueError('GPS association changed the original training cut')
    training = dict(gps_tags_ms=tags[:cut], query_times_s=times[:cut].tolist(),
                    coordinates={key: array[:cut].tolist() for key, array in tracks.items()})
    scoring = dict(gps_tags_ms=tags[cut:], query_times_s=times[cut:].tolist(),
                   coordinates={key: array[cut:].tolist() for key, array in tracks.items()})
    return training, scoring


def prepared_artifacts(original, geometry, source, context, saved, offset):
    """Decode and bind one recording to the unchanged split and three GPS tracks."""
    values, times, _, provenance = extract_segment(original, context, source['segment'])
    if (provenance['source_sha256'] != geometry['source_sha256']
            or provenance['source_bytes'] > MAX_SOURCE_BYTES
            or provenance['group1_observations_used'] or not provenance['all_original_integers_preserved']):
        raise ValueError('physical decoding provenance differs')
    clocks = clock_support(values, times, cut=geometry['training_epochs'], time_offset_s=offset)
    training, scoring = _receiver_material(geometry, source, saved, times)
    buffer = io.BytesIO()
    np.save(buffer, values, allow_pickle=False)
    recipe = dict(segment_id=geometry['segment_id'], query_times_s=times.tolist(),
                  training_epochs=geometry['training_epochs'], later_position_count=geometry['prediction_epochs'],
                  clocks=clocks, source_sha256=geometry['source_sha256'], time_offset_s=offset)
    payloads = {'packets.npy.gz': gzip.compress(buffer.getvalue(), mtime=0),
                'queries.json': encoded(recipe), 'training.json': encoded(training),
                'scoring.json': encoded(scoring), 'packet-provenance.json': encoded(provenance)}
    return payloads, clocks, provenance


def _prepare_case(root, output, geometry, source, context, saved, offset, freeze_sha256):
    physical = Path(source['source_path'])
    relative = physical.relative_to(root).as_posix() if physical.is_absolute() else physical.as_posix()
    if (not relative.startswith('data/ilvis0-ready/') or geometry['source_task'] != source['task']
            or geometry['source_sha256'] != context['inspection']['source_sha256']):
        raise ValueError('documented retained original required')
    original = safe_path(root, relative)
    case = output/geometry['segment_id']
    case.mkdir(exist_ok=True)
    seal = case/'input-receipt.json'
    if seal.is_file():
        record = json.loads(seal.read_bytes())
        if (record['freeze_sha256'] != freeze_sha256 or record['source_sha256'] != geometry['source_sha256']
                or any(digest(safe_path(root, item['path']).read_bytes()) != item['sha256']
                       for item in record['artifacts'].values())):
            raise ValueError('prepared input receipt or hashed artifact changed')
        return record
    payloads, clocks, provenance = prepared_artifacts(original, geometry, source, context, saved, offset)
    artifacts = {}
    for name, raw in payloads.items():
        path = case/name
        _write_equal(path, raw)
        artifacts[name] = dict(path=path.relative_to(root).as_posix(), sha256=digest(raw), bytes=len(raw))
    record = dict(segment_id=geometry['segment_id'], source_sha256=geometry['source_sha256'],
                  freeze_sha256=freeze_sha256, imu_type=geometry['imu_type'], clocks=clocks,
                  training_epochs=geometry['training_epochs'], scoring_epochs=geometry['prediction_epochs'],
                  source_packets=provenance['native_packets'], original_reads=1, imu_fit_starts=0,
                  artifacts=artifacts, scientific_decision='abstain')
    _write_equal(seal, encoded(record))
    return record


def prepare(root):
    root = Path(root).resolve()
    frozen = (root/FREEZE).read_bytes()
    config = configuration(root)
    if frozen != encoded(config):
        raise ValueError('recorded preparation differs from its source or environment freeze')
    output = root/'data'/ID
    output.mkdir(parents=True, exist_ok=True)
    with (output/'prepare.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        layout, selected = _fixed_inputs(root)
        sources, contexts = _recipes(root, layout)
        picks, saved, prior = _matching_positions(root)
        if picks != selected['selected']:
            raise ValueError('parent GPS position reprocessing differs from the fixed selection')
        records = []
        for geometry in layout['layouts']:
            source = sources[geometry['segment_id']]
            task = source['task']
            records.append(_prepare_case(root, output, geometry, source, contexts[task],
                                         saved[task], config['time_offset_s'], digest(frozen)))
        result = dict(freeze_sha256=digest(frozen), position_parent=prior,
                      recordings=records, imu_fit_starts=0, scientific_decision='abstain')
        _write_equal(root/RECEIPT, encoded(result))
    return {row['segment_id']: {key: row[key] for key in
             ('source_packets', 'training_epochs', 'scoring_epochs', 'clocks')} for row in records}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'prepare'))
    args = parser.parse_args()
    root = Path.cwd()
    if args.action == 'freeze':
        blob = encoded(configuration(root))
        _write_equal(root/FREEZE, blob)
        print(digest(blob))
    else:
        print(json.dumps(prepare(root), sort_keys=True))
