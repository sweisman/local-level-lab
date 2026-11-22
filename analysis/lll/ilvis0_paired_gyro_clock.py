# SPDX-License-Identifier: AGPL-3.0-or-later
"""Earlier-only timing and relative gyro alignment on two frozen NASA pairs."""

import argparse
from contextlib import ExitStack, closing
import hashlib
import json
import math
from pathlib import Path

from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_paired_accelerometers import CLOCKS, FOLDER, ID as PARENT, LEGS, MAX_PACKETS, WINDOW_SUPPORT
from .ilvis0_paired_accelerometers import RESULT as PARENT_REPORT
from .studies.artifacts import digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'ilvis0-paired-gyro-clock-v1'
SCOPE = 'Whole-packet paired NASA recorder alignment across a finite clock-shift grid'
PLAN = FOLDER+'PAIRED_GYRO_CLOCK_PLAN.md'
RESULT = FOLDER+'paired-gyro-clock-result.json'
REQUEST = FOLDER+'paired-gyro-clock-qualification.json'
REPORT = FOLDER+'paired-gyro-clock-tests.xml'
PARENT_SHA = '0c10c258ed231dd9060c0fb74388df4914b748ce8efc365df1fdcc7cf0d1dd2a'
TEST = 'analysis/tests/test_ilvis0_paired_gyro_clock.py'
TESTS = ('test_window_sums_signed_packets_and_ignores_partial_edges',
         'test_shifted_windows_cannot_cross_split_or_overlap_end',
         'test_align_from_earlier_half_only_and_recover_delay')
WIDTHS = (.25, 1.)
SHIFTS = tuple(step*.005 for step in range(-60, 61))
COMPARISONS = len(CLOCKS)*len(WIDTHS)
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=2+COMPARISONS*(len(SHIFTS)+2), bound_steps=2*MAX_PACKETS)


class PacketRates:
    """Whole-packet durations and signed angle sums in a shared time origin."""

    def __init__(self, ends, durations, increments):
        import numpy as np

        ends, dt, angle = (np.asarray(a, float) for a in (ends, durations, increments))
        if (ends.ndim != 1 or not 2 <= len(ends) <= MAX_PACKETS or dt.shape != ends.shape
                or angle.shape != (len(ends), 3) or any(not np.isfinite(a).all() for a in (ends, dt, angle))
                or np.any(dt <= 0.) or np.any(np.diff(ends) <= 0.)
                or np.any(abs(np.diff(ends)-dt[1:]) > 1e-8)):
            raise ValueError('finite contiguous timed increments required')
        self.ends, self.starts = ends, ends-dt
        self.duration = np.r_[0., np.cumsum(dt)]
        self.angles = np.vstack((np.zeros(3), np.cumsum(angle, axis=0)))

    def bounds(self, starts, width):
        import numpy as np

        query = np.asarray(starts, float)
        if (query.ndim != 1 or not np.isfinite(query).all() or not math.isfinite(width) or width <= 0.
                or np.any(np.diff(query) < width-1e-8)):
            raise ValueError('finite disjoint windows with a positive width required')
        first = np.searchsorted(self.starts, query-1e-9, side='left')
        last = np.maximum(first, np.searchsorted(self.ends, query+width+1e-9, side='right'))
        return first, last, self.duration[last]-self.duration[first]

    def coverage(self, starts, width):
        return self.bounds(starts, width)[2]/width

    def windows(self, starts, width):
        import numpy as np

        first, last, used = self.bounds(starts, width)
        valid = used >= WINDOW_SUPPORT*width
        rate = np.full((len(first), 3), np.nan)
        rate[valid] = (self.angles[last[valid]]-self.angles[first[valid]])/used[valid, None]
        return rate, used/width


def split_windows(starts, width, duration, shift):
    midpoint = duration/2.
    return ((starts-shift >= 0.) & (starts+width+shift <= midpoint),
            (starts-shift >= midpoint) & (starts+width+shift <= duration))


