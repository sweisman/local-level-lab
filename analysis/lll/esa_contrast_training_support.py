# SPDX-License-Identifier: AGPL-3.0-or-later
"""Certify earlier-loss support in the already verified ESA forecast direction."""

import argparse
from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
from pathlib import Path

from .esa_calibration_conditioned_margin import BASE, RECOVER, RECOVERY, WALL_S, _parent
from .esa_compact_forecast_margin import ARTIFACT as PARENT_ARTIFACT
from .esa_compact_forecast_margin import ID as PARENT_ID, RESULT as PARENT, TASK as PARENT_TASK
from .esa_linked_training_support import INCREASE, LATER, MODELS, TRAIN, training_inputs
from .forecast_training_margin import earlier_disposition, margin_from_support
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_saved_prediction_audit import endpoint
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'esa-contrast-training-support-v1'
SCOPE = 'Earlier-loss allowances for the unchanged compact ESA forecast contrast'
PLAN = BASE+'ESA_CONTRAST_TRAINING_SUPPORT_PLAN.md'
RESULT = BASE+'esa-contrast-training-support-result.json'
REQUEST = BASE+'esa-contrast-training-support-qualification.json'
XML = BASE+'esa-contrast-training-support-tests.xml'
PARENT_SHA = 'e2c4292e8552707492cd62717f96f63d6334d5629f1d3e18809b3f72ef65eeb7'
ARTIFACT = 'training-support.json'
TESTS = ('test_signed_training_support_uses_both_independent_adverse_changes',
         'test_training_witness_exclusion_needs_outward_lower_bound_above_ceiling')
GAMMAS = (0., .1)
TASK = dict(identity='compact-contrast-earlier-support', input_key='shape', payload=dict(gammas=list(GAMMAS)),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=5, bound_steps=5))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_forecast_training_margin.py')
    sources, env = source_closure(root, seeds), runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=env, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=env, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources, env


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite support allowance')
    sources, env = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=env,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        parent, row = _parent(root, PARENT, PARENT_SHA, PARENT_ID, PARENT_TASK, PARENT_ARTIFACT, stack)
        if (parent.envelope(PARENT_TASK['identity'])['charged'] != PARENT_TASK['limits']
                or row['proposal']['point'] is None or len(row['exact_later_taps']) != 3*LATER):
            raise ValueError('exact original compact contrast and upper witness required')
        keys = ['shape', 'nominal', 'later-operator', *(model+suffix for model in MODELS
                                                       for suffix in ('', '-weights', '-settings'))]
        inputs_raw = {key: parent.input(key, raw=True) for key in keys}
        inputs_raw['witness'] = encoded(dict(point=row['proposal']['point'], taps=row['exact_later_taps'],
                                             lower=row['best_lower_exact']))
    inputs_raw.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=PARENT, qualification=REQUEST, qualification_tests=XML)
    for key, value in inputs_raw.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, value)
        inputs[key] = path
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .conditioned_position_margin import reverse_intervals
    from .esa_calibration_witness import check_point
    from .esa_shared_profile_score import support as coefficients
    from .ilvis0_linked_training_support import support
    from .innovations_snapshot import restore
    from .state_space_directional_bound import adjoint_intervals

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the original witness and both sensitivity settings are required')

    def raw(key):
        return context.input_path(key).read_bytes()

    context.charge(bound_calls=1, bound_steps=1)
    shape, centers, saved = map(lambda key: json.loads(raw(key)), ('shape', 'nominal', 'witness'))
    later = restore(raw('later-operator'), expected_sha256=shape['factors_sha256'],
                    expected_configuration=shape['configuration'], maximum_bytes=2**26)
    taps = list(map(F, saved['taps']))
    earlier = [(-hi, -lo) for lo, hi in reverse_intervals(later, taps, cut=TRAIN)]
    weights = earlier + [(value, value) for value in taps]
    weight_norm = sum(max(abs(lo), abs(hi)) for lo, hi in weights)
    tap_lower = [endpoint(lo, False) for lo, _ in weights]
    tap_upper = [endpoint(hi, True) for _, hi in weights]
    metric = np.tile(shape['metric'], TRAIN+LATER)
    first, second = [np.asarray(centers[model], float).ravel().tolist() for model in MODELS]
    nominal = sum(tap*(F(b)-F(a)) for tap, a, b in zip(taps, first, second, strict=True))
    point = np.asarray(saved['point'], float).reshape(len(MODELS), 51)
    models = {}
    for model, change_sign, proposal in zip(MODELS, (-1, 1), point, strict=True):
        residual, raw_design, design, lower, upper, operator, settings = training_inputs(raw, model)
        if (settings['shape'] != shape or np.any(proposal < lower) or np.any(proposal > upper)):
            raise ValueError('unchanged admissible calibration box and forecast weights required')
        axis = residual + design @ proposal
        coefs = coefficients(tap_lower, tap_upper, metric, raw_design)
        lo, hi = adjoint_intervals(operator, axis)
        train = coefficients(lo, hi, np.ones(len(residual)), raw_design[:len(residual)])
        training = tuple(zip(train['lower'], train['upper'], strict=True))
        target = tuple(zip(coefs['lower'], coefs['upper'], strict=True))
        rows = []
        for gamma in GAMMAS:
            context.charge(bound_calls=1, bound_steps=1)
            loss = check_point(operator, raw_design[:len(residual)], residual, ((F(0), F(0)),)*51, proposal,
                               unshared=gamma)
            adverse = {str(sign): support(residual, axis, training,
                       target if sign*change_sign == -1 else tuple((-b, -a) for a, b in target),
                       lower, upper, increase=INCREASE, unshared=gamma) for sign in (1, -1)}
            rows.append(dict(gamma=gamma, witness=earlier_disposition(loss, residual, increase=INCREASE, unshared=gamma),
                             loss=loss, adverse=adverse))
        models[model] = rows
    results = []
    for index, gamma in enumerate(GAMMAS):
        limits = {sign: [models[model][index]['adverse'][str(sign)]['exact_upper'] for model in MODELS]
                  for sign in (1, -1)}
        margin, sign, gaps = margin_from_support(nominal, weight_norm, limits)
        results.append(dict(gamma=gamma, new_lower_exact=str(margin), orientation=sign,
                            best_lower_m=endpoint(max(margin, F(saved['lower'])), False),
                            checked_lower_m=endpoint(margin, False), gaps={str(key): str(val) for key, val in gaps.items()}))
    outcome = dict(results=results, model_checks=models, passed=True, scientific_decision='abstain',
                   new_fits=0, protected_reads=0)
    context.save(ARTIFACT, outcome)
    return outcome


def recover(root):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as study:
            if study.input('recovery_policy') != RECOVER:
                raise ValueError('unchanged recovery policy required')
            identity = TASK['identity']
            if identity in study.rows and study.envelope(identity)['status'] == 'complete':
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVER)
    return resume_campaign(root, continuation)


def report(root):
    prefix, identity = 'data/'+ID, TASK['identity']
    continuation = root/(prefix+'-recovery')
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        study = original
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, continuation)['selected'][identity]['origin']
            if origin != prefix:
                study = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
        row, raw = study.envelope(identity), study.artifact(identity, ARTIFACT)
        if row['status'] != 'complete' or row['charged'] != TASK['limits'] or raw != row['result']:
            raise ValueError('the exact declared support work is required')
        _write_equal(root/RESULT, encoded(dict(raw, completion=study.completion)))
    return dict(margins=[r['best_lower_m'] for r in raw['results']],
                witnesses={key: [r['witness'] for r in rows] for key, rows in raw['model_checks'].items()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
