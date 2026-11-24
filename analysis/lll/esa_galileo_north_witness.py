# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the saved GPS north-only displacement against the raw Galileo carriers."""

import argparse
from contextlib import closing
from fractions import Fraction
import gzip
import json
from pathlib import Path

from . import esa_galileo_phase_path as galileo
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-galileo-north-witness-v1'
SCOPE = 'ESA 187 fixed GPS north-only displacement replay on the original Galileo carrier phases'
FOLDER = galileo.FOLDER
PLAN = FOLDER+'ESA_GALILEO_NORTH_WITNESS_PLAN.md'
RESULT = FOLDER+'esa-galileo-north-witness-result.json'
START, END = 388614, 388734
PARENTS = {
    'galileo': (galileo.RESULT, '362dacd2021256c7d6a9a11103f85fd0bfe5045ea8fd16500eefa0d1ee494c0d'),
    'axis': (FOLDER+'esa-motion-axis-support-result.json',
             '046621104bcf9a3d000bd338655832e06ccaa5a7c99c90374022dbf53018bc40'),
    'witness': (FOLDER+'esa-nuuk-between-samples-result.json',
                '2baf051f00af95e8ec9021bcdd84bda30fef442c61158b8e2d8b015518e64f75'),
    'horizontal': (FOLDER+'esa-girafe-horizontal-witness-result.json',
                   'b3bc6462ee236179f8918a7e585c788bf79c5ce55878a229f37a06ef46e790ed'),
}
TASK = dict(identity='galileo-fixed-north', input_key='mosaic03', payload={}, limits=dict(
    native_calls=0, packet_visits=0, bound_calls=END-START, bound_steps=80*(END-START)))


def compare_ranges(measured, original, shifted):
    import numpy as np

    from .shared_motion_carrier import centre

    m, a, b = map(lambda values: np.asarray(values, float), (measured, original, shifted))
    if (m.ndim != 1 or not len(m) or m.shape != a.shape or m.shape != b.shape
            or any(not np.isfinite(values).all() for values in (m, a, b))):
        raise ValueError('matching finite range changes are required')
    return centre(m-a), centre(m-b), centre(b-a)


def prepare(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('retain the original finite Galileo replay')
    reports = {}
    for key, (path, sha) in PARENTS.items():
        raw = (root/path).read_bytes()
        if digest(raw) != sha:
            raise ValueError('the exact development receipt is required: '+path)
        reports[key] = json.loads(raw)
    with closing(ClosedStudy(root, 'data/'+galileo.ID)) as parent:
        envelope = parent.envelope(galileo.TASK['identity'])
        if (parent.completion['manifest_sha256'] != reports['galileo']['manifest_sha256']
                or envelope['charged'] != galileo.TASK['limits'] or not envelope['result']['passed']):
            raise ValueError('the original complete Galileo reception is required')
        saved = parent.artifact(galileo.TASK['identity'], 'galileo-paths.json')['records']
        expected = [[row['seconds'], row['accepted']] for row in saved if START <= row['seconds'] < END]
        if [second for second, _ in expected] != list(range(START, END)):
            raise ValueError('the sealed Galileo support must cover all fixed seconds')
        values = {key: parent.input(key, raw=True) for key in (*galileo.RECEIVERS, 'track', 'orbit', 'clock')}
        values['support'] = encoded(expected)
        with closing(ClosedStudy(root, 'data/esa-girafe-horizontal-witness-v1', store=parent.store)) as horizontal:
            if horizontal.completion != reports['horizontal']['completion'] or not horizontal.summary['passed']:
                raise ValueError('the original horizontal-witness metric and clock are required')
            values.update({key: horizontal.input(key, raw=True) for key in ('anchor', 'metric')})
    inputs = dict(plan=PLAN, **{key: p for key, (p, _) in PARENTS.items()})
    for key, raw in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, raw)
        inputs[key] = name
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=[TASK],
        sources=source_closure(root, (adapter, PLAN, 'analysis/tests/test_esa_galileo_north_witness.py')),
        workers=1, threads=1, maximum_wall_s=60.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def _receiver_path(data):
    import numpy as np

    from .gnss_position import ecef
    from .shared_motion_carrier import displacement_at

    start = data('anchor')['time_s']
    north_metric = data('metric')[0]
    fraction = data('axis')['energy_fraction']['north']
    archived = data('witness')['knots']
    knots = [dict(elapsed_s=float(Fraction(row['elapsed_s_exact'])), position_m=row['position_m'],
                  velocity_mps=row['speed_mps']) for row in archived]
    acceleration = np.asarray([[float(Fraction(v)) for v in row['acceleration_exact_mps2']] for row in archived])
    rows = [row for row in data('track')['positions'] if START <= row['seconds'] <= END and row['seconds'] % 1 == 0]
    if (len(knots) != 125 or not 0 < fraction <= 1 or not north_metric > 0
            or [row['seconds'] for row in rows] != list(range(START, END+1))):
        raise ValueError('the frozen north path and integer-second GPS baseline are required')
    positions = np.asarray([row['position'] for row in rows])
    distance = np.asarray([displacement_at(knots, t-start, acceleration)[0]/fraction for t in range(START, END+1)])
    changed = positions.copy()
    changed[:, 0] += distance/north_metric
    return tuple(np.asarray([ecef(*p) for p in points]) for points in (positions, changed)), distance


