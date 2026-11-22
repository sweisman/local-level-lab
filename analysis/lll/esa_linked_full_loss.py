# SPDX-License-Identifier: AGPL-3.0-or-later
"""Use guaranteed earlier residual energy in ESA calibration certificates."""

import argparse
from contextlib import ExitStack, closing
from fractions import Fraction as F
from functools import partial
import json
from pathlib import Path

from .esa_linked_child_certificates import RANGES, read_dispositions, recombine_bounds, task_for
from .esa_linked_graph_cuts import ID as PARENT, RESULT as PRIOR, scaled_proposal
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_saved_prediction_audit import endpoint
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-linked-full-loss-v1'
SCOPE = 'Residual energy retained by full earlier loss on eleven saved ESA calibration ranges'
BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_LINKED_FULL_LOSS_PLAN.md'
RESULT = BASE+'esa-linked-full-loss-result.json'
REQUEST = BASE+'esa-linked-full-loss-qualification.json'
REPORT = BASE+'esa-linked-full-loss-tests.xml'
TEST = 'analysis/tests/test_affine_loss_support.py'
PRIOR_SHA = '6f57bff0701f7ce99258b8663491a58e28777e5ecb876496a989a0fb6624c64f'
TESTS = ('test_full_loss_uses_all_error_coordinates_and_keeps_fixed_values',
         'test_full_loss_proposes_a_direction_for_disjoint_regions',
         'test_full_loss_proposals_respect_even_a_one_evaluation_budget',
         'test_projected_loss_removes_only_certified_constant_energy',
         'test_projected_loss_never_discards_the_free_canceling_component',
         'test_projected_loss_row_contains_every_valid_example_under_interval_uncertainty')