def alignment(target, source):
    import numpy as np
    from .ilvis0_pair_alignment import MIN_SINGULAR_RATIO

    ma, mb = target.mean(axis=0), source.mean(axis=0)
    a, b = target-ma, source-mb
    singular = np.linalg.svd(b, compute_uv=False)
    ratio = float(singular[-1]/singular[0]) if singular[0] > 0. else 0.
    if ratio < MIN_SINGULAR_RATIO:
        return ratio, None
    u, _, vt = np.linalg.svd(a.T@b)
    rotation = (u*np.array([1., 1., np.linalg.det(u@vt)]))@vt
    offset = ma-rotation@mb
    rms = float(np.sqrt(np.mean(np.sum((target-source@rotation.T-offset)**2, axis=1))))
    return ratio, (rms, rotation, offset)


def compare(left, right, *, duration, width, reserve):
    import numpy as np
    from .ilvis0_pair_alignment import MIN_HALF_SECONDS, _metrics, _window_vector_rms

    starts = width*np.arange(math.floor(duration/width))
    reserve()
    earlier, later = split_windows(starts, width, duration, max(SHIFTS))
    valid = left.coverage(starts, width) >= WINDOW_SUPPORT
    for shift in SHIFTS:
        valid &= right.coverage(starts+shift, width) >= WINDOW_SUPPORT
    train, hold = np.flatnonzero(earlier & valid), np.flatnonzero(later & valid)
    if min(len(train), len(hold))*width < MIN_HALF_SECONDS:
        raise ValueError('less than 60 seconds of common whole-packet support in one half')

    target = left.windows(starts[train], width)[0]
    curve, fitted = [], {}
    for shift in SHIFTS:
        reserve()
        ratio, fit = alignment(target, right.windows(starts[train]+shift, width)[0])
        curve.append(dict(shift_s=shift, ratio=ratio, vector_rms_dph=None if fit is None else fit[0]))
        if fit is not None:
            fitted[shift] = fit
    reserve()
    result = dict(earlier_windows=len(train), later_windows=len(hold), earlier_curve=curve)
    if 0. not in fitted:
        return dict(result, status='unresolved_zero_shift_alignment')
    chosen = min(fitted, key=lambda shift: (fitted[shift][0], abs(shift), shift))
    actual = left.windows(starts[hold], width)[0]
    scores = {}
    for name, shift in (('zero', 0.), ('shifted', chosen)):
        earlier_rms, rotation, offset = fitted[shift]
        residual = actual - right.windows(starts[hold]+shift, width)[0] @ rotation.T - offset
        weights = np.ones(len(hold))
        scores[name] = dict(rotation=rotation.tolist(), offset_dph=offset.tolist(), earlier_rms_dph=earlier_rms,
            **_metrics(residual, weights), ten_second=_window_vector_rms(hold, residual, weights, int(10/width)))
    return dict(result, status='scored', shift_s=chosen, later=scores)


def task_for(identity):
    return dict(identity=identity, input_key=identity, limits=LIMITS)


def qualification(root, *, check):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), TEST, PLAN))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('reuse the existing paired gyro timing freeze')
    sources = qualification(root, check=True)
    prior = (root/PARENT_REPORT).read_bytes()
    if digest(prior) != PARENT_SHA:
        raise ValueError('exact earlier paired recorder report required')
    sealed = json.loads(prior)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    materials = dict(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_POLICY))
    inputs = dict(plan=PLAN, prior=PARENT_REPORT, qualification=REQUEST, qualification_tests=REPORT)
    originals = {}
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if (any(sealed[key] != value for key, value in parent.completion.items())
                or not parent.summary['passed'] or set(parent.rows) != set(LEGS)):
            raise ValueError('exact complete earlier recorder comparison required')
        for identity in LEGS:
            if parent.artifact(identity, 'paired-accelerometers.json') != parent.envelope(identity)['result']:
                raise ValueError('paired recorder evidence differs from its seal')
            layout = parent.input(identity)
            for side in layout['sides']:
                key = side['original']
                record = parent.manifest['inputs'][key]
                original = safe_path(root, record['source'])
                if not record['source'].startswith('data/ilvis0-ready/') or not original.is_file():
                    raise ValueError('selected original recorder file required in the open NASA corpus')
                with original.open('rb') as stream:
                    if hashlib.file_digest(stream, 'sha256').hexdigest() != record['sha256']:
                        raise ValueError('compressed original differs from the earlier recording freeze')
                inputs[key], originals[key] = record['source'], record['sha256']
            materials[identity] = encoded(dict(layout, compressed_shas={side['original']: originals[side['original']]
                                                                         for side in layout['sides']}))
    for key, raw in materials.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, raw)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=inputs,
        sources=sources, tasks=[task_for(identity) for identity in LEGS], workers=2, threads=1, maximum_wall_s=180.)
    manifest = Definition.from_dict(definition, root).prepare(root)
    if any(manifest['inputs'][key]['sha256'] != saved for key, saved in originals.items()):
        raise ValueError('compressed original differs from the earlier recording freeze')
    return manifest['limits']


