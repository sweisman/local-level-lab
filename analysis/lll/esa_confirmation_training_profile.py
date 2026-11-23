# SPDX-License-Identifier: AGPL-3.0-or-later
"""Profile only the earlier receiver conditions of the seven fixed reserved layouts."""
import argparse
import json
from math import atan2, degrees, hypot, isfinite
from pathlib import Path
from statistics import quantiles

from .esa_confirmation_queries import DOCS, INPUTS, TRAINING, WITHHELD, _read
from .esa_confirmation_timing import INVENTORY, INVENTORY_SHA
from .esa_forecast_receiver_split import QUERY_STRIDE, read_split
from .esa_forecast_receiver_split_check import FREEZE as DEVELOPMENT, RESULT as DEVELOPMENT_RESULT
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded, safe_path


PLAN = DOCS+'ESA_CONFIRMATION_TRAINING_PROFILE_PLAN.md'
REQUEST = DOCS+'esa-confirmation-training-profile-qualification.json'
XML = DOCS+'esa-confirmation-training-profile-tests.xml'
FREEZE = DOCS+'esa-confirmation-training-profile-freeze.json'
RESULT = DOCS+'esa-confirmation-training-profile-result.json'
DEVELOPMENT_SHA = '23b3cca7ba8c1ec98d03f938c111931fd936f77e6b3936b4ee65af1aa2a71f5b'
DEVELOPMENT_RESULT_SHA = '6aec0e27d1fb4c67c65373a67707057af723a9fa5b67d3fa5b5096846d277ed9'
CADENCE = DOCS+'esa-confirmation-queries-v2-freeze.json'
CADENCE_SHA = 'b4222f513c8044c9f2e0e71470cae00ceec2d995b89f5ae28993ad7055052b79'
TIMES = DOCS+'esa-confirmation-queries-v2-result.json'
TIMES_SHA = 'aafdc46792f96c8c6908f85abf009022d482eae6628ebfd3bc49a9466daa9234'
PARENTS = {CADENCE: CADENCE_SHA, TIMES: TIMES_SHA, INVENTORY: INVENTORY_SHA,
           DEVELOPMENT: DEVELOPMENT_SHA, DEVELOPMENT_RESULT: DEVELOPMENT_RESULT_SHA}


def profile(rows):
    """Aggregate geometry and receiver-reported quantities on an earlier block."""
    def summary(values):
        values = list(values)
        if not values or not all(map(isfinite, values)):
            raise ValueError('finite training-profile values required')
        q = quantiles(values, n=20, method='inclusive') if len(values) > 1 else values*19
        return dict(p05=q[0], median=q[9], p95=q[-1])

    times = [row['time_s'] for row in rows]
    durations = [b-a for a, b in zip(times[:-1], times[1:], strict=True)]
    if not durations or any(dt <= 0. or not isfinite(dt) for dt in durations):
        raise ValueError('ordered training clock required')
    horizontal = [(r['north_mps'], r['east_mps']) for r in rows]
    speed = [hypot(n, e) for n, e in horizontal]
    if any(not value > 0. for value in speed):
        raise ValueError('positive horizontal speed required to define receiver course')
    rates = [abs(degrees(atan2(n0*e1-e0*n1, n0*n1+e0*e1)))/dt
             for (n0, e0), (n1, e1), dt in zip(horizontal[:-1], horizontal[1:], durations, strict=True)]
    return dict(rows=len(rows), horizontal_speed_mps=summary(speed), absolute_course_rate_degps=summary(rates),
                ellipsoidal_height_m=summary(r['height_m'] for r in rows),
                absolute_vertical_speed_mps=summary(abs(r['up_mps']) for r in rows),
                pdop=summary(r['pdop'] for r in rows), satellites=summary(r['satellites'] for r in rows),
                reported_height_sd_m=summary(r['reported_height_sd_m'] for r in rows))


