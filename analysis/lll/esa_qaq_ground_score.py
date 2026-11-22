# SPDX-License-Identifier: AGPL-3.0-or-later
"""Use the distant Qaqortoq phase record on the frozen ESA 187 score."""
import argparse
from contextlib import ExitStack, closing
import gzip
import json
from pathlib import Path

from . import esa_carrier_score_bound as bound
from . import esa_nkar_score_study as nkar
from . import esa_qaq_ground_intake as qaq
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


ID = 'esa-qaq-ground-score-v1'
SCOPE = 'Distant Qaqortoq one-second carrier test on the frozen ESA 187 score'
PLAN = qaq.orbit.carrier.FOLDER+'ESA_QAQ_GROUND_SCORE_PLAN.md'
REQUEST = qaq.orbit.carrier.FOLDER+'esa-qaq-ground-score-qualification.json'
XML = qaq.orbit.carrier.FOLDER+'esa-qaq-ground-score-tests.xml'
RESULT = qaq.orbit.carrier.FOLDER+'esa-qaq-ground-score-result.json'
ARTIFACT = 'qaq-ground-score.json'
INTAKE_SHA = '0cd8b21d3015f105d750d29290016f3eac353e85d2ab65c6cab4cfaeeb82c6e8'
TASK = dict(nkar.TASK, identity='qaq-ground-score')


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    tests = ('test_esa_qaq_ground_score.py', 'test_esa_qaq_ground_intake.py', 'test_esa_nkar_score.py')
    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
                                    *(f'analysis/tests/{test}' for test in tests)))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=(
        'test_qaq_compares_only_the_frozen_dual_frequency_arc',
        'test_actual_coverage_projection_preserves_gaps_and_clock_invariance',
        'test_final_station_range_includes_clock_and_delay_with_expected_sign'), minimum_tests=6)
    return sources, environment


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite distant ground score study')
    sources, environment = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    receipt = (root/qaq.REPORT).read_bytes()
    if digest(receipt) != INTAKE_SHA or digest((root/qaq.EXCERPT).read_bytes()) != json.loads(receipt)['excerpt_sha256']:
        raise ValueError('the exact archived Qaqortoq intake is required')
    with ExitStack() as stack:
        orbit = qaq.orbit
        phase, _ = _parent(root, orbit.RESULT, bound.PRODUCT_SHA, orbit.ID, orbit.TASK, orbit.ARTIFACT, stack)
        score, _ = _parent(root, bound.RESULT, nkar.BOUND_SHA, bound.ID, bound.TASK, bound.ARTIFACT, stack)
        if (phase.envelope(orbit.TASK['identity'])['charged'] != orbit.TASK['limits']
                or score.envelope(bound.TASK['identity'])['charged'] != bound.TASK['limits']):
            raise ValueError('complete accounting for the parent evidence is required')
        values = {key: phase.input(key, raw=True) for key in ('navigation', 'orbit', 'clock')}
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, ground=qaq.EXCERPT.as_posix(), intake=qaq.REPORT, ranges=orbit.RESULT, score=bound.RESULT,
                  qualification=REQUEST, qualification_tests=XML)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=qaq.orbit.carrier.WALL_S), root).prepare(root)['limits']


def reference_residual(first, last, candidates, continued, model):
    from .esa_carrier_phase_support import (DUAL_DIFFERENCE_LIMIT_M, GAMMA, L1_DOPPLER_LIMIT_CYCLES,
                                            L1_WAVELENGTH, L2_WAVELENGTH)

    prns, codes, measured = [], [[], []], {}
    for prn in sorted(set(candidates) & continued):
        a, b = [row['satellites'][prn] for row in (first, last)]
        codes_m = [row['code_m'] for row in (a, b)]
        if (any(x is None or not 1e6 < x < 6e7 for x in codes_m)
                or any(row['l1'] is None or row['doppler'] is None or '2W' not in row['l2'] for row in (a, b))):
            continue
        if any(row['l1'][1] or row['l2']['2W'][1] for row in (a, b)):
            continue
        cycles = b['l1'][0]-a['l1'][0]
        d1 = L1_WAVELENGTH*cycles
        d2 = L2_WAVELENGTH*(b['l2']['2W'][0]-a['l2']['2W'][0])
        if (abs(cycles+(a['doppler']+b['doppler'])/2.) > L1_DOPPLER_LIMIT_CYCLES
                or abs(d1-d2) > DUAL_DIFFERENCE_LIMIT_M):
            continue
        prns.append(prn)
        codes[0].append(codes_m[0])
        codes[1].append(codes_m[1])
        measured[prn] = (GAMMA*d1-d2)/(GAMMA-1.)
    if not prns:
        return {}
    return {prn: measured[prn]-prediction for prn, prediction in model(first, last, prns, codes).items()}


