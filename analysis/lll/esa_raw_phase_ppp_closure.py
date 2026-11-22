# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare signed PPP changes with archived raw GPS carrier contrasts."""

import argparse
from contextlib import ExitStack, closing
import gzip
import json
import math
from pathlib import Path

from .esa_carrier_phase_continuous import ID as ORBITS
from .esa_forecast_receiver_transfer import BASE, PPP_AUDIT, PPP_SHA, RECOVER, RECOVERY, WALL_S
from .esa_parallel_raw_receiver import ID as CARRIER
from .esa_parallel_raw_receiver import FIRST_SHARED, INTERVALS, LAST_SHARED, PAIRS, RESULT as PRIOR
from .esa_parallel_raw_receiver import TASK as CARRIER_TASK
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-raw-phase-ppp-closure-v1'
SCOPE = 'ESA 187 same-antenna PPP position changes versus raw carrier phase contrasts'
PLAN = BASE+'ESA_RAW_PHASE_PPP_CLOSURE_PLAN.md'
RESULT = BASE+'esa-raw-phase-ppp-closure-result.json'
REQUEST = BASE+'esa-raw-phase-ppp-closure-qualification.json'
REPORT = BASE+'esa-raw-phase-ppp-closure-tests.xml'
TEST = 'analysis/tests/test_esa_raw_phase_ppp_closure.py'
TESTS = (
    'test_reported_velocity_corrects_receiver_to_shared_epoch',
    'test_satellite_projection_uses_signed_motion_and_clock_invariance',
    'test_endpoint_geometry_change_is_kept_even_for_constant_receiver_offset',
)
PRIOR_SHA = '203f383949f94620e1d306d32e159996157afc077a423915253d8b456ba58196'
ORBITS_MANIFEST = '93fcfc884ffe80067ae434f2d6a9abdb272337c732847a2541d620b768781d43'
PORTIONS = ('earlier', 'later')


def corrected_position(row, second, *, tolerance=.002):
    import numpy as np
    from .gnss_position import ecef, local_rotation

    offset = row['time_s']-second
    if not math.isfinite(offset) or abs(offset) > tolerance:
        raise ValueError('receiver epoch exceeds the original time tolerance')
    latitude, longitude = (math.radians(row[name]) for name in ('latitude_deg', 'longitude_deg'))
    velocity = np.asarray([row[name] for name in ('north_mps', 'east_mps', 'up_mps')], float)
    if not np.isfinite(velocity).all():
        raise ValueError('finite reported receiver velocity required')
    return ecef(latitude, longitude, row['height_m'])-local_rotation(latitude, longitude).T@velocity*offset


def range_comparison(first, last, first_difference, last_difference, measured, rotation):
    """Remove one clock per step and retain both endpoint geometries."""
    import numpy as np
    from .gnss_carrier_phase import MAX_CONDITION

    design = np.column_stack((last, np.ones(len(last))))
    condition = float(np.linalg.cond(design))
    if not math.isfinite(condition) or condition > MAX_CONDITION:
        return dict(reason='ill-conditioned satellite geometry')
    predicted = last@last_difference-first@first_difference
    predicted -= np.median(predicted)
    measured = np.asarray(measured, float)-np.median(measured)
    residual = measured-predicted
    directions = np.linalg.lstsq(design, np.column_stack((measured, predicted)), rcond=None)[0]
    neu = rotation@directions[:3]
    return dict(predicted_range_m=predicted.tolist(), measured_range_m=measured.tolist(),
                residual_squared_m2=float(residual@residual), zero_squared_m2=float(measured@measured),
                observed_neu_m=neu[:, 0].tolist(), predicted_neu_m=neu[:, 1].tolist(), condition=condition)


def align_exports(root, audit):
    from .airquantumgrav_receiver import records
    from .esa_full_parallel_gnss import AIR1, BASE as SOURCE_DIRECTORY, _sha
    from .esa_full_parallel_gnss_v2 import EXPECTED_ROLLOVERS
    from .esa_parallel_gnss import match_times
    from .esa_ppp_acquisition import TARGETS, verify_complete
    from .esa_receiver_sequence_wrap import records_with_sequence_wrap
    from .esa_rinex_window import WEEK

    base = root/SOURCE_DIRECTORY
    targets = [dict(time_s=t) for t in range(FIRST_SHARED, LAST_SHARED+1)]
    tolerance = audit['match_tolerance_s']
    sources = {}

    def align(rows):
        matched = match_times(targets, rows, tolerance_s=tolerance)
        result = {}
        for index, row in matched:
            second = targets[index]['time_s']
            if row['gps_week'] != WEEK:
                raise ValueError('exact original GPS week required')
            result[str(second)] = dict(ecef_m=corrected_position(row, second, tolerance=tolerance).tolist(),
                                      offset_s=row['time_s']-second)
        return result

    air1 = base/AIR1
    if (audit['reference_file'] != AIR1 or audit['protected_group_reads'] != 0
            or _sha(air1) != audit['reference_sha256']):
        raise ValueError('the verified opened air1 source is required')
    with air1.open() as stream:
        sources['air1'] = align(records(stream))
    for name, size in TARGETS.items():
        receiver = name.split('_')[1]
        previous = next(row for row in audit['sources'] if row['filename'] == name)
        receipt = (base/(name+'.receipt.json')).read_bytes()
        path = base/name
        if (digest(receipt) != previous['receipt_sha256']
                or verify_complete(path, size, json.loads(receipt)) != previous['source_sha256']):
            raise ValueError('the original verified alternate PPP source is required')
        sequence = {}
        with path.open() as stream:
            parsed = records_with_sequence_wrap(stream, expected_rollovers=EXPECTED_ROLLOVERS[name], audit=sequence)
            sources[receiver] = align(parsed)
            for _ in parsed:
                pass
        if sequence != previous['sequence_audit']:
            raise ValueError('alternate receiver audit differs')
    return sources


