# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare saved force-direction limits with travel on identical gyro intervals."""

from contextlib import closing
import csv
import gzip
import json
from pathlib import Path

from . import ilvis0_paired_accelerometers as paired
from . import ilvis0_paired_gyro_motion as motion
from . import ilvis0_recorded_motion_rate as prior
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_remaining_prediction_layouts import CONTEXT, POPULATION
from .studies.artifacts import ArchiveStore, digest, encoded, safe_path


ID = 'ilvis0-paired-gyro-intervals-v2'
SCOPE = 'Earlier fixed force histories compared with two paired logged gyros on the same intervals'
PLAN = prior.FOLDER+'PAIRED_GYRO_INTERVAL_PLAN.md'
SOURCE_BINDING = prior.FOLDER+'PAIRED_GYRO_INTERVAL_SOURCE_BINDING.md'
LEG = 'leg-590ee7971efb'
SEGMENTS = ('3df34ea39a6cbdbe15bb0f36', '233183f67270980491416678')
ORIGINAL_HASHES = ('5e597ef0cd42c391c2fa032a8392300e69bf40dd0420360eea89c30119a85363',
                   'dc223d82d68dd667db8bb628fd67546aa793934754c552982d363da54b9380de')
HASHES = {'pair-table': 'f3d8d293e2020595ba1d53eeb1462630a70f0cf547cc220b5237b99e608efc88',
          'force-freeze': 'af3bf4864f9ca9f54da89e24a159a316ca48a842371962c21fcdc147b5a2233e',
          'force-result': 'af3eff4157b9c70431c3ac409e93f208999ff96ae0c5fdaf4d0ec948da860072'}
OFFSET = .15
MAX_CASES = 32
MAX_FORCE = 15_856
MAX_INTERVALS = 608
MAX_PACKETS = motion.parent.MAX_PACKETS
TASK = dict(identity=LEG, input_key='layout', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=3+MAX_CASES,
                bound_steps=2*MAX_PACKETS+MAX_FORCE+2*MAX_CASES*MAX_INTERVALS))


def _travel_index(ends, durations, increments, angle_scale):
    import numpy as np

    packet = motion.parent.PacketRates(ends, durations, increments)
    unsigned = np.linalg.norm(increments, axis=1)+np.sqrt(3)*angle_scale/2
    return packet.ends, packet.starts, np.r_[0., np.cumsum(unsigned)]


def travel(ends, durations, increments, left, right, angle_scale):
    return _travel(_travel_index(ends, durations, increments, angle_scale), left, right)


def _travel(index, left, right):
    import numpy as np

    ends, starts, total = index
    lo, hi = np.asarray(left)-OFFSET, np.asarray(right)+OFFSET
    first = np.searchsorted(ends, lo, side='left')
    last = np.searchsorted(starts, hi, side='right')
    return np.where((lo >= starts[0]) & (hi <= ends[-1]), total[last]-total[first], np.nan)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('preserve the existing bounded interval comparison')
    inputs = {'pair-table': paired.PAIRS, 'force-freeze': prior.FREEZE, 'force-result': prior.RESULT}
    for key, path in inputs.items():
        if digest((root/path).read_bytes()) != HASHES[key]:
            raise ValueError('the retained overlap and force evidence is required')
    with (root/paired.PAIRS).open() as stream:
        match, = (row for row in csv.DictReader(stream) if row['shared_leg_id'] == LEG)
    if (match['same_track_candidate'] != 'True'
            or tuple(match[k] for k in ('left_segment_id', 'right_segment_id')) != SEGMENTS):
        raise ValueError('the exact 24 October flight overlap required')
    with closing(ArchiveStore(root)) as store:
        selected = json.loads(gzip.decompress(store.read(POPULATION)))['selected']
        contexts = json.loads(store.read(CONTEXT))['results']
    selections = {row['segment']['segment_id']: row for row in selected}
    by_task = {r['task_id']: r for r in contexts}
    sides, compressed_shas = [], {}
    for side, segment, sha, kind in zip(('left', 'right'), SEGMENTS, ORIGINAL_HASHES, (8,21), strict=True):
        selected_row = selections[segment]
        record = by_task[selected_row['task']]
        geometry = selected_row['segment']
        path = Path(selected_row['source_path'])
        relative = (path.relative_to(root) if path.is_absolute() else path).as_posix()
        if (record['inspection']['source_sha256'] != sha or geometry['imu_type'] != kind
                or path.name != match[f'{side}_filename']+'.gz'
                or not relative.startswith('data/ilvis0-ready/')):
            raise ValueError('selected original recorder identity differs')
        key = LEG+'-'+side
        inputs[key] = relative
        compressed_shas[key] = digest(safe_path(root, relative).read_bytes())
        sides.append(dict(original=key, context=record, segment=geometry))
    layout = dict(begin=float(match['overlap_start_utc_week_s']), end=float(match['overlap_end_utc_week_s']),
                  sides=sides, compressed_shas=compressed_shas)
    layout_path = f'data/{ID}-inputs/layout.json'
    _write_equal(root/layout_path, encoded(layout))
    inputs['layout'] = layout_path
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, [adapter, PLAN, SOURCE_BINDING, 'analysis/tests/test_ilvis0_paired_gyro_intervals.py'])
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=90.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def force_histories(root, freeze, receipt, segment):
    import numpy as np

    path = prior.paths
    raw, source, _, pairs = path.carrier._checked_inputs(root)
    record_manifest, prepared = path.SUPPORT._inputs(root)
    raw.update(prepared)
    if {name: digest(value) for name, value in raw.items()} != freeze['inputs']:
        raise ValueError('same sealed motion histories required')
    records, origin = {}, None
    for case in record_manifest['recordings']:
        rec = path.SUPPORT._record(case, raw)
        rec['midpoints'] = tuple(np.cumsum(dt)-dt/2 for dt in rec['periods'])
        records[case['segment_id']] = rec
        if case['segment_id'] == segment:
            provenance = json.loads(raw[case['artifacts']['packet-provenance.json']['path']])
            origin = provenance['first_interval_start_utc_s']
    if origin is None:
        raise ValueError('matching original force source required before force replay')
    selected, groups = prior.collect(root, raw, source, pairs, records)
    if digest(encoded(selected)) != receipt['packet_selection_sha256']:
        raise ValueError('original packet selection and absolute clock required')
    return origin, {key: rows for key, rows in groups.items() if key[0] == segment}


