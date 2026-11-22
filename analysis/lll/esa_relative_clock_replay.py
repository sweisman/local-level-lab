# SPDX-License-Identifier: AGPL-3.0-or-later
"""Isolate temporal GPS satellite clock differences on development flight 187."""

from collections import defaultdict
import gzip
import json
import math
from pathlib import Path
import sys

from .esa_final_orbit_replay import BASELINE, BLOCK, COUNT, _baseline_rows, _range_step
from .esa_precise_gps_support import CLOCK_STEP_S, MAXIMUM_LOOKBACK_S, _product_epoch
from .esa_rinex_code import observation_epochs, read_navigation
from .esa_rinex_code_study import _BASE, _INPUTS, _NAV, _OBS
from .esa_rinex_window import FOLDER, WEEK, read_header
from .studies.artifacts import atomic, digest, encoded


ID = 'esa-relative-clock-replay-v1'
PLAN = FOLDER + 'ESA_RELATIVE_CLOCK_REPLAY_PLAN.md'
SCOPE = 'ESA 187 differential changes in GPS clock correction on matched reduced satellite sets'
CLOCK = _BASE + 'products/IGS0OPSFIN_20231870000_01D_30S_CLK.CLK.gz'
CLOCK_SHA = 'fbd3f1fac8b3767a28c02b160fdb3d5ea0a2f3543461d61355d8b8c440b4ede4'
REFERENCE_PRN, EXCLUDED_PRN = 1, 17
MAX_EVALUATIONS = 4
INPUTS = dict(observations=_OBS, navigation=_NAV, baseline=BASELINE, clock=CLOCK)


def _clock_records(text):
    header, found, body = text.partition('END OF HEADER')
    if not found or 'CLOCKS ARE ALIGNED TO GPS TIME' not in header:
        raise ValueError('expected IGS clock product aligned to GPS time')
    table = defaultdict(dict)
    for line in body.splitlines():
        if not line.startswith('AS G'):
            continue
        fields = line.split()
        epoch = _product_epoch(fields[2:8], CLOCK_STEP_S)
        prn, correction = int(fields[1][1:]), float(fields[9])
        if (not 1 <= prn <= 32 or not math.isfinite(correction)
                or abs(correction) >= .1 or epoch in table[prn]):
            raise ValueError('invalid or duplicate GPS clock correction')
        table[prn][epoch] = correction
    return table


def interpolate_clock(samples, seconds):
    lower = math.floor(seconds / CLOCK_STEP_S) * CLOCK_STEP_S
    upper = math.ceil(seconds / CLOCK_STEP_S) * CLOCK_STEP_S
    if lower not in samples or upper not in samples:
        raise ValueError('missing bracketing GPS clock sample')
    return samples[lower] + (samples[upper] - samples[lower]) * ((seconds - lower) / CLOCK_STEP_S)


def relative_differences(differences):
    if REFERENCE_PRN not in differences:
        raise ValueError('designated common GPS clock reference missing')
    reference = differences[REFERENCE_PRN]
    return {prn: correction - reference for prn, correction in differences.items()}


def _load(read):
    obs = gzip.decompress(read('observations'))
    nav, clock = read('navigation'), read('clock')
    if (digest(obs) != _INPUTS[_OBS] or digest(nav) != _INPUTS[_NAV]
            or digest(clock) != CLOCK_SHA):
        raise ValueError('opened GPS observations and clock/navigation products differ')
    header, metadata = read_header(obs)
    records = list(observation_epochs(obs[len(header):].decode('ascii'), metadata['observation_types']))
    baseline = _baseline_rows(read('baseline'))
    if len(records) != COUNT or any(
            row['gps_week'] != WEEK or row['gps_week_seconds'] != saved['gps_week_seconds']
            for row, saved in zip(records, baseline, strict=True)):
        raise ValueError('complete matched GPS epochs required')
    navigation, ionosphere = read_navigation(gzip.decompress(nav).decode('ascii'))
    clocks = _clock_records(gzip.decompress(clock).decode('ascii'))
    return records, baseline, navigation, ionosphere, clocks


def _selected(row, saved, navigation):
    from .gnss_position import observations

    available, _ = observations(row, navigation, 'dual_frequency')
    by_prn = {item['sv_id']: item for item in available}
    prns = saved['used_satellites']
    if saved['status'] != 'converged' or not {REFERENCE_PRN, EXCLUDED_PRN} <= set(prns):
        raise ValueError('unchanged full-set solution required')
    return [by_prn[prn] for prn in prns]


def _differences(selected, seconds, clocks):
    differences = {}
    for item in selected:
        prn, tx = item['sv_id'], item['transmit_gps_seconds']
        if not seconds - MAXIMUM_LOOKBACK_S <= tx <= seconds:
            raise ValueError('transmit epoch outside checked product support')
        if prn != EXCLUDED_PRN:
            differences[prn] = interpolate_clock(clocks[prn], tx) - item['satellite_clock_s']
    return relative_differences(differences)


def _anchors(records, baseline, navigation, clocks):
    first = {}
    for index, saved in enumerate(baseline):
        for prn in saved['dual_frequency']['used_satellites']:
            if prn != EXCLUDED_PRN:
                first.setdefault(prn, index)
    by_index = {
        index: _differences(_selected(records[index], baseline[index]['dual_frequency'], navigation),
                            records[index]['gps_week_seconds'], clocks)
        for index in sorted(set(first.values()))
    }
    return {str(prn): dict(index=index, seconds=by_index[index][prn]) for prn, index in first.items()}


