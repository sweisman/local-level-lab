# SPDX-License-Identifier: AGPL-3.0-or-later
"""Binding of the two GPS development recordings to archived inertial inputs."""

from contextlib import closing
import csv
import gzip
import json
from pathlib import Path

from .ilvis0_gps_reconstruction_pilot import FOLDER, SELECTION
from .ilvis0_prediction_layout import prediction_layout
from .ilvis0_receiver_overlap import WEEK_MS
from .ilvis0_remaining_prediction_layouts import CONTEXT, POPULATION
from .studies.artifacts import ArchiveStore, atomic, digest, encoded, safe_path


BASELINE = 'docs/ilvis0-current-findings-20261015/current-stretches.csv'
OUTPUT = FOLDER+'matched-observed-layout.json'


def build(root):
    root = Path(root).resolve()
    with closing(ArchiveStore(root)) as store:
        catalog = store.catalog()
        raw = {name: store._read(name, catalog) for name in (CONTEXT, POPULATION)}
    raw.update({name: (root/name).read_bytes() for name in (BASELINE, SELECTION)})
    picks = json.loads(raw[SELECTION])['selected']
    baseline = {row['segment_id']: row for row in csv.DictReader(raw[BASELINE].decode().splitlines())}
    population = json.loads(gzip.decompress(raw[POPULATION]))
    sources = {row['segment']['segment_id']: row for row in population['selected']}
    contexts = {row['task_id']: row for row in json.loads(raw[CONTEXT])['results']}
    if (len(picks) != 2 or len({row['group_id'] for row in picks}) != 2
            or len(sources) != 53):
        raise ValueError('exact two GPS recordings in the preserved baseline required')
    rows = []
    for pick in picks:
        key = pick['segment_id']
        source = sources[key]
        context = contexts[source['task']]
        chosen = dict(baseline[key], group_id=pick['group_id'])
        layout = prediction_layout(chosen, source, context)
        if pick['source_sha256'] != layout['source_sha256'] or pick['identity'] != source['task']:
            raise ValueError('GPS pilot and original inertial source differ')
        physical = Path(source['source_path'])
        relative = physical.relative_to(root).as_posix() if physical.is_absolute() else physical.as_posix()
        if not relative.startswith('data/ilvis0-ready/') or not safe_path(root, relative).is_file():
            raise ValueError('expected retained original is not present')
        leap_ms = round(context['timing']['gps_minus_utc_s']*1000)
        tags = pick['gps_millisecond_tags']
        converted = [(tag-leap_ms) % WEEK_MS for tag in tags]
        if sorted(set(converted)) != converted:
            raise ValueError('receiver week rollover needs its own timing policy')
        cut_ms = round(layout['first_prediction_utc_week_s']*1000)
        original_tags = [round(float(row['time_s'])*1000) for row in source['segment']['receiver_fixes']]
        if len(original_tags) != len(set(original_tags)):
            raise ValueError('ambiguous original receiver epochs at saved precision')
        common = sorted(set(original_tags) & set(converted))
        layout.update(receiver_position_pilot_epochs=len(converted),
                      exact_common_receiver_epochs=len(common),
                      exact_common_training_epochs=sum(tag < cut_ms for tag in common),
                      exact_common_prediction_epochs=sum(tag >= cut_ms for tag in common),
                      source_task=source['task'], gps_minus_utc_s=leap_ms/1000.,
                      retained_original_present=True)
        rows.append(layout)
    return dict(version='ilvis0-matched-observed-layout-v1', layouts=rows,
                inputs={name: digest(blob) for name, blob in raw.items()},
                builder_sha256=digest(Path(__file__).read_bytes()),
                original_reads=0, position_solves=0, imu_fit_starts=0,
                scope='metadata-only two-thirds training and later receiver comparison',
                scientific_decision='abstain')


if __name__ == '__main__':
    result = build('.')
    path = Path(OUTPUT)
    raw = encoded(result)
    if path.is_file() and path.read_bytes() != raw:
        raise ValueError('observed metadata layout changed')
    if not path.is_file():
        atomic(path, raw)
    print(json.dumps(result['layouts'], sort_keys=True))
