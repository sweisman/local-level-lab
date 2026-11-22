# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved NASA force-envelope comparisons across the full scalar gain range."""

import argparse
from collections import defaultdict
from contextlib import closing
import gzip
import json
import math
from pathlib import Path

from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-force-gain-range-v1'
SCOPE = 'Training-admissible scalar gain and held-out NASA force contrast'
FOLDER = 'docs/ilvis0-measurement-contribution/'
PLAN = FOLDER+'FORCE_GAIN_RANGE_PLAN.md'
REQUEST = FOLDER+'force-gain-range-qualification.json'
TEST_REPORT = FOLDER+'force-gain-range-tests.xml'
RESULT = FOLDER+'force-gain-range-result.json'
INPUT_REPORT = FOLDER+'matched-extension-force-result.json'
INPUT_SHA = '883f2f119ba52104992f8f46254d0816281b56a2fd48f6fe7c8946b90e704771'
TEST = 'analysis/tests/test_ilvis0_force_gain_range.py'
TESTS = ('test_earlier_gain_range_distinguishes_minimum_from_all_allowed_gains',
         'test_minimax_uses_one_ratio_for_conflicting_force_windows',
         'test_minimax_keeps_training_restriction_and_interval_overlap')
PROFILES = 14
STEPS = 48
ROUNDING = 1e-12


def gain_compatibility(training, later, cap):
    """One-sided inequalities identify lower limits on a constant gain."""
    from .ilvis0_matched_force_gain import compare

    first = compare(training, later)
    required = first['required_training_gain']
    required_later = max(0., max(lo/hi-1. for lo, hi in later))
    joint = max(required, required_later)
    return dict(earlier_gain_range=[required, cap] if required <= cap else None,
                joint_gain_range=[joint, cap] if joint <= cap else None,
                later_gain_floor=required_later, later_status=(
                    'none' if joint > cap else 'depends_on_gain' if joint > required else 'all'))


def minimax_separation(intervals, ratio_range):
    """Bracket the minimum maximum interval separation with one gain ratio."""
    import numpy as np

    rows = np.asarray(intervals, dtype=float)
    lo, hi = map(float, ratio_range)
    if (rows.ndim != 2 or rows.shape[1] != 4 or not len(rows)
            or not np.isfinite(rows).all() or not 0. < np.min(rows) <= np.max(rows) <= 100.
            or np.any(rows[:, ::2] > rows[:, 1::2]) or not 0. < lo <= hi <= 2.):
        raise ValueError('ordered positive force intervals and supported gain range required')
    a_lo, a_hi, b_lo, b_hi = rows.T

    def slacks(ratio):
        return float(np.max(a_lo-ratio*b_hi)), float(np.max(ratio*b_lo-a_hi))

    if slacks(lo)[0] <= slacks(lo)[1]:
        hi = lo
    elif slacks(hi)[0] >= slacks(hi)[1]:
        lo = hi
    else:
        for _ in range(STEPS):
            middle = lo+(hi-lo)/2.
            left, right = slacks(middle)
            if left > right:
                lo = middle
            else:
                hi = middle
    lows, highs = slacks(lo), slacks(hi)
    lower = max(0., max(highs[0], lows[1])-ROUNDING)
    ratio = lo if max(lows) <= max(highs) else hi
    upper = max(0., min(max(lows), max(highs)))+ROUNDING
    return lower, upper, ratio


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def limits(count):
    return dict(native_calls=0, packet_visits=0, bound_calls=4+PROFILES,
                bound_steps=count*(4+PROFILES*(STEPS+8)))


