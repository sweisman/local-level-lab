# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check recorder disagreement on the saved NASA force-only windows."""

import argparse
from contextlib import ExitStack, closing
import gzip
import io
import json
import math
from pathlib import Path

from .studies.artifacts import digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'ilvis0-paired-force-windows-v1'
SCOPE = 'Optimistic paired recorder disagreement on retained NASA force windows'
FOLDER = 'docs/ilvis0-measurement-contribution/'
PLAN = FOLDER+'PAIRED_FORCE_WINDOW_PLAN.md'
REQUEST = FOLDER+'paired-force-window-qualification-v2.json'
TEST_REPORT = FOLDER+'paired-force-window-tests-v2.xml'
RESULT = FOLDER+'paired-force-window-result.json'
TEST = 'analysis/tests/test_ilvis0_paired_force_windows.py'
TESTS = ('test_companion_bounds_do_not_interpolate_edge_packets',
         'test_clock_allowance_widens_packet_bounds_and_missing_support_is_explicit',
         'test_common_offset_gap_keeps_relative_gain_constant_across_windows')
PARENT_REPORTS = {
    'matched-extension-force-result.json': '883f2f119ba52104992f8f46254d0816281b56a2fd48f6fe7c8946b90e704771',
    'paired-accelerometers-result.json': '0c10c258ed231dd9060c0fb74388df4914b748ce8efc365df1fdcc7cf0d1dd2a',
    'matched-extension-inputs-receipt.json': '582cf25123f6223da9cfbd884d75bbf863604932dac0339de2fdfb3fb47e8bee',
}
CLOCKS = ('nominal_200Hz', 'header_elapsed')
OFFSETS = (0., .005, .30)
MAX_GAIN = 1.15
MAX_PACKETS = 150_000
STEPS = 48
ROUNDING = 1e-9


def companion_bounds(edges, packet_bounds, starts, ends, offset):
    """Bound an average of nonnegative packet masses with unallocated edges."""
    import numpy as np

    edges, values, starts, ends = map(np.asarray, (edges, packet_bounds, starts, ends))
    if (edges.ndim != 1 or len(edges) < 2 or np.any(np.diff(edges) <= 0.)
            or values.shape != (len(edges)-1, 2) or np.any(values[:, 0] < 0.)
            or np.any(values[:, 1] < values[:, 0]) or starts.ndim != 1 or ends.shape != starts.shape
            or np.any(ends <= starts) or not 0. <= offset <= .30
            or any(not np.isfinite(v).all() for v in (edges, values, starts, ends))):
        raise ValueError('ordered packet and window supports required')
    good = (starts-offset >= edges[0]) & (ends+offset <= edges[-1])
    inner_first = np.searchsorted(edges, starts+offset, side='left')
    inner_last = np.searchsorted(edges, ends-offset, side='right')-1
    outer_first = np.searchsorted(edges, starts-offset, side='right')-1
    outer_last = np.searchsorted(edges, ends+offset, side='left')
    low, high = np.full(starts.shape, np.nan), np.full(starts.shape, np.nan)
    sums = np.vstack(([0., 0.], np.cumsum(values, axis=0, dtype=np.longdouble)))
    first, last = inner_first[good], np.maximum(inner_first[good], inner_last[good])
    duration = ends[good]-starts[good]
    low[good] = np.maximum(0., (sums[last, 0]-sums[first, 0])/duration-ROUNDING)
    high[good] = (sums[outer_last[good], 1]-sums[outer_first[good], 1])/duration+ROUNDING
    return low, high


