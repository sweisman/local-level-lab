# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare the two nearby Nuuk stations on the frozen ESA GPS score."""

import argparse
from contextlib import ExitStack, closing
import gzip
import json
import math
from pathlib import Path

from . import esa_nkar_score_study as museum
from . import esa_nuuk_highrate_intake as intake
from . import esa_qaq_ground_score as qaqortoq
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .esa_nkar_phase_transfer import PARENTS
from .esa_rinex_window import epoch_offsets, read_header
from .esa_two_station_score import minimum_station_error
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


ID = 'esa-nuuk-near-stations-v1'
SCOPE = 'Permanent Nuuk and Nuuk Museum on the same frozen ESA 187 score'
BASE = museum.carrier.FOLDER
PLAN = BASE + 'ESA_NUUK_NEAR_STATIONS_PLAN.md'
RESULT = BASE + 'esa-nuuk-near-stations-result.json'
INTAKE_SHA = '57ee63863da83ad379c9b63274ad9449948db98c2accd38b52087f4854ae29b0'
FIRST, LAST = museum.intake.SCORE_WINDOW
COUNT = LAST - FIRST
TASK = dict(identity='nuuk-near-stations', input_key='ground', payload={}, limits=dict(
    native_calls=0, packet_visits=0, bound_calls=1+COUNT+3, bound_steps=1+64*COUNT+3*COUNT))


def matched_rows(**stations):
    """Compare uniquely timed intervals on exactly the same satellite support."""
    import numpy as np

    from .shared_motion_carrier import centre

    if len(stations) < 2:
        raise ValueError('at least two ground stations required')
    tables = {}
    for name, rows in stations.items():
        table = {row['start_gps_s']: row for row in rows}
        if len(table) != len(rows) or any(row['stop_gps_s'] != t+1 for t, row in table.items()):
            raise ValueError('unique one-second ground intervals required')
        tables[name] = table
    output = []
    for time in sorted(set.intersection(*(set(table) for table in tables.values()))):
        rows = {name: table[time] for name, table in tables.items()}
        prns = sorted(set.intersection(*(set(row['satellites']) for row in rows.values())))
        if len(prns) < 5:
            continue

        def select(row, key):
            values = dict(zip(row['satellites'], row[key], strict=True))
            if len(values) != len(row['satellites']):
                raise ValueError('duplicate satellites in a saved interval')
            return centre([values[prn] for prn in prns])

        reference = next(iter(rows.values()))
        aircraft = select(reference, 'air_range_m')
        weights = select(reference, 'aggregate_weights')
        result = dict(start_gps_s=time, satellites=prns, weights=weights.tolist(), aircraft_m=aircraft.tolist())
        for name, row in rows.items():
            if not np.allclose(aircraft, select(row, 'air_range_m'), rtol=0., atol=1e-12):
                raise ValueError('saved aircraft observations disagree on common satellites')
            if not np.allclose(weights, select(row, 'aggregate_weights'), rtol=0., atol=1e-12):
                raise ValueError('saved score weights disagree on common satellites')
            result[name+'_m'] = select(row, 'ground_range_m').tolist()
        output.append(result)
    return output


def decode_ground(raw):
    from .esa_carrier_phase_support import _fields
    from .esa_nkar_score import station_geometry

    header, layout = read_header(raw, expected_interval=1., expected_systems=intake.SYSTEMS, expected_version='3.05')
    fields = {line[60:].strip(): line[:60] for line in header.splitlines()}
    if fields.get(b'MARKER NAME', b'').strip() != b'NUUK00GRL':
        raise ValueError('permanent Nuuk station required')
    for key, label in (('approx_xyz_m', b'APPROX POSITION XYZ'), ('antenna_delta_hen_m', b'ANTENNA: DELTA H/E/N')):
        value = fields[label]
        layout[key] = [float(value[i:i+14]) for i in (0, 14, 28)]
    body = raw[len(header):]
    markers = epoch_offsets(body, offset=0)
    ends = [row[0] for row in markers[1:]]+[len(body)]
    epochs = {}
    for (offset, week, sec, flag, count), end in zip(markers, ends, strict=True):
        if not FIRST <= sec <= LAST:
            continue
        head, *lines = body[offset:end].decode('ascii').splitlines()
        if week != intake.WEEK or flag or len(lines) != count or len(head.split()) != 9:
            raise ValueError('normal GPS epochs without explicit receiver clock offsets required')
        epochs[sec] = dict(seconds=sec, week=week, satellites={
            int(line[1:3]): _fields(line, layout['observation_types']['G']) for line in lines if line.startswith('G')})
    if list(epochs) != list(range(FIRST, LAST+1)):
        raise ValueError('the original permanent Nuuk comparison interval must reproduce')
    return epochs, station_geometry(layout)