def evaluate(task, context):
    import numpy as np

    from .models import OMEGA_E

    declared = {key: value for key, value in task.items() if key not in ('index','shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact paired packet interval task required')
    layout = json.loads(context.input_path('layout').read_bytes())
    overlap = layout['end']-layout['begin']
    sources = list(motion.streams(context, layout))
    if (tuple(source['segment_id'] for _, source, _, _ in sources) != SEGMENTS
            or tuple(source['source_sha256'] for _, source, _, _ in sources) != ORIGINAL_HASHES):
        raise ValueError('original paired recorder identity differs')
    travel_indexes = {clock: [_travel_index(*by_clock[clock], angles, source['angle_scale_rad_per_count'])
                        for _, source, angles, by_clock in sources] for clock in motion.parent.CLOCKS}
    context.charge(bound_calls=1, bound_steps=MAX_FORCE)
    evidence = {}
    for key, expected in HASHES.items():
        raw = context.input_path(key).read_bytes()
        if digest(raw) != expected:
            raise ValueError('changed sealed paired motion or force evidence')
        if key != 'pair-table':
            evidence[key] = json.loads(raw)
    segment = sources[0][1]['segment_id']
    origin, histories = force_histories(context.root.parents[1], evidence['force-freeze'],
                                      evidence['force-result'], segment)
    previous = {(r['segment_id'],r['side'],r['track'],r['clock'],r['model']): r
                for r in evidence['force-result']['rows']}
    if len(histories) != MAX_CASES:
        raise ValueError('expected both splits, both paths, both clocks and four candidates')
    summaries = []
    for key, rows in sorted(histories.items()):
        _, side, track, clock, model = key
        times, counts, force, position = (np.asarray(v) for v in zip(*rows, strict=True))
        if not 2 <= len(times) <= MAX_INTERVALS:
            raise ValueError('original sample limit required')
        context.charge(bound_calls=1, bound_steps=2*MAX_INTERVALS)
        required = prior.force_in_fixed_frame(force, position, model=model)
        errors = np.arcsin(np.sqrt(3)*prior.paths.SUPPORT.COUNT_ERROR/np.linalg.norm(counts, axis=1))
        screen = prior.screen(counts, required, times, maximum_rate_rad_s=0.,
                              body_direction_error_rad=errors, frame_direction_error_rad=np.zeros(len(times)))
        angles = np.asarray(screen['necessary_turn_rad'])
        durations = np.diff(times)
        if abs(np.max(angles/durations)-previous[key]['initial_lower_rads']) > 1e-12:
            raise ValueError('required motion bound did not reproduce')
        epochs = times+(origin-layout['begin'])
        pair = np.asarray([_travel(index, epochs[:-1], epochs[1:]) for index in travel_indexes[clock]])
        good = np.isfinite(pair).all(axis=0) & (epochs[:-1]>=OFFSET) & (epochs[1:]<=overlap-OFFSET)
        if not good.any():
            raise ValueError('no common supported packet intervals')
        budgets = pair[:, good]+OMEGA_E*durations[good]
        shortfall = (angles[good]-np.max(budgets, axis=0))/durations[good]
        worst = int(np.argmax(shortfall))
        mids = np.flatnonzero(good)[worst]
        summaries.append(dict(side=side, track=track, clock=clock, model=model, intervals=len(angles),
            covered=int(good.sum()), above_each=np.sum(angles[good]>budgets, axis=1).tolist(),
            above_both=int(np.sum(shortfall>0)), max_shortfall_rad_s=float(shortfall[worst]),
            max_shortfall_pair_s=epochs[mids:mids+2].tolist()))
    context.save_bytes('paired-gyro-intervals.json', encoded(dict(summaries=summaries, fit_starts=0,
        group1_observations_used=False, scientific_decision='abstain')))
    return dict(passed=True, summaries=len(summaries), scientific_decision='abstain')
