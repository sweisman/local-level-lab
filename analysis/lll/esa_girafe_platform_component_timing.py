# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the candidate platform clock against saved horizontal measurements."""

from contextlib import closing
import json
import math
from pathlib import Path
import sys

from . import esa_girafe_platform_timing as timing
from .esa_direction_holdout_forecast import frozen_input
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-girafe-platform-component-timing-v3'
SCOPE = 'saved horizontal GIRAFE force signals at a fixed candidate clock offset'
PLAN = timing.probe.clock.forecast.selection.FOLDER+'ESA_GIRAFE_PLATFORM_COMPONENT_TIMING_PLAN.md'
RESULT = timing.probe.clock.forecast.selection.FOLDER+'esa-girafe-platform-component-timing-stable-result.json'
PARENT_SHA = '89f55710675bf6f16e8413916581644ab6a267c276072fbf8e26b4dcb8b8df86'
SIGNALS = ('x', 'y', 'horizontal_magnitude')
TASK = dict(identity='compare-horizontal-force-at-locked-clock', input_key='parent', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=1+len(timing.probe.OFFSETS)*(1+len(SIGNALS)),
                bound_steps=timing.REFERENCE_BYTES+len(timing.probe.OFFSETS)*(
                    timing.RANGE_BYTES+len(SIGNALS)*timing.REFERENCE_ROWS)))


def horizontal_signals(vectors):
    import numpy as np

    horizontal = vectors[:, :2]
    return np.column_stack((horizontal, np.linalg.norm(horizontal, axis=1)))


def candidate_offset(parent):
    ranges = parent['ranges']
    offset, later = (case['alignment']['best_offset_s'] for case in ranges[1:])
    if (not math.isclose(offset, later, rel_tol=0., abs_tol=1e-8) or parent['coarse_clock_passed']
            or any(row['status'] != 'scored' for row in ranges)):
        raise ValueError('two equal candidate offsets and a preserved failed decision required')
    return offset


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing component timing study must stay sealed')
    with closing(ClosedStudy(root, 'data/'+timing.ID)) as parent:
        if parent.summary['passed'] or digest((root/timing.RESULT).read_bytes()) != PARENT_SHA:
            raise ValueError('exact failed original timing study required')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter,
        inputs=dict(parent=timing.RESULT, probes=timing.probe.RESULT, layout=timing.probe.AUDIT_RESULT),
        tasks=[TASK], sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_girafe_platform_timing.py']),
        workers=1, threads=1, maximum_wall_s=45.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact saved component timing task required')
    parent = frozen_input(context, 'parent', PARENT_SHA)
    probes = frozen_input(context, 'probes', timing.probe.PROBE_SHA)
    layout = frozen_input(context, 'layout', timing.LAYOUT_SHA)
    ranges = parent['ranges']
    offset = candidate_offset(parent)
    root = context.root.parents[1]
    context.charge(bound_calls=1, bound_steps=timing.REFERENCE_BYTES)
    reference = timing.reference_vectors(safe_path(root, (timing.girafe.BASE/timing.REFERENCE).as_posix()))
    targets = horizontal_signals(reference[:, 1:4])
    output = []
    for case, old_probe, audit in zip(ranges, probes['probes'], layout['probes'], strict=True):
        start = case['offset']
        context.charge(bound_calls=1, bound_steps=timing.RANGE_BYTES)
        path = safe_path(root, (timing.DIRECTORY/f'range-{start}.asc').as_posix())
        if path.stat().st_size != timing.RANGE_BYTES:
            raise ValueError('one complete saved timing range required')
        raw = path.read_bytes()
        if digest(raw) != case['sha256'] or old_probe['offset'] != start or audit['offset'] != start:
            raise ValueError('local timing range or byte provenance differs')
        samples, _ = timing.timing_records(raw, start, old_probe, audit)
        times, values = timing.tenth_second_values(samples[:, 0], horizontal_signals(samples[:, 1:4]))
        comparisons = {}
        for i, name in enumerate(SIGNALS):
            context.charge(bound_calls=1, bound_steps=timing.REFERENCE_ROWS)
            comparisons[name] = timing.locate_clock(reference[:, 0], targets[:, i], times, values[:, i],
                                                     locked_offset=offset)
        output.append(dict(offset=start, raw_sha256=case['sha256'], by_signal=comparisons))
    context.save_bytes('component-check.json', encoded(dict(ranges=output, provisional_offset_s=offset,
        parent_sha256=PARENT_SHA, network_calls=0, protected_reads=0, scientific_decision='abstain')))
    return dict(passed=len(output) == len(timing.probe.OFFSETS), ranges=len(output), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        identity = TASK['identity']
        if not study.summary['passed'] or study.rows[identity]['charged'] != TASK['limits']:
            raise ValueError('complete saved component check and charges required')
        result = study.artifact(identity, 'component-check.json')
        result['manifest_sha256'] = study.completion['manifest_sha256']
        result['charged'] = study.summary['charged']
    raw = encoded(result)
    target = root/RESULT
    if not target.exists():
        atomic(target, raw)
    if target.read_bytes() != raw:
        raise ValueError('component timing report differs from preserved evidence')
    return dict(sha256=digest(raw), ranges=len(result['ranges']))


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
