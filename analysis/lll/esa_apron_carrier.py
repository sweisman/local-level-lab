# SPDX-License-Identifier: AGPL-3.0-or-later
"""Measure ESA 187 GPS range residuals against a fixed Nuuk apron position."""

import argparse
from contextlib import closing
import gzip
import json
import math
from pathlib import Path

from . import esa_rinex_window as source
from .studies.artifacts import digest, encoded


ID = 'esa-apron-carrier-v2'
SCOPE = 'ESA 187 fixed-position carrier check on the sealed Nuuk apron prefix'
FOLDER = source.FOLDER
PLAN = FOLDER+'ESA_APRON_CARRIER_CLOCK_PLAN.md'
STOPPED = FOLDER+'esa-apron-carrier-v1-terminal.json'
RESULT = FOLDER+'esa-apron-carrier-result.json'
PREFIX = source.LOCAL+'/rinex-400-120-stream/prefix.bin'
TIE = FOLDER+'esa-girafe-ground-ties-result.json'
GROUND = FOLDER+'ground-imu-rate-result.json'
PRODUCTS = 'data/esa-nkar-ground-score-v1'
PRODUCT_MANIFEST = 'b8ce7324cacdbdc2d2d2b39c17a9778311883637718d3372fbde7cb9d2ddae7f'
PRODUCT_SUMMARY = '27e74822ed62e82e63742693f297bee979c4468d9439d8dda331e86cefeea2bf'
FIRST, LAST = 383697., 383715.5
PAIRS = int(2*(LAST-FIRST))
TASK = dict(identity='fixed-apron-ranges', input_key='prefix', payload={},
            limits=dict(native_calls=0, packet_visits=0, bound_calls=1+7*PAIRS,
                        bound_steps=1+7*PAIRS*66))


def rms_steps(pairs):
    """Center half-second and non-overlapping one-second ranges on their own support."""
    from .shared_motion_carrier import centre

    def result(rows):
        blocks = [centre(list(row.values())) for row in rows if len(row) >= 2]
        count = sum(map(len, blocks))
        squared = math.fsum(float(values@values) for values in blocks)
        return dict(intervals=len(blocks), ranges=count, rms_m=math.sqrt(squared/count) if count else None)

    return {'half_second': result(pairs), 'one_second': result(one_second_ranges(pairs))}


def one_second_ranges(pairs):
    return [{prn: a[prn]+b[prn] for prn in sorted(a.keys() & b.keys())}
            for a, b in zip(pairs[::2], pairs[1::2])]


def corrected_receive(epoch, codes, offset):
    from .gnss_position import C

    return dict(epoch, seconds=epoch['seconds']-offset), [code-C*offset for code in codes]


def prepare(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the original finite apron check')
    references = {
        'prefix': (PREFIX, source.PREFIX_SHA),
        'tie': (TIE, 'bf717afbfb617995c5209519f722f9e0f929121a2115a1c9e945d5b65c5d2153'),
        'ground': (GROUND, 'e587348ea92fd3918183bd2b7986e959b4038e77134fc1ded72396fd4e8a12e3'),
    }
    inputs = {'plan': PLAN}
    for name, (path, sha) in references.items():
        if digest((root/path).read_bytes()) != sha:
            raise ValueError('source hash differs: '+path)
        inputs[name] = path
    with closing(ClosedStudy(root, 'data/esa-apron-carrier-v1')) as study:
        stopped = study.envelope(TASK['identity'])
        if (study.completion['state'] != 'terminal' or stopped['charged']['bound_calls'] != 1
                or stopped['result']['reason'] != 'unexpected recorded receiver time offset'):
            raise ValueError('the original pre-score stop must be preserved')
        _write_equal(root/STOPPED, encoded(dict(completion=study.completion, terminal_result=stopped)))
        inputs['stopped'] = STOPPED
    with closing(ClosedStudy(root, PRODUCTS)) as study:
        if study.completion != dict(state='complete', manifest_sha256=PRODUCT_MANIFEST, summary_sha256=PRODUCT_SUMMARY):
            raise ValueError('the original matched station and aircraft products are required')
        study.envelope('nkar-ground-score')
        for key in ('navigation', 'orbit', 'clock'):
            path = f'data/{ID}-inputs/{key}'
            _write_equal(root/path, study.input(key, raw=True))
            inputs[key] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, 'analysis/tests/test_esa_apron_carrier.py'))
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=60)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def load_apron(raw):
    import numpy as np

    from .esa_carrier_phase_support import phase_epochs
    from .esa_precise_gps_support import read_orbit_positions
    from .esa_relative_clock_replay import _clock_records
    from .esa_rinex_code import read_navigation
    from .gnss_position import ecef, local_rotation

    def product(key):
        return gzip.decompress(raw(key)).decode('ascii')

    aircraft = raw('prefix')
    tie, parked = (json.loads(raw(key)) for key in ('tie', 'ground'))
    stop = tie['ground_stops'][0]
    selection = parked['receiver_selection_time_s']
    if (stop['airport'] != 'GOH' or not selection[0] <= FIRST < LAST <= selection[1]
            or LAST >= parked['imu_overlap_time_s'][0]):
        raise ValueError('the receiver-selected Nuuk stop must cover the exact prefix window')
    header, _ = source.read_header(aircraft)
    declared = [line[:6].strip() for line in header.splitlines()
                if line[60:].strip() == b'RCV CLOCK OFFS APPL']
    if declared not in ([], [b'0']):
        raise ValueError('only the unapplied receiver clock convention is qualified')
    markers = source.epoch_offsets(aircraft[len(header):], offset=len(header))
    offsets = {row[2]: row[0] for row in markers if row[1] == source.WEEK}
    if FIRST not in offsets or LAST+.5 not in offsets:
        raise ValueError('a complete following epoch marker is required')
    body = aircraft[offsets[FIRST]:offsets[LAST+.5]]
    epoch_fields = [line.split() for line in body.splitlines() if line.startswith(b'> ')]
    if any(len(fields) != 10 for fields in epoch_fields):
        raise ValueError('all retained epochs need a recorded clock offset')
    clock_offsets = [float(fields[9]) for fields in epoch_fields]
    if (any(not math.isfinite(value) or abs(value) > .001 for value in clock_offsets)
            or any(abs(b-a) > 2e-6 for a, b in zip(clock_offsets, clock_offsets[1:]))):
        raise ValueError('clock correction exceeds the frozen offset or step limits')
    epochs = list(phase_epochs(header+body, first=FIRST, last=LAST))
    ref = stop['airport_reference']
    lat, lon = map(math.radians, (ref['latitude_deg'], ref['longitude_deg']))
    rotation = local_rotation(lat, lon)
    nominal = ecef(lat, lon, ref['height_m'])+rotation.T@np.asarray(stop['antenna_neu_from_reference_m'])
    navigation, atmosphere = read_navigation(product('navigation'))
    orbits = read_orbit_positions(product('orbit'))
    clocks = _clock_records(product('clock'))
    return epochs, clock_offsets, nominal, rotation, (navigation, atmosphere, orbits, clocks)


