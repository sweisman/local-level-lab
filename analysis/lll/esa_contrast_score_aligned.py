# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound the saved compact contrast with earlier directions chosen for its score."""

import argparse
from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
from pathlib import Path

from .esa_calibration_conditioned_margin import BASE, RECOVER, RECOVERY, WALL_S, _parent
from .esa_contrast_training_support import ARTIFACT as PRIOR_ARTIFACT
from .esa_contrast_training_support import ID as PRIOR_ID, RESULT as PRIOR, TASK as PRIOR_TASK
from .esa_linked_training_support import INCREASE, LATER, MODELS, TRAIN, training_inputs
from .forecast_training_margin import margin_from_support
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_saved_prediction_audit import endpoint
from .score_aligned_training import score_directions
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'esa-contrast-score-aligned-v1'
SCOPE = 'Score-aligned earlier GPS support for the unchanged compact ESA contrast'
PLAN = BASE+'ESA_CONTRAST_SCORE_ALIGNED_PLAN.md'
RESULT = BASE+'esa-contrast-score-aligned-result.json'
REQUEST = BASE+'esa-contrast-score-aligned-qualification.json'
XML = BASE+'esa-contrast-score-aligned-tests.xml'
PRIOR_SHA = 'ac00c02c1fca713d43c6c646a2a2ea903fd8351e8c8dd6c78bf0620166457595'
ARTIFACT = 'aligned-support.json'
TESTS = ('test_aligned_axes_follow_the_score_at_distinct_calibration_widths',
         'test_zero_training_design_produces_no_false_direction')
CUTOFFS = (1e-4, 1e-7, 1e-10)
GAMMAS = (0., .1)
TASK = dict(identity='earlier-score-aligned-support', input_key='shape',
            payload=dict(cutoffs=list(CUTOFFS), gammas=list(GAMMAS)),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=27, bound_steps=27))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_score_aligned_training.py')
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
        raise ValueError('retain the previous finite allowance')
    sources, env = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=env,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        parent, row = _parent(root, PRIOR, PRIOR_SHA, PRIOR_ID, PRIOR_TASK, PRIOR_ARTIFACT, stack)
        if (parent.envelope(PRIOR_TASK['identity'])['charged'] != PRIOR_TASK['limits']
                or [profile['gamma'] for profile in row['results']] != list(GAMMAS)):
            raise ValueError('exact earlier support and charged ledger required')
        keys = ['shape', 'nominal', 'later-operator', 'witness', *(model+suffix for model in MODELS
                                                                 for suffix in ('', '-weights', '-settings'))]
        staged = {key: parent.input(key, raw=True) for key in keys}
        staged['prior-support'] = encoded(row)
    staged.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=XML)
    for key, value in staged.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, value)
        inputs[key] = path
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .conditioned_position_margin import reverse_intervals
    from .esa_shared_profile_score import support as coefficients
    from .ilvis0_linked_training_support import support
    from .innovations_snapshot import restore
    from .state_space_directional_bound import adjoint_intervals

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('frozen directions and allowances required')

    def raw(key):
        return context.input_path(key).read_bytes()

    context.charge(bound_calls=1, bound_steps=1)
    shape, centers, saved, prior = map(lambda key: json.loads(raw(key)), ('shape', 'nominal', 'witness', 'prior-support'))
    later = restore(raw('later-operator'), expected_sha256=shape['factors_sha256'],
                    expected_configuration=shape['configuration'], maximum_bytes=2**26)
    taps = list(map(F, saved['taps']))
    weights = [(-hi, -lo) for lo, hi in reverse_intervals(later, taps, cut=TRAIN)] + [(value, value) for value in taps]
    norm = sum(max(abs(lo), abs(hi)) for lo, hi in weights)
    tap_lower = [endpoint(lo, False) for lo, _ in weights]
    tap_upper = [endpoint(hi, True) for _, hi in weights]
    metric = np.tile(shape['metric'], TRAIN+LATER)
    first, second = [np.asarray(centers[model], float).ravel().tolist() for model in MODELS]
    nominal = sum(tap*(F(b)-F(a)) for tap, a, b in zip(taps, first, second, strict=True))
    checks, best = {}, {}
    for model, change_sign in zip(MODELS, (-1, 1), strict=True):
        context.charge(bound_calls=1, bound_steps=1)
        residual, raw_design, design, lower, upper, operator, settings = training_inputs(raw, model)
        if settings['shape'] != shape:
            raise ValueError('unchanged model forecasts and covariance required')
        projected = coefficients(tap_lower, tap_upper, metric, raw_design)
        target = tuple(zip(projected['lower'], projected['upper'], strict=True))
        midpoint = np.array([float((lo+hi)/2) for lo, hi in target])
        directions = score_directions(design, midpoint, lower, upper, cutoffs=CUTOFFS)
        model_rows = []
        best[model] = {sign: [F(row['adverse'][str(sign)]['exact_upper']) for row in prior['model_checks'][model]]
                       for sign in (1, -1)}
        for proposed in directions:
            rows = []
            for sign in (1, -1):
                oriented = target if sign*change_sign == -1 else tuple((-hi, -lo) for lo, hi in target)
                axis = proposed['axis']
                if axis is not None:
                    axis = -sign*change_sign*axis
                    lo, hi = adjoint_intervals(operator, axis)
                    train = coefficients(lo, hi, np.ones(len(residual)), raw_design[:len(residual)])
                    training = tuple(zip(train['lower'], train['upper'], strict=True))
                for index, gamma in enumerate(GAMMAS):
                    context.charge(bound_calls=1, bound_steps=1)
                    proof = None if axis is None else support(residual, axis, training, oriented, lower, upper,
                                                               increase=INCREASE, unshared=gamma)
                    if proof is not None:
                        best[model][sign][index] = min(best[model][sign][index], F(proof['exact_upper']))
                    rows.append(dict(orientation=sign, gamma=gamma, proof=proof))
            model_rows.append(dict(cutoff=proposed['cutoff'], rank=proposed['rank'], checks=rows,
                                   axis=None if proposed['axis'] is None else proposed['axis'].tolist()))
        checks[model] = model_rows
    results = []
    for index, gamma in enumerate(GAMMAS):
        limits = {sign: [best[model][sign][index] for model in MODELS] for sign in (1, -1)}
        margin, sign, gaps = margin_from_support(nominal, norm, limits)
        bound = max(margin, F(saved['lower']), F(prior['results'][index]['new_lower_exact']))
        results.append(dict(gamma=gamma, computed_lower_exact=str(margin), orientation=sign,
                            best_lower_m=endpoint(bound, False), gaps={str(key): str(val) for key, val in gaps.items()}))
    result = dict(rows=results, checks=checks, passed=True, scientific_decision='abstain', new_fits=0, protected_reads=0)
    context.save(ARTIFACT, result)
    return result


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
        source = original
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, continuation)['selected'][identity]['origin']
            if origin != prefix:
                source = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
        row = source.envelope(identity)
        raw = source.artifact(identity, ARTIFACT)
        if row['status'] != 'complete' or row['charged'] != TASK['limits'] or raw != row['result']:
            raise ValueError('exact charge and result required')
        _write_equal(root/RESULT, encoded(dict(raw, completion=source.completion)))
    return raw['rows']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