def _task(start):
    end = min(start + BLOCK, COUNT)
    size = end - start
    return dict(identity=f'epochs-{start:04d}-{end:04d}', input_key='observations',
                payload=dict(start=start, end=end),
                limits=dict(native_calls=0, packet_visits=0, bound_calls=2 * size,
                            bound_steps=(1 + 2 * MAX_EVALUATIONS) * size))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    output = root / 'data' / ID
    if output.exists():
        raise ValueError('clock replay already frozen')
    records, baseline, navigation, _, clocks = _load(lambda key: (root / INPUTS[key]).read_bytes())
    anchors = _anchors(records, baseline, navigation, clocks)
    relative_anchors = 'data/' + ID + '-inputs/anchors.json'
    atomic(root / relative_anchors, encoded(anchors))
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, adapter=adapter, inputs=INPUTS | dict(anchors=relative_anchors),
        tasks=[_task(start) for start in range(0, COUNT, BLOCK)],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_relative_clock_replay.py']),
        workers=1, threads=1, maximum_wall_s=180., scope=SCOPE)
    manifest = Definition.from_dict(definition, root).prepare(root)
    print(encoded(dict(id=ID, limits=manifest['limits'], anchors=anchors)).decode(), end='')


def _settle(initial, selected, seconds, ionosphere):
    import numpy as np

    state = initial.copy()
    for evaluation in range(1, MAX_EVALUATIONS + 1):
        step, rms = _range_step(state, selected, seconds, ionosphere)
        if np.linalg.norm(step) <= 1e-5:
            return state, rms, evaluation
        state += step
    raise ValueError('satellite clock replay exceeded its fixed evaluation limit')


def _replay(row, saved, navigation, ionosphere, clocks, anchors, charge):
    import numpy as np
    from . import gnss_position as gps

    seconds = row['gps_week_seconds']
    selected = _selected(row, saved, navigation)
    state = np.array([*saved['ecef_m'], saved['receiver_clock_m']], dtype=float)
    charge(bound_calls=1, bound_steps=1 + MAX_EVALUATIONS)
    step, rms = _range_step(state, selected, seconds, ionosphere)
    if np.linalg.norm(step) > 1e-4 or abs(rms - saved['range_rms_m']) > 1e-7:
        raise ValueError('sealed full-set broadcast solution did not reproduce')
    restricted = [item for item in selected if item['sv_id'] != EXCLUDED_PRN]
    control, control_rms, control_steps = _settle(state, restricted, seconds, ionosphere)
    differences = _differences(restricted, seconds, clocks)
    changes = {prn: value - anchors[str(prn)]['seconds'] for prn, value in differences.items()}
    adjusted = [item | dict(satellite_clock_s=item['satellite_clock_s'] + changes[item['sv_id']])
                for item in restricted]
    charge(bound_calls=1, bound_steps=MAX_EVALUATIONS)
    shifted, shifted_rms, shifted_steps = _settle(control, adjusted, seconds, ionosphere)
    rotation = gps.local_rotation(saved['latitude_rad'], saved['longitude_rad'])
    return dict(
        gps_week_seconds=seconds, passed=True, satellites=[item['sv_id'] for item in restricted],
        restricted_position=list(gps.geodetic(control[:3])),
        clock_adjusted_position=list(gps.geodetic(shifted[:3])),
        excluded_minus_full_neu_m=(rotation @ (control[:3] - state[:3])).tolist(),
        adjusted_minus_restricted_neu_m=(rotation @ (shifted[:3] - control[:3])).tolist(),
        maximum_clock_correction_range_m=max(abs(value) for value in changes.values()) * gps.C,
        control_rms_m=control_rms, adjusted_rms_m=shifted_rms,
        range_evaluations=1 + control_steps + shifted_steps,
    )


def evaluate(declared, context):
    start, end = (declared['payload'][key] for key in ('start', 'end'))
    if context.manifest['scope'] != SCOPE or end != _task(start)['payload']['end']:
        raise ValueError('unexpected clock replay block')
    records, baseline, navigation, ionosphere, clocks = _load(
        lambda key: context.input_path(key).read_bytes())
    anchors = json.loads(context.input_path('anchors').read_bytes())
    results = []
    for index in range(start, end):
        row = records[index]
        try:
            result = _replay(row, baseline[index]['dual_frequency'], navigation,
                             ionosphere, clocks, anchors, context.charge)
        except (ValueError, KeyError, ArithmeticError) as exc:
            result = dict(gps_week_seconds=row['gps_week_seconds'], passed=False, reason=str(exc))
        results.append(result)
    context.save_bytes('clock-epochs.json', encoded(results))
    passing = sum(row['passed'] for row in results)
    return dict(passed=passing == end - start, epochs=end - start, passing=passing,
                scientific_decision='abstain')


if __name__ == '__main__':
    if sys.argv[1:] != ['prepare']:
        raise SystemExit('usage: python -m lll.esa_relative_clock_replay prepare')
    prepare(Path.cwd())