def evaluate(task, context):
    import numpy as np
    from .ilvis0_segments import extract_segment
    from .ilvis0_stretch_analytics import DPH

    identity = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or identity not in LEGS or declared != task_for(identity):
        raise ValueError('exact frozen NASA recorder pair required')
    layout = json.loads(context.input_path().read_bytes())
    begin, end = layout['begin'], layout['end']
    if any(context.manifest['inputs'][side['original']]['sha256'] != layout['compressed_shas'][side['original']]
           for side in layout['sides']):
        raise ValueError('packed input contents must match the earlier raw sources')
    streams, records = [], []
    for side, imu_type in zip(layout['sides'], LEGS[identity], strict=True):
        context.charge(bound_calls=1, bound_steps=MAX_PACKETS)
        values, _, _, provenance = extract_segment(context.input_path(side['original']), side['context'], side['segment'])
        if (not 2 <= len(values) <= MAX_PACKETS or provenance['group1_observations_used']
                or side['segment']['imu_type'] != imu_type):
            raise ValueError('original increment allowance and recorder type must match')
        streams.append((values[:, 1]-begin, values[:, 2], values[:, 9:12]*DPH))
        records.append(dict(imu_type=imu_type, **provenance))

    def reserve():
        context.charge(bound_calls=1, bound_steps=0)

    rows = []
    for clock in CLOCKS:
        if clock == 'nominal_200Hz':
            rates = [PacketRates(times[0]-dt[0]+.005*np.arange(1, len(dt)+1), np.full(len(dt), .005), angle)
                     for times, dt, angle in streams]
        else:
            rates = [PacketRates(*stream) for stream in streams]
        for width in WIDTHS:
            scores = compare(*rates, duration=end-begin, width=width, reserve=reserve)
            rows.append(dict(clock=clock, window_seconds=width, **scores))
    result = dict(pair=identity, recorders=records, comparisons=rows, new_fits=0, protected_reads=0,
                  scientific_decision='abstain', passed=True)
    context.save('paired-clock.json', result)
    return result


def report(root):
    from .studies.task_resume import resume_campaign
    from .studies.validation_resume import _stage_paths

    prefix = 'data/'+ID
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        studies = [original]
        if len(original.rows) != len(original.tasks) or any(original.envelope(i)['status'] == 'interrupted'
                                                             for i in original.rows):
            continuation = root/(prefix+'-recovery')
            if resume_campaign(root, continuation, launch=False)['state'] != 'all_tasks_finished':
                raise ValueError('verified recorder continuation required')
            studies.extend(stack.enter_context(closing(ClosedStudy(root, p.relative_to(root).as_posix(),
                          store=original.store))) for p in _stage_paths(continuation))
        rows = {}
        for study in studies:
            for identity in study.rows:
                envelope = study.envelope(identity)
                if envelope['status'] == 'interrupted':
                    continue
                if identity in rows or envelope['status'] != 'complete' or identity not in LEGS:
                    raise ValueError('one terminal result per paired-leg identity required')
                result = envelope['result']
                if result['passed'] and (envelope['charged'] != LIMITS or result != study.artifact(identity, 'paired-clock.json')):
                    raise ValueError('sealed pair timing evidence differs from its work')
                rows[identity] = result
        if set(rows) != set(LEGS) or original.manifest['scope'] != SCOPE:
            raise ValueError('both frozen recorder identities must be terminal')
        closures = {study.prefix: study.completion for study in studies}
    _write_equal(root/RESULT, encoded(dict(rows=rows, closures=closures, new_fits=0, protected_reads=0,
                                         scientific_decision='abstain')))
    return dict(pairs=len(rows), technical_passes=sum(row['passed'] for row in rows.values()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, check=False) if action == 'request' else {'prepare': prepare, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