def task_for(portion, count):
    return dict(identity=portion, input_key=portion, payload=dict(portion=portion, count=count),
                limits=dict(native_calls=0, packet_visits=0, bound_calls=count, bound_steps=3*count))


def qualification(root, *, check):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the existing frozen comparison')
    prior, ppp = ((root/name).read_bytes() for name in (PRIOR, PPP_AUDIT))
    if digest(prior) != PRIOR_SHA or digest(ppp) != PPP_SHA:
        raise ValueError('the original carrier and PPP audit reports are required')
    scores = json.loads(prior)
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with (closing(ClosedStudy(root, 'data/'+CARRIER)) as carrier,
          closing(ClosedStudy(root, 'data/'+ORBITS)) as orbit):
        if (carrier.completion['manifest_sha256'] != scores['manifest_sha256']
                or orbit.completion['manifest_sha256'] != ORBITS_MANIFEST
                or not carrier.summary['passed'] or not orbit.summary['passed']):
            raise ValueError('verified archived carrier contrast and orbit inputs required')
        rows = carrier.artifact(CARRIER_TASK['identity'], 'carrier-differences.json')
        if ([row['first_gps_seconds'] for row in rows] != list(range(FIRST_SHARED, LAST_SHARED))
                or len(rows) != INTERVALS
                or [row['first_gps_seconds'] for row in rows if 'skipped' in row] != scores['clock_skips']):
            raise ValueError('the exact 519 intervals including the clock skip are required')
        staged = dict(navigation=orbit.input('navigation', raw=True), rinex=carrier.input('air1', raw=True))
    selected = {part: [row for row in rows if row['portion'] == part] for part in PORTIONS}
    tasks = [task_for(part, len(rows)) for part, rows in selected.items()]
    staged.update({part: encoded(rows) for part, rows in selected.items()})
    staged.update(positions=encoded(align_exports(root, json.loads(ppp))), recovery=recovery,
                  recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, raw_comparison=PRIOR, ppp_audit=PPP_AUDIT, qualification=REQUEST, qualification_tests=REPORT)
    for key, raw in staged.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, raw)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=inputs, sources=sources, tasks=tasks, workers=2, threads=1, maximum_wall_s=WALL_S)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def interval_geometry(first, last, satellites, ppp_air1, phase, ephemerides):
    import numpy as np
    from .gnss_carrier_phase import _geometry, shared_ephemerides
    from .gnss_position import geodetic, local_rotation, satellite_state

    ends = [phase[second] for second in (first, last)]
    orbits = shared_ephemerides(ephemerides, *[dict(gps_week=row['week'], gps_week_seconds=row['seconds']) for row in ends])
    if not set(satellites) <= set(orbits):
        return None
    jacobians = []
    for row, receiver in zip(ends, ppp_air1, strict=True):
        codes = [row['satellites'][prn]['code_m'] for prn in satellites]
        if any(code is None or not 1e6 < code < 6e7 for code in codes):
            return None
        states = [satellite_state(orbits[prn], row['week'], row['seconds'], code)[0]
                  for prn, code in zip(satellites, codes, strict=True)]
        jacobians.append(_geometry(np.asarray(receiver), np.asarray(states))[1][:, :3])
    rotation = local_rotation(*geodetic(ppp_air1[-1])[:2])
    return *jacobians, rotation


