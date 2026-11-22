# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare donor-selected window scale mixtures with Gaussian forecast errors."""

import argparse
from contextlib import ExitStack, closing
import json
import math
from pathlib import Path

from .esa_joint_persistence import BASE, LAWS, PersistenceScore, scorer
from .esa_persistence_analytic import ID as PARENT, RESULT as PRIOR
from .esa_persistence_stopping import DonorInputs
from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-window-scale-mixture-v1'
SCOPE = 'Mean-preserving window variance mixture on eight saved ESA 187 forecast windows'
PLAN = BASE+'ESA_WINDOW_SCALE_MIXTURE_PLAN.md'
RESULT = BASE+'esa-window-scale-mixture-result.json'
REQUEST = BASE+'esa-window-scale-mixture-qualification.json'
REPORT = BASE+'esa-window-scale-mixture-tests.xml'
PRIOR_SHA = '1d07f836e7ac81dc97cabd2ee3f3bd8739222ad1bac9bcdb23f85af46e07125b'
TEST = 'analysis/tests/test_esa_window_scale_mixture.py'
TESTS = (
    'test_normalized_scores_match_independent_multivariate_densities',
    'test_reference_preserves_expected_quadratic_and_tail_probabilities',
    'test_donor_selection_charges_full_grid_and_can_choose_either_limit',
)
CANDIDATES = (None, 320, 160, 80, 40, 20, 10)
DIMENSION = 360
TAIL = .05/16
WALL_S = 180
RECOVER = dict(RECOVERY_POLICY, maximum_wall_s=WALL_S)
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=25, bound_steps=68)


def negative_log_score(gaussian, dimension, dof):
    from scipy.special import gammaln

    base, quadratic = gaussian['negative_log_score'], gaussian['quadratic']
    if not (dimension > 0 and math.isfinite(quadratic) and quadratic >= 0 and math.isfinite(base)):
        raise ValueError('finite Gaussian score and positive dimension required')
    if dof is None:
        return base
    if dof <= 2:
        raise ValueError('the distribution must have finite covariance')
    half_d = dimension/2
    half_nu = dof/2
    return float(base + gammaln(half_nu) - gammaln(half_nu+half_d)
                 + half_d*math.log(half_nu-1)
                 + (half_nu+half_d)*math.log1p(quadratic/(dof-2)) - quadratic/2)


def window_score(gaussian, dimension, dof):
    from scipy.stats import chi2, f

    score = negative_log_score(gaussian, dimension, dof)
    probabilities = [TAIL, 1-TAIL]
    if dof is None:
        lower, upper = chi2.ppf(probabilities, dimension)
    else:
        lower, upper = ((dof-2)/dof)*dimension*f.ppf(probabilities, dimension, dof)
    quadratic = gaussian['quadratic']
    return dict(quadratic=quadratic, lower=float(lower), upper=float(upper),
                within_reference=bool(lower <= quadratic <= upper), negative_log_score=score)


