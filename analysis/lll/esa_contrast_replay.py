# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the compact ESA direction on four sealed nonlinear calibration examples."""

import argparse
from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
from pathlib import Path
import sys


BASE = 'docs/prediction-observed-development/'
ID = 'esa-contrast-replay-v1'
SCOPE = 'Original ESA physical points scored by the certified compact forecast contrast'
PLAN = BASE+'ESA_CONTRAST_REPLAY_PLAN.md'
RESULT = BASE+'esa-contrast-replay-result.json'
REQUEST = BASE+'esa-contrast-replay-qualification.json'
XML = BASE+'esa-contrast-replay-tests.xml'
OLD_MANIFEST = '92cd0062b34b7f46f8fef9545639764e75c22e23dfc43d5aac95efbf9d3e7f32'
COMPACT_SHA = 'e2c4292e8552707492cd62717f96f63d6334d5629f1d3e18809b3f72ef65eeb7'
SUPPORT_SHA = '4e3eae50b6e904ba4c521b7c25669ea59f36c715973a5edba855f05ea6b2ed93'
ARTIFACT = 'contrast-replay.json'
TESTS = ('test_replay_preserves_subtraction_and_projects_signed_error_enclosure',
         'test_replay_requires_all_epochs_and_complete_cut')


def tasks():
    from .esa_linked_physical_replay import tasks as original

    return [dict(task, limits=dict(task['limits'], bound_calls=2, bound_steps=2)) for task in original()]


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .shape_remainder_witness import COMPANIONS
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    seeds = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_contrast_replay.py', *COMPANIONS)
    sources, env = source_closure(root, seeds), runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=env, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=env, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources, env


def prepare(root):
    from .airquantumgrav_inventory import environment
    from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, WALL_S, _parent
    from .esa_compact_forecast_margin import ARTIFACT as COMPACT_ARTIFACT
    from .esa_compact_forecast_margin import ID as COMPACT_ID, RESULT as COMPACT, TASK as COMPACT_TASK
    from .esa_integrated_contrast_support import ARTIFACT as SUPPORT_ARTIFACT
    from .esa_integrated_contrast_support import ID as SUPPORT_ID, RESULT as SUPPORT, TASK as SUPPORT_TASK
    from .esa_linked_physical_replay import GAMMAS, ID as OLD_ID, tasks as original
    from .ilvis0_matched_observed_inputs import _write_equal
    from .shape_remainder_witness import COMPANIONS, MODEL_INPUTS, SHARED
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite replay allowance')
    sources, env = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=env,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        old = stack.enter_context(closing(ClosedStudy(root, 'data/'+OLD_ID)))
        compact, contrast = _parent(root, COMPACT, COMPACT_SHA, COMPACT_ID, COMPACT_TASK, COMPACT_ARTIFACT, stack)
        support, budget = _parent(root, SUPPORT, SUPPORT_SHA, SUPPORT_ID, SUPPORT_TASK, SUPPORT_ARTIFACT, stack)
        if (old.completion['manifest_sha256'] != OLD_MANIFEST or not old.summary['passed']
                or old.input('environment') != environment() or compact.input('times') != old.input('forecast_times')
                or compact.input('later-operator', raw=True) != old.input('later-operator', raw=True)
                or compact.input('shape') != old.input('shape-direction')
                or support.input('direction')['exact_later_taps'] != contrast['exact_later_taps']
                or any(digest((root/name).read_bytes()) != old.manifest['sources'][name] for name in COMPANIONS)):
            raise ValueError('the original replay, source companions, times, forecast and support must all match')
        values = {key: old.input(key, raw=True) for key in (*SHARED, 'shape-direction', 'later-operator')}
        for task in original():
            model = task['identity']
            if old.envelope(model)['charged'] != task['limits']:
                raise ValueError('original three-pass charge required')
            for name in (*MODEL_INPUTS, 'probes', 'approximations'):
                key = model+'-'+name
                values[key] = old.input(key, raw=True)
            results = old.artifact(model, 'linked-replay.json')
            if [row['gamma'] for row in results['checks']] != list(GAMMAS):
                raise ValueError('all original linked examples required')
            values[model+'-verified'] = encoded(results)
        values['direction'] = encoded(dict(taps=contrast['exact_later_taps'],
                                          gap=budget['score_gap_lower_exact'], limits=budget['limits']))
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, qualification=REQUEST, qualification_tests=XML, compact=COMPACT, support=SUPPORT)
    for key, value in values.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, value)
        inputs[key] = path
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=tasks(), workers=2, threads=1,
                                     maximum_wall_s=WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    import math
    import numpy as np

    from .airquantumgrav_inventory import environment
    from .conditioned_position_margin import reverse_intervals
    from .contrast_replay import summarize_error
    from .esa_linked_physical_replay import CALLS, EARLIER, score_replay
    from .esa_tangent_remainder import invoke_frozen
    from .ilvis0_saved_prediction_audit import endpoint
    from .innovations_snapshot import restore
    from .shape_remainder_witness import COMPANIONS, MODEL_INPUTS, MODELS, SHARED

    model = task['identity']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}

    def read(name):
        return json.loads(context.input_path(name).read_bytes())

    if context.manifest['scope'] != SCOPE or declared not in tasks() or read('environment') != environment():
        raise ValueError('the original source, environment and charged replay are required')
    inputs = (*SHARED, *(model+'-'+name for name in (*MODEL_INPUTS, 'probes')))
    raw = invoke_frozen(context, entry=Path(__file__), calls=CALLS, inputs=inputs, companions=COMPANIONS)
    context.save_bytes('integrated-paths.json', raw)
    measured = json.loads(raw)
    shape, direction, original = read('shape-direction'), read('direction'), read(model+'-verified')
    probes, fit = read(model+'-probes'), read(model+'-fit')
    if measured['model'] != model or measured['baseline_scalar_max_m'] != original['baseline_scalar_max_m']:
        raise ValueError('the exact original scalar baseline is required')
    earlier = restore(context.input_path(model+'-weights').read_bytes(),
                      expected_sha256=read(model+'-weights-receipt')['snapshot_sha256'],
                      expected_configuration=read(model+'-forecast')['error_training_configuration'], maximum_bytes=2**26)
    later = restore(context.input_path('later-operator').read_bytes(), expected_sha256=shape['factors_sha256'],
                    expected_configuration=shape['configuration'], maximum_bytes=2**26)
    late = list(map(F, direction['taps']))
    taps = [(-hi, -lo) for lo, hi in reverse_intervals(later, late, cut=EARLIER)] + [(tap, tap) for tap in late]
    baseline = np.asarray(measured['baseline'], dtype=float)
    approximations = np.load(context.input_path(model+'-approximations'), allow_pickle=False)
    timestamps, metric = read('forecast_times'), np.asarray(shape['metric'])
    residual = np.asarray(fit['local_linearization']['residual'])
    results = []
    for original_row, probe, integrated, affine in zip(original['checks'], probes, measured['paths'], approximations, strict=True):
        context.charge(bound_calls=1, bound_steps=1)
        integrated = np.asarray(integrated, float)
        original_score = score_replay(integrated-baseline, affine, residual, earlier, later, metric,
                                      np.asarray(shape['direction']), split=EARLIER, sign=1 if model == MODELS[0] else -1)
        agreement = all(original_row[key] == value if type(value) is bool else
                        math.isclose(original_row[key], value, rel_tol=1e-10, abs_tol=1e-10)
                        for key, value in original_score.items())
        if original_row['gamma'] != probe['gamma'] or not agreement:
            raise ValueError('the original replay loss, score and gate must reproduce')
        result = summarize_error(integrated.tolist(), baseline.tolist(), affine.tolist(), metric.tolist(), timestamps,
                                 taps, cut=EARLIER)
        score_lo, score_hi = result.pop('score_bounds')
        results.append(dict(gamma=probe['gamma'], original=original_score,
                            score_bounds=[endpoint(score_lo, False), endpoint(score_hi, True)],
                            score_exact=[str(score_lo), str(score_hi)],
                            fraction_of_gap=endpoint(max(abs(score_lo), abs(score_hi))/F(direction['gap']), True),
                            **{key: [endpoint(v, True) for v in values] for key, values in result.items()}))
    outcome = dict(model=model, checks=results, baseline_scalar_max_m=measured['baseline_scalar_max_m'],
                   gap_lower=endpoint(F(direction['gap']), False), new_fits=0, protected_reads=0,
                   passed=True, scientific_decision='abstain')
    context.save(ARTIFACT, outcome)
    return outcome


