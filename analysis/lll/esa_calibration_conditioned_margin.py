# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the best affine margin for the saved ESA forecast conditioning."""

import argparse
from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
from pathlib import Path

from .calibration_maximum_margin import ITERATIONS, smooth_rows
from .calibration_orthogonal import annihilate_quadratics
from .conditioned_position_margin import lower_certificate, propose, upper_certificate
from .esa_calibration_maximum_margin import ID as MAXIMUM_ID, RESULT as MAXIMUM, TASK as MAXIMUM_TASK
from .esa_calibration_orthogonal import BASE, MODELS, RECOVER, RECOVERY, WALL_S
from .esa_calibration_orthogonal import ID as PRIOR_ID, RESULT as PRIOR, TASK as PRIOR_TASK
from .esa_linked_training_support import LATER, TRAIN, training_inputs
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_saved_prediction_audit import endpoint
from .innovations_snapshot import restore
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-calibration-conditioned-margin-v1'
SCOPE = 'Best linear uniform-error allowance with the original ESA forecast conditioning'
PLAN = BASE+'ESA_CALIBRATION_CONDITIONED_MARGIN_PLAN.md'
RESULT = BASE+'esa-calibration-conditioned-margin-result.json'
REQUEST = BASE+'esa-calibration-conditioned-margin-qualification.json'
XML = BASE+'esa-calibration-conditioned-margin-tests.xml'
TEST = 'analysis/tests/test_conditioned_position_margin.py'
TESTS = ('test_conditional_forward_and_adjoint_match_independent_closed_form',
         'test_conditional_linear_program_and_certificates_agree')
MAXIMUM_SHA = 'cc27a7890f343220f1f7e1207ec737f1bc69d16e0bf562365dc60eac717f7f7e'
PRIOR_SHA = '3e128a40456e7ae070ab56c11221c036d7acc8fbd4b311d87377ccf799c4604f'
TASK = dict(identity='conditioned-box-margin', input_key='nominal', payload=dict(cut=TRAIN, later=LATER),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=6, bound_steps=2006))


def qualification(root, *, check):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources


def _parent(root, path, sha, study, task, artifact, stack):
    raw = (root/path).read_bytes()
    if digest(raw) != sha:
        raise ValueError(f'the exact verified result at {path} is required')
    report = json.loads(raw)
    source = stack.enter_context(closing(ClosedStudy(root, 'data/'+study)))
    row = source.artifact(task['identity'], artifact)
    if (source.completion != report['completion'] or not source.summary['passed']
            or any(value != report[key] for key, value in row.items())):
        raise ValueError(f'{path} differs from the completed evidence')
    return source, row


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
        base, maximum = _parent(root, MAXIMUM, MAXIMUM_SHA, MAXIMUM_ID, MAXIMUM_TASK, 'margin.json', stack)
        prior, contrast = _parent(root, PRIOR, PRIOR_SHA, PRIOR_ID, PRIOR_TASK, 'orthogonal-contrast.json', stack)
        keys = ['shape', 'times', 'nominal', *(model+suffix
                for model in MODELS for suffix in ('', '-weights', '-settings'))]
        staged = {key: base.input(key, raw=True) for key in keys}
        if any(prior.input(key, raw=True) != staged[key] for key in keys):
            raise ValueError('the parent studies must have the same affine inputs')
        staged.update({'later-operator': prior.input('later-operator', raw=True),
                       'prior-taps': encoded(contrast['directions']['full calibration span']['weights_exact']),
                       'broader-upper': encoded(maximum['upper_exact'])})
    staged.update(recovery=recovery, recovery_tests=recovery_tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=PRIOR, maximum=MAXIMUM, qualification=REQUEST, qualification_tests=XML)
    for name, value in staged.items():
        path = f'data/{ID}-inputs/{name}'
        _write_equal(root/path, value)
        inputs[name] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1, maximum_wall_s=WALL_S)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the original contrast pair and conditioning cut are required')

    def raw(name):
        return context.input_path(name).read_bytes()

    context.charge(bound_calls=1, bound_steps=1)
    shape, times, centers = map(lambda key: json.loads(raw(key)), ('shape', 'times', 'nominal'))
    operator = restore(raw('later-operator'), expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)
    if len(times) != TRAIN+LATER or operator.epoch_count != len(times) or operator.observation_dimension != 3:
        raise ValueError('the fixed chronological 400/120 position split is required')
    metric = np.tile(shape['metric'], TRAIN+LATER).tolist()
    if any(not scale > 0 for scale in metric):
        raise ValueError('positive position scales required')
    matrices, boxes = [], []
    for model, factor in zip(MODELS, (-1, 1), strict=True):
        _, design, _, lower, upper, _, settings = training_inputs(raw, model)
        if design.shape[1] != 51 or any(settings['shape'][key] != shape[key]
                                      for key in ('direction', 'metric', 'nominal', 'factors_sha256')):
            raise ValueError('the original weighting and all 102 calibration terms are required')
        matrices.append(factor*design)
        boxes.append((lower.tolist(), upper.tolist()))
    lower, upper = (sum((box[axis] for box in boxes), []) for axis in (0, 1))
    first, second = [np.asarray(centers[model], float).ravel().tolist() for model in MODELS]
    if len(first) != 3*LATER or len(second) != 3*LATER:
        raise ValueError('both nominal forecasts must cover the same future window')
    nominal = [F(0)]*(3*TRAIN)+[F(b)-F(a) for a, b in zip(first, second, strict=True)]
    smooth = smooth_rows(times[TRAIN:], len(nominal))
    inputs = operator, nominal, np.column_stack(matrices), metric, lower, upper

    context.charge(bound_calls=1, bound_steps=1)
    baseline_taps = annihilate_quadratics(json.loads(raw('prior-taps'))[3*TRAIN:], times[TRAIN:])
    baseline, _ = lower_certificate(*inputs, baseline_taps, cut=TRAIN)
    context.charge(bound_calls=1, bound_steps=ITERATIONS)
    choice = propose(*inputs, smooth, cut=TRAIN, iterations=ITERATIONS)
    context.charge(bound_calls=1, bound_steps=1)
    upper_bound = upper_certificate(*inputs, smooth, choice, cut=TRAIN) if choice['point'] is not None else None
    context.charge(bound_calls=1, bound_steps=1)
    if choice['later_taps'] is None:
        proposed, earlier_fraction, taps = F(0), F(0), []
    else:
        taps = annihilate_quadratics(choice['later_taps'], times[TRAIN:])
        proposed, earlier_fraction = lower_certificate(*inputs, taps, cut=TRAIN)
    context.charge(bound_calls=1, bound_steps=2)
    broader = F(json.loads(raw('broader-upper')))
    best_upper = min(upper_bound, broader) if upper_bound is not None else broader
    best_lower = max(baseline, proposed)
    if best_upper < best_lower:
        raise ArithmeticError('the independently verified affine bounds are inconsistent')
    result = dict(proposal=choice, exact_later_taps=list(map(str, taps)),
                  baseline_lower_m=endpoint(baseline, False), proposed_lower_m=endpoint(proposed, False),
                  earlier_weight_fraction_bound=endpoint(earlier_fraction, True),
                  conditioned_upper_exact=None if upper_bound is None else str(upper_bound),
                  best_lower_exact=str(best_lower), best_upper_exact=str(best_upper),
                  best_lower_m=endpoint(best_lower, False), best_upper_m=endpoint(best_upper, True),
                  passed=True, scientific_decision='abstain', new_fits=0, protected_reads=0)
    context.save('conditioned-margin.json', result)
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
        row = source.artifact(identity, 'conditioned-margin.json')
        if envelope['status'] != 'complete' or envelope['charged'] != TASK['limits'] or row != envelope['result']:
            raise ValueError('the exact declared outcome and charge are required')
        result = dict(row, completion=source.completion)
    _write_equal(root/RESULT, encoded(result))
    return {key: result[key] for key in ('baseline_lower_m', 'best_lower_m', 'best_upper_m')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    output = qualification(root, check=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(output, sort_keys=True))
