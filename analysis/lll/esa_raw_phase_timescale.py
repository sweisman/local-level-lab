# SPDX-License-Identifier: AGPL-3.0-or-later
"""Accumulate archived receiver contrasts on fixed blocks with common satellites."""

import argparse
from collections import Counter
from contextlib import ExitStack, closing
import json
import math
from pathlib import Path
from statistics import median

from .esa_raw_phase_ppp_closure import BASE, PAIRS, PORTIONS, RECOVER, RECOVERY, WALL_S
from .esa_raw_phase_ppp_closure import ID as PARENT, RESULT as PRIOR
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-raw-phase-ppp-timescale-v1'
SCOPE = 'Fixed durations of relative phase and PPP agreement on ESA recording 187'
PLAN = BASE+'ESA_RAW_PHASE_PPP_TIMESCALE_PLAN.md'
RESULT = BASE+'esa-raw-phase-ppp-timescale-result.json'
REQUEST = BASE+'esa-raw-phase-ppp-timescale-qualification.json'
REPORT = BASE+'esa-raw-phase-ppp-timescale-tests.xml'
TEST = 'analysis/tests/test_esa_raw_phase_timescale.py'
TESTS = ('test_accumulation_uses_common_satellites_and_removes_shared_clock',
         'test_blocks_preserve_clock_exclusions_and_do_not_count_partial_tails')
PRIOR_SHA = 'de7ac709a0ca3b54697d55b146b343d07271095375b8ab6f97b790e0c7beecfe'
DURATIONS = (1, 4, 16, 60)
MIN_SATELLITES = 5


def blocks(rows, duration):
    count, tail = divmod(len(rows), duration)
    return [rows[i*duration:(i+1)*duration] for i in range(count)], tail


def stacked_contrast(rows):
    if (not rows or any(row['last_gps_seconds'] != row['first_gps_seconds']+1 for row in rows)
            or any(a['last_gps_seconds'] != b['first_gps_seconds'] for a, b in zip(rows, rows[1:]))):
        raise ValueError('consecutive unit intervals required')
    if any('skipped' in row for row in rows):
        return dict(skipped='archived interval excluded')
    common = sorted(set.intersection(*(set(row['satellites']) for row in rows)))
    if len(common) < MIN_SATELLITES:
        return dict(skipped='fewer than five common satellites')
    by_satellite = [{prn: i for i, prn in enumerate(row['satellites'])} for row in rows]
    pair_names = set(rows[0]['pairs'])
    if any(set(row['pairs']) != pair_names for row in rows):
        raise ValueError('same archived pairs are required')
    pairs = {}
    for name in sorted(pair_names):
        centered = {}
        for target, source in (('measured_m', 'measured_range_m'), ('predicted_m', 'predicted_range_m')):
            values = [math.fsum(row['pairs'][name][source][lookup[prn]]
                      for row, lookup in zip(rows, by_satellite, strict=True)) for prn in common]
            clock = median(values)
            centered[target] = [value-clock for value in values]
        pairs[name] = centered
    return dict(satellites=common, pairs=pairs)


def task_for(portion, count):
    calls = sum(count//duration for duration in DURATIONS)
    steps = sum(3*duration*(count//duration) for duration in DURATIONS)
    return dict(identity=portion, input_key=portion, payload=dict(portion=portion, count=count),
                limits=dict(native_calls=0, packet_visits=0, bound_calls=calls, bound_steps=steps))


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
        raise ValueError('preserve the frozen duration comparison')
    raw = (root/PRIOR).read_bytes()
    if digest(raw) != PRIOR_SHA:
        raise ValueError('the exact sealed one-second result is required')
    prior = json.loads(raw)
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    tasks, materials = [], {}
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if parent.completion != prior['closures'][parent.prefix] or not parent.summary['passed']:
            raise ValueError('both verified original portions are required')
        for portion in PORTIONS:
            rows = parent.artifact(portion, 'phase-closure.json')
            if (len(rows) != prior['results'][portion]['intervals']
                    or sum('pairs' in row for row in rows) != prior['results'][portion]['usable']):
                raise ValueError('exact original signed projections and skips required')
            materials[portion] = encoded(rows)
            tasks.append(task_for(portion, len(rows)))
    materials.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=REPORT)
    for key, raw in materials.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, raw)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=inputs, sources=sources, tasks=tasks, workers=2, threads=1, maximum_wall_s=WALL_S)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    portion, count = (task['payload'][key] for key in ('portion', 'count'))
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or portion not in PORTIONS or declared != task_for(portion, count):
        raise ValueError('exact fixed portion and its allowances required')
    rows = json.loads(context.input_path(portion).read_bytes())
    if len(rows) != count:
        raise ValueError('original interval count must be preserved')
    comparisons = {}
    for duration in DURATIONS:
        chunks, tail = blocks(rows, duration)
        entries = []
        for chunk in chunks:
            context.charge(bound_calls=1, bound_steps=3*duration)
            entries.append(dict(first_gps_seconds=chunk[0]['first_gps_seconds'], **stacked_contrast(chunk)))
        comparisons[str(duration)] = dict(results=entries, partial_tail_s=tail)
    context.save('durations.json', comparisons)
    return dict(portion=portion, intervals=len(rows), passed=True, new_fits=0, protected_reads=0,
                scientific_decision='abstain')


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


def summarize(comparisons):
    result = {}
    for duration, row in comparisons.items():
        valid = [item for item in row['results'] if 'pairs' in item]
        count = sum(len(item['satellites']) for item in valid)
        pairs = {}
        for left, right in PAIRS:
            key = f'{left}-{right}'
            samples = [item['pairs'][key] for item in valid]
            if not samples:
                continue
            a, b = ([value for item in samples for value in item[name]] for name in ('measured_m', 'predicted_m'))
            zero = math.fsum(x*x for x in a)
            error = math.fsum((x-y)**2 for x, y in zip(a, b, strict=True))
            mean_a, mean_b = math.fsum(a)/count, math.fsum(b)/count
            qa = math.fsum((x-mean_a)**2 for x in a)
            qb = math.fsum((y-mean_b)**2 for y in b)
            cross = math.fsum((x-mean_a)*(y-mean_b) for x, y in zip(a, b, strict=True))
            pairs[key] = dict(rms_m=math.sqrt(error/count), zero_rms_m=math.sqrt(zero/count),
                              relative_squared_error=error/zero if zero else None,
                              correlation=cross/math.sqrt(qa*qb) if qa and qb else None)
        result[duration] = dict(blocks=len(row['results']), retained=len(valid), satellite_blocks=count,
                                partial_tail_s=row['partial_tail_s'], pairs=pairs,
                                skipped=dict(Counter(item['skipped'] for item in row['results'] if 'skipped' in item)))
    return result


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
            rows = source.artifact(identity, 'durations.json')
            expected = task_for(identity, envelope['result']['intervals'])['limits']
            if envelope['charged'] != expected or envelope['status'] != 'complete':
                raise ValueError('verified source and charges required')
            results[identity] = summarize(rows)
        result = dict(results=results, complete=len(results),
                      closures={key: study.completion for key, study in sources.items()})
    _write_equal(root/RESULT, encoded(result))
    return {'complete': result['complete'], 'retained': {
        portion: {length: row['retained'] for length, row in durations.items()}
        for portion, durations in results.items()}
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    output = qualification(root, check=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(output, sort_keys=True))
