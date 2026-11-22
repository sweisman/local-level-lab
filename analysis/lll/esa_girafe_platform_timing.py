# SPDX-License-Identifier: AGPL-3.0-or-later
"""Locate the platform clock using force changes on the opened GIRAFE flight."""

from contextlib import closing
import json
from pathlib import Path
import sys

from . import esa_girafe as girafe
from . import esa_girafe_platform_probe as probe
from .esa_direction_holdout_forecast import frozen_input
from .esa_ftps_bounded_read import GIRAFE_REMOTE, GIRAFE_SOURCE_BYTES, read_esa_range
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-girafe-platform-timing-v1'
SCOPE = 'coarse force-based clock alignment of the opened 187 GIRAFE platform log'
PLAN = probe.clock.forecast.selection.FOLDER+'ESA_GIRAFE_PLATFORM_TIMING_PLAN.md'
RESULT = probe.clock.forecast.selection.FOLDER+'esa-girafe-platform-timing-result.json'
LAYOUT_SHA = 'd259645ee75c7cdbfffaaf7731f02d172a3f869a45d3ac1ca2c2070d160f0c8b'
DIRECTORY = girafe.BASE/'girafe-platform-timing-v1'
REFERENCE = 'GIRAFE_raw_acc_187a-Nuuk-Rey.txt'
REFERENCE_BYTES = girafe.TARGETS[REFERENCE][0]
REFERENCE_ROWS = 234_193
RANGE_BYTES = 1024**2
MIN_CORR, MIN_PEAK_GAP, MAX_OFFSET_CHANGE_S = .70, .10, .2
TASK = dict(identity='girafe-force-clock-match', input_key='layout', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=1+2*len(probe.OFFSETS),
                bound_steps=REFERENCE_BYTES+len(probe.OFFSETS)*(RANGE_BYTES+REFERENCE_ROWS)))


def timing_records(raw, offset, original, audit):
    """Validate complete interior rows against the previously read prefix of this range."""
    import numpy as np

    if len(raw) != RANGE_BYTES or digest(raw[:original['bytes_received']]) != original['sha256']:
        raise ValueError('larger range does not reproduce the saved smaller byte probe')
    first, *inside, last = raw.split(b'\r\n')
    if len(first)+2 != audit['leading_partial_bytes'] or len(last) > probe.ROW_BYTES or len(inside) < 2:
        raise ValueError('unexpected acquisition boundaries')
    checked = probe.inspect_records([row+b'\r\n' for row in inside], audit['first_clock_index'])
    lo = min(checked['phase_min_64ths_tick'], audit['phase_min_64ths_tick'])
    hi = max(checked['phase_max_64ths_tick'], audit['phase_max_64ths_tick'])
    if hi-lo > 64 or checked['first_tag_s'] != audit['first_tag_s']:
        raise ValueError('platform samples do not follow the sealed 1024 Hz clock pattern')
    rows = np.asarray([tuple(map(float, row.split()[:4])) for row in inside])
    receipt = dict(checked, offset=offset, sha256=digest(raw), leading_partial_bytes=len(first)+2,
                   trailing_partial_bytes=len(last), bytes_received=len(raw))
    return rows, receipt


def tenth_second_force(rows):
    """Time-weight candidate vector magnitudes within fully covered tenth seconds."""
    import numpy as np

    centers, magnitudes = tenth_second_values(rows[:, 0], np.linalg.norm(rows[:, 1:4], axis=1)[:, None])
    return centers, magnitudes[:, 0]


def tenth_second_values(time, values):
    import numpy as np

    time, values = np.asarray(time, float), np.asarray(values, float)
    dt = np.diff(time)
    if (time.ndim != 1 or values.ndim != 2 or len(values) != len(time) or len(time) < 3
            or not np.isfinite(time).all() or not np.isfinite(values).all() or np.any((dt <= 0.) | (dt > .0011))):
        raise ValueError('complete sampled force vectors on the validated platform clock required')
    edges = np.arange(np.ceil(time[0]*10), np.floor(time[-1]*10)+1)/10.
    if len(edges) < 41:
        raise ValueError('at least four complete seconds are required for a force fingerprint')
    return (edges[:-1]+edges[1:])/2., held_cell_means(time, values[:-1], edges)


