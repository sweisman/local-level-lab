# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score donor-selected forecasts of relative GPS position offsets."""

import argparse
from contextlib import ExitStack, closing
import json
import math
from pathlib import Path

from .esa_ppp_covariance_chronology import BASE, BATCH_SIZES, RECOVER, RECOVERY, WALL_S, closed_stage
from .esa_ppp_covariance_chronology import RESULT as PRIOR
from .ilvis0_matched_observed_inputs import _write_equal
from .receiver_contrast_covariance import gaussian_loss
from .receiver_offset_forecast import CANDIDATES, fit_candidate, forecast
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-ppp-offset-forecast-v1'
SCOPE = 'ESA 187 early-to-late conditional prediction of relative GPS offsets'
PLAN = BASE+'ESA_PPP_OFFSET_FORECAST_PLAN.md'
RESULT = BASE+'esa-ppp-offset-forecast-result.json'
REQUEST = BASE+'esa-ppp-offset-forecast-qualification.json'
REPORT = BASE+'esa-ppp-offset-forecast-tests.xml'
TEST = 'analysis/tests/test_receiver_offset_forecast.py'
TESTS = ('test_random_walk_variance_scales_with_elapsed_window_count',
         'test_reverting_mean_and_variance_have_stationary_limit',
         'test_walk_fit_uses_elapsed_cadence_and_only_the_named_donors')
PRIOR_SHA = '65716c54acf4220096a7706e05f2ea9c6612377c4c052acac73f9041ee6714a9'
LEADS = (1, 4, 12)
TASK = dict(identity='offset-transfer', input_key='train', payload=dict(leads=list(LEADS)),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=496, bound_steps=1455))


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
        raise ValueError('retain the frozen offset comparison')
    raw = (root/PRIOR).read_bytes()
    if digest(raw) != PRIOR_SHA:
        raise ValueError('the original chronological report is required')
    prior = json.loads(raw)
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        donor, _, train_closures = closed_stage(root, 'train', stack)
        later, _, score_closures = closed_stage(root, 'score', stack)
        if (prior['closures'] != dict(train=train_closures, score=score_closures)
                or prior['selection'] != later.input('selection')
                or donor.input('selection') != prior['selection']):
            raise ValueError('the original chronological split is required')
        staged = {name: (donor if name == 'train' else later).input(name, raw=True) for name in BATCH_SIZES}
    for name, material in staged.items():
        if digest(material) != prior['selection']['hashes'][name]:
            raise ValueError('the signed original position differences are required')
    staged.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER),
                  identities=encoded({name: [row['identity'] for row in rows]
                                      for name, rows in prior['selection']['batches'].items()}))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=REPORT)
    for name, material in staged.items():
        path = f'data/{ID}-inputs/{name}'
        _write_equal(root/path, material)
        inputs[name] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1, maximum_wall_s=WALL_S)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def prediction_score(model, earlier, observed, elapsed):
    import numpy as np

    mean, covariance = forecast(model, earlier, elapsed)
    error = observed-mean
    loss = gaussian_loss(error[None, :], covariance)
    normalization = 6.*math.log(2.*math.pi)+np.linalg.slogdet(covariance)[1]
    return dict(error_m=error.tolist(), quadratic=2.*loss-normalization, negative_log_score=loss)


def evaluate(task, context):
    import numpy as np

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the original single fixed comparison is required')
    identities = json.loads(context.input_path('identities').read_bytes())

    def read(batch):
        raw = json.loads(context.input_path(batch).read_bytes())
        if [row['identity'] for row in raw] != identities[batch] or len(raw) != BATCH_SIZES[batch]:
            raise ValueError('the exact earlier/later identities are required')
        means = []
        for row in raw:
            context.charge(bound_calls=1, bound_steps=1)
            if not row['complete']:
                means.append(None)
                continue
            positions = np.asarray(row['contrasts'], float)
            if positions.shape != (120, 6) or not np.isfinite(positions).all():
                raise ValueError('the exact six-channel window is required')
            means.append(positions.mean(axis=0))
        return means

    earlier = read('train')
    fit_ids = [i for i, value in zip(identities['train'], earlier, strict=True) if value is not None]
    earlier_values = [value for value in earlier if value is not None]
    candidates = []
    for law, memory in CANDIDATES:
        context.charge(bound_calls=1, bound_steps=96)
        candidates.append(fit_candidate(fit_ids, earlier_values, law, memory))
    reference = candidates[0]
    selected = min(candidates[1:], key=lambda model: model['negative_log_score'])
    context.save('donor-offset-models.json', dict(fit_ids=fit_ids, candidates=candidates, chosen=selected))
    all_ids = list(identities['train'])
    values = list(earlier)
    for batch in BATCH_SIZES:
        if batch != 'train':
            all_ids.extend(identities[batch])
            values.extend(read(batch))
    if sorted(set(all_ids)) != all_ids:
        raise ValueError('the original increasing chronology is required')
    scores = {}
    for horizon in LEADS:
        records = []
        for index in range(len(earlier), len(values)):
            context.charge(bound_calls=1, bound_steps=2)
            previous, observed = values[index-horizon], values[index]
            elapsed = all_ids[index]-all_ids[index-horizon]
            row = dict(target=all_ids[index], earlier=all_ids[index-horizon], elapsed_s=elapsed*120)
            if previous is None or observed is None:
                records.append(dict(row, skipped='missing complete earlier or later window'))
                continue
            records.append(dict(row, independent=prediction_score(reference, previous, observed, elapsed),
                                changing=prediction_score(selected, previous, observed, elapsed)))
        scores[str(horizon)] = records
    context.save('offset-scores.json', scores)
    return dict(passed=True, targets=len(values)-len(earlier), new_fits=0, protected_reads=0,
                scientific_decision='abstain')


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
            if TASK['identity'] in original.rows and original.envelope(TASK['identity'])['status'] == 'complete':
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVER)
    return resume_campaign(root, continuation)


def report(root):
    prefix = 'data/'+ID
    continuation = root/(prefix+'-recovery')
    identity = TASK['identity']
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        source = original
        if continuation.is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, continuation)['selected'][identity]['origin']
            if origin != prefix:
                source = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
        envelope = source.envelope(identity)
        data = source.artifact(identity, 'offset-scores.json')
        model = source.artifact(identity, 'donor-offset-models.json')
        if (envelope['status'] != 'complete' or envelope['charged'] != TASK['limits']
                or set(data) != {str(horizon) for horizon in LEADS}):
            raise ValueError('verified score and work receipt required')
        rows = {}
        for horizon, values in data.items():
            if len(values) != envelope['result']['targets']:
                raise ValueError('every original target must be retained')
            valid = [row for row in values if 'skipped' not in row]
            count = 6*len(valid)
            rows[horizon] = dict(
                evaluated=len(valid), missing=len(values)-len(valid),
                elapsed_s=[min(row['elapsed_s'] for row in valid), max(row['elapsed_s'] for row in valid)],
                scores={law: dict(negative_log_score=math.fsum(row[law]['negative_log_score'] for row in valid),
                                  mean_squared_standardized=math.fsum(row[law]['quadratic'] for row in valid)/count,
                                  rms_m=math.sqrt(math.fsum(x*x for row in valid for x in row[law]['error_m'])/count))
                        for law in ('independent', 'changing')})
        result = dict(model=model, leads=rows, original=original.completion, selected=source.completion)
    _write_equal(root/RESULT, encoded(result))
    return {key: result[key] for key in ('leads',)} | {'selected': (model['chosen']['law'], model['chosen']['memory'])}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    output = qualification(root, check=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(output, sort_keys=True))