def evaluate(task, context):
    import numpy as np
    from .esa_carrier_phase_support import phase_epochs
    from .esa_rinex_code import read_navigation

    portion, count = (task['payload'][key] for key in ('portion', 'count'))
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or portion not in PORTIONS or declared != task_for(portion, count):
        raise ValueError('exact frozen two-portion comparison required')
    rows = json.loads(context.input_path(portion).read_bytes())
    positions = json.loads(context.input_path('positions').read_bytes())
    if len(rows) != count or set(positions) != {name for pair in PAIRS for name in pair}:
        raise ValueError('complete input inventory required')
    phase = {row['seconds']: row for row in phase_epochs(gzip.decompress(context.input_path('rinex').read_bytes()))}
    ephemerides, _ = read_navigation(gzip.decompress(context.input_path('navigation').read_bytes()).decode('ascii'))
    results = []
    for row in rows:
        context.charge(bound_calls=1, bound_steps=3)
        first, last = (row[key] for key in ('first_gps_seconds', 'last_gps_seconds'))
        base = dict(first_gps_seconds=first, last_gps_seconds=last)
        if 'skipped' in row:
            results.append(dict(base, skipped=row['skipped']))
            continue
        if any(str(time) not in values for time in (first, last) for values in positions.values()):
            results.append(dict(base, skipped='unmatched PPP endpoint'))
            continue
        sats = row['pairs']['air1-mosaic03']['satellites']
        if any(value['satellites'] != sats or 'signed_differences_m' not in value for value in row['pairs'].values()):
            raise ValueError('identical frozen satellite lists required')
        a, b = (str(time) for time in (first, last))
        air1 = [positions['air1'][time]['ecef_m'] for time in (a, b)]
        geometry = interval_geometry(first, last, sats, air1, phase, ephemerides)
        if geometry is None:
            results.append(dict(base, skipped='incomplete healthy broadcast geometry'))
            continue
        begin, end, rotation = geometry
        pairs = {}
        for left, right in PAIRS:
            key = f'{left}-{right}'
            d = [np.asarray(positions[left][time]['ecef_m'])-np.asarray(positions[right][time]['ecef_m'])
                 for time in (a, b)]
            pairs[key] = range_comparison(begin, end, *d, row['pairs'][key]['signed_differences_m'], rotation)
        if any('reason' in comparison for comparison in pairs.values()):
            results.append(dict(base, skipped='ill-conditioned satellite geometry'))
            continue
        results.append(dict(base, satellites=sats, pairs=pairs))
    context.save('phase-closure.json', results)
    return dict(portion=portion, count=len(results), usable=sum('pairs' in row for row in results),
                passed=True, new_fits=0, protected_reads=0, scientific_decision='abstain')


def recover(root):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as original:
            if original.input('recovery_policy') != RECOVER:
                raise ValueError('unchanged recovery allowance required')
            if all(identity in original.rows and original.envelope(identity)['status'] == 'complete'
                   for identity in original.tasks):
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVER)
    return resume_campaign(root, continuation)


def summarize(rows):
    import numpy as np
    from collections import Counter

    usable = [row for row in rows if 'pairs' in row]
    count = sum(len(row['satellites']) for row in usable)
    pairs = {}
    for left, right in PAIRS:
        key = f'{left}-{right}'
        if not count:
            break
        observations = [row['pairs'][key] for row in usable]
        squared = math.fsum(row['residual_squared_m2'] for row in observations)
        zero = math.fsum(row['zero_squared_m2'] for row in observations)
        measured, predicted = [np.asarray([row[name] for row in observations])
                               for name in ('observed_neu_m', 'predicted_neu_m')]
        correlation = [float(np.corrcoef(a, b)[0, 1]) if np.std(a) and np.std(b) else None
                       for a, b in zip(measured.T, predicted.T, strict=True)]
        pairs[key] = dict(rms_m=math.sqrt(squared/count), zero_rms_m=math.sqrt(zero/count),
                          relative_squared_error=squared/zero if zero else None,
                          correlation_neu=correlation,
                          signed_residual_mean_neu_m=(measured-predicted).mean(axis=0).tolist())
    return dict(intervals=len(rows), usable=len(usable), satellite_intervals=count, pairs=pairs,
                skipped=dict(Counter(row['skipped'] for row in rows if 'skipped' in row)))


def report(root):
    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        sources = {prefix: original}
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            selected = {identity: row['origin'] for identity, row in inspect(root, continuation)['selected'].items()}
        else:
            selected = {identity: prefix for identity in original.rows
                        if original.envelope(identity)['status'] == 'complete'}
        results = {}
        for identity, origin in selected.items():
            if origin not in sources:
                sources[origin] = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
            source = sources[origin]
            envelope = source.envelope(identity)
            rows = source.artifact(identity, 'phase-closure.json')
            summary = summarize(rows)
            expected = task_for(identity, len(rows))['limits']
            if (envelope['charged'] != expected or envelope['status'] != 'complete'
                    or summary['usable'] != envelope['result']['usable']):
                raise ValueError('verified completed tasks and charges required')
            results[identity] = summary
        result = dict(results=results, complete=len(results),
                      closures={key: study.completion for key, study in sources.items()})
    _write_equal(root/RESULT, encoded(result))
    return {key: result[key] for key in ('complete', 'results')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    output = qualification(root, check=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(output, sort_keys=True))
