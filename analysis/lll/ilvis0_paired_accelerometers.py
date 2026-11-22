# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare accelerometer magnitudes on two archived simultaneous flight legs."""

import argparse
from contextlib import closing
import csv
import gzip
import json
import math
from pathlib import Path

from .studies.artifacts import ArchiveStore, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'ilvis0-paired-accelerometers-v1'
SCOPE = 'paired NASA accelerometer magnitude differences at five window lengths'
FOLDER = 'docs/ilvis0-measurement-contribution/'
PLAN = FOLDER+'PAIRED_ACCELEROMETER_PLAN.md'
REQUEST = FOLDER+'paired-accelerometers-qualification.json'
TEST_REPORT = FOLDER+'paired-accelerometers-tests.xml'
RESULT = FOLDER+'paired-accelerometers-result.json'
TEST = 'analysis/tests/test_ilvis0_paired_accelerometers.py'
TESTS = ('test_window_uses_only_whole_packets_and_rejects_low_coverage',
         'test_window_magnitude_does_not_cancel_reversed_vectors',
         'test_compare_halves_uses_earlier_difference_and_excludes_crossings')
PAIRS = 'docs/ilvis0-current-findings-20261015/shared-leg-pairs.csv'
LEGS = {'leg-13805a9a35c4': (8, 21), 'leg-9c109162b404': (21, 21)}
WIDTHS = (.05, .25, 1., 10., 30.)
CLOCKS = ('nominal_200Hz', 'header_elapsed')
WINDOW_SUPPORT = .80
MAX_PACKETS = 150_000
MAX_BYTES = 300_000_000
READS = 2
COMPARISONS = len(WIDTHS)*len(CLOCKS)
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=READS+COMPARISONS,
              bound_steps=READS*MAX_PACKETS*(1+COMPARISONS))


def window_magnitudes(ends, durations, increments, starts, width):
    import numpy as np

    ends, dt, dv, starts = map(lambda x: np.asarray(x, dtype=float),
                               (ends, durations, increments, starts))
    if (ends.ndim != 1 or len(ends) == 0 or dt.shape != ends.shape or dv.shape != (len(dt), 3)
            or starts.ndim != 1 or not all(np.isfinite(x).all() for x in (ends, dt, dv, starts))
            or not math.isfinite(width) or width <= 0. or np.any(dt <= 0.)
            or np.any(np.diff(ends) <= 0.) or np.any(abs(np.diff(ends)-dt[1:]) > 1e-8)
            or np.any(np.diff(starts) < width-1e-8)):
        raise ValueError('finite contiguous packets and disjoint positive windows required')
    # The tolerance is below the source clock precision. No partial packet is weighted.
    first = np.searchsorted(ends-dt, starts-1e-9, side='left')
    last = np.searchsorted(ends, starts+width+1e-9, side='right')
    last = np.maximum(first, last)
    elapsed = np.r_[0., np.cumsum(dt)]
    amount = np.r_[0., np.cumsum(np.linalg.norm(dv, axis=1))]
    support = elapsed[last]-elapsed[first]
    good = support >= WINDOW_SUPPORT*width
    mean = np.full(starts.shape, np.nan)
    mean[good] = (amount[last[good]]-amount[first[good]])/support[good]
    return mean, support/width