def calculate_residuals(epochs, clock_offsets, model, before_pair):
    from .esa_carrier_phase_support import pair_satellites
    from .gnss_position import C

    residuals = []
    unmodeled = set()
    for first, last, delta_a, delta_b in zip(
            epochs[:-1], epochs[1:], clock_offsets[:-1], clock_offsets[1:], strict=True):
        before_pair()
        signals, _ = pair_satellites(first, last)
        if len(signals) > 16:
            raise ValueError('the frozen satellite ceiling was exceeded')
        predicted = {}
        if signals:
            codes = list(zip(*(row['broadcast_input_code_m'] for row in signals.values())))
            a, a_codes = corrected_receive(first, codes[0], delta_a)
            b, b_codes = corrected_receive(last, codes[1], delta_b)
            predicted = model(a, b, list(signals), [a_codes, b_codes])
        unmodeled.update(set(signals)-set(predicted))
        common_phase = C*(delta_b-delta_a)
        residuals.append({prn: signals[prn]['ionosphere_free_displacement_m']-common_phase-value
                          for prn, value in predicted.items()} if len(predicted) >= 5 else {})
    return residuals, unmodeled


def evaluate(task, context):
    import numpy as np

    from .esa_nkar_score import final_range_model

    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('the frozen apron range check is required')
    context.charge(bound_calls=1, bound_steps=1)

    def raw(key):
        return context.input_path(key).read_bytes()

    epochs, clock_offsets, nominal, rotation, products = load_apron(raw)
    _, _, orbits, clocks = products
    names = ('nominal', 'north_plus', 'east_plus', 'up_plus', 'north_minus', 'east_minus', 'up_minus')
    shifts = [np.zeros(3), *list(5*np.eye(3)), *list(-5*np.eye(3))]
    rows = {}
    for name, shift in zip(names, shifts, strict=True):
        model = final_range_model(*products, nominal+rotation.T@shift)
        residuals, unmodeled = calculate_residuals(
            epochs, clock_offsets, model, lambda: context.charge(bound_calls=1, bound_steps=66))
        rows[name] = dict(**rms_steps(residuals), unmodeled_prns=sorted(unmodeled),
                          prns_without_final_products=sorted(unmodeled-(set(orbits)&set(clocks))))
    context.save('apron-residuals.json', rows)
    return dict(passed=True, scientific_decision='abstain', aircraft_error_cap_established=False,
                first_gps_s=FIRST, last_gps_s=LAST, epochs=len(epochs), nominal=rows['nominal'], cases=rows,
                receiver_clock_offset_s=[min(clock_offsets), max(clock_offsets)],
                original_downloads=0, protected_reads=0, new_fits=0)


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('the complete charged apron check is required')
        result = dict(envelope['result'], completion=study.completion, inputs=study.manifest['inputs'],
                      charged=envelope['charged'])
    _write_equal(root/RESULT, encoded(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    print(json.dumps({'prepare': prepare, 'report': report}[parser.parse_args().action](Path.cwd()), sort_keys=True))
