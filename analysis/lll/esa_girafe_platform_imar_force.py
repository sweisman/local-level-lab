# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare saved platform force changes to separately recorded iMAR forces."""

from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sys

from . import esa_direction_holdout_score as imar
from . import esa_girafe_platform_timing as timing
from . import esa_girafe_platform_vertical_holdout as holdout
from . import esa_girafe_platform_vertical_response as response
from .esa_direction_holdout_forecast import frozen_input
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-girafe-platform-imar-force-v1'
SCOPE = 'check the fixed 187 platform clock against separately recorded iMAR force'
PLAN = holdout.FOLDER+'ESA_GIRAFE_PLATFORM_IMAR_FORCE_PLAN.md'
RESULT = holdout.FOLDER+'esa-girafe-platform-imar-force-result.json'
RESPONSE_SHA = '6ace84fe9ba24ef55508683fae0123b8bfd8d652de707928987be4c04fc00657'
CLOCK_SHA = 'd92ab61e055f215c26f0e31650cfd3ddf52030f126b04c993f85a3958ae743e4'
MAX_INTERVALS = 5000
LAG_STEPS = 20
WIDTH = 11
SIGNALS = ('force_norm', 'candidate_vertical')
TASK = dict(identity='compare-force-on-separate-imar-clock', input_key='clock', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=1+len(holdout.OFFSETS)*(2+len(SIGNALS)),
        bound_steps=imar.SOURCE_BYTES+len(holdout.OFFSETS)*(
            timing.RANGE_BYTES+MAX_INTERVALS+len(SIGNALS)*(2*LAG_STEPS+1))))