def prepare(root):
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .ilvis0_matched_observed_inputs import _write_equal, runtime_environment
    from .ilvis0_matched_extension_force import ID as PARENT
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('use the already frozen gain range study')
    raw = (root/INPUT_REPORT).read_bytes()
    if digest(raw) != INPUT_SHA:
        raise ValueError('saved force envelope report changed')
    parent = json.loads(raw)
    deps, environment = sources(root), runtime_environment()
    qualification, tests = checked(root, REQUEST, sources=deps, environment=environment,
                                   required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    inputs = dict(plan=PLAN, parent_report=INPUT_REPORT)
    materials = dict(qualification=qualification, qualification_tests=tests, recovery=recovery,
        recovery_tests=recovery_tests, recovery_policy=encoded(dict(RECOVERY_POLICY, maximum_wall_s=180)))
    tasks = []
    with closing(ClosedStudy(root, 'data/'+PARENT)) as study:
        if (any(parent[k] != v for k, v in study.completion.items()) or not study.summary['passed']
                or parent['new_fits'] or len(parent['flights']) != 2):
            raise ValueError('both closed force envelope tasks are required')
        for flight in parent['flights']:
            segment = flight['segment_id']
            values = study.artifact(segment, 'windows.json.gz', raw=True)
            if digest(values) != flight['windows_sha256']:
                raise ValueError('saved window evidence changed')
            materials[segment] = values
            count = flight['model_envelopes']
            tasks.append(dict(identity=segment, input_key=segment, rows=count, limits=limits(count)))
    for key, data in materials.items():
        relative = f'data/{ID}-inputs/{key}'
        _write_equal(root/relative, data)
        inputs[key] = relative
    definition = dict(id=ID, scope=SCOPE, sources=deps, inputs=inputs, tasks=tasks,
        adapter=Path(__file__).relative_to(root).as_posix(), workers=2, threads=1, maximum_wall_s=120.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    from .ilvis0_matched_extension_forecast import SHAPES
    from .ilvis0_matched_force_average import TRACKS
    from .ilvis0_matched_force_gain import GAIN_CAP
    from .ilvis0_matched_force_support import CLOCKS

    rows = json.loads(gzip.decompress(context.input_path().read_bytes()))['comparisons']
    count = task['rows']
    if context.manifest['scope'] != SCOPE or len(rows) != count or task['limits'] != limits(count):
        raise ValueError('exact saved force support and allowance required')
    measured = defaultdict(list)
    windows = defaultdict(dict)
    for row in rows:
        model, role = row['model'], row['side']
        key = role, row['clock'], row['gps_stream'], row['gps_millisecond_tag']
        if model in windows[key]:
            raise ValueError('duplicated model on saved force window')
        measured[model, role].append((row['measured_lower_mps2'], row['required_upper_mps2']))
        windows[key][model] = (row['required_lower_mps2'], row['required_upper_mps2'])
    models = {name for pair in SHAPES.values() for name in pair}
    if any(set(pair) != models for pair in windows.values()):
        raise ValueError('all four candidates must share each window')
    gain = {}
    for model in sorted(models):
        context.charge(bound_calls=1, bound_steps=count)
        gain[model] = gain_compatibility(measured[model, 'training'], measured[model, 'later'], GAIN_CAP)
    profiles = []
    scopes = [(clock, track) for clock in CLOCKS for track in TRACKS]+[(None, None)]
    for field, (globe, disc) in SHAPES.items():
        a, b = (gain[m]['earlier_gain_range'] for m in (globe, disc))
        if a is None or b is None:
            raise ValueError('both saved models must admit an earlier gain range')
        ratios = (math.nextafter((1.+b[0])/(1.+a[1]), -math.inf),
                  math.nextafter((1.+b[1])/(1.+a[0]), math.inf))
        for clock, track in scopes:
            context.charge(bound_calls=1, bound_steps=count*(STEPS+8))
            samples = [(*pair[globe], *pair[disc]) for (role, c, t, _), pair in windows.items()
                       if role == 'later' and (clock is None or (c, t) == (clock, track))]
            lower, upper, ratio = minimax_separation(samples, ratios)
            profiles.append(dict(field=field, clock=clock, gps=track, windows=len(samples),
                lower_mps2=lower, upper_mps2=upper, gain_ratio=ratio, earlier_ratio_range=ratios))
    result = dict(passed=True, identity=task['identity'], gain=gain, profiles=profiles,
                  new_fits=0, scientific_decision='abstain')
    context.save('gain-range.json', result)
    return result


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if len(study.rows) != 2 or study.manifest['scope'] != SCOPE:
            raise ValueError('both saved gain range tasks must seal')
        results = []
        for identity in study.rows:
            envelope = study.envelope(identity)
            result = envelope['result']
            if result['passed'] and (result != study.artifact(identity, 'gain-range.json')
                    or envelope['charged'] != limits(study.tasks[identity]['rows'])
                    or len(result['profiles']) != PROFILES):
                raise ValueError('closed gain range result or allowance differs')
            results.append(result)
        value = dict(study.completion, flights=results, charged=study.summary['charged'],
                     new_fits=0, scientific_decision='abstain')
    raw = encoded(value)
    _write_equal(root/RESULT, raw)
    return dict(result_sha256=digest(raw), charged=value['charged'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    print(json.dumps({'request': request, 'prepare': prepare, 'report': report}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
