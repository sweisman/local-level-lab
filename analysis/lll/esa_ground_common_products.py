# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare Nuuk and Qaqortoq using one saved aircraft path and product set."""

import argparse
from contextlib import ExitStack, closing
import gzip
import json
import math
from pathlib import Path

from . import esa_ground_cadence_comparison as prior
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-ground-common-products-v1'
SCOPE = 'Matched 30-second ground reference products on ESA development flight 187'
PLAN = prior.BASE+'ESA_GROUND_COMMON_PRODUCTS_PLAN.md'
RESULT = prior.BASE+'esa-ground-common-products-result.json'
REQUEST = prior.BASE+'esa-ground-common-products-qualification.json'
XML = prior.BASE+'esa-ground-common-products-tests.xml'
TEST = 'analysis/tests/test_esa_ground_common_products.py'
TESTS = ('test_two_band_change_subtracts_geometry_with_the_correct_sign',
         'test_matching_centres_both_ground_stations_against_the_same_aircraft')
ARTIFACT = 'comparison.json'
PAIRED = prior.BASE+prior.OUTPUT
PAIRED_SHA = '4766fca39254d1b638209f87341a0c4c20209ba8fde6ba341634f51e32c41cd8'
INTERVALS = len(prior.EARLIER)+len(prior.LATER)
TASK = dict(identity='common-ground-products', input_key='paired', payload=dict(intervals=INTERVALS),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=1+INTERVALS, bound_steps=1+22*INTERVALS))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources, environment


def prepare(root):
    from . import esa_nuuk_phase_transfer as nuuk
    from . import esa_qaq_ground_score as qaq
    from . import esa_qaq_phase_transfer as early
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the frozen common product allowance')
    sources, environment = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    if digest((root/PAIRED).read_bytes()) != PAIRED_SHA:
        raise ValueError('the exact saved cadence comparison is required')
    with ExitStack() as stack:
        parents = []
        for module in (nuuk, early, qaq):
            sha = prior.SOURCES[Path(module.RESULT).name]
            study, _ = _parent(root, module.RESULT, sha, module.ID, module.TASK, module.ARTIFACT, stack)
            if study.envelope(module.TASK['identity'])['charged'] != module.TASK['limits']:
                raise ValueError('complete parent accounting required')
            parents.append(study)
        near, early_far, later_far = parents
        values = {key: later_far.input(key, raw=True) for key in ('navigation', 'orbit', 'clock')}
        if any(early_far.input(key, raw=True) != value for key, value in values.items()):
            raise ValueError('both Qaqortoq blocks must use the same satellite products')
        values['ground'] = near.input('ground', raw=True)
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, paired=PAIRED, qualification=REQUEST, qualification_tests=XML)
    for name, value in values.items():
        name_path = f'data/{ID}-inputs/{name}'
        _write_equal(root/name_path, value)
        inputs[name] = name_path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=inputs,
                      sources=sources, tasks=[TASK], workers=1, threads=1, maximum_wall_s=90)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def phase_residual(first, last, modeled_change):
    from .esa_carrier_phase_support import L1_WAVELENGTH, L2_WAVELENGTH
    from .gnss_position import GAMMA

    l1 = (last[0]-first[0])*L1_WAVELENGTH
    l2 = (last[1]-first[1])*L2_WAVELENGTH
    return (GAMMA*l1-l2)/(GAMMA-1.)-modeled_change


def match_products(row, near_ranges):
    indices = {prn: i for i, prn in enumerate(row['satellites'])}
    prns = sorted(indices.keys() & near_ranges.keys())
    if len(prns) < 5:
        return None

    def center(values):
        mean = math.fsum(values)/len(values)
        return [v-mean for v in values]

    def saved(key):
        return center([row[key][indices[prn]] for prn in prns])

    aircraft = saved('qaq_aircraft_m')
    return dict(start_gps_s=row['start_gps_s'], satellites=prns, nuuk_aircraft_m=aircraft, qaq_aircraft_m=aircraft,
                qaq_ground_m=saved('qaq_ground_m'), nuuk_broadcast_ground_m=saved('nuuk_ground_m'),
                nuuk_ground_m=center([near_ranges[prn] for prn in prns]))


