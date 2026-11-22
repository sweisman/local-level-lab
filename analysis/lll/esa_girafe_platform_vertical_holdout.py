# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test a frozen GIRAFE platform clock offset on newly captured vertical force."""

from contextlib import closing
import json
from pathlib import Path
import sys

from . import esa_girafe_platform_timing as timing
from .esa_direction_holdout_forecast import frozen_input
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-girafe-platform-vertical-holdout-v1'
SCOPE = 'local vertical GIRAFE force check on three sealed excerpts at a fixed clock offset'
FOLDER = timing.probe.clock.forecast.selection.FOLDER
PLAN = FOLDER+'ESA_GIRAFE_PLATFORM_VERTICAL_HOLDOUT_PLAN.md'
RESULT = FOLDER+'esa-girafe-platform-vertical-holdout-result.json'
DIRECTORY = timing.girafe.BASE/'girafe-platform-vertical-holdout-v1'
RECEIPT_SHA = 'ba900265ae8f9830370585d7ccf17ff76237afab0f98d2456f3326e1cc33357e'
PROVISIONAL_OFFSET_S = 38474.26739992
OFFSETS = (466124214, 931200441, 1396276591)
OVERLAP_BYTES = 512
GUARD_S = 2.
TASK = dict(identity='vertical-force-clock-holdouts', input_key='receipt', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=1+2*len(OFFSETS),
                bound_steps=timing.REFERENCE_BYTES+len(OFFSETS)*(timing.RANGE_BYTES+timing.REFERENCE_ROWS)))


def new_samples(raw, receipt, prefix, *, all_force_axes=False, include_candidate_rates=False):
    """Keep only original complete records after the overlap and guard."""
    import numpy as np

    if (len(raw) != timing.RANGE_BYTES or digest(raw) != receipt['sha256']
            or digest(raw[:OVERLAP_BYTES]) != receipt['expected_overlap_sha256']):
        raise ValueError('saved excerpt length, hash or overlap differs')
    layout = timing.probe.inspect_range_fragments(raw, round(prefix['first_tag_s']*10_000))
    low = min(prefix['phase_min_64ths_tick'], layout['phase_min_64ths_tick'])
    high = max(prefix['phase_max_64ths_tick'], layout['phase_max_64ths_tick'])
    if high-low > 64:
        raise ValueError('new range does not reproduce the validated recorder clock phase')
    first, *inside, _ = raw.split(b'\r\n')
    starts = len(first)+2+np.r_[0, np.cumsum([len(row)+2 for row in inside[:-1]])]
    if include_candidate_rates:
        columns = range(7)
    else:
        columns = (0, 1, 2, 3) if all_force_axes else (0, 3)
    fields = (row.split() for row in inside)
    rows = np.asarray([tuple(float(row[i]) for i in columns) for row in fields])
    after_overlap = int(np.searchsorted(starts, OVERLAP_BYTES))
    guard_end = rows[after_overlap, 0]+GUARD_S
    return rows[rows[:, 0] >= guard_end], dict(layout, first_after_overlap_s=float(rows[after_overlap, 0]),
                                               guard_end_s=float(guard_end))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing vertical clock holdout must stay sealed')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter,
        inputs=dict(receipt=(DIRECTORY/'transfer-receipt.json').as_posix(), probes=timing.probe.RESULT),
        tasks=[TASK], sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_girafe_platform_timing.py',
                                                   'analysis/tests/test_esa_girafe_platform_probe.py']),
        workers=1, threads=1, maximum_wall_s=45.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    declared = {name: value for name, value in task.items() if name not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact vertical clock holdout task required')
    transfer = frozen_input(context, 'receipt', RECEIPT_SHA)
    prefix = frozen_input(context, 'probes', timing.probe.PROBE_SHA)['prefix']
    if tuple(r['offset'] for r in transfer['ranges']) != OFFSETS or transfer['verified_overlap_bytes'] != OVERLAP_BYTES:
        raise ValueError('exact preselected local acquisition required')
    root = context.root.parents[1]
    context.charge(bound_calls=1, bound_steps=timing.REFERENCE_BYTES)
    reference = timing.reference_vectors(safe_path(root, (timing.girafe.BASE/timing.REFERENCE).as_posix()))
    reference_vertical = np.abs(reference[:, 3])
    output = []
    for record in transfer['ranges']:
        offset = record['offset']
        context.charge(bound_calls=1, bound_steps=timing.RANGE_BYTES)
        path = safe_path(root, (DIRECTORY/f'range-{offset}.asc').as_posix())
        row = dict(offset=offset, raw_sha256=record['sha256'], curl_exit_code=record['curl_exit_code'])
        try:
            if path.stat().st_size != timing.RANGE_BYTES:
                raise ValueError('one complete saved excerpt required')
            samples, layout = new_samples(path.read_bytes(), record, prefix)
            times, magnitude = timing.tenth_second_values(samples[:, 0], np.abs(samples[:, 1:2]))
        except (OSError, ValueError) as error:
            row.update(status='invalid_support', reason=str(error))
        else:
            context.charge(bound_calls=1, bound_steps=timing.REFERENCE_ROWS)
            result = timing.locate_clock(reference[:, 0], reference_vertical, times, magnitude[:, 0],
                                         locked_offset=PROVISIONAL_OFFSET_S)
            row.update(status='scored', layout=layout, alignment=result)
        output.append(row)
        context.save_bytes(f'range-{offset}.json', encoded(row))
    passed = sum(row.get('alignment', {}).get('passes', False) for row in output)
    context.save_bytes('vertical-holdouts.json', encoded(dict(ranges=output, candidate_offset_s=PROVISIONAL_OFFSET_S,
        receipt_sha256=RECEIPT_SHA, reference_sha256=timing.girafe.TARGETS[timing.REFERENCE][1],
        qualified_holdouts=passed, network_calls=0, protected_reads=0, scientific_decision='abstain')))
    return dict(passed=passed == len(OFFSETS), qualified_holdouts=passed, scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        identity = TASK['identity']
        result = study.artifact(identity, 'vertical-holdouts.json')
        charges = dict(TASK['limits'])
        if tuple(row['offset'] for row in result['ranges']) != OFFSETS:
            raise ValueError('every fixed excerpt must be retained')
        for row in result['ranges']:
            if study.artifact(identity, f"range-{row['offset']}.json") != row:
                raise ValueError('per-range audit differs from the result index')
            if row['status'] != 'scored':
                charges['bound_calls'] -= 1
                charges['bound_steps'] -= timing.REFERENCE_ROWS
        if study.rows[identity]['charged'] != charges:
            raise ValueError('vertical clock result differs from the operation ledger')
        result['charged'] = charges
        result['manifest_sha256'] = study.completion['manifest_sha256']
    raw = encoded(result)
    path = root/RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('vertical timing report differs from preserved evidence')
    return dict(sha256=digest(raw), qualified_holdouts=result['qualified_holdouts'])


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