def held_cell_means(time, values, edges):
    """Average left-held samples over fully covered, ordered target cells."""
    import numpy as np

    time, values, edges = (np.asarray(x, float) for x in (time, values, edges))
    if (time.ndim != 1 or len(time) < 2 or edges.ndim != 1 or len(edges) < 2
            or values.ndim != 2 or len(values) != len(time)-1
            or not all(np.isfinite(x).all() for x in (time, values, edges))
            or np.any(np.diff(time) <= 0.) or np.any(np.diff(edges) <= 0.)
            or edges[0] < time[0] or edges[-1] > time[-1]):
        raise ValueError('complete left-held intervals must bracket the target cells')
    baseline = values.mean(axis=0)
    integral = np.cumsum((values-baseline)*np.diff(time)[:, None], axis=0)
    at_edges = np.column_stack([np.interp(edges, time, np.r_[0., axis]) for axis in integral.T])
    return baseline+np.diff(at_edges, axis=0)/np.diff(edges)[:, None]


def reference_series(path):
    import numpy as np

    rows = reference_vectors(path)
    return rows[:, 0], np.linalg.norm(rows[:, 1:], axis=1)


def reference_vectors(path):
    import numpy as np

    girafe.verify_file(path, REFERENCE)
    with path.open('rb') as stream:
        def values():
            for i, row in enumerate(girafe.read_rows(stream)):
                if i == REFERENCE_ROWS:
                    raise ValueError('reference epoch allowance exceeded')
                yield row.utc_seconds, *row.xyz_mps2

        rows = np.fromiter(values(), dtype=np.dtype((float, 4)))
    if len(rows) != REFERENCE_ROWS or np.any(abs(np.diff(rows[:, 0])-.1) > .002):
        raise ValueError('exact complete 10 Hz reference required')
    return rows


def alignment_scores(reference, template):
    """Calculate Pearson correlations for all complete discrete clock offsets."""
    import numpy as np

    ref, target = (np.diff(np.asarray(y, float)) for y in (reference, template))
    size = len(target)
    if size < 3 or size >= len(ref) or not np.isfinite(ref).all() or not np.isfinite(target).all():
        raise ValueError('finite reference and shorter force fingerprint required')
    target -= target.mean()
    shape_energy = float(target@target)
    if shape_energy <= 1e-20:
        raise ValueError('constant platform fingerprint cannot identify the clock')
    windows = np.lib.stride_tricks.sliding_window_view(ref, size)
    scores = np.full(len(windows), -np.inf)
    amplitudes = np.zeros(len(windows))
    for start in range(0, len(windows), 4096):
        block = windows[start:start+4096]
        centered = block-block.mean(axis=1, keepdims=True)
        energy = np.einsum('ij,ij->i', centered, centered)
        cross = centered@target
        valid = energy > 1e-20
        region = slice(start, start+len(block))
        scores[region][valid] = np.clip(cross[valid]/np.sqrt(energy[valid]*shape_energy), -1., 1.)
        amplitudes[region] = cross/shape_energy
    if not np.isfinite(scores).any():
        raise ValueError('reference force changes are too small to score a clock offset')
    return scores, amplitudes


