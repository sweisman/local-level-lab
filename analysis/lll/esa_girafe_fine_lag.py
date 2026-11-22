# SPDX-License-Identifier: AGPL-3.0-or-later
"""Retrospective fine-lag comparison on six unchanged GIRAFE clips."""

from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sys

from . import esa_girafe_ground_rate as ground
from . import esa_girafe_platform_imar_force as pair
from .esa_direction_holdout_forecast import frozen_input
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-girafe-fine-lag-v1'
SCOPE = 'score unchanged ground and airborne GIRAFE forces against iMAR on a fine lag grid'
PLAN = ground.rate.holdout.FOLDER+'ESA_GIRAFE_FINE_LAG_PLAN.md'
RESULT = ground.rate.holdout.FOLDER+'esa-girafe-fine-lag-result.json'
WIDTHS = (1, 3, 11, 21)
PRIMARY = WIDTHS.index(pair.WIDTH)
GUARD = 200
LAGS_MS = tuple(range(-10*GUARD, 10*GUARD+1, 10))
GROUND_BYTES = ground.RANGE_BYTES+2*ground.OVERLAP
CLIPS = len(ground.TARGETS)+len(pair.holdout.OFFSETS)
SCORED = CLIPS*len(WIDTHS)*len(LAGS_MS)
INPUTS = dict(ground=ground.RESULT, air=pair.RESULT, ground_ranges=ground.TRANSFER,
              air_ranges=(pair.holdout.DIRECTORY/'transfer-receipt.json').as_posix(), probes=pair.timing.probe.RESULT)
SHAS = dict(
    ground='20d8de070f7fd4e14ba0e7117fe8ab8b53cf76f03f03d6196a59b56c8ae1d8dd',
    air='3b54ab955d1e5e22280d65c5be3dbc1929521408c1d7eb1bc7c607a3778e9e68',
    ground_ranges='85dac9fb22237a32b8b8dcebc96291327ba19d5d16d5d4504cfe71c2a696c656',
    air_ranges=pair.holdout.RECEIPT_SHA, probes=pair.timing.probe.PROBE_SHA)
TASK = dict(identity='fine-force-lag-on-six-saved-clips', input_key='ground', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=1+3*CLIPS,
        bound_steps=ground.SOURCE_BYTES+len(ground.TARGETS)*GROUND_BYTES+
                    len(pair.holdout.OFFSETS)*ground.RANGE_BYTES+CLIPS*pair.MAX_INTERVALS+SCORED))


def lagged_cell_means(edges, values, *, first, count):
    """Integrate held samples over every tenth-second cell in each lag."""
    import numpy as np

    grid = first+np.arange(-GUARD, 10*count+GUARD+1)/100.
    fine = pair.timing.held_cell_means(edges, np.asarray(values)[:, None], grid)[:, 0]
    baseline = fine.mean()
    integrated = np.r_[0., np.cumsum((fine-baseline)*np.diff(grid))]
    lo = np.arange(len(LAGS_MS))[:, None]+10*np.arange(count)
    hi = lo+10
    return baseline+(integrated[hi]-integrated[lo])/(grid[hi]-grid[lo])


def score_lags(platform, reference, *, width):
    return [dict(lag_ms=lag, **pair.response.force_response(platform, values, width))
            for lag, values in zip(LAGS_MS, reference, strict=True)]


