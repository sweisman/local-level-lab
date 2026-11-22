# SPDX-License-Identifier: AGPL-3.0-or-later
"""Budget timed integration errors on the certified ESA contrast."""

import argparse
from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
from pathlib import Path

from .conditioned_position_margin import reverse_intervals
from .esa_calibration_conditioned_margin import BASE, RECOVER, RECOVERY, WALL_S, _parent
from .esa_compact_forecast_margin import ARTIFACT as PRIOR_ARTIFACT
from .esa_compact_forecast_margin import ID as PRIOR_STUDY, RESULT as PRIOR, TASK as PRIOR_TASK
from .esa_linked_training_support import LATER, TRAIN
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_saved_prediction_audit import endpoint
from .innovations_snapshot import restore
from .integrated_contrast_bound import contrast_allowances
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'esa-integrated-contrast-support-v1'
SCOPE = 'Cut-conditioned ESA contrast applied to accumulated velocity errors'
PLAN = BASE+'ESA_INTEGRATED_CONTRAST_SUPPORT_PLAN.md'
REQUEST = BASE+'esa-integrated-contrast-support-qualification.json'
XML = BASE+'esa-integrated-contrast-support-tests.xml'
RESULT = BASE+'esa-integrated-contrast-support-result.json'
PRIOR_SHA = 'e2c4292e8552707492cd62717f96f63d6334d5629f1d3e18809b3f72ef65eeb7'
ARTIFACT = 'support.json'
TESTS = ('test_integrated_weights_reach_the_exact_vertex_maximum',
         'test_directional_enclosure_preserves_interleaved_axes_and_uncertainty',
         'test_allowance_uses_the_same_gap_and_assigns_cross_cut_interval_to_forecast')
TASK = dict(identity='timed-velocity-support', input_key='times', payload=dict(cut=TRAIN, later=LATER),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=3, bound_steps=3))


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_integrated_contrast_bound.py')
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
        parent, row = _parent(root, PRIOR, PRIOR_SHA, PRIOR_STUDY, PRIOR_TASK, PRIOR_ARTIFACT, stack)
        if (parent.envelope(PRIOR_TASK['identity'])['charged'] != PRIOR_TASK['limits']
                or F(row['proposed_lower_exact']) <= 0 or len(row['exact_later_taps']) != 3*LATER):
            raise ValueError('the frozen certified direction is required')
        values = {key: parent.input(key, raw=True) for key in ('shape', 'times', 'later-operator')}
        values['direction'] = encoded({key: row[key] for key in ('proposed_lower_exact', 'exact_later_taps')})
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=XML)
    for key, value in values.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, value)
        inputs[key] = path
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the frozen comparison and cut are required')

    def raw(name):
        return context.input_path(name).read_bytes()

    context.charge(bound_calls=1, bound_steps=1)
    shape, times, direction = map(lambda key: json.loads(raw(key)), ('shape', 'times', 'direction'))
    operator = restore(raw('later-operator'), expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)
    if operator.epoch_count != len(times) or len(times) != TRAIN+LATER or operator.observation_dimension != 3:
        raise ValueError('the original chronology and positions are required')
    late = list(map(F, direction['exact_later_taps']))
    context.charge(bound_calls=1, bound_steps=1)
    early = [(-hi, -lo) for lo, hi in reverse_intervals(operator, late, cut=TRAIN)]
    taps = early + [(value, value) for value in late]
    context.charge(bound_calls=1, bound_steps=1)
    coefficients, gap, limits = contrast_allowances(times, taps, F(direction['proposed_lower_exact']), axes=3, cut=TRAIN)
    values = {key: None if limit is None else endpoint(limit, False) for key, limit in limits.items()}
    result = dict(coefficients={key: list(map(str, row)) for key, row in coefficients.items()},
                  score_gap_lower_exact=str(gap), limits=values,
                  limits_exact={key: None if value is None else str(value) for key, value in limits.items()},
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
        row = study.envelope(identity)
        verdict = study.artifact(identity, ARTIFACT)
        if row['status'] != 'complete' or row['charged'] != TASK['limits'] or verdict != row['result']:
            raise ValueError('the exact declared support work is required')
        _write_equal(root/RESULT, encoded(dict(verdict, completion=study.completion)))
        return verdict['limits']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, verify=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