def locate_clock(reference_times, reference, platform_times, template, *, locked_offset=None):
    import numpy as np

    scores, amplitudes = alignment_scores(reference, template)
    starts = np.asarray(reference_times)[:len(scores)]
    if len(starts) != len(scores) or len(platform_times) != len(template) or not np.all(np.diff(starts)>0.):
        raise ValueError('chronological reference and template clocks required')
    best = int(np.argmax(scores))
    separated = np.where(abs(starts-starts[best]) >= 2.-1e-8, scores, -np.inf)
    second = int(np.argmax(separated))
    second_value = float(separated[second]) if np.isfinite(separated[second]) else None
    offset = float(starts[best]-platform_times[0])
    result = dict(best_correlation=float(scores[best]), best_offset_s=offset,
        best_reference_start_utc_s=float(starts[best]), amplitude=float(amplitudes[best]),
        alternate_correlation=second_value, alternate_offset_s=float(starts[second]-platform_times[0])
            if second_value is not None else None,
        candidate_offsets=len(scores), fingerprint_samples=len(template),
        platform_sample_span_s=[float(platform_times[0]), float(platform_times[-1])])
    if locked_offset is None:
        result['passes'] = bool(scores[best] >= MIN_CORR and second_value is not None
                                and scores[best]-second_value >= MIN_PEAK_GAP)
    else:
        nearest = int(np.argmin(abs(starts-(platform_times[0]+locked_offset))))
        result['locked_offset_s'] = locked_offset
        result['locked_correlation'] = float(scores[nearest]) if np.isfinite(scores[nearest]) else None
        result['locked_amplitude'] = float(amplitudes[nearest])
        result['independent_offset_change_s'] = float(offset-locked_offset)
        result['passes'] = bool(scores[nearest] >= MIN_CORR and abs(offset-locked_offset) <= MAX_OFFSET_CHANGE_S)
    return result


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing platform timing study must stay sealed')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=dict(layout=probe.AUDIT_RESULT, ranges=probe.RESULT),
        tasks=[TASK], sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_girafe_platform_timing.py']),
        workers=1, threads=1, maximum_wall_s=180.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact platform timing task required')
    layout = frozen_input(context, 'layout', LAYOUT_SHA)
    old = frozen_input(context, 'ranges', probe.PROBE_SHA)
    if (not layout['common_relative_clock_at_probes'] or layout['parent_sha256'] != probe.PROBE_SHA
            or [row['offset'] for row in layout['probes']] != probe.OFFSETS):
        raise ValueError('checked original platform byte ranges required')
    root = context.root.parents[1]
    certificate, credential = probe.connection_files(root)
    context.charge(bound_calls=1, bound_steps=REFERENCE_BYTES)
    ref_time, ref_force = reference_series(safe_path(root, (girafe.BASE/REFERENCE).as_posix()))
    results = []
    locked = None
    for i, (original, audit) in enumerate(zip(old['probes'], layout['probes'], strict=True)):
        offset = audit['offset']
        row = dict(offset=offset, role='anchor' if i == 0 else 'holdout')
        context.charge(bound_calls=1, bound_steps=RANGE_BYTES)
        try:
            raw = read_esa_range(GIRAFE_REMOTE, GIRAFE_SOURCE_BYTES, offset, RANGE_BYTES, certificate, credential)
        except (ValueError, OSError) as error:
            row.update(status='read_failed', error_type=type(error).__name__)
        else:
            path = safe_path(root, (DIRECTORY/f'range-{offset}.asc').as_posix())
            if not path.exists():
                atomic(path, raw)
            if path.read_bytes() != raw:
                raise ValueError('existing timing range bytes differ')
            row['sha256'] = digest(raw)
            try:
                samples, details = timing_records(raw, offset, original, audit)
                platform_time, platform_force = tenth_second_force(samples)
            except ValueError as error:
                row.update(status='invalid_fingerprint', reason=str(error))
            else:
                row['layout'] = details
                context.charge(bound_calls=1, bound_steps=REFERENCE_ROWS)
                match = locate_clock(ref_time, ref_force, platform_time, platform_force, locked_offset=locked)
                if i == 0 and match['passes']:
                    locked = match['best_offset_s']
                if i and locked is None:
                    match['passes'] = False
                    match['status'] = 'anchor_unavailable'
                row.update(status='scored', alignment=match)
        context.save_bytes(f'range-{offset}.json', encoded(row))
        results.append(row)
    count = sum(row.get('alignment', {}).get('passes', False) for row in results)
    context.save_bytes('timing.json', encoded(dict(ranges=results, reference_sha256=girafe.TARGETS[REFERENCE][1],
        layout_sha256=LAYOUT_SHA, locked_offset_s=locked, coarse_clock_passed=count == len(probe.OFFSETS),
        protected_reads=0, scientific_decision='abstain')))
    return dict(passed=count == len(probe.OFFSETS), qualified_ranges=count, scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        identity = TASK['identity']
        result = study.artifact(identity, 'timing.json')
        expected = dict(TASK['limits'])
        for row in result['ranges']:
            if study.artifact(identity, f"range-{row['offset']}.json") != row:
                raise ValueError('timing window receipt differs from the archive')
            if row['status'] != 'scored':
                expected['bound_calls'] -= 1
                expected['bound_steps'] -= REFERENCE_ROWS
            if 'sha256' in row:
                original = safe_path(root, (DIRECTORY/f"range-{row['offset']}.asc").as_posix())
                if digest(original.read_bytes()) != row['sha256']:
                    raise ValueError('captured platform bytes differ from their receipt')
        if study.rows[identity]['charged'] != expected:
            raise ValueError('platform timing ledger differs from the saved work')
        result['charged'] = expected
        result['manifest_sha256'] = study.completion['manifest_sha256']
    raw = encoded(result)
    target = root/RESULT
    if not target.exists():
        atomic(target, raw)
    if target.read_bytes() != raw:
        raise ValueError('published timing result differs from sealed evidence')
    return dict(sha256=digest(raw), coarse_clock_passed=result['coarse_clock_passed'])


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