def _verified(root, path, checksum):
    raw = (root/path).read_bytes()
    if digest(raw) != checksum:
        raise ValueError(f'frozen source differs: {path}')
    return raw


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the existing finite comparison')
    receipt = json.loads(_verified(root, intake.REPORT, INTAKE_SHA))
    _verified(root, intake.EXCERPT, receipt['excerpt_sha256'])
    _verified(root, museum.RESULT, PARENTS['later-nkar'][1])
    _verified(root, qaqortoq.RESULT, PARENTS['later-qaq'][1])
    orbit = museum.orbit
    _verified(root, museum.bound.RESULT, museum.BOUND_SHA)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        phase, _ = _parent(root, orbit.RESULT, museum.bound.PRODUCT_SHA, orbit.ID, orbit.TASK, orbit.ARTIFACT, stack)
        if phase.envelope(orbit.TASK['identity'])['charged'] != orbit.TASK['limits']:
            raise ValueError('complete source range accounting required')
        values = {key: phase.input(key, raw=True) for key in ('navigation', 'orbit', 'clock')}
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, ground=intake.EXCERPT, intake=intake.REPORT, museum=museum.RESULT,
                  qaqortoq=qaqortoq.RESULT, ranges=orbit.RESULT, score=museum.bound.RESULT)
    for key, raw in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, raw)
        inputs[key] = name
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, 'analysis/tests/test_esa_nuuk_near_stations.py'))
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=60)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def flatten(rows, field):
    return [value for row in rows for value in row[field]]


def _difference(a, b):
    return math.sqrt(math.fsum((x-y)**2 for x, y in zip(a, b, strict=True))/len(a))


def compare_frozen_score(context, *, ground_residual=qaqortoq.reference_residual, interval_steps=64):
    from .esa_nkar_score import compare_score, final_range_model
    from .esa_precise_gps_support import read_orbit_positions
    from .esa_relative_clock_replay import _clock_records
    from .esa_rinex_code import read_navigation

    context.charge(bound_calls=1, bound_steps=1)

    def read(name):
        return context.input_path(name).read_bytes()

    def product(name):
        return gzip.decompress(read(name)).decode('ascii')

    inputs, ranges, score, nkar, qaq = [json.loads(read(key)) for key in ('intake', 'ranges', 'score', 'museum', 'qaqortoq')]
    packed = read('ground')
    gap = score['score_gap']
    if (digest(packed) != inputs['excerpt_sha256'] or not gap > 0
            or gap != nkar['score_gap'] or gap != qaq['score_gap'] or score['endpoint_gps_s'] != [FIRST, LAST]):
        raise ValueError('identical frozen aircraft score and original station excerpt required')
    station, antenna = decode_ground(gzip.decompress(packed))
    arcs = {row['time_s']: {int(sv[1:]) for sv in row['continued']} for row in inputs['rows']}
    nav, atmosphere = read_navigation(product('navigation'))
    model = final_range_model(nav, atmosphere, read_orbit_positions(product('orbit')),
                              _clock_records(product('clock')), antenna)
    permanent = compare_score(ranges['rows'], score['bound']['dual_weights'], FIRST, station,
        lambda a, b, prns: ground_residual(a, b, prns, arcs[b['seconds']], model),
        before_interval=lambda: context.charge(bound_calls=1, bound_steps=interval_steps))
    return permanent, nkar, qaq, gap


def summarize_comparison(context, permanent, nkar, qaq, gap):
    sources = dict(museum=nkar['intervals'], permanent=permanent['intervals'])
    near = matched_rows(**sources)
    triple = matched_rows(**sources, qaqortoq=qaq['intervals'])
    if not near or not triple:
        raise ValueError('nonempty common nearby and three-station supports required')
    a, b, weights = [flatten(near, key) for key in ('museum_m', 'permanent_m', 'weights')]
    witnesses = {}
    for key, target in (('unrestricted', None), ('negative_gap', -gap), ('positive_gap', gap)):
        context.charge(bound_calls=1, bound_steps=COUNT)
        witnesses[key] = minimum_station_error(a, b, weights, target=target)
    three = [flatten(triple, field) for field in ('museum_m', 'permanent_m', 'qaqortoq_m')]
    context.save('shared-range-evidence.json', dict(near=near, triple=triple, witnesses=witnesses))
    return dict(passed=True, scientific_decision='abstain', recording=187, score_gap=gap,
        planned_intervals=COUNT, permanent_intervals=permanent['matched_intervals'], nearby_intervals=len(near),
        nearby_ranges=len(a), minimum_nearby_satellites=min(len(row['satellites']) for row in near),
        nearby_difference_rms_m=_difference(a, b),
        nearby_shares={key: math.fsum(w*x for w, x in zip(weights, values, strict=True))/gap
                       for key, values in (('museum', a), ('permanent', b))},
        triple_intervals=len(triple), triple_ranges=len(three[0]),
        triple_rms_m=dict(museum_permanent=_difference(three[0], three[1]),
                          museum_qaqortoq=_difference(three[0], three[2]),
                          permanent_qaqortoq=_difference(three[1], three[2])),
        cases={key: {name: item for name, item in value.items() if name != 'common'} for key, value in witnesses.items()},
        new_fits=0, original_downloads=0, protected_reads=0, independent_aircraft_error_cap_established=False)


def evaluate(task, context):
    if (context.manifest['scope'] != SCOPE
            or {key: val for key, val in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('the frozen permanent Nuuk comparison is required')
    return summarize_comparison(context, *compare_frozen_score(context))


def report(root):
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('the complete charged nearby-station comparison is required')
        summary = dict(envelope['result'], completion=study.completion, charged=envelope['charged'],
                       sources=study.manifest['inputs'])
        evidence = study.artifact(TASK['identity'], 'shared-range-evidence.json')
    _write_equal(root/RESULT, encoded(dict(summary, evidence=evidence)))
    return {key: value for key, value in summary.items() if key != 'sources'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    print(json.dumps({'prepare': prepare, 'report': report}[parser.parse_args().action](Path.cwd()), sort_keys=True))
