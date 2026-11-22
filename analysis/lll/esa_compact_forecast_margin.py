# SPDX-License-Identifier: AGPL-3.0-or-later
"""Certify the compact forecast proposal on the previously frozen ESA pair."""

import argparse
from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
from pathlib import Path

from .calibration_maximum_margin import ITERATIONS, smooth_rows
from .calibration_orthogonal import annihilate_quadratics
from .conditioned_position_margin import lower_certificate, upper_certificate
from .esa_calibration_conditioned_margin import BASE, MODELS, RECOVER, RECOVERY, WALL_S, _parent
from .esa_calibration_conditioned_margin import ID as PARENT_ID, RESULT as PARENT, TASK as PARENT_TASK
from .esa_linked_training_support import LATER, TRAIN, training_inputs
from .forecast_conditioned_lp import propose_compact
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_saved_prediction_audit import endpoint
from .innovations_snapshot import restore
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'esa-compact-forecast-margin-v1'
SCOPE = 'State-linked linear program for the unchanged ESA affine forecast comparison'
PLAN = BASE+'ESA_COMPACT_FORECAST_MARGIN_PLAN.md'
RESULT = BASE+'esa-compact-forecast-margin-result.json'
REQUEST = BASE+'esa-compact-forecast-margin-qualification.json'
XML = BASE+'esa-compact-forecast-margin-tests.xml'
PARENT_SHA = '7fa0df9ff6f1ef92cd4af8b9265640684a9cf68f3e461c854a704b7b8c1b98cb'
ARTIFACT = 'compact-margin.json'
TESTS = ('test_forecast_factors_reproduce_the_dense_map_at_each_cut',
         'test_compact_program_certifies_known_optimum_for_nonzero_cut_state',
         'test_compact_and_dense_programs_match_with_cross_axis_calibration')
TASK = dict(identity='compact-conditioned-box-margin', input_key='nominal', payload=dict(cut=TRAIN, later=LATER),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=5, bound_steps=2004))


def qualification(root, *, check):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_forecast_conditioned_lp.py',
             'analysis/tests/test_conditioned_position_margin.py')
    sources = source_closure(root, seeds)
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite proposal allowance')
    sources = qualification(root, check=True)
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
                                       environment=runtime_environment(), required_tests=REQUIRED_TESTS,
                                       minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        parent, row = _parent(root, PARENT, PARENT_SHA, PARENT_ID, PARENT_TASK, 'conditioned-margin.json', stack)
        if parent.envelope(PARENT_TASK['identity'])['charged'] != PARENT_TASK['limits']:
            raise ValueError('the exact earlier completion ledger is required')
        keys = ['shape', 'times', 'nominal', 'later-operator', *(model+suffix
                for model in MODELS for suffix in ('', '-weights', '-settings'))]
        staged = {key: parent.input(key, raw=True) for key in keys}
        staged['prior-bracket'] = encoded([row['best_lower_exact'], row['best_upper_exact']])
    staged.update(recovery=recovery, recovery_tests=recovery_tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=PARENT, qualification=REQUEST, qualification_tests=XML)
    for name, value in staged.items():
        path = f'data/{ID}-inputs/{name}'
        _write_equal(root/path, value)
        inputs[name] = path
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                    inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                    maximum_wall_s=WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the frozen pair and cut are required')

    def raw(name):
        return context.input_path(name).read_bytes()

    context.charge(bound_calls=1, bound_steps=1)
    shape, times, centers = map(lambda key: json.loads(raw(key)), ('shape', 'times', 'nominal'))
    operator = restore(raw('later-operator'), expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)
    if (operator.epoch_count != len(times) or len(times) != TRAIN+LATER or operator.observation_dimension != 3
            or len(shape['metric']) != 3 or any(not scale > 0 for scale in shape['metric'])):
        raise ValueError('the chronological position layout and physical scales are required')
    matrices, lower, upper = [], [], []
    for model, sign in zip(MODELS, (-1, 1), strict=True):
        _, design, _, lo, hi, _, settings = training_inputs(raw, model)
        if design.shape != (3*len(times), 51) or any(settings['shape'][key] != shape[key]
                                                    for key in ('direction', 'metric', 'nominal', 'factors_sha256')):
            raise ValueError('the original model columns and weights are required')
        matrices.append(sign*design)
        lower.extend(lo.tolist())
        upper.extend(hi.tolist())
    first, second = [np.asarray(centers[model], float).ravel().tolist() for model in MODELS]
    if len(first) != 3*LATER or len(second) != 3*LATER:
        raise ValueError('both nominal conditional forecasts are required')
    nominal = [F(0)]*(3*TRAIN)+[F(b)-F(a) for a, b in zip(first, second, strict=True)]
    smooth = smooth_rows(times[TRAIN:], len(nominal))
    args = operator, nominal, np.column_stack(matrices), np.tile(shape['metric'], len(times)).tolist(), lower, upper

    context.charge(bound_calls=1, bound_steps=ITERATIONS)
    choice = propose_compact(*args, smooth, cut=TRAIN, iterations=ITERATIONS)
    context.charge(bound_calls=1, bound_steps=1)
    hi = upper_certificate(*args, smooth, choice, cut=TRAIN) if choice['point'] is not None else None
    context.charge(bound_calls=1, bound_steps=1)
    taps, lo = [], F(0)
    if choice['later_taps'] is not None:
        taps = annihilate_quadratics(choice['later_taps'], times[TRAIN:])
        lo, _ = lower_certificate(*args, taps, cut=TRAIN)
    context.charge(bound_calls=1, bound_steps=1)
    earlier_lo, earlier_hi = map(F, json.loads(raw('prior-bracket')))
    best_lo = max(earlier_lo, lo)
    best_hi = min(earlier_hi, hi) if hi is not None else earlier_hi
    if best_hi < best_lo:
        raise ArithmeticError('the independently verified forecasts give incompatible bounds')
    result = dict(proposal=choice, exact_later_taps=list(map(str, taps)),
                  proposed_lower_exact=str(lo), proposed_upper_exact=None if hi is None else str(hi),
                  best_lower_exact=str(best_lo), best_upper_exact=str(best_hi),
                  best_lower_m=endpoint(best_lo, False), best_upper_m=endpoint(best_hi, True),
                  passed=True, scientific_decision='abstain', new_fits=0, protected_reads=0)
    context.save(ARTIFACT, result)
    return result


def recover(root):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as original:
            if original.input('recovery_policy') != RECOVER:
                raise ValueError('unchanged recovery allowance required')
            identity = TASK['identity']
            if identity in original.rows and original.envelope(identity)['status'] == 'complete':
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVER)
    return resume_campaign(root, continuation)


def report(root):
    prefix, identity = 'data/'+ID, TASK['identity']
    continuation = root/(prefix+'-recovery')
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        source = original
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, continuation)['selected'][identity]['origin']
            if origin != prefix:
                source = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
        envelope = source.envelope(identity)
        row = source.artifact(identity, ARTIFACT)
        if envelope['status'] != 'complete' or envelope['charged'] != TASK['limits'] or row != envelope['result']:
            raise ValueError('the exact declared outcome and charge are required')
        result = dict(row, completion=source.completion)
    _write_equal(root/RESULT, encoded(result))
    return {key: result[key] for key in ('best_lower_m', 'best_upper_m')} | {
        key: result['proposal'][key] for key in ('status', 'iterations', 'crossover_iterations',
                                            'dense_conditioning_entries', 'compact_conditioning_entries')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    output = qualification(root, check=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(output, sort_keys=True))