def common_offset_gap(intervals, ratio_range):
    """Bracket the smallest uniform interval gap after one gain and offset."""
    import numpy as np

    rows = np.asarray(intervals, dtype=float)
    lo, hi = ratio_range
    if (rows.ndim != 2 or rows.shape[1] != 4 or not len(rows) or not np.isfinite(rows).all()
            or np.min(rows) < 0. or np.max(rows) > 100. or np.any(rows[:, ::2] > rows[:, 1::2])
            or not 0. < lo <= hi <= 2.):
        raise ValueError('finite nonnegative intervals and a positive ordered gain range required')
    a_lo, a_hi, b_lo, b_hi = rows.T

    def support(ratio):
        lower, upper = a_lo-ratio*b_hi, a_hi-ratio*b_lo
        left, right = np.argmax(lower), np.argmin(upper)
        return (float(lower[left]-upper[right])/2., float(b_lo[right]-b_hi[left])/2.)

    for _ in range(STEPS):
        mid = lo+(hi-lo)/2.
        _, slope = support(mid)
        if slope < 0.:
            lo = mid
        elif slope > 0.:
            hi = mid
        else:
            lo = hi = mid
            break
    endpoints = [(ratio, *support(ratio)) for ratio in (lo, hi)]
    lower = max(value + min(slope*(lo-ratio), slope*(hi-ratio))
                for ratio, value, slope in endpoints)
    gain, upper, _ = min(endpoints, key=lambda row: row[1])
    return max(0., lower-ROUNDING), max(0., upper)+ROUNDING, gain


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def limits(windows):
    per_clock = (MAX_PACKETS+windows+2*windows*(STEPS+2))*len(OFFSETS)
    return dict(native_calls=0, packet_visits=0, bound_calls=1+len(CLOCKS)*len(OFFSETS),
                bound_steps=MAX_PACKETS+len(CLOCKS)*per_clock)


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .ilvis0_matched_extension_force import ID as FORCE
    from .ilvis0_matched_extension_inputs import ID as ALIGNED
    from .ilvis0_matched_observed_inputs import _write_equal
    from .ilvis0_paired_accelerometers import ID as PAIRED
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('use the already frozen paired force-window study')
    deps, environment = sources(root), runtime_environment()
    qualification, tests = checked(root, REQUEST, sources=deps, environment=environment,
                                   required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    materials = dict(qualification=qualification, qualification_tests=tests, recovery=recovery,
        recovery_tests=recovery_tests, recovery_policy=encoded(dict(RECOVERY_POLICY, maximum_wall_s=240)))
    inputs, tasks = {'plan': PLAN}, []
    with ExitStack() as stack:
        force = stack.enter_context(closing(ClosedStudy(root, 'data/'+FORCE)))
        paired, aligned = [stack.enter_context(closing(ClosedStudy(root, 'data/'+name, store=force.store)))
                           for name in (PAIRED, ALIGNED)]
        for study, (filename, expected) in zip((force, paired, aligned), PARENT_REPORTS.items(), strict=True):
            path = FOLDER+filename
            raw = safe_path(root, path).read_bytes()
            if (digest(raw) != expected or not study.summary['passed'] or len(study.rows) != 2
                    or any(json.loads(raw)[key] != value for key, value in study.completion.items())):
                raise ValueError('exact verified paired, alignment and window parents required')
            inputs[filename] = path
        for leg in paired.rows:
            layout = paired.input(leg)
            saved = paired.artifact(leg, 'paired-accelerometers.json')
            primary, = [row for row in saved['recorders'] if row['segment_id'] in aligned.rows]
            companion, = [row for row in saved['recorders'] if row is not primary]
            recording, = [row for row in layout['sides'] if row['segment']['segment_id'] == companion['segment_id']]
            original = paired.manifest['inputs'][recording['original']]
            if digest(safe_path(root, original['source']).read_bytes()) != original['sha256']:
                raise ValueError('the original frozen companion stream is required')
            identity = primary['segment_id']
            pin = aligned.artifact(identity, 'packet-provenance.json')
            if any(primary[key] != pin[key] for key in pin):
                raise ValueError('the primary recording and packet support must match')
            raw_windows = force.artifact(identity, 'windows.json.gz', raw=True)
            windows = json.loads(gzip.decompress(raw_windows))['windows']
            targets = [row for row in windows if row['state'] == 'supported']
            count = len(targets)
            if len(windows) != force.tasks[identity]['targets'] or not 1 <= count <= 600:
                raise ValueError('saved force window count differs')
            inputs[leg+'-original'] = original['source']
            materials[leg+'-packets'] = aligned.artifact(identity, 'packets.npy.gz', raw=True)
            materials[leg] = encoded(dict(primary=pin, companion=companion, recording=recording,
                begin=layout['begin'], end=layout['end'], windows=targets, original_windows=len(windows)))
            tasks.append(dict(identity=leg, input_key=leg, windows=count, limits=limits(count)))
    for key, data in materials.items():
        relative = f'data/{ID}-inputs/{key}'
        _write_equal(root/relative, data)
        inputs[key] = relative
    definition = dict(id=ID, scope=SCOPE, sources=deps, inputs=inputs, tasks=tasks,
        adapter=Path(__file__).relative_to(root).as_posix(), workers=2, threads=1, maximum_wall_s=180.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .ilvis0_segments import extract_segment

    leg, count = task['identity'], task['windows']
    layout = json.loads(context.input_path().read_bytes())
    windows = layout['windows']
    if context.manifest['scope'] != SCOPE or len(windows) != count or task['limits'] != limits(count):
        raise ValueError('exact saved paired window allowance required')
    primary = np.load(io.BytesIO(gzip.decompress(context.input_path(leg+'-packets').read_bytes())),
                      allow_pickle=False)
    context.charge(bound_calls=1, bound_steps=MAX_PACKETS)
    recording = layout['recording']
    other, _, _, provenance = extract_segment(context.input_path(leg+'-original'),
                                              recording['context'], recording['segment'])
    if (any(value != layout['companion'][name] for name, value in provenance.items())
            or primary.shape != (layout['primary']['native_packets'], 15)
            or len(primary) > MAX_PACKETS or len(other) > MAX_PACKETS):
        raise ValueError('unchanged original signed packets required')
    origin = layout['primary']['first_interval_start_utc_s']
    shift = provenance['first_interval_start_utc_s']-origin
    bounds = np.abs(other[:, 3:6])
    masses = provenance['velocity_scale_mps_per_count']*np.column_stack((
        np.linalg.norm(np.maximum(0., bounds-.5), axis=1), np.linalg.norm(bounds+.5, axis=1)))
    starts = np.array([row['packet_first'] for row in windows])
    stops = np.array([row['packet_stop'] for row in windows])
    earlier = np.array([row['side'] == 'training' for row in windows])
    profiles, details = [], []
    for clock in CLOCKS:
        p_edges = np.r_[0., primary[:, 1]-origin] if clock == 'header_elapsed' else .005*np.arange(len(primary)+1)
        c_edges = np.r_[shift, other[:, 1]-origin] if clock == 'header_elapsed' else shift+.005*np.arange(len(other)+1)
        lo = np.array([row[clock+'_lower_mps2'] for row in windows])
        hi = np.array([row[clock+'_upper_mps2'] for row in windows])
        for offset in OFFSETS:
            context.charge(bound_calls=1, bound_steps=MAX_PACKETS+count+2*count*(STEPS+2))
            a, b = p_edges[starts], p_edges[stops]
            low, high = companion_bounds(c_edges, masses, a, b, offset)
            keep = (np.isfinite(low) & (a-offset >= layout['begin']-origin)
                    & (b+offset <= layout['end']-origin))
            if not np.any(keep & earlier) or not np.any(keep & ~earlier):
                raise ValueError('both portions need complete common recorder support')
            values = np.column_stack((lo, hi, low, high))
            row = dict(clock=clock, maximum_relative_offset_s=offset, retained=int(keep.sum()),
                excluded=int((~keep).sum()), earlier_windows=int((keep & earlier).sum()),
                later_windows=int((keep & ~earlier).sum()),
                median_edge_width_mps2=float(np.median((high-low)[keep])))
            for role, selected in (('earlier', keep & earlier), ('all', keep)):
                result = common_offset_gap(values[selected], (1./MAX_GAIN, MAX_GAIN))
                row[role] = dict(lower_mps2=result[0], upper_mps2=result[1], ratio=result[2],
                                 per_recorder_error_floor_mps2=result[0]/(2.*MAX_GAIN))
            row['later_requires_more_than_earlier'] = row['all']['lower_mps2'] > row['earlier']['upper_mps2']
            profiles.append(row)
            details.append(dict(clock=clock, offset=offset, windows=[
                dict(tag=w['gps_millisecond_tag'], role=w['side'], bounds_mps2=values[i].tolist() if good else None)
                for i, (w, good) in enumerate(zip(windows, keep, strict=True))]))
    result = dict(passed=True, identity=leg, segment_id=layout['primary']['segment_id'],
                  profiles=profiles, new_fits=0, scientific_decision='abstain')
    context.save_bytes('window-bounds.json.gz', gzip.compress(encoded(details), mtime=0))
    context.save('paired-force.json', result)
    return result


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if len(study.rows) != 2 or study.manifest['scope'] != SCOPE:
            raise ValueError('both paired window tasks must seal')
        results = []
        for identity in study.rows:
            envelope = study.envelope(identity)
            result = envelope['result']
            if result['passed']:
                if (result != study.artifact(identity, 'paired-force.json')
                        or envelope['charged'] != limits(study.tasks[identity]['windows'])):
                    raise ValueError('paired window result or charges changed')
                result = dict(result, support_sha256=digest(study.artifact(identity, 'window-bounds.json.gz', raw=True)))
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