def frozen_replay(inputs, output):
    from lll.esa_tangent_remainder import scalar_replay
    from lll.studies.artifacts import encoded

    model, = (name.removesuffix('-fit') for name in inputs if name.endswith('-fit'))
    inputs.update({name[len(model)+1:]:value for name,value in inputs.copy().items() if name.startswith(model+'-')})
    probes = json.loads(Path(inputs['probes']).read_bytes())
    if [row['gamma'] for row in probes] != [0., .1]:
        raise ValueError('exact original calibration examples required')
    _, _, _, _, baseline, baseline_max, displacement = scalar_replay(inputs, output, expected_model=model)
    paths = [displacement(probe['point']).tolist() for probe in probes]
    output.write_bytes(encoded(dict(model=model, baseline=baseline.tolist(), baseline_scalar_max_m=baseline_max, paths=paths)))


def recover(root):
    from .esa_calibration_conditioned_margin import RECOVER, RECOVERY
    from .studies.closed import ClosedStudy
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as study:
            if study.input('recovery_policy') != RECOVER:
                raise ValueError('unchanged recovery policy required')
            if all(task['identity'] in study.rows and study.envelope(task['identity'])['status'] == 'complete' for task in tasks()):
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVER)
    return resume_campaign(root, continuation)


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import encoded
    from .studies.closed import ClosedStudy

    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    selected = {}
    if continuation.is_dir():
        from .studies.combined_task_evidence import inspect

        selected = inspect(root, continuation)['selected']
    summaries = {}
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        for task in tasks():
            identity = task['identity']
            origin = selected.get(identity, {}).get('origin', prefix)
            study = original if origin == prefix else stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
            row, raw = study.envelope(identity), study.artifact(identity, ARTIFACT)
            if row['status'] != 'complete' or row['charged'] != task['limits'] or raw != row['result']:
                raise ValueError('the exact declared replay and charges are required')
            summaries[identity] = dict(result=raw, completion=study.completion)
    _write_equal(root/RESULT, encoded(summaries))
    return {identity: [dict(gamma=r['gamma'], fraction=r['fraction_of_gap'], after_cut_mps=max(r['later_velocity_max']))
                      for r in row['result']['checks']] for identity, row in summaries.items()}


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '_frozen':
        frozen_replay(json.loads(sys.argv[2]), Path(sys.argv[3]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
        action = parser.parse_args().action
        root = Path.cwd()
        result = qualification(root, verify=False) if action == 'request' else {
            'prepare': prepare, 'recover': recover, 'report': report}[action](root)
        print(json.dumps(result, sort_keys=True))
