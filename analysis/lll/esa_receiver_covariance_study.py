# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the compatibility of donor receiver terms with fixed ESA covariance."""

import argparse
from contextlib import ExitStack, closing
import json
import math
from pathlib import Path

from .esa_forecast_receiver_transfer import BASE, LAWS, RECOVER, RECOVERY, REPORTS, WALL_S
from .esa_forecast_receiver_transfer import ID as TRANSFER, RESULT as TRANSFER_REPORT
from .esa_receiver_contrast_study import ID as CONTRAST, RESULT as CONTRAST_REPORT
from .esa_window_scale_mixture import window_score
from .ilvis0_matched_observed_inputs import _write_equal
from .receiver_covariance_compatibility import (
    ForecastWhitener, gaussian_score, receiver_root, replacement_capacity, replace_receiver,
)
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-receiver-covariance-compatibility-v1'
SCOPE = 'Receiver covariance replacement compatibility on eight fixed ESA 187 forecasts'
PLAN = BASE+'ESA_RECEIVER_COVARIANCE_COMPATIBILITY_PLAN.md'
RESULT = BASE+'esa-receiver-covariance-compatibility-result.json'
REQUEST = BASE+'esa-receiver-covariance-compatibility-qualification.json'
REPORT = BASE+'esa-receiver-covariance-compatibility-tests.xml'
TEST = 'analysis/tests/test_receiver_covariance_compatibility.py'
TESTS = (
    'test_receiver_root_recovers_band_covariances_and_excludes_constant_mode',
    'test_working_whitener_matches_independent_dense_covariance',
    'test_exact_receiver_capacity_and_replacement_are_not_clipped',
)
INPUT_REPORTS = {
    TRANSFER_REPORT: '86b324d0d336a84e98ed7e11d54d8a51251f5f74affc5d2ef0dcc18c3d75166a',
    CONTRAST_REPORT: '94b71900dc7414fa1b43463e3ef42e1c47ef5c3ce3d2181f8ad34cacfae01ccf',
}
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=8, bound_steps=10)


