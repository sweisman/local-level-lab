# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test earlier-only transfer of the Qaqortoq satellite-range correction."""
import argparse
from contextlib import ExitStack, closing
import gzip
import json
from pathlib import Path
import subprocess

from . import esa_carrier_phase_continuous as path
from . import esa_nuuk_phase_transfer as nuuk
from . import esa_qaq_ground_score as qaq
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


ID = 'esa-qaq-phase-transfer-v1'
SCOPE = 'Earlier-only Qaqortoq one-second phase correction, development record 187'
PLAN = path.FOLDER+'ESA_QAQ_PHASE_TRANSFER_PLAN.md'
REQUEST = path.FOLDER+'esa-qaq-phase-transfer-qualification.json'
XML = path.FOLDER+'esa-qaq-phase-transfer-tests.xml'
RESULT = path.FOLDER+'esa-qaq-phase-transfer-result.json'
ARTIFACT = 'qaq-phase-transfer.json'
PARENT_SHA = '98251d43fbaed81aeb24cb3fd8555b74636fab0c1c982a296fb315772e68a185'
FIRST, LAST = 388215, 388550
COUNT = LAST-FIRST
TASK = dict(identity='qaq-phase-transfer', input_key='ground', payload=dict(training_seconds=COUNT),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=COUNT+2,
                        bound_steps=1+262*COUNT+120))


def transfer(training, withheld):
    """Estimate one multiplier with ragged satellite rows and disjoint times."""
    import numpy as np

    times = [t for t, _, _ in (*training, *withheld)]
    if (not training or not withheld or times != sorted(set(times)) or withheld[0][0]-training[-1][0] < 2):
        raise ValueError('disjoint chronological training and withheld epochs required')

    def flatten(rows):
        for _, a, g in rows:
            if len(a) != len(g) or not len(a):
                raise ValueError('finite aligned station and aircraft residuals required')
        air = np.concatenate([a for _, a, _ in rows])
        ground = np.concatenate([g for _, _, g in rows])
        if not np.isfinite(air).all() or not np.isfinite(ground).all():
            raise ValueError('finite aligned station and aircraft residuals required')
        return air, ground

    air, station = flatten(training)
    scale = station@station
    if scale <= 0.:
        raise ValueError('positive earlier station variation required')
    gain = float(air@station/scale)

    def rms(values):
        return float(np.sqrt(np.mean(values**2)))

    def compare(a, g):
        return dict(values=len(a), no_ground_rms_m=rms(a), ground_rms_m=rms(g), unit_ground_rms_m=rms(a-g),
                    earlier_gain_rms_m=rms(a-gain*g))

    return dict(trained_gain=gain, training=compare(air, station), withheld=compare(*flatten(withheld)))


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    tests = ('test_esa_qaq_phase_transfer.py', 'test_esa_qaq_ground_score.py', 'test_esa_nkar_score.py')
    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
                                    *(f'analysis/tests/{test}' for test in tests)))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=(
        'test_qaq_transfer_fits_earlier_rows_only_with_variable_satellite_counts',
        'test_qaq_transfer_refuses_a_later_interval_that_uses_a_training_epoch',
        'test_qaq_compares_only_the_frozen_dual_frequency_arc'), minimum_tests=6)
    return sources, environment