def _ground_input(raw, times):
    from .esa_fixed_reference_phase import unpack
    from .esa_nkar_score import station_geometry
    from .esa_nuuk_ground_intake import SYSTEMS
    from .esa_nuuk_phase_study import PRNS
    from .esa_rinex_window import read_header

    header, _ = read_header(raw, expected_interval=30., expected_systems=SYSTEMS, expected_version='3.05')
    records, phases, (marker, clock_applied) = unpack(raw, times, list(PRNS), station=True,
                                                       station_version='3.05', station_systems=SYSTEMS)
    offsets = [list(map(float, line[:60].split())) for line in header.decode('ascii').splitlines()
               if line[60:].strip() == 'ANTENNA: DELTA H/E/N']
    if len(offsets) != 1 or (not clock_applied and any(r['receiver_clock_offset_s'] for r in records)):
        raise ValueError('a single antenna offset and no unapplied receiver clock offset required')
    antenna = station_geometry(dict(approx_xyz_m=marker, antenna_delta_hen_m=offsets[0]))
    data = {}
    for row, cycles in zip(records, phases, strict=True):
        time = row['gps_week_seconds']
        code = {sat['sv_id']: signal['pseudorange_m'] for sat in row['satellites'] for signal in sat['signals']
                if (signal['band'], signal['track_type']) == (0, 0) and 1e6 < signal['pseudorange_m'] < 6e7}
        data[time] = (dict(week=row['gps_week'], seconds=time), code, dict(zip(PRNS, cycles, strict=True)))
    return data, antenna


def evaluate(task, context):
    from .esa_nkar_score import final_range_model
    from .esa_precise_gps_support import read_orbit_positions
    from .esa_relative_clock_replay import _clock_records
    from .esa_rinex_code import read_navigation

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the single frozen matched ground task is required')
    context.charge(bound_calls=1, bound_steps=1)

    def product(name):
        return gzip.decompress(context.input_path(name).read_bytes())

    raw = context.input_path('paired').read_bytes()
    if digest(raw) != PAIRED_SHA:
        raise ValueError('same archived time intervals and aircraft path required')
    original = json.loads(raw)
    starts = [*prior.EARLIER, *prior.LATER]
    if [row['start_gps_s'] for row in original['earlier']+original['later']] != starts:
        raise ValueError('all planned earlier and later intervals are required')
    times = sorted(set(starts) | {s+30 for s in starts})
    ground, antenna = _ground_input(product('ground'), times)
    nav, atmosphere = read_navigation(product('navigation').decode('ascii'))
    orbits = read_orbit_positions(product('orbit').decode('ascii'))
    clocks = _clock_records(product('clock').decode('ascii'))
    model = final_range_model(nav, atmosphere, orbits, clocks, antenna)
    earlier, later, missing = [], [], []
    for group, matched in ((original['earlier'], earlier), (original['later'], later)):
        for row in group:
            context.charge(bound_calls=1, bound_steps=22)
            start = row['start_gps_s']
            first, first_code, first_phases = ground[start]
            last, last_code, last_phases = ground[start+30]
            prns = sorted(set(row['satellites']) & first_code.keys() & last_code.keys())
            ranges = model(first, last, prns, [[code[p] for p in prns] for code in (first_code, last_code)])
            residuals = {p: phase_residual(first_phases[p], last_phases[p], value) for p, value in ranges.items()}
            control = match_products(row, residuals)
            if control is None:
                missing.append(start)
            else:
                matched.append(control)

    if not earlier or not later:
        raise ValueError('the comparison needs matched support in both blocks')
    changes = [a-b for row in later for a, b in zip(row['nuuk_ground_m'], row['nuuk_broadcast_ground_m'], strict=True)]
    metrics = prior._summarize(earlier, later)
    result = dict(earlier=earlier, later=later, unavailable_starts_gps_s=missing, metrics=metrics,
                  later_nuuk_product_change_rms_m=math.sqrt(math.fsum(x*x for x in changes)/len(changes)),
                  new_fits=0, protected_reads=0, scientific_decision='abstain', passed=True)
    context.save(ARTIFACT, result)
    return result


def report(root):
    from .studies.combined_task_evidence import inspect

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    if continuation.is_dir():
        prefix = inspect(root, continuation)['selected'][TASK['identity']]['origin']
    with closing(ClosedStudy(root, prefix)) as study:
        identity = TASK['identity']
        envelope, result = study.envelope(identity), study.artifact(identity, ARTIFACT)
        if envelope['charged'] != TASK['limits'] or envelope['result'] != result or not result['passed']:
            raise ValueError('sealed exact common ground accounting is required')
        output = encoded(dict(result, completion=study.completion))
        _write_equal(root/RESULT, output)
    return dict(sha256=digest(output), earlier=len(result['earlier']), later=len(result['later']),
                metrics=result['metrics'], later_nuuk_product_change_rms_m=result['later_nuuk_product_change_rms_m'])


def main():
    from .esa_shared_motion_carrier import recover_signature

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report', 'recover'))
    action = parser.parse_args().action
    root = Path.cwd()
    if action == 'request':
        result = qualification(root, verify=False)
    elif action == 'prepare':
        result = prepare(root)
    elif action == 'recover':
        result = recover_signature(root, study_id=ID, task=TASK)
    else:
        result = report(root)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