def summarize(clips):
    stops = [row['widths'][PRIMARY]['scores'] for row in clips if row['phase'] == 'ground']
    if len(stops) != len(ground.TARGETS):
        raise ValueError('all fixed ground clips are required to choose the common lag')
    index = max(range(len(LAGS_MS)), key=lambda i: (min(s[i]['correlation'] for s in stops), -abs(LAGS_MS[i])))
    rows = []
    for clip in clips:
        widths = []
        for width_row in clip['widths']:
            scores = width_row['scores']
            if tuple(row['lag_ms'] for row in scores) != LAGS_MS:
                raise ValueError('complete ordered lag grid required')
            best = max(scores, key=lambda row: (row['correlation'], -abs(row['lag_ms'])))
            widths.append(dict(width_samples=width_row['width_samples'], best=best,
                               original=scores[GUARD], common=scores[index]))
        rows.append(dict(phase=clip['phase'], offset=clip['offset'], widths=widths))
    return dict(common_lag_ms=LAGS_MS[index], clips=rows)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('keep the existing saved-clip comparison sealed')
    for key in ('ground', 'air'):
        if digest((root/INPUTS[key]).read_bytes()) != SHAS[key]:
            raise ValueError('prior exact saved comparison required')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=INPUTS, tasks=[TASK],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_girafe_fine_lag.py']),
        workers=1, threads=1, maximum_wall_s=120.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def _prepared_rows(root, entry, prefix, phase):
    offset = entry['offset']
    if phase == 'ground':
        raw, probe = ground._source_ranges(root, offset)
        if digest(probe) != entry['short_sha256'] or ground.overlap_digest(raw, probe) != entry['expected_overlap_sha256']:
            raise ValueError('original ground transfer differs')
        return ground._checked_rows(raw, entry, prefix)[0]
    path = safe_path(root, (pair.holdout.DIRECTORY/f'range-{offset}.asc').as_posix())
    if path.stat().st_size != ground.RANGE_BYTES:
        raise ValueError('precisely one saved airborne platform range required')
    return pair.holdout.new_samples(path.read_bytes(), entry, prefix, all_force_axes=True)[0]


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if declared != TASK or context.manifest['scope'] != SCOPE:
        raise ValueError('exact finite saved lag comparison required')
    inputs = {key: frozen_input(context, key, sha) for key, sha in SHAS.items()}
    source_sha = inputs['ground']['imar_sha256']
    if (source_sha != inputs['air']['imu_source_sha256']
            or tuple(row['offset'] for row in inputs['ground_ranges']['range_receipts']) != tuple(o for _, o in ground.TARGETS)
            or tuple(row['offset'] for row in inputs['air_ranges']['ranges']) != pair.holdout.OFFSETS):
        raise ValueError('exact ground and airborne clips from a common recording required')
    root = context.root.parents[1]
    original = safe_path(root, ground.SOURCE)
    cohorts = (
        ('ground', inputs['ground_ranges']['range_receipts'], inputs['ground']['excerpts'], GROUND_BYTES),
        ('air', inputs['air_ranges']['ranges'], inputs['air']['ranges'], ground.RANGE_BYTES),
    )
    clips = []
    with original.open('rb') as stream:
        context.charge(bound_calls=1, bound_steps=ground.SOURCE_BYTES)
        before = os.fstat(stream.fileno())
        if before.st_size != ground.SOURCE_BYTES or hashlib.file_digest(stream, 'sha256').hexdigest() != source_sha:
            raise ValueError('original iMAR log differs')
        stream.seek(0)
        header = stream.read(ground.WIDTH)
        for phase, entries, previous, allowance in cohorts:
            for entry, old in zip(entries, previous, strict=True):
                offset = entry['offset']
                if offset != old['offset'] or entry['sha256'] != old.get('platform_sha256', old.get('source_sha256')):
                    raise ValueError('same complete earlier scored platform clip required')
                context.charge(bound_calls=1, bound_steps=allowance)
                rows = _prepared_rows(root, entry, inputs['probes']['prefix'], phase)
                force = np.linalg.norm(rows[:, 1:4], axis=1)
                centers, platform = pair.timing.tenth_second_values(rows[:, 0], force[:, None])
                first = centers[0]-.05+ground.DELTA_GPS_S
                count = len(centers)
                lower, upper = first-GUARD/100., first+(10*count+GUARD)/100.
                saved_span = old.get('imar_gps_span_s', old.get('target_gps_span_s'))
                if not np.allclose([lower, upper], saved_span, rtol=0., atol=1e-9):
                    raise ValueError('new grid must keep the original independent source support')
                context.charge(bound_calls=1, bound_steps=pair.MAX_INTERVALS)
                time, values, _ = ground.held_measurements(stream, header, row_bytes=ground.WIDTH, row_count=ground.RECORDS,
                    maximum_samples=pair.MAX_INTERVALS, lower=lower, upper=upper)
                reference = lagged_cell_means(time, np.linalg.norm(values, axis=1), first=first, count=count)
                context.charge(bound_calls=1, bound_steps=len(WIDTHS)*len(LAGS_MS))
                widths = [dict(width_samples=width, scores=score_lags(platform[:, 0], reference, width=width)) for width in WIDTHS]
                prior = old['force_clock'] if phase == 'ground' else old['comparisons']['force_norm']
                coarse = widths[PRIMARY]['scores'][::10]
                error = max(abs(a['correlation']-b['correlation']) for a, b in zip(coarse, prior['scores'], strict=True))
                if error > 5e-8:
                    raise ValueError('fine grid did not reproduce previous coarse lag correlations')
                clip = dict(phase=phase, offset=offset, widths=widths, coarse_replay_max_error=error)
                clips.append(clip)
                context.save_bytes(f'range-{offset}.json', encoded(clip))
        after = os.fstat(stream.fileno())
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('iMAR log changed during verification')
    result = summarize(clips)
    context.save_bytes('fine-lag-summary.json', encoded(dict(result, inputs=SHAS, scores=SCORED,
        scientific_decision='abstain', absolute_timing_qualified=False, model_fits=0, protected_reads=0)))
    return dict(passed=len(clips) == CLIPS, clips=len(clips), scientific_decision='abstain')


def report(root):
    identity = TASK['identity']
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.rows[identity]['charged'] != TASK['limits']:
            raise ValueError('closed lag comparison and complete charges required')
        result = study.artifact(identity, 'fine-lag-summary.json')
        expected = tuple(o for _, o in ground.TARGETS)+pair.holdout.OFFSETS
        clips = [study.artifact(identity, f'range-{offset}.json') for offset in expected]
        if tuple(clip['offset'] for clip in clips) != expected or any(result[key] != value for key, value in summarize(clips).items()):
            raise ValueError('saved common lag or summaries differ')
        result.update(manifest_sha256=study.completion['manifest_sha256'], charged=TASK['limits'],
                      coarse_replay_max_error=max(clip['coarse_replay_max_error'] for clip in clips))
    raw = encoded(result)
    path = root/RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved lag report differs from the sealed study')
    return dict(sha256=digest(raw), common_lag_ms=result['common_lag_ms'], scores=result['scores'])


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