def lag_scores(platform, reference, *, width=WIDTH, lag_steps=LAG_STEPS):
    if len(reference) != len(platform)+2*lag_steps:
        raise ValueError('complete paired supports at every declared lag required')
    scores = [dict(lag_tenths_s=shift, **response.force_response(platform,
                    reference[shift+lag_steps:shift+lag_steps+len(platform)], width))
              for shift in range(-lag_steps, lag_steps+1)]
    best = max(scores, key=lambda row: (row['correlation'], -abs(row['lag_tenths_s'])))
    locked = scores[lag_steps]
    return dict(locked=locked, best=best, scores=scores,
                passes=locked['correlation'] >= .70 and abs(best['lag_tenths_s']) <= 2)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing iMAR force check must stay sealed')
    with closing(ClosedStudy(root, 'data/'+response.ID)) as study:
        if not study.summary['passed'] or digest((root/response.RESULT).read_bytes()) != RESPONSE_SHA:
            raise ValueError('exact sealed response diagnosis required')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=dict(response=response.RESULT,
        clock=imar.forecast.selection.FOLDER+'esa-direction-holdout-clock.json',
        receipt=(holdout.DIRECTORY/'transfer-receipt.json').as_posix(), probes=timing.probe.RESULT),
        tasks=[TASK], sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_girafe_platform_timing.py']),
        workers=1, threads=1, maximum_wall_s=60.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    declared = {name: value for name, value in task.items() if name not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact local iMAR force task required')
    clock = frozen_input(context, 'clock', CLOCK_SHA)
    saved = frozen_input(context, 'response', RESPONSE_SHA)
    transfer = frozen_input(context, 'receipt', holdout.RECEIPT_SHA)
    prefix = frozen_input(context, 'probes', timing.probe.PROBE_SHA)['prefix']
    if (clock['source']['group_id'] != 'esa-99f1530c3eda4318'
            or saved['candidate_offset_s'] != holdout.PROVISIONAL_OFFSET_S
            or tuple(entry['offset'] for entry in transfer['ranges']) != holdout.OFFSETS):
        raise ValueError('unchanged opened recording and fixed platform excerpts required')
    root = context.root.parents[1]
    imu = Path(imar.METADATA['inspection']).with_name(imar.IMU_NAME).as_posix()
    output = []
    with safe_path(root, imu).open('rb') as stream:
        context.charge(bound_calls=1, bound_steps=imar.SOURCE_BYTES)
        before = os.fstat(stream.fileno())
        if (before.st_size != imar.SOURCE_BYTES or hashlib.file_digest(stream, 'sha256').hexdigest()
                != clock['source']['imu_source_sha256']):
            raise ValueError('original iMAR hash or byte count differs')
        stream.seek(0)
        header = stream.read(imar.WIDTH)
        for entry in transfer['ranges']:
            offset = entry['offset']
            row = dict(offset=offset, source_sha256=entry['sha256'], charges_before_comparison=0)
            context.charge(bound_calls=1, bound_steps=timing.RANGE_BYTES)
            path = safe_path(root, (holdout.DIRECTORY/f'range-{offset}.asc').as_posix())
            try:
                if path.stat().st_size != timing.RANGE_BYTES:
                    raise ValueError('one complete saved excerpt required')
                samples, _ = holdout.new_samples(path.read_bytes(), entry, prefix, all_force_axes=True)
                platform = np.column_stack((np.linalg.norm(samples[:, 1:4], axis=1), np.abs(samples[:, 3])))
                times, platform_cells = timing.tenth_second_values(samples[:, 0], platform)
                first = times[0]-.05+holdout.PROVISIONAL_OFFSET_S+timing.girafe.GPS_AT_UTC_MIDNIGHT
                target = first+np.arange(-LAG_STEPS, len(times)+LAG_STEPS+1)/10.
                context.charge(bound_calls=1, bound_steps=MAX_INTERVALS)
                row['charges_before_comparison'] = 1
                edges, force, _ = imar.held_measurements(stream, header, row_bytes=imar.WIDTH, row_count=imar.RECORDS,
                    maximum_samples=MAX_INTERVALS, lower=target[0], upper=target[-1])
                cells = timing.held_cell_means(edges, np.linalg.norm(force, axis=1)[:, None], target)[:, 0]
            except (OSError, ValueError) as error:
                row.update(status='invalid_support', reason=str(error))
            else:
                comparisons = {}
                for i, name in enumerate(SIGNALS):
                    context.charge(bound_calls=1, bound_steps=2*LAG_STEPS+1)
                    try:
                        comparisons[name] = lag_scores(platform_cells[:, i], cells)
                    except ValueError as error:
                        comparisons[name] = dict(passes=False, reason=str(error))
                row.update(status='scored', comparisons=comparisons, imar_intervals=len(force),
                           target_gps_span_s=[float(target[0]), float(target[-1])])
            output.append(row)
            context.save_bytes(f'range-{offset}.json', encoded(row))
        after = os.fstat(stream.fileno())
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('original iMAR changed during verified reads')
    count = sum(row.get('comparisons', {}).get('force_norm', {}).get('passes', False) for row in output)
    context.save_bytes('imar-force.json', encoded(dict(ranges=output, qualified_ranges=count, response_sha256=RESPONSE_SHA,
        imu_source_sha256=clock['source']['imu_source_sha256'], candidate_offset_s=holdout.PROVISIONAL_OFFSET_S,
        network_calls=0, protected_reads=0, scientific_decision='abstain')))
    return dict(passed=count == len(holdout.OFFSETS), qualified_ranges=count, scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        identity = TASK['identity']
        result = study.artifact(identity, 'imar-force.json')
        limits = dict(TASK['limits'])
        if tuple(row['offset'] for row in result['ranges']) != holdout.OFFSETS:
            raise ValueError('every fixed excerpt must be reported')
        for row in result['ranges']:
            if study.artifact(identity, f"range-{row['offset']}.json") != row:
                raise ValueError('iMAR range receipt differs from the closed report')
            if row['status'] != 'scored':
                limits['bound_calls'] -= len(SIGNALS)
                limits['bound_steps'] -= len(SIGNALS)*(2*LAG_STEPS+1)
            if not row['charges_before_comparison']:
                limits['bound_calls'] -= 1
                limits['bound_steps'] -= MAX_INTERVALS
        if study.rows[identity]['charged'] != limits:
            raise ValueError('iMAR force receipt differs from the closed charge ledger')
        result['charged'] = limits
        result['manifest_sha256'] = study.completion['manifest_sha256']
    raw = encoded(result)
    target = root/RESULT
    if not target.exists():
        atomic(target, raw)
    if target.read_bytes() != raw:
        raise ValueError('iMAR force receipt differs from preserved evidence')
    return dict(sha256=digest(raw), qualified_ranges=result['qualified_ranges'])


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