def select(donors, dimension, *, reserve):
    if len(donors) != 6:
        raise ValueError('exactly six donor windows required')
    scores = []
    for dof in CANDIDATES:
        reserve()
        loss = math.fsum(negative_log_score(row, dimension, dof) for row in donors)
        scores.append(dict(dof=dof, negative_log_score=loss))
    best = min(scores, key=lambda row: row['negative_log_score'])
    return dict(dof=best['dof'], donor_scores=scores)


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

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('reuse the existing frozen comparison')
    prior_raw = (root/PRIOR).read_bytes()
    if digest(prior_raw) != PRIOR_SHA:
        raise ValueError('the original analytic comparison report is required')
    prior = json.loads(prior_raw)
    sources = qualification(root, check=True)
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
                                       environment=runtime_environment(), required_tests=REQUIRED_TESTS,
                                       minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if parent.completion != prior['completion'] or not parent.summary['passed']:
            raise ValueError('the original verified completion is required')
        design = parent.input('design')
        indices = [index for pair in design['pairs'] for index in pair]
        if len(indices) != 8 or len(set(indices)) != 8 or any(len(pair) != 2 for pair in design['pairs']):
            raise ValueError('four disjoint omitted pairs are required')
        tasks = [task_for(pair, law) for pair in design['pairs'] for law in LAWS]
        keys = ['design', *(f'observed-{index}' for index in indices)]
        keys.extend(f'forecast-{index}-{law}' for index in indices for law in LAWS)
        staged = {key: parent.input(key, raw=True) for key in keys}
        for task in tasks:
            identity = task['identity']
            row = parent.artifact(identity, 'analytic-result.json')
            if (row != prior['folds'][identity] or row != parent.envelope(identity)['result']
                    or not row['verified'] or not row['fit']['converged']):
                raise ValueError('the original verified Gaussian fit is required')
            staged[identity] = encoded(dict(pair=row['pair'], law=row['law'], donor_ids=row['donor_ids'],
                                            fit=row['fit'], heldout=row['heldout']))
    staged.update(recovery=recovery, recovery_tests=recovery_tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=REPORT)
    for key, raw in staged.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, raw)
        inputs[key] = name
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=inputs, sources=sources, tasks=tasks, workers=2, threads=1,
                      maximum_wall_s=WALL_S)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    pair, law = (task['payload'][key] for key in ('pair', 'law'))
    design = json.loads(context.input_path('design').read_bytes())
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or pair not in design['pairs'] or law not in LAWS
            or declared != task_for(pair, law)):
        raise ValueError('exact frozen window comparison required')
    saved = json.loads(context.input_path(task['identity']).read_bytes())
    donors = [index for other in design['pairs'] for index in other if index not in pair]
    if saved['pair'] != pair or saved['law'] != law or saved['donor_ids'] != donors:
        raise ValueError('the original fold is required')
    fit = saved['fit']
    point = fit['parameters']
    donor_context = DonorInputs(context, frozenset(key for index in donors
                               for key in (f'observed-{index}', f'forecast-{index}-{law}')))

    def gaussian(source, index):
        item = scorer(source, index, law, design['scores'][f'{index}-{law}'])
        times = json.loads(source.input_path(f'forecast-{index}-{law}').read_bytes())['times_s']
        if len(item.y) != DIMENSION:
            raise ValueError('exact original 120-position window required')
        source.charge(bound_calls=1, bound_steps=1)
        return PersistenceScore(item, times, point[:4]).score(*map(math.exp, point[4:]))

    scores = [gaussian(donor_context, index) for index in donors]
    selected = select(scores, DIMENSION, reserve=lambda: context.charge(bound_calls=1, bound_steps=6))
    if not math.isclose(selected['donor_scores'][0]['negative_log_score'], fit['negative_log_score'],
                        rel_tol=0., abs_tol=1e-6):
        raise ValueError('the original Gaussian donor score did not reproduce')
    context.save('selection.json', dict(pair=pair, law=law, donors=donors, **selected))
    heldout = []
    for index, original in zip(pair, saved['heldout'], strict=True):
        score = gaussian(context, index)
        if (original['index'] != index or any(not math.isclose(score[key], original['updated'][key],
              rel_tol=1e-10, abs_tol=1e-8) for key in ('quadratic', 'negative_log_score'))
                or score['within_reference'] != original['updated']['within_reference']):
            raise ValueError('the original Gaussian omitted-window score did not reproduce')
        context.charge(bound_calls=1, bound_steps=1)
        heldout.append(dict(index=index, gaussian=score, mixture=window_score(score, DIMENSION, selected['dof'])))
    result = dict(pair=pair, law=law, donors=donors, **selected, heldout=heldout,
                  new_trajectory_fits=0, scientific_decision='abstain', passed=True)
    context.save('comparison.json', result)
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
            record = source.envelope(identity)
            row = record['result']
            if (record['status'] != 'complete' or record['charged'] != LIMITS
                    or row != source.artifact(identity, 'comparison.json')):
                raise ValueError('verified outcomes and charges required')
            folds[identity] = row
        laws = {}
        for law in LAWS:
            heldout = [item for row in folds.values() if row['law'] == law for item in row['heldout']]
            laws[law] = {method: dict(
                negative_log_score=math.fsum(item[method]['negative_log_score'] for item in heldout),
                within_reference=sum(item[method]['within_reference'] for item in heldout),
            ) for method in ('gaussian', 'mixture')}
        improved = len(folds) == 8 and all(row['mixture']['negative_log_score'] < row['gaussian']['negative_log_score']
                                          for row in laws.values())
        result = dict(folds=folds, laws=laws, complete=len(folds), improved_both=improved,
                      closures={key: value.completion for key, value in sources.items()})
    _write_equal(root/RESULT, encoded(result))
    return {key: result[key] for key in ('complete', 'laws', 'improved_both')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, check=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
