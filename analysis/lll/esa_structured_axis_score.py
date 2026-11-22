# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify linear-memory conditional axis scores against the sealed dense replay."""

import argparse
from contextlib import closing
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from . import esa_height_role as dense
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-structured-axis-score-v1-20261121'
PLAN = dense.FOLDER+'ESA_STRUCTURED_AXIS_SCORE_PLAN.md'
RESULT = dense.FOLDER+'esa-structured-axis-score.json'
SCOPE = 'Verify structured axis scores on the saved ESA 187 covariance arms and two generated lengths'
DENSE_SHA = '0aa738ba98469a8d22ececba79ef5c32715762bba4779d58eb5193f0793d2bd3'
BENCHMARKS = {'generated-2048': 2048, 'generated-4096': 4096}
MAXIMUM_BYTES = 16_000_000


def task_for(key):
    return dict(identity=key, input_key=key, payload={},
        limits=dict(native_calls=0, packet_visits=0, bound_calls=21 if key in dense.CASES else 1,
                    bound_steps=0))


def _generated_operator(times):
    full = dense.FULL
    weights = np.broadcast_to(np.eye(3)*full.POLICY['receiver_white_std_m'], (len(times), 3, 3))
    keys = ('acceleration_psd', 'jerk_psd', 'snap_psd', 'receiver_random_walk_psd',
            'initial_receiver_offset_std_m')
    return full.integrated_drift_v2_operator(times, origin_s=0.,
        initial_position_std_m=0., initial_velocity_std_mps=0.,
        initial_acceleration_std_mps2=0., initial_jerk_std_mps3=0., receiver_loading=weights,
        maximum_bytes=MAXIMUM_BYTES, **{k: full.POLICY[k] for k in keys})


def _score(data, reference, context):
    law, _ = dense.CASES[data['identity']]
    if len(data['rows']) != 20 or set(reference) != {row['identity'] for row in data['rows']}:
        raise ValueError('same 20 scored paths required')
    context.charge(bound_calls=1, bound_steps=0)
    maker = dense.FULL.operator if law == 'full' else dense.REDUCED.no_snap_operator
    operator = maker(data['times'], np.asarray(data['weights']))
    if operator.configuration != data['operator_configuration']:
        raise ValueError('same original covariance required')
    narrow = operator.conditional_axes((0, 1), first_epoch=dense.CUT, maximum_bytes=MAXIMUM_BYTES)
    paths = np.asarray([r['difference'] for r in data['rows']], float)
    if paths.shape != (20, dense.LATER, 3):
        raise ValueError('exact common later support required')
    for _ in data['rows']:
        context.charge(bound_calls=1, bound_steps=0)
    trajectories = paths.transpose(1, 2, 0)
    earlier = np.zeros((dense.CUT*3, len(paths)))
    _, state = operator.apply_block(earlier, first_epoch=0)
    white, _ = operator.apply_block(trajectories.reshape(-1, len(paths)),
                                   first_epoch=dense.CUT, state=state)
    horizontal = narrow.whiten(trajectories[:, :2].reshape(-1, len(paths)))
    scores = dict(full=np.sum(white**2, axis=0), horizontal=np.sum(horizontal**2, axis=0))
    result, deltas = {}, {}
    for name, values in scores.items():
        expected = np.array([reference[r['identity']][name] for r in data['rows']])
        if not np.allclose(values, expected, rtol=1e-8, atol=1e-9):
            raise ValueError('structured score differs from sealed dense replay')
        deltas[name] = float(np.max(abs(values-expected)))
        result[name] = {r['identity']: float(v) for r, v in zip(data['rows'], values, strict=True)}
    return dict(scores=result, maximum_absolute_score_difference=deltas,
                operator_bytes=operator.storage_bytes+narrow.storage_bytes,
                marginal_operator_bytes=narrow.storage_bytes)