def compare_halves(left, right, starts, width, midpoint):
    import numpy as np

    left, right, starts = map(np.asarray, (left, right, starts))
    matched = np.isfinite(left) & np.isfinite(right)
    earlier = matched & (starts+width <= midpoint+1e-9)
    later = matched & (starts >= midpoint-1e-9)
    result = dict(earlier_windows=int(earlier.sum()), later_windows=int(later.sum()),
                  unmatched_windows=int((~matched).sum()),
                  straddling_windows=int((matched & ~earlier & ~later).sum()))
    if min(result['earlier_windows'], result['later_windows']) < 2:
        raise ValueError('both halves require at least two matched complete windows')
    residual = left-right
    offset = float(np.mean(residual[earlier]))
    a, b = left[later], right[later]
    correlation = float(np.corrcoef(a, b)[0, 1]) if np.ptp(a) > 0. and np.ptp(b) > 0. else None
    return dict(result, earlier_offset_mps2=offset, later_correlation=correlation,
                later_unadjusted_rms_mps2=float(np.sqrt(np.mean(residual[later]**2))),
                later_adjusted_rms_mps2=float(np.sqrt(np.mean((residual[later]-offset)**2))),
                later_left_std_mps2=float(np.std(a)), later_right_std_mps2=float(np.std(b)))


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .ilvis0_remaining_prediction_layouts import CONTEXT, POPULATION
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('retain the original paired comparison allowance')
    deps, environment = sources(root), runtime_environment()
    qualification, tests = checked(root, REQUEST, sources=deps, environment=environment,
                                   required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    store = ArchiveStore(root)
    selected_raw, context_raw = store.read(POPULATION), store.read(CONTEXT)
    selections = json.loads(gzip.decompress(selected_raw))['selected']
    segments = {row['segment']['segment_id']: row for row in selections}
    records = {row['task_id']: row for row in json.loads(context_raw)['results']}
    pair_table = safe_path(root, PAIRS).read_text()
    pairs = {row['shared_leg_id']: row for row in csv.DictReader(pair_table.splitlines())
             if row['shared_leg_id'] in LEGS}
    inputs = dict(plan=PLAN, pair_table=PAIRS)
    raw = dict(qualification=qualification, qualification_tests=tests, recovery=recovery,
               recovery_tests=recovery_tests, recovery_policy=encoded(RECOVERY_POLICY))
    tasks = []
    for key, kinds in LEGS.items():
        pair = pairs[key]
        begin, end = (float(pair[f'overlap_{name}_utc_week_s']) for name in ('start', 'end'))
        if not 240. <= end-begin <= MAX_PACKETS*.0075 or pair['same_track_candidate'] != 'True':
            raise ValueError('a preselected simultaneous flight leg is required')
        sides = []
        for side, kind in zip(('left', 'right'), kinds, strict=True):
            source = segments[pair[f'{side}_segment_id']]
            record = records[source['task']]
            segment = source['segment']
            path = Path(source['source_path'])
            relative = path.relative_to(root) if path.is_absolute() else path
            original_key = f'{key}-{side}'
            if (not relative.as_posix().startswith('data/ilvis0-ready/')
                    or relative.name != pair[f'{side}_filename']+'.gz'
                    or not 0 < safe_path(root, relative.as_posix()).stat().st_size <= MAX_BYTES
                    or not 0 < record['inspection']['source_bytes'] <= MAX_BYTES
                    or segment['imu_type'] != kind):
                raise ValueError('selected recorder source or conversion hypothesis differs')
            inputs[original_key] = relative.as_posix()
            sides.append(dict(original=original_key, segment=segment, context=record))
        raw[key] = encoded(dict(begin=begin, end=end, sides=sides,
                               selection_sha256=digest(selected_raw), context_sha256=digest(context_raw)))
        tasks.append(dict(identity=key, input_key=key, limits=LIMITS))
    for key, value in raw.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, tasks=tasks, sources=deps,
        adapter=Path(__file__).relative_to(root).as_posix(), workers=2, threads=1, maximum_wall_s=300.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .ilvis0_segments import extract_segment

    if context.manifest['scope'] != SCOPE or task['limits'] != LIMITS:
        raise ValueError('paired comparison scope and allowance must match')
    layout = json.loads(context.input_path().read_bytes())
    begin, end = layout['begin'], layout['end']
    streams, readings = [], []
    for side in layout['sides']:
        context.charge(bound_calls=1, bound_steps=MAX_PACKETS)
        values, _, _, provenance = extract_segment(context.input_path(side['original']),
                                                   side['context'], side['segment'])
        if not 2 <= len(values) <= MAX_PACKETS or provenance['group1_observations_used']:
            raise ValueError('selected original packet allowance or provenance differs')
        delta_velocity = values[:, 3:6]*provenance['velocity_scale_mps_per_count']
        clock = values[:, 1]-begin
        streams.append((clock, values[:, 2], delta_velocity))
        readings.append(dict(imu_type=side['segment']['imu_type'], packets=len(values), **provenance))
    duration = end-begin
    rows = []
    for clock_name in CLOCKS:
        for width in WIDTHS:
            context.charge(bound_calls=1, bound_steps=sum(len(clock) for clock, _, _ in streams))
            starts = width*np.arange(math.floor(duration/width))
            windowed = []
            for clock, dt, delta_velocity in streams:
                if clock_name == 'nominal_200Hz':
                    clock = clock[0]-dt[0]+.005*np.arange(1, len(clock)+1)
                    dt = np.full(len(clock), .005)
                mean, _ = window_magnitudes(clock, dt, delta_velocity, starts, width)
                windowed.append(mean)
            rows.append(dict(clock=clock_name, window_seconds=width,
                             **compare_halves(*windowed, starts, width, duration/2)))
    result = dict(passed=True, identity=task['identity'], overlap_seconds=duration,
                  recorders=readings, comparisons=rows, scientific_decision='abstain')
    context.save('paired-accelerometers.json', result)
    return result


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if set(study.rows) != set(LEGS) or study.manifest['scope'] != SCOPE:
            raise ValueError('both original paired flight legs must seal')
        rows = []
        for identity in study.rows:
            envelope = study.envelope(identity)
            result = envelope['result']
            if result['passed'] and (result != study.artifact(identity, 'paired-accelerometers.json')
                    or envelope['charged']['bound_calls'] != LIMITS['bound_calls']
                    or len(result['comparisons']) != COMPARISONS):
                raise ValueError('paired comparison or work count differs')
            rows.append(result)
        value = dict(study.completion, pairs=rows, charged=study.summary['charged'],
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