def definitions(root):
    cadence, times, inventory, development, earlier = [_read(root, path, sha) for path, sha in PARENTS.items()]
    if (times['freeze_sha256'] != CADENCE_SHA or earlier['freeze_sha256'] != DEVELOPMENT_SHA
            or times['supported_groups'] != 7 or len(cadence['cases']) != 7
            or set(cadence['cases']) != set(times['records']) or times['protected_outcome_reads']
            or earlier['later_coordinates_decoded'] or earlier['protected_reads']):
        raise ValueError('the unchanged protected slice and development bindings are required')
    for result in times['records'].values():
        if (not result['supported'] or result['source_stride'] != QUERY_STRIDE
                or result['withheld']['reports'] != WITHHELD
                or any(result['training'][str(n)]['reports'] != n for n in TRAINING)):
            raise ValueError('verified complete original query layouts required')

    def row(path, size, total, sha, group, first, last, hashes, withheld):
        return dict(path=path, bytes=size, reports=total, sha256=sha, group=group,
                    first=first, last=last, training_times_sha256=hashes, later_times_sha256=withheld)

    cases = {'187': row(development['receiver_path'], development['receiver_bytes_per_pass'],
                        development['receiver_report_count'], development['receiver_sha256'], development['receiver_group'],
                        development['first_index'], development['last_index'],
                        {n: layout['training_times_sha256'] for n, layout in earlier['training'].items()},
                        earlier['withheld_times_sha256'])}
    for name, item in cadence['cases'].items():
        original, layout = inventory['records'][name]['result'], times['records'][name]
        source = item['receiver']
        if source != original['source']:
            raise ValueError('reserved receiver acquisition identities differ')
        cases[name] = row(INPUTS+source['filename'], source['size_bytes'], original['receiver_epochs'], source['sha256'],
                          source['group_id'], layout['training'][str(TRAINING[-1])]['first_source_index'],
                          layout['withheld']['last_source_index'],
                          {n: split['times_sha256'] for n, split in layout['training'].items()},
                          layout['withheld']['times_sha256'])
    if len({case['group'] for case in cases.values()}) != 8:
        raise ValueError('seven separate reserved groups and one development group required')
    return cases


def calculate(root, case):
    indexes = tuple(range(case['first'], case['last']+1, QUERY_STRIDE))
    if len(indexes) != TRAINING[-1]+WITHHELD:
        raise ValueError('original 800 plus 120 report layout required')
    with safe_path(root, case['path']).open('rb') as stream:
        split = read_split(stream, indices=indexes, training_count=TRAINING[-1], source_bytes=case['bytes'],
                           source_reports=case['reports'], source_sha256=case['sha256'])
    earlier = split['query_times_s'][:TRAINING[-1]]
    later = split['query_times_s'][TRAINING[-1]:]
    if (digest(encoded(later)) != case['later_times_sha256']
            or any(digest(encoded(earlier[-n:])) != case['training_times_sha256'][str(n)] for n in TRAINING)):
        raise ValueError('training and later query clocks must match the sealed selections')
    return {str(n): profile(split['training_rows'][-n:]) for n in TRAINING}


def run(root, action):
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    tests = ('test_esa_confirmation_training_profile.py', 'test_esa_forecast_receiver_split.py')
    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
                                   *(f'analysis/tests/{test}' for test in tests)))
    environment = runtime_environment()
    if action == 'request':
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    binding, evidence = checked(root, REQUEST, sources=sources, environment=environment, required_tests=(
        'test_receiver_profile_uses_actual_time_and_wraps_course',
        'test_unparseable_later_positions_and_weights_never_enter_training'), minimum_tests=6)
    cases = definitions(root)
    freeze = encoded(dict(cases=cases, source_sha256=PARENTS, qualification_sha256=digest(binding),
                          tests_sha256=digest(evidence), maximum_files=8, maximum_file_passes=8,
                          maximum_bytes=sum(c['bytes'] for c in cases.values()),
                          maximum_reports=sum(c['reports'] for c in cases.values()), threads=1,
                          new_fits=0, raw_imu_reads=0, later_coordinates_decoded=0, protected_outcome_reads=0))
    if action == 'freeze':
        _write_equal(root/FREEZE, freeze)
        return dict(freeze_sha256=digest(freeze), files=len(cases))
    if (root/FREEZE).read_bytes() != freeze or (root/RESULT).exists():
        raise ValueError('the original freeze and an unused profile receipt are required')
    results = {name: calculate(root, case) for name, case in cases.items()}
    comparisons = {}
    for n, baseline in results['187'].items():
        comparisons[n] = {recording: sorted(key for key, reference in baseline.items() if key != 'rows'
                             and not reference['p05'] <= value[n][key]['median'] <= reference['p95'])
                          for recording, value in results.items() if recording != '187'}
    result = dict(freeze_sha256=digest(freeze), records=results, outside_development_central_90_percent=comparisons,
                  reserved_groups=7, new_fits=0, raw_imu_reads=0, later_coordinates_decoded=0,
                  protected_outcome_reads=0, scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(result))
    return dict(result_sha256=digest(encoded(result)), profiled_groups=8, reserved_groups=7,
                later_coordinates_decoded=0, protected_outcome_reads=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'freeze', 'check'))
    args = parser.parse_args()
    print(json.dumps(run(Path.cwd(), args.action), sort_keys=True))