def _benchmark(count, context):
    context.charge(bound_calls=1, bound_steps=0)
    time = np.arange(dense.CUT+count, dtype=float)
    before = perf_counter()
    operator = _generated_operator(time)
    marginal = operator.conditional_axes((0, 1), first_epoch=dense.CUT, maximum_bytes=MAXIMUM_BYTES)
    # A deterministic nonzero centered path exercises the whole filter.
    path = np.column_stack((np.sin(time[-count:]/9.), np.cos(time[-count:]/17.))).ravel()
    score = float(np.linalg.norm(marginal.whiten(path))**2)
    if not np.isfinite(score) or score <= 0:
        raise ValueError('finite nonzero complete benchmark score required')
    return dict(later_epochs=count, full_operator_bytes=operator.storage_bytes,
        marginal_operator_bytes=marginal.storage_bytes,
        combined_operator_bytes=operator.storage_bytes+marginal.storage_bytes,
        dense_full_factor_bytes=(3*count)**2*8, score=score, elapsed_s=perf_counter()-before)


def evaluate(task, context):
    key = task['identity']
    declared = {k: v for k, v in task.items() if k not in ('index', 'shard')}
    data = json.loads(context.input_path().read_bytes())
    if (context.manifest['scope'] != SCOPE or declared != task_for(key)
            or data['identity'] != key):
        raise ValueError('unchanged structured scoring tasks required')
    if key in dense.CASES:
        outcome = _score(data['arm'], data['scores'], context)
    else:
        if data['epochs'] != BENCHMARKS[key]:
            raise ValueError('unchanged generated length required')
        outcome = _benchmark(data['epochs'], context)
    result = dict(identity=key, result=outcome, scientific_decision='abstain')
    context.save('structured-score.json', result)
    return dict(result, passed=True)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing structured score freeze')
    recorded = dense._checked(root, dense.RESULT, DENSE_SHA)
    reference = {r['identity']: r for r in recorded['results']}
    staging = {}
    with closing(ClosedStudy(root, 'data/'+dense.RANKING_ID)) as study:
        if (any(recorded[k] != v for k, v in study.completion.items()) or not study.summary['passed']
                or set(study.rows) != set(dense.CASES) or study.summary['bound_evaluations'] != 84):
            raise ValueError('exact completed dense-score study required')
        for key in dense.CASES:
            saved = study.artifact(key, 'height-role.json')
            if saved != reference[key] or dict(saved, passed=True) != study.envelope(key)['result']:
                raise ValueError('dense score report differs from sealed output')
            staging[key] = dict(identity=key, arm=study.input(key), scores=saved['result']['rows'])
    staging.update({key: dict(identity=key, epochs=count) for key, count in BENCHMARKS.items()})
    base.mkdir()
    inputs = {'plan': PLAN, 'dense-score': dense.RESULT}
    for key, record in staging.items():
        path = base/(key+'.json')
        atomic(path, encoded(record))
        inputs[key] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    test = 'analysis/tests/test_conditional_axis_innovations.py'
    manifest = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs,
        tasks=[task_for(key) for key in staging], sources=source_closure(root, (adapter, PLAN, test)),
        workers=1, threads=1, maximum_wall_s=90.), root).prepare(root)
    print(json.dumps(manifest['limits'], sort_keys=True))


def collect(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if (set(study.rows) != {*dense.CASES, *BENCHMARKS} or not study.summary['passed']
                or study.summary['bound_evaluations'] != 86):
            raise ValueError('all four covariance arms and both generated lengths must be sealed')
        results = []
        for key in (*dense.CASES, *BENCHMARKS):
            row = study.artifact(key, 'structured-score.json')
            if dict(row, passed=True) != study.envelope(key)['result'] or row['identity'] != key:
                raise ValueError('archived structured score differs from its sealed task')
            results.append(row)
        raw = encoded(dict(results=results, dense_score_sha256=DENSE_SHA, **study.completion,
            scientific_decision='abstain'))
    _write_equal(root/RESULT, raw)
    print(digest(raw))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'collect'))
    {'prepare': prepare, 'collect': collect}[parser.parse_args().action](Path.cwd())
