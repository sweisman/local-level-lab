# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare the same vertical force changes under common averaging widths."""

from contextlib import closing
import json
from pathlib import Path
import sys

from . import esa_girafe_platform_timing as timing
from . import esa_girafe_platform_vertical_holdout as holdout
from .esa_direction_holdout_forecast import frozen_input
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-girafe-platform-vertical-response-v1'
SCOPE = 'compare shared averaging widths on saved vertical force holdouts'
PLAN = holdout.FOLDER+'ESA_GIRAFE_PLATFORM_VERTICAL_RESPONSE_PLAN.md'
RESULT = holdout.FOLDER+'esa-girafe-platform-vertical-response-result.json'
PARENT_SHA = '9f6240a6625bfd586148ac901f14a2e61be9f29e30dc39d89028183065bce54f'
WIDTHS = (1, 3, 7, 11)
MAX_POINTS = 400
TASK = dict(identity='compare-force-response-at-locked-clock', input_key='holdouts', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=1+len(holdout.OFFSETS)*(1+len(WIDTHS)),
        bound_steps=timing.REFERENCE_BYTES+len(holdout.OFFSETS)*(timing.RANGE_BYTES+len(WIDTHS)*MAX_POINTS)))


def force_response(platform, reference, width):
    """Compare matched first differences of the two moving averages."""
    import numpy as np

    raw = np.asarray([platform, reference], float)
    if (raw.ndim != 2 or not 0 < width < raw.shape[1]-2 or raw.shape[1] > MAX_POINTS
            or not np.isfinite(raw).all()):
        raise ValueError('complete bounded paired samples required')
    delta = (raw[:, width:]-raw[:, :-width])/width
    delta -= delta.mean(axis=1, keepdims=True)
    norm = np.linalg.norm(delta, axis=1)
    if np.min(norm) <= 1e-20:
        raise ValueError('finite nonconstant force changes required')
    return dict(width_samples=width, paired_differences=delta.shape[1],
                correlation=float((delta[0]@delta[1])/(norm[0]*norm[1])),
                platform_rms=float(np.sqrt(np.mean(delta[0]**2))),
                reference_rms=float(np.sqrt(np.mean(delta[1]**2))),
                difference_rms=float(np.sqrt(np.mean((delta[0]-delta[1])**2))))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing force response diagnosis must stay sealed')
    with closing(ClosedStudy(root, 'data/'+holdout.ID)) as study:
        if study.summary['passed'] or digest((root/holdout.RESULT).read_bytes()) != PARENT_SHA:
            raise ValueError('exact terminal vertical holdout required')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter,
        inputs=dict(holdouts=holdout.RESULT, receipt=(holdout.DIRECTORY/'transfer-receipt.json').as_posix(),
                    probes=timing.probe.RESULT), tasks=[TASK],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_girafe_platform_timing.py']),
        workers=1, threads=1, maximum_wall_s=30.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    declared = {name: value for name, value in task.items() if name not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact force response task required')
    saved = frozen_input(context, 'holdouts', PARENT_SHA)
    transfer = frozen_input(context, 'receipt', holdout.RECEIPT_SHA)
    prefix = frozen_input(context, 'probes', timing.probe.PROBE_SHA)['prefix']
    root = context.root.parents[1]
    context.charge(bound_calls=1, bound_steps=timing.REFERENCE_BYTES)
    reference = timing.reference_vectors(safe_path(root, (timing.girafe.BASE/timing.REFERENCE).as_posix()))
    output = []
    for old, entry in zip(saved['ranges'], transfer['ranges'], strict=True):
        offset = entry['offset']
        if (old['offset'] != offset or old['status'] != 'scored' or old['raw_sha256'] != entry['sha256']):
            raise ValueError('source excerpt differs from the completed holdout')
        context.charge(bound_calls=1, bound_steps=timing.RANGE_BYTES)
        path = safe_path(root, (holdout.DIRECTORY/f'range-{offset}.asc').as_posix())
        if path.stat().st_size != timing.RANGE_BYTES:
            raise ValueError('one complete saved excerpt required')
        samples, _ = holdout.new_samples(path.read_bytes(), entry, prefix)
        times, magnitude = timing.tenth_second_values(samples[:, 0], np.abs(samples[:, 1:2]))
        target = times+holdout.PROVISIONAL_OFFSET_S
        first = int(np.argmin(abs(reference[:, 0]-target[0])))
        rows = reference[first:first+len(times)]
        if len(rows) != len(times) or np.max(abs(rows[:, 0]-target)) > .002:
            raise ValueError('frozen offset does not match the complete reference support')
        scores = []
        for width in WIDTHS:
            context.charge(bound_calls=1, bound_steps=MAX_POINTS)
            scores.append(force_response(magnitude[:, 0], np.abs(rows[:, 3]), width))
        if abs(scores[0]['correlation']-old['alignment']['locked_correlation']) > 1e-10:
            raise ValueError('shortest width failed to reproduce the locked correlation')
        output.append(dict(offset=offset, reference_start_s=float(rows[0, 0]), by_width=scores))
    context.save_bytes('responses.json', encoded(dict(ranges=output, holdout_sha256=PARENT_SHA,
        candidate_offset_s=holdout.PROVISIONAL_OFFSET_S, network_calls=0, protected_reads=0,
        scientific_decision='abstain')))
    return dict(passed=len(output) == len(holdout.OFFSETS), ranges=len(output), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        identity = TASK['identity']
        if not study.summary['passed'] or study.rows[identity]['charged'] != TASK['limits']:
            raise ValueError('complete force response comparison and charge ledger required')
        result = study.artifact(identity, 'responses.json')
        result['charged'] = study.summary['charged']
        result['manifest_sha256'] = study.completion['manifest_sha256']
    raw = encoded(result)
    path = root/RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('force response receipt differs from preserved evidence')
    return dict(sha256=digest(raw), ranges=len(result['ranges']))


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