def decode_ground(raw, window=qaq.SCORE_WINDOW):
    from .esa_carrier_phase_support import _fields
    from .esa_nkar_score import station_geometry

    header, body, gps = qaq.station_header(raw)
    layout = {}
    for line in header.decode('ascii').splitlines():
        label = line[60:].strip()
        if label in ('APPROX POSITION XYZ', 'ANTENNA: DELTA H/E/N'):
            key = 'approx_xyz_m' if label == 'APPROX POSITION XYZ' else 'antenna_delta_hen_m'
            layout[key] = [float(line[i:i+14]) for i in (0, 14, 28)]
    markers = qaq.epoch_offsets(body, offset=0)
    start, stop = window
    ends = [r[0] for r in markers[1:]]+[len(body)]
    selected = [(marker, end) for marker, end in zip(markers, ends, strict=True) if start <= marker[2] <= stop]
    if [(w, s) for (_, w, s, _, _), _ in selected] != [(qaq.WEEK, s) for s in range(start, stop+1)]:
        raise ValueError('the exact Qaqortoq window must reproduce')
    epochs = {}
    for (offset, week, sec, flag, count), end in selected:
        head, *lines = body[offset:end].decode('ascii').splitlines()
        if flag or len(lines) != count or len(head.split()) != 9:
            raise ValueError('normal Qaqortoq records without explicit epoch clock offsets required')
        epochs[sec] = dict(seconds=sec, week=week,
                           satellites={int(row[1:3]): _fields(row, gps) for row in lines if row.startswith('G')})
    return epochs, station_geometry(layout)


def evaluate(task, context):
    from .esa_nkar_score import compare_score, final_range_model
    from .esa_precise_gps_support import read_orbit_positions
    from .esa_relative_clock_replay import _clock_records
    from .esa_rinex_code import read_navigation

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen distant ground comparison is required')
    context.charge(bound_calls=1, bound_steps=1)

    def read(name):
        return context.input_path(name).read_bytes()

    def product(name):
        return gzip.decompress(read(name)).decode('ascii')

    intake, ranges, score = [json.loads(read(key)) for key in ('intake', 'ranges', 'score')]
    station, antenna = decode_ground(gzip.decompress(read('ground')))
    continuity = {row['time_s']: {int(sv[1:]) for sv in row['continued']} for row in intake['rows']}
    nav, atmosphere = read_navigation(product('navigation'))
    model = final_range_model(nav, atmosphere, read_orbit_positions(product('orbit')),
                              _clock_records(product('clock')), antenna)
    result = compare_score(ranges['rows'], score['bound']['dual_weights'], score['endpoint_gps_s'][0], station,
                           lambda a, b, prns: reference_residual(a, b, prns, continuity[b['seconds']], model),
                           before_interval=lambda: context.charge(bound_calls=1, bound_steps=64))
    result.update(score_gap=score['score_gap'], source=intake['source'], station=qaq.STATION,
                  approximate_distance_km=intake['approximate_distance_km'], new_fits=0, protected_reads=0,
                  aircraft_accuracy_established=False, scientific_decision='abstain', passed=True)
    context.save(ARTIFACT, result)
    return result


def report(root):
    from .studies.closed import ClosedStudy

    prefix, identity = 'data/'+ID, TASK['identity']
    with ExitStack() as stack:
        study = stack.enter_context(closing(ClosedStudy(root, prefix)))
        if (root/(prefix+'-recovery')).is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, root/(prefix+'-recovery'))['selected'][identity]['origin']
            if origin != prefix:
                study = stack.enter_context(closing(ClosedStudy(root, origin, store=study.store)))
        envelope, result = study.envelope(identity), study.artifact(identity, ARTIFACT)
        if envelope['charged'] != TASK['limits'] or envelope['result'] != result or not result['passed']:
            raise ValueError('sealed and complete distant ground evidence required')
        _write_equal(root/RESULT, encoded(dict(result, intake_sha256=INTAKE_SHA, completion=study.completion)))
    return {key: result[key] for key in ('matched_intervals', 'observable_norm_fraction', 'aircraft_score_equivalent',
                'ground_score_equivalent', 'air_minus_ground_score_equivalent', 'score_gap')}


if __name__ == '__main__':
    from functools import partial

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    actions = dict(request=partial(qualification, verify=False), prepare=prepare, report=report,
                   recover=partial(qaq.orbit.carrier.recover_signature, study_id=ID, task=TASK))
    print(json.dumps(actions[action](Path.cwd()), sort_keys=True))