def task_for(pair, law):
    return dict(identity=f'{pair[0]}-{law}', input_key='design',
                payload=dict(pair=pair, law=law), limits=LIMITS)


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
        raise ValueError('retain the existing study and its allowance')
    reports = {}
    for name, expected in INPUT_REPORTS.items():
        raw = (root/name).read_bytes()
        if digest(raw) != expected:
            raise ValueError('exact previous comparison reports required')
        reports[name] = json.loads(raw)
    transfer_report, contrast_report = (reports[name] for name in INPUT_REPORTS)
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with (closing(ClosedStudy(root, 'data/'+TRANSFER)) as transfer,
          closing(ClosedStudy(root, 'data/'+CONTRAST)) as contrast):
        if (transfer.completion != transfer_report['closures'][transfer.prefix]
                or contrast.completion != contrast_report['closures'][contrast.prefix]
                or not transfer.summary['passed'] or not contrast.summary['passed']
                or not contrast_report['candidate_retained'] or transfer_report['available'] != 32):
            raise ValueError('verified full receiver comparison and eligible donor fits required')
        design = transfer.input('design')
        pairs = design['pairs']
        indices = [index for pair in pairs for index in pair]
        if len(set(indices)) != len(indices) or len(indices) != 8 or contrast.input('design') != pairs:
            raise ValueError('exact matched omitted pairs required')
        tasks = [task_for(pair, law) for pair in pairs for law in LAWS]
        keys = ['design', *(f'observed-{index}' for index in indices)]
        keys.extend(f'{name}-{index}-{law}' for name in ('forecast', 'substitutions')
                    for index in indices for law in LAWS)
        staged = {key: transfer.input(key, raw=True) for key in keys}
        for pair in pairs:
            identity = str(pair[0])
            fit = contrast.artifact(identity, 'donor-covariances.json')
            row = contrast.envelope(identity)['result']
            if (row != contrast_report['folds'][identity] or fit['pair'] != pair
                    or any(value != row[key] for key, value in fit.items())
                    or set(fit['donors']) != set(indices)-set(pair)):
                raise ValueError('verified donor-only covariance required')
            staged['fit-'+identity] = encoded(fit['covariances'])
            for law in LAWS:
                paired = task_for(pair, law)['identity']
                result = transfer.artifact(paired, 'receiver-transfer.json')
                if result != transfer_report['results'][paired] or result != transfer.envelope(paired)['result']:
                    raise ValueError('verified original scoring anchors required')
                staged[paired] = encoded(dict(fixed=transfer.input(paired), verified=result))
    staged.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, transfer_report=TRANSFER_REPORT, contrast_report=CONTRAST_REPORT,
                  qualification=REQUEST, qualification_tests=REPORT)
    for name, raw in staged.items():
        path = f'data/{ID}-inputs/{name}'
        _write_equal(root/path, raw)
        inputs[name] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=inputs, sources=sources, tasks=tasks, workers=2, threads=1, maximum_wall_s=WALL_S)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np
    from scipy.linalg import LinAlgError

    from .esa_motion_innovation_scale import scorer
    from .esa_ppp_acquisition import TARGETS
    from .esa_repeat_turn_scoring import NATIVE_VARIANCE, _lower

    pair, law = (task['payload'][key] for key in ('pair', 'law'))

    def read(name):
        return json.loads(context.input_path(name).read_bytes())

    design = read('design')
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or pair not in design['pairs'] or law not in LAWS
            or declared != task_for(pair, law)):
        raise ValueError('the exact frozen forecast pair is required')
    saved = read(task['identity'])
    point = saved['fixed']['fit']['parameters']
    dof = saved['fixed']['dof']
    components = np.asarray([row['raw_components'] for row in read(f'fit-{pair[0]}')])
    windows = []
    for index, row in zip(pair, saved['verified']['windows'], strict=True):
        key = f'{index}-{law}'
        baseline = scorer(context, index, law, design['scores'][key])
        forecast, substitutions = read('forecast-'+key), read('substitutions-'+key)
        times = forecast['times_s']
        dimension = 3*len(times)
        if (index != row['index'] or len(times) != REPORTS or times != substitutions['times_s']
                or set(substitutions['sources']) != set(TARGETS)):
            raise ValueError('the original 120 matched epochs are required')
        context.charge(bound_calls=1, bound_steps=1)
        native = _lower(forecast['native_root_neu_m'], dimension)*math.sqrt(NATIVE_VARIANCE[law])
        space = ForecastWhitener(baseline, native, times, point)
        original = gaussian_score(space.residual, space.logdet)
        expected = row['air1']['gaussian']
        expected_logdet = 2*expected['negative_log_score']-expected['quadratic']-dimension*math.log(2*math.pi)
        if (abs(space.logdet-expected_logdet) > 1e-6 or abs(original['quadratic']-expected['quadratic']) > 1e-6):
            raise ValueError('fixed working covariance did not reproduce')
        air1 = space.apply(receiver_root(REPORTS, components[:, 0]))
        capacity, margin = replacement_capacity(air1)
        compatible = capacity is None or capacity >= 1.
        alternate = {}
        for component, name in enumerate(TARGETS, start=1):
            offsets = substitutions['sources'][name]['offsets_m']
            if not compatible or offsets is None:
                alternate[name] = dict(scored=False, reason='incompatible' if not compatible else 'missing')
                continue
            context.charge(bound_calls=1, bound_steps=1)
            mode = space.apply(receiver_root(REPORTS, components[:, component]))
            shifted = space.residual+space.apply(np.asarray(offsets, float).reshape(-1, 1))[:, 0]
            try:
                revised = replace_receiver(shifted, air1, mode, logdet=space.logdet)
            except LinAlgError:
                alternate[name] = dict(scored=False, reason='singular')
            else:
                alternate[name] = dict(scored=True, gaussian=revised, mixture=window_score(revised, dimension, dof))
        windows.append(dict(index=index, capacity=capacity, margin=margin, compatible=compatible,
                            fixed_gaussian=original, alternate=alternate))
    result = dict(pair=pair, law=law, windows=windows, passed=True, scientific_decision='abstain',
                  new_fits=0, original_reads=0, protected_reads=0)
    context.save('receiver-compatibility.json', result)
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
            if all(identity in original.rows and original.envelope(identity)['status'] == 'complete'
                   for identity in original.tasks):
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVER)
    return resume_campaign(root, continuation)


def report(root):
    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        sources = {prefix: original}
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            selected = {identity: row['origin'] for identity, row in inspect(root, continuation)['selected'].items()}
        else:
            selected = {identity: prefix for identity in original.rows
                        if original.envelope(identity)['status'] == 'complete'}
        results = {}
        for identity, origin in selected.items():
            if origin not in sources:
                sources[origin] = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
            source = sources[origin]
            envelope = source.envelope(identity)
            row = source.artifact(identity, 'receiver-compatibility.json')
            attempts = sum(value['scored'] or value.get('reason') == 'singular'
                           for window in row['windows'] for value in window['alternate'].values())
            expected = dict(LIMITS, bound_calls=4+attempts, bound_steps=6+attempts)
            if envelope['result'] != row or envelope['charged'] != expected or envelope['status'] != 'complete':
                raise ValueError('verified result and work charges required')
            results[identity] = row
        windows = [window for row in results.values() for window in row['windows']]
        result = dict(results=results, complete=len(results), windows=len(windows),
                      compatible=sum(item['compatible'] for item in windows),
                      scored=sum(item['scored'] for row in windows for item in row['alternate'].values()),
                      closures={key: study.completion for key, study in sources.items()})
    _write_equal(root/RESULT, encoded(result))
    return {key: result[key] for key in ('complete', 'windows', 'compatible', 'scored')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    output = qualification(root, check=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(output, sort_keys=True))
