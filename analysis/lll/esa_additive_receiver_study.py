# SPDX-License-Identifier: AGPL-3.0-or-later
"""Forecast score transfer with positive shared and receiver covariance terms."""

import argparse
from contextlib import ExitStack, closing
import json
import math
from pathlib import Path

from .esa_forecast_receiver_transfer import BASE, LAWS, RECOVER, RECOVERY, REPORTS, WALL_S
from .esa_receiver_covariance_study import ID as PARENT, RESULT as PRIOR, task_for as previous_task
from .esa_window_scale_mixture import window_score
from .ilvis0_matched_observed_inputs import _write_equal
from .receiver_covariance_additive import additive_spectrum, select_scale
from .receiver_covariance_compatibility import ForecastWhitener, gaussian_score, receiver_root
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-additive-receiver-covariance-v1'
SCOPE = 'Matched ESA 187 covariance scores with shared and receiver-specific terms'
PLAN = BASE+'ESA_ADDITIVE_RECEIVER_COVARIANCE_PLAN.md'
RESULT = BASE+'esa-additive-receiver-covariance-result.json'
REQUEST = BASE+'esa-additive-receiver-covariance-qualification.json'
REPORT = BASE+'esa-additive-receiver-covariance-tests.xml'
TEST = 'analysis/tests/test_receiver_covariance_additive.py'
TESTS = ('test_additive_score_matches_dense_for_rank_deficient_receiver_component',
         'test_shared_scale_uses_the_donor_grid_once_and_all_three_marginals')
PRIOR_SHA = '2c11690bddd5fe97ef2acacd47c713ca29727c2730dff073bd30b0e3c068c629'
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=49, bound_steps=198)


