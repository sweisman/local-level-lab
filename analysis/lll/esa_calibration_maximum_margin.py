# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify lower and upper bounds on ESA's best full-box linear shape contrast."""

import argparse
from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
from pathlib import Path

from .calibration_maximum_margin import ITERATIONS, METHODS, exact_contrast, exact_discrepancy, propose
from .esa_calibration_orthogonal import BASE, MODELS, RECOVER, RECOVERY, WALL_S
from .esa_calibration_orthogonal import ID as PRIOR_STUDY, RESULT as PRIOR
from .esa_calibration_orthogonal import TASK as PRIOR_TASK
from .esa_linked_training_support import LATER, TRAIN, training_inputs
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_saved_prediction_audit import endpoint
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-calibration-maximum-margin-v1'
SCOPE = 'Best possible linear uniform-error allowance under the archived ESA calibration boxes'
PLAN = BASE+'ESA_CALIBRATION_MAXIMUM_MARGIN_PLAN.md'
RESULT = BASE+'esa-calibration-maximum-margin-result.json'
REQUEST = BASE+'esa-calibration-maximum-margin-qualification.json'
REPORT = BASE+'esa-calibration-maximum-margin-tests.xml'
TEST = 'analysis/tests/test_calibration_maximum_margin.py'
TESTS = ('test_exact_primal_and_contrast_close_a_known_margin',
         'test_exact_smooth_corrections_reject_out_of_box_witnesses',
         'test_both_sides_keep_roundoff_in_original_physical_units')
PRIOR_SHA = '3e128a40456e7ae070ab56c11221c036d7acc8fbd4b311d87377ccf799c4604f'
TASK = dict(identity='full-box-margin', input_key='nominal', payload=dict(methods=list(METHODS)),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=8, bound_steps=4006))


def qualification(root, *, check):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite proposal allowance')
    raw = (root/PRIOR).read_bytes()
    if digest(raw) != PRIOR_SHA:
        raise ValueError('verified earlier contrast result required')
    report = json.loads(raw)
    sources = qualification(root, check=True)
    recovery, test_results = checked(root, RECOVERY, sources=qualification_sources(root),
                                     environment=runtime_environment(), required_tests=REQUIRED_TESTS,
                                     minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, 'data/'+PRIOR_STUDY)) as prior:
        if prior.completion != report['completion'] or not prior.summary['passed']:
            raise ValueError('the exact prior completed comparison is required')
        earlier = prior.artifact(PRIOR_TASK['identity'], 'orthogonal-contrast.json')
        if any(value != report[key] for key, value in earlier.items()):
            raise ValueError('the prior report differs from its verified seal')
        keys = ['shape', 'times', 'nominal', *(model+suffix
                for model in MODELS for suffix in ('', '-weights', '-settings'))]
        staged = {key: prior.input(key, raw=True) for key in keys}
        staged['prior-taps'] = encoded(earlier['directions']['full calibration span'])
    staged.update(recovery=recovery, recovery_tests=test_results, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=REPORT)
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
        raise ValueError('the exact original pair and contrast search are required')

    def raw(name):
        return context.input_path(name).read_bytes()

    context.charge(bound_calls=1, bound_steps=1)
    shape, times, centers = map(lambda key: json.loads(raw(key)), ('shape', 'times', 'nominal'))
    metric = np.tile(np.asarray(shape['metric']), TRAIN+LATER).tolist()
    later_times = times[TRAIN:]
    if len(times) != TRAIN+LATER:
        raise ValueError('520 original chronological epochs required')
    matrices, boxes = [], []
    for model, factor in zip(MODELS, (-1, 1), strict=True):
        _, design, _, lower, upper, _, settings = training_inputs(raw, model)
        if design.shape[1] != 51 or any(settings['shape'][key] != shape[key]
                                      for key in ('direction', 'metric', 'nominal', 'factors_sha256')):
            raise ValueError('original weighting and all calibration terms required')
        matrices.append(factor*design)
        boxes.append((lower.tolist(), upper.tolist()))
    design = np.column_stack(matrices)
    lower, upper = (sum((box[axis] for box in boxes), []) for axis in (0, 1))
    first, second = [np.asarray(centers[model], float).ravel().tolist() for model in MODELS]
    if len(first) != 3*LATER or len(second) != 3*LATER:
        raise ValueError('the two nominal means must share every later epoch')
    nominal = [F(0)]*(3*TRAIN)+[F(b)-F(a) for a, b in zip(first, second, strict=True)]
    argument = nominal, design, metric, lower, upper, later_times

    context.charge(bound_calls=1, bound_steps=1)
    previous = json.loads(raw('prior-taps'))
    baseline = exact_contrast(*argument, previous['weights_exact'])
    if endpoint(baseline['bound'], False) != previous['max_position_remainder_m']:
        raise ValueError('the earlier contrast must reproduce exactly with all columns')
    established_lower = baseline['bound']
    established_upper = None
    trials = []
    for method in METHODS:
        context.charge(bound_calls=1, bound_steps=ITERATIONS)
        choice = propose(*argument, method=method)
        context.charge(bound_calls=1, bound_steps=1)
        upper_bound = None
        if choice['point'] is not None:
            upper_bound = exact_discrepancy(*argument, choice['point'], choice['smooth'])/2
            established_upper = upper_bound if established_upper is None else min(established_upper, upper_bound)
        context.charge(bound_calls=1, bound_steps=1)
        lower_bound = None
        if choice['taps'] is not None:
            contrast = exact_contrast(*argument, choice['taps'])
            lower_bound = contrast['bound']
            established_lower = max(established_lower, lower_bound)
            choice['exact_taps'] = list(map(str, contrast['taps']))
        trials.append(dict(choice, upper_exact=None if upper_bound is None else str(upper_bound),
                           lower_exact=None if lower_bound is None else str(lower_bound)))
    if established_upper is not None and established_upper < established_lower:
        raise ArithmeticError('exact upper and lower certificates contradict each other')
    result = dict(reference_lower_m=endpoint(baseline['bound'], False),
                  best_lower_m=endpoint(established_lower, False), lower_exact=str(established_lower),
                  upper_exact=None if established_upper is None else str(established_upper),
                  best_upper_m=None if established_upper is None else endpoint(established_upper, True),
                  trials=trials, passed=True, scientific_decision='abstain', new_fits=0, protected_reads=0)
    context.save('margin.json', result)
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
        row = source.artifact(identity, 'margin.json')
        if (envelope['status'] != 'complete' or envelope['charged'] != TASK['limits']
                or row != envelope['result'] or [trial['method'] for trial in row['trials']] != list(METHODS)):
            raise ValueError('the exact declared proposal outcomes and work receipts are required')
        result = dict(row, completion=source.completion)
    _write_equal(root/RESULT, encoded(result))
    return {key: result[key] for key in ('reference_lower_m', 'best_lower_m', 'best_upper_m')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    output = qualification(root, check=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(output, sort_keys=True))