def prepare(root, converter):
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite Qaqortoq transfer study')
    sources, environment = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    raw = (root/path.RESULT).read_bytes()
    compact = (root/qaq.qaq.LOCAL/qaq.qaq.MEMBER).read_bytes()
    if digest(raw) != nuuk.PATH_SHA or digest(compact) != qaq.qaq.MEMBER_SHA:
        raise ValueError('the pinned continuous track and compact Qaqortoq source are required')
    expanded = subprocess.run([str(converter.resolve())], input=compact, capture_output=True, check=True).stdout
    if digest(expanded) != qaq.qaq.EXPANDED_SHA:
        raise ValueError('the original expanded Qaqortoq quarter-hour is required')
    with ExitStack() as stack:
        later, result = _parent(root, qaq.RESULT, PARENT_SHA, qaq.ID, qaq.TASK, qaq.ARTIFACT, stack)
        carrier = qaq.qaq.orbit
        phase, _ = _parent(root, carrier.RESULT, qaq.bound.PRODUCT_SHA, carrier.ID, carrier.TASK, carrier.ARTIFACT, stack)
        earlier = stack.enter_context(closing(ClosedStudy(root, 'data/'+path.ID)))
        if (earlier.completion['manifest_sha256'] != json.loads(raw)['study_manifest_sha256']
                or earlier.envelope(path.TASK['identity'])['charged'] != path.TASK['limits']
                or later.envelope(qaq.TASK['identity'])['charged'] != qaq.TASK['limits'] or len(result['intervals']) != 120):
            raise ValueError('exact complete earlier and later phase evidence is required')
        coordinates = earlier.artifact(path.TASK['identity'], 'carrier-path.json')['positions']
        values = {key: phase.input(key, raw=True) for key in ('rinex', 'navigation', 'clock', 'orbit', 'continuity')}
        if any(values[k] != earlier.input(k, raw=True) for k in ('rinex', 'navigation')):
            raise ValueError('the same aircraft observations and navigation are required')
        clock = earlier.input('clock')['result']['second_gps_seconds']
        if not LAST < clock < result['intervals'][0]['start_gps_s']:
            raise ValueError('the training interval and held-out block must exclude the clock step')
    values.update(ground=gzip.compress(expanded, mtime=0), path=encoded(coordinates), recovery=recovery,
                  recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, earlier=path.RESULT, later=qaq.RESULT, qualification=REQUEST, qualification_tests=XML)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=qaq.qaq.orbit.carrier.WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .esa_carrier_phase_support import phase_epochs
    from .esa_final_orbit_replay import interpolate_orbit
    from .esa_nkar_score import final_range_model
    from .esa_precise_gps_support import read_orbit_positions
    from .esa_relative_clock_replay import _clock_records
    from .esa_rinex_code import read_navigation
    from .esa_rinex_window import read_header
    from .fixed_reference_pair import coverage, observation_blocks
    from .shared_motion_carrier import centre

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen earlier correction test is required')
    context.charge(bound_calls=1, bound_steps=1)

    def read(name):
        return context.input_path(name).read_bytes()

    def product(name):
        return gzip.decompress(read(name)).decode('ascii')

    path_rows, flags, later = [json.loads(read(key)) for key in ('path', 'continuity', 'later')]
    by_time = {row['seconds']: row for row in path_rows}
    raw = gzip.decompress(read('rinex'))
    phase = list(phase_epochs(raw))
    headers, layout = read_header(raw)
    aircraft_codes = observation_blocks(raw[len(headers):], layout['observation_types']['G'])
    ground = gzip.decompress(read('ground'))
    _, body, gps = qaq.qaq.station_header(ground)
    ground_codes = observation_blocks(body, gps)
    times = range(FIRST, LAST+1)
    arc = coverage(aircraft_codes, ground_codes, week=qaq.qaq.WEEK, times=times, station_interval_s=1.)
    stations, antenna = qaq.decode_ground(ground, (FIRST, LAST))
    nav, atmosphere = read_navigation(product('navigation'))
    orbits, clocks = read_orbit_positions(product('orbit')), _clock_records(product('clock'))
    ground_model = final_range_model(nav, atmosphere, orbits, clocks, antenna)
    carrier = qaq.qaq.orbit.carrier

    def final_orbit(prn, seconds):
        return interpolate_orbit(orbits[prn], seconds)

    def aircraft_range(start, end):
        a, b = by_time[start], by_time[end]
        first, last = [phase[row['index']] for row in (a, b)]
        if [first['seconds'], last['seconds']] != [start, end]:
            raise ValueError('exact early half-second path and phase alignment required')
        prns = sorted(b['satellites'])
        _, common, _, clock, orbit, base = carrier.pair_signature(
            first, last, flags['result']['per_pair'][a['index']]['accepted_prns'], prns,
            (a['position'], b['position']), np.zeros((2, 3)), nav, clocks,
            ionosphere=atmosphere, final_orbit_position=final_orbit)
        return dict(zip((prns[i] for i in common), centre(base[common])-clock-orbit, strict=True))

    earlier, rows = [], []
    for t, row in zip(range(FIRST, LAST), arc[1:], strict=True):
        context.charge(bound_calls=1, bound_steps=262)
        first, second = aircraft_range(t, t+.5), aircraft_range(t+.5, t+1)
        eligible = {int(sv[1:]) for sv in row['continued']}
        ground_delta = qaq.reference_residual(stations[t], stations[t+1], first.keys() & second.keys(), eligible, ground_model)
        satellites = sorted(ground_delta)
        if len(satellites) >= 5:
            a = centre([first[prn]+second[prn] for prn in satellites]).tolist()
            g = centre([ground_delta[prn] for prn in satellites]).tolist()
            earlier.append((t, a, g))
            rows.append(dict(start_gps_s=t, satellites=satellites, aircraft_m=a, ground_m=g))
    context.charge(bound_calls=1, bound_steps=120)
    withheld = [(row['start_gps_s'], row['air_range_m'], row['ground_range_m']) for row in later['intervals']]
    result = transfer(earlier, withheld)
    gain = result['trained_gain']
    correction = gain*later['ground_score_equivalent']
    result.update(training_rows=rows, matched_training_intervals=len(rows), planned_training_intervals=COUNT,
                  matched_withheld_intervals=len(withheld), later_score_shift=-correction,
                  later_score_equivalent=later['aircraft_score_equivalent']-correction, score_gap=later['score_gap'],
                  new_fits=0, protected_reads=0, passed=True, scientific_decision='abstain')
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
            raise ValueError('sealed and complete distant ground transfer evidence required')
        _write_equal(root/RESULT, encoded(dict(result, later_sha256=PARENT_SHA, completion=study.completion)))
    return {key: value for key, value in result.items() if key != 'training_rows'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    parser.add_argument('--converter', type=Path)
    args = parser.parse_args()
    root = Path.cwd()
    if args.action == 'prepare':
        if args.converter is None:
            parser.error('prepare requires --converter')
        result = prepare(root, args.converter)
    elif args.action == 'request':
        result = qualification(root, False)
    elif args.action == 'recover':
        result = qaq.qaq.orbit.carrier.recover_signature(root, study_id=ID, task=TASK)
    else:
        result = report(root)
    print(json.dumps(result, sort_keys=True))