def _predicted(positions, endpoints):
    import numpy as np

    from .gnss_carrier_phase import _geometry

    modeled = []
    for rx, records in zip(positions, endpoints, strict=True):
        states, offsets = map(np.asarray, zip(*records, strict=True))
        delays = galileo.atmosphere(rx, states)
        if None in delays:
            raise ValueError('a fixed candidate leaves the original Galileo elevation mask')
        ranges, _ = _geometry(rx, states)
        modeled.append(ranges-galileo.C*offsets+np.asarray(delays))
    return modeled[1]-modeled[0]


def evaluate(task, context):
    import numpy as np

    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('the frozen north-path replay is required')

    def data(key):
        return json.loads(context.input_path(key).read_bytes())

    with gzip.open(context.input_path('orbit'), 'rt', encoding='ascii') as stream:
        orbit, _ = galileo.read_orbit(iter(stream))
    with gzip.open(context.input_path('clock'), 'rt', encoding='ascii') as stream:
        clocks = galileo.read_clock(iter(stream))
    tables = galileo.receiver_epoch_tables(context)
    support = data('support')
    if [time for time, _ in support] != list(range(START, END)):
        raise ValueError('the exact earlier satellite support must be preserved')
    rows = {name: [] for name in tables}
    for i, (second, prns) in enumerate(support):
        context.charge(bound_calls=1, bound_steps=80)
        if i == 0:
            (original, shifted), distance = _receiver_path(data)
        before, after = original[i:i+2], shifted[i:i+2]
        paired, _ = galileo.step_inputs(tables, second, orbit, clocks, before)
        if list(paired) != prns or not 5 <= len(prns) <= 20:
            raise ValueError('the exact published Galileo support did not reproduce')
        for side, name in enumerate(tables):
            measured = [phase[side] for phase, _ in paired.values()]
            endpoints = tuple(zip(*(state[side] for _, state in paired.values()), strict=True))
            a, b, change = compare_ranges(measured, _predicted(before, endpoints), _predicted(after, endpoints))
            rows[name].append(dict(time_gps_s=second, satellites=prns, original_m=a.tolist(),
                                   shifted_m=b.tolist(), predicted_shift_m=change.tolist()))
    summaries = {}
    for name, observed in rows.items():
        a, b, shift = (np.concatenate([r[key] for r in observed])
                       for key in ('original_m', 'shifted_m', 'predicted_shift_m'))
        rms = lambda value: float(np.sqrt(np.mean(value**2)))
        summaries[name] = dict(ranges=len(a), original_rms_m=rms(a), shifted_rms_m=rms(b),
                               predicted_shift_rms_m=rms(shift), signed_residual_scale=float((a@shift)/(shift@shift)))
    context.save('galileo-signed-ranges.json', rows)
    return dict(passed=True, scientific_decision='abstain', independent_aircraft_error_cap_established=False,
                first_gps_s=START, last_gps_s=END, intervals=END-START, summaries=summaries,
                peak_sampled_north_shift_m=float(np.max(np.abs(distance))),
                new_fits=0, original_downloads=0, protected_reads=0)


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('the complete charged Galileo witness replay is required')
        summary = dict(envelope['result'], completion=study.completion, charged=envelope['charged'],
                       inputs=study.manifest['inputs'])
        residuals = study.artifact(TASK['identity'], 'galileo-signed-ranges.json')
    _write_equal(root/RESULT, encoded(dict(summary, residuals=residuals)))
    return {key: value for key, value in summary.items() if key != 'inputs'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    print(json.dumps({'prepare': prepare, 'report': report}[parser.parse_args().action](Path.cwd()), sort_keys=True))
