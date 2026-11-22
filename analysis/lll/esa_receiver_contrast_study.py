# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate fixed-band receiver covariance on omitted pairs from ESA 187."""

import argparse
from contextlib import ExitStack, closing
import json
import math
from pathlib import Path

from .esa_forecast_receiver_transfer import BASE, RECOVER, RECOVERY, WALL_S
from .esa_forecast_receiver_transfer import ID as PARENT, RESULT as PRIOR
from .ilvis0_matched_observed_inputs import _write_equal
from .receiver_contrast_covariance import BAND_EDGES_HZ, contrast_covariances, gaussian_loss, split_bands
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-receiver-contrast-covariance-v1'
SCOPE = 'Paired GPS receiver contrast covariance on eight fixed ESA 187 windows'
PLAN = BASE+'ESA_RECEIVER_CONTRAST_COVARIANCE_PLAN.md'
RESULT = BASE+'esa-receiver-contrast-covariance-result.json'
REQUEST = BASE+'esa-receiver-contrast-covariance-qualification.json'
REPORT = BASE+'esa-receiver-contrast-covariance-tests.xml'
TEST = 'analysis/tests/test_receiver_contrast_covariance.py'
PRIOR_SHA = '86b324d0d336a84e98ed7e11d54d8a51251f5f74affc5d2ef0dcc18c3d75166a'
TESTS = (
    'test_separate_receiver_matrices_recover_exact_independent_components',
    'test_invalid_components_are_recorded_and_structured_score_stays_finite',
    'test_cosine_band_partition_preserves_dc_free_energy',
)
LAWS = ('independent', 'unrestricted', 'isotropic')
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=24, bound_steps=72)
EXPECTED = dict(LIMITS, bound_calls=20, bound_steps=60)


def task_for(pair):
    return dict(identity=str(pair[0]), input_key='design', payload=dict(pair=pair), limits=LIMITS)


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
        raise ValueError('retain the existing frozen comparison')
    raw = (root/PRIOR).read_bytes()
    if digest(raw) != PRIOR_SHA:
        raise ValueError('the verified receiver substitution report is required')
    previous = json.loads(raw)
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if (parent.completion != previous['closures'][parent.prefix] or not parent.summary['passed']
                or previous['available'] != 32 or previous['complete'] != 8):
            raise ValueError('all eight windows must have both alternate receivers')
        pairs = parent.input('design')['pairs']
        indices = [index for pair in pairs for index in pair]
        if len(indices) != 8 or len(set(indices)) != 8 or any(len(pair) != 2 for pair in pairs):
            raise ValueError('the original four disjoint pairs are required')
        staged = {str(index): parent.input(f'substitutions-{index}-point', raw=True) for index in indices}
    staged.update(design=encoded(pairs), recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=REPORT)
    for key, raw in staged.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, raw)
        inputs[key] = name
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=inputs,
                      sources=sources, tasks=[task_for(pair) for pair in pairs], workers=2, threads=1,
                      maximum_wall_s=WALL_S)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np
    from .esa_ppp_acquisition import TARGETS

    pair = task['payload']['pair']
    pairs = json.loads(context.input_path('design').read_bytes())
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or pair not in pairs or declared != task_for(pair)):
        raise ValueError('the exact frozen pair is required')
    donors = [index for other in pairs for index in other if index not in pair]
    if len(donors) != 6:
        raise ValueError('exactly six donors required')

    def bands(index):
        context.charge(bound_calls=1, bound_steps=3)
        row = json.loads(context.input_path(str(index)).read_bytes())
        if (set(row['sources']) != set(TARGETS)
                or any(source['matched'] != 120 for source in row['sources'].values())):
            raise ValueError('both alternate coordinates required at every epoch')
        offsets = [row['sources'][name]['offsets_m'] for name in TARGETS]
        return split_bands(np.column_stack(offsets), row['absolute_times_s'])

    earlier = [bands(index) for index in donors]
    fits = []
    for blocks in zip(*(value[0] for value in earlier), strict=True):
        context.charge(bound_calls=1, bound_steps=6)
        observations = np.concatenate(blocks)
        fits.append(contrast_covariances(observations.T@observations/len(observations)))
    selection = dict(pair=pair, donors=donors, covariances=[{
        key: value.tolist() if isinstance(value, np.ndarray) else value for key, value in fit.items()
    } for fit in fits])
    context.save('donor-covariances.json', selection)
    heldout = [bands(index) for index in pair]
    scores = []
    for upper, fit, samples in zip(BAND_EDGES_HZ, fits, zip(*(row[0] for row in heldout), strict=True), strict=True):
        values = {}
        for law in LAWS:
            context.charge(bound_calls=1, bound_steps=2)
            values[law] = [gaussian_loss(sample, fit[law]) for sample in samples]
        scores.append(dict(upper_hz=upper, coefficients_per_window=len(samples[0]), negative_log_scores=values))
    result = dict(**selection, scores=scores,
                  omitted_mean_offsets_m=[(row[1]/math.sqrt(120.)).tolist() for row in heldout],
                  passed=True, new_fits=0, scientific_decision='abstain')
    context.save('contrast-covariance.json', result)
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
        folds = {}
        for identity, origin in selected.items():
            if origin not in sources:
                sources[origin] = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
            source = sources[origin]
            envelope = source.envelope(identity)
            row = source.artifact(identity, 'contrast-covariance.json')
            if envelope['result'] != row or envelope['charged'] != EXPECTED or envelope['status'] != 'complete':
                raise ValueError('verified results and allowance required')
            folds[identity] = row
        totals = {law: math.fsum(value for row in folds.values() for band in row['scores']
                                 for value in band['negative_log_scores'][law]) for law in LAWS}
        gain = totals['isotropic']-totals['unrestricted']
        eligible = len(folds) == 4 and gain > 0 and totals['independent'] <= totals['unrestricted']+.01*gain
        result = dict(folds=folds, totals=totals, complete=len(folds), candidate_retained=eligible,
                      closures={key: study.completion for key, study in sources.items()})
    _write_equal(root/RESULT, encoded(result))
    return {key: result[key] for key in ('complete', 'totals', 'candidate_retained')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    output = qualification(root, check=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(output, sort_keys=True))