def task_for(pair, law):
    return dict(previous_task(pair, law), limits=LIMITS)


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
        raise ValueError('reuse the existing frozen comparison')
    raw = (root/PRIOR).read_bytes()
    if digest(raw) != PRIOR_SHA:
        raise ValueError('the original compatibility report is required')
    prior = json.loads(raw)
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if (parent.completion != prior['closures'][parent.prefix] or not parent.summary['passed']
                or prior['complete'] != 8 or prior['windows'] != 16 or prior['compatible'] != 0):
            raise ValueError('the completed incompatibility check is required')
        design = parent.input('design')
        pairs = design['pairs']
        indices = [index for pair in pairs for index in pair]
        if len(indices) != 8 or len(set(indices)) != 8 or any(len(pair) != 2 for pair in pairs):
            raise ValueError('original disjoint window pairs required')
        tasks = [task_for(pair, law) for pair in pairs for law in LAWS]
        keys = ['design', *(f'observed-{index}' for index in indices)]
        keys.extend(f'{name}-{index}-{law}' for name in ('forecast', 'substitutions')
                    for index in indices for law in LAWS)
        keys.extend(f'fit-{pair[0]}' for pair in pairs)
        staged = {key: parent.input(key, raw=True) for key in keys}
        for task in tasks:
            identity = task['identity']
            if prior['results'][identity] != parent.envelope(identity)['result']:
                raise ValueError('the sealed prior fold is required')
            row = parent.input(identity)
            staged[identity] = encoded(row['fixed']['fit']['parameters'])
            staged[identity+'-reference'] = encoded(dict(dof=row['fixed']['dof'], windows=row['verified']['windows']))
    staged.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=REPORT)
    for key, raw in staged.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, raw)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=inputs, sources=sources, tasks=tasks, workers=2, threads=1, maximum_wall_s=WALL_S)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .esa_motion_innovation_scale import scorer
    from .esa_ppp_acquisition import TARGETS
    from .esa_repeat_turn_scoring import NATIVE_VARIANCE, _lower

    pair, law = (task['payload'][key] for key in ('pair', 'law'))

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    design = read('design')
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or pair not in design['pairs'] or law not in LAWS
            or declared != task_for(pair, law)):
        raise ValueError('the original paired forecast task is required')
    point = read(task['identity'])
    components = np.asarray([row['raw_components'] for row in read(f'fit-{pair[0]}')])
    roots = [receiver_root(REPORTS, components[:, index]) for index in range(3)]
    donor_ids = [index for other in design['pairs'] for index in other if index not in pair]

    def spectra(index):
        key = f'{index}-{law}'
        baseline = scorer(context, index, law, design['scores'][key])
        forecast, substitutions = read('forecast-'+key), read('substitutions-'+key)
        times = forecast['times_s']
        if (len(times) != REPORTS or times != substitutions['times_s']
                or set(substitutions['sources']) != set(TARGETS)
                or any(row['matched'] != REPORTS for row in substitutions['sources'].values())):
            raise ValueError('the original matched receiver epochs are required')
        context.charge(bound_calls=1, bound_steps=1)
        native = _lower(forecast['native_root_neu_m'], 3*REPORTS)*math.sqrt(NATIVE_VARIANCE[law])
        space = ForecastWhitener(baseline, native, times, point)
        offsets = {name: np.asarray(substitutions['sources'][name]['offsets_m'], float).reshape(-1, 1)
                   for name in TARGETS}
        residuals = {'air1': space.residual}
        residuals.update({name: space.residual+space.apply(values)[:, 0] for name, values in offsets.items()})
        values = {}
        for (name, residual), root in zip(residuals.items(), roots, strict=True):
            context.charge(bound_calls=1, bound_steps=1)
            spectrum = additive_spectrum(residual, space.apply(root), space.logdet)
            values[name] = (spectrum, gaussian_score(residual, space.logdet))
        return values

    donors = [spectrum for index in donor_ids for spectrum, _ in spectra(index).values()]
    selection = select_scale(donors, reserve=lambda: context.charge(bound_calls=1, bound_steps=18))
    context.save('donor-scale.json', dict(pair=pair, donor_ids=donor_ids, **selection))
    reference = read(task['identity']+'-reference')
    dof = reference['dof']
    changed = []
    for index, old in zip(pair, reference['windows'], strict=True):
        if index != old['index']:
            raise ValueError('the original omitted window is required')
        rows = spectra(index)
        results = {}
        for receiver, (spectrum, fixed) in rows.items():
            previous = old['air1'] if receiver == 'air1' else old['alternate'][receiver]
            if any(abs(fixed[name]-previous['gaussian'][name]) > 1e-6
                   for name in ('quadratic', 'negative_log_score')):
                raise ValueError('the original scoring reference did not reproduce')
            results[receiver] = dict(fixed=fixed, original_reference=previous['mixture']['within_reference'])
            results[receiver]['new'] = spectrum
        changed.append(dict(index=index, receivers=results))
    context.charge(bound_calls=1, bound_steps=6)
    for row in changed:
        for receiver in row['receivers'].values():
            additive = receiver.pop('new').score(selection['scale'])
            receiver.update(additive=additive, new_reference=window_score(additive, 3*REPORTS, dof)['within_reference'])
    result = dict(pair=pair, law=law, selection=selection, windows=changed, passed=True,
                  scientific_decision='abstain', new_fits=0, protected_reads=0)
    context.save('additive-receiver.json', result)
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
            row = source.artifact(identity, 'additive-receiver.json')
            if envelope['result'] != row or envelope['charged'] != LIMITS or envelope['status'] != 'complete':
                raise ValueError('verified original task and charges required')
            results[identity] = row
        totals = {}
        for law in LAWS:
            windows = [window for row in results.values() if row['law'] == law for window in row['windows']]
            totals[law] = {method: math.fsum(receiver[method]['negative_log_score']
                           for window in windows for receiver in window['receivers'].values())
                           for method in ('fixed', 'additive')}
        improved = len(results) == 8 and all(row['additive'] < row['fixed'] for row in totals.values())
        result = dict(results=results, complete=len(results), totals=totals, improved_both=improved,
                      closures={key: study.completion for key, study in sources.items()})
    _write_equal(root/RESULT, encoded(result))
    return {key: result[key] for key in ('complete', 'totals', 'improved_both')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    output = qualification(root, check=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(output, sort_keys=True))