MAX_EVALUATIONS = 128
frozen_task = partial(task_for, bound_calls=9, bound_steps=2*MAX_EVALUATIONS+7)


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
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('retain the existing full-loss allowance')
    prior_bytes = (root/PRIOR).read_bytes()
    if digest(prior_bytes) != PRIOR_SHA:
        raise ValueError('exact closed graph-cut report required')
    prior = json.loads(prior_bytes)
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    materials = dict(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_POLICY))
    tasks = []
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if (any(prior[key] != parent.completion[key] for key in ('manifest_sha256', 'summary_sha256'))
                or not parent.summary['passed'] or len(parent.tasks) != 11):
            raise ValueError('exact complete parent graph check required')
        groups = ('cover', 'sensitivity', 'later-operator', 'earlier-linked-report', 'first-split')
        names = [*groups, *(model+suffix for model in RANGES for suffix in ('', '-weights', '-settings', '-support'))]
        materials.update({key: parent.input(key, raw=True) for key in names})
        for identity, task in parent.tasks.items():
            row = parent.envelope(identity)['result']
            if row != prior['rows'][identity] or row['excluded'] or prior['dispositions'][identity]['upper'] != row['upper']:
                raise ValueError('original survivors and bounds must remain unchanged')
            child = parent.input(identity+'-child')
            child['prior'].update(upper=row['upper'], witnesses=row['witnesses'])
            support = parent.input(identity+'-floors')
            cuts = parent.artifact(identity, 'graph-cuts.json')['cuts']
            support['rows'].extend([cut['row'], cut['limit']] for cut in cuts if cut['added'])
            materials[identity+'-child'] = encoded(child)
            materials[identity+'-region'] = encoded(support)
            tasks.append(frozen_task(*(task['payload'][key] for key in ('parent', 'model', 'child'))))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=REPORT)
    for key, value in materials.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    specification = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=inputs,
                         tasks=tasks, sources=sources, workers=3, threads=1, maximum_wall_s=360.)
    return Definition.from_dict(specification, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .affine_loss_support import full_loss_proposals, projected_loss_budget, projected_loss_row
    from .esa_linked_coordinates import INCREASE, relaxed_row
    from .esa_linked_joint_score import checked_score, score_objective
    from .esa_linked_training_support import load_projection_inputs
    from .esa_shared_profile_score import support
    from .ilvis0_control_shards import _check_continue
    from .state_space_directional_bound import adjoint_intervals

    identity = task['identity']
    parent, model, index = (task['payload'][key] for key in ('parent', 'model', 'child'))
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != frozen_task(parent, model, index):
        raise ValueError('exact saved full-loss task required')
    frozen, region = [json.loads(context.input_path(identity+suffix).read_bytes()) for suffix in ('-child', '-region')]
    saved = json.loads(context.input_path(model+'-support').read_bytes())
    cell = next(row for row in saved['ranges'] if row['identity'] == frozen['pair'])
    rows = [*cell['static'], *(row for row, _ in region['rows'])]
    limits = [*cell['limits'], *(value for _, value in region['rows'])]
    lo, hi = region['lower'], region['upper']
    prior, child = frozen['prior'], frozen['child']
    if (len(lo) != 60 or len(hi) != 60 or len(cell['static']) != 270 or len(region['rows']) < 12):
        raise ValueError('all sixty linked coordinates and prior constraints required')
    witnesses = [F(row['score_lower']) for row in saved['points'] if all(a <= value <= b
                 for a, value, b in zip(child['lower'], row['point'], child['upper'], strict=True))]
    if len(witnesses) != prior['witnesses']:
        raise ValueError('all earlier witnesses required')
    residual, raw, design, _, _, earlier, target, _ = load_projection_inputs(context, model)
    zeros = ((F(0), F(0)),)*9
    objective, allowance = score_objective(target+zeros, lo, hi)
    design = np.pad(design, ((0, 0), (0, 9)))
    width = np.asarray(hi)-lo
    centered = residual+design@(np.asarray(lo)+width/2.)
    scaled = design*width
    check = lambda: _check_continue(context.root, context.manifest)

    def coefficients(direction):
        a, b = adjoint_intervals(earlier, direction)
        projection = support(a, b, np.ones(len(residual)), raw)
        return tuple(zip(projection['lower'], projection['upper'], strict=True))+zeros

    # The numerical direction helps expose fixed residual energy. Only the
    # outward box projection below is used to subtract it from the budget.
    # Its solve is included in the reservation for the first projection.
    context.charge(bound_calls=1, bound_steps=1)
    fixed = centered-scaled@np.linalg.lstsq(scaled, centered, rcond=None)[0]
    if float(fixed@fixed) == 0.:
        fixed[0] = 1.
    budget = projected_loss_budget(residual, fixed, coefficients(fixed), lo, hi, increase=INCREASE)
    best, excluded, checks = F(prior['upper']), budget['squared'] < 0, []
    proposals = {}
    if not excluded:
        w = fixed/np.linalg.norm(fixed)
        projected = design-np.outer(w, w@design)
        reduced = residual-w*(w@residual)
        proposals = full_loss_proposals(lo, hi, rows, limits, objective, reduced, projected,
            float(budget['squared']), maximum=MAX_EVALUATIONS, check_continue=check,
            reserve=lambda: context.charge(bound_calls=1, bound_steps=MAX_EVALUATIONS))
        for label, trial in proposals.items():
            context.charge(bound_calls=1, bound_steps=1)
            d = residual+design@trial['point']
            projection, right = projected_loss_row(residual, d, coefficients(d), budget)
            row, right = relaxed_row(projection, right, lo, hi)
            augmented, bounds = [*rows, row], [*limits, right]
            context.charge(bound_calls=1, bound_steps=1)
            fit = scaled_proposal(lo, hi, augmented, bounds, objective)
            record = dict(label=label, row=row, limit=right, direction=d.tolist(), upper=None, excluded=False)
            if fit is not None:
                upper = checked_score(lo, hi, augmented, bounds, objective, fit[1], allowance)
                best = min(best, upper)
                record.update(upper=str(upper), weights=fit[1].tolist())
            else:
                negative = [-v for v in row]
                context.charge(bound_calls=1, bound_steps=1)
                proof = scaled_proposal(lo, hi, rows, limits, negative)
                if proof is not None:
                    margin = -checked_score(lo, hi, rows, limits, negative, proof[1], F(0))-F(right)
                    excluded = margin > 0
                    record.update(excluded=excluded, exact_exclusion_margin=str(margin), weights=proof[1].tolist())
            checks.append(record)
            rows, limits = augmented, bounds
            if excluded:
                break
    if any(excluded or best < value for value in witnesses):
        raise ValueError('revised proof contradicts a saved physical witness')
    removed = budget['guaranteed']/(budget['guaranteed']+budget['squared'])
    context.save('full-loss.json', dict(fixed_direction=fixed.tolist(), projected_range=list(map(str, budget['fixed_range'])),
        remaining_squared_budget=str(budget['squared']), proposals=proposals, checks=checks))
    result = dict(identity=identity, model=model, parent=parent, child=index, excluded=excluded,
        previous_upper=prior['upper'], upper=None if excluded else endpoint(best, True), witnesses=len(witnesses),
        guaranteed_energy_fraction=float(removed), proposals_checked=len(checks),
        passed=True, scientific_decision='abstain')
    context.save('child-certificate.json', result)
    return result


def report(root):
    from .studies.task_resume import resume_campaign
    from .studies.validation_resume import _stage_paths

    prefix = 'data/'+ID
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, prefix)))
        prior, cover = original.input('prior'), original.input('first-split')
        rows, dispositions = read_dispositions(original)
        closures = {prefix: original.completion}
        if any(row['status'] in ('missing', 'interrupted') for row in dispositions.values()):
            continuation = root/(prefix+'-recovery')
            if resume_campaign(root, continuation, launch=False)['state'] != 'all_tasks_finished':
                raise ValueError('verified continuation closure required')
            for path in _stage_paths(continuation):
                stage = stack.enter_context(closing(ClosedStudy(root, path.relative_to(root).as_posix(), store=original.store)))
                recovered, status = read_dispositions(stage)
                for identity, record in status.items():
                    if record['status'] not in ('missing', 'interrupted'):
                        if dispositions[identity]['status'] not in ('missing', 'interrupted'):
                            raise ValueError('duplicate terminal certificate outcome')
                        dispositions[identity] = record
                rows.update(recovered)
                closures[stage.prefix] = stage.completion
        combined = dict(prior['dispositions'], **dispositions)
        models = recombine_bounds(original, cover, combined, prior['candidate_bounds'])
        outcome = dict(rows=rows, dispositions=combined, candidate_bounds=models, closures=closures,
                       nominal_separation=cover['nominal_separation'], combined_upper=endpoint(
                           sum(F(row['refined']) for row in models.values()), True),
                       scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(outcome))
    return dict(combined_upper=outcome['combined_upper'], nominal_separation=outcome['nominal_separation'],
                certified=len(rows), excluded=sum(row['excluded'] for row in rows.values()), candidate_bounds=models)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, check=False) if action == 'request' else {'prepare': prepare, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
