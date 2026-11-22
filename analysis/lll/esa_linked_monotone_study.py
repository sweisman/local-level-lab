# SPDX-License-Identifier: AGPL-3.0-or-later
"""Recheck saved calibration graph cuts with certified maximizing faces."""

import argparse
from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
from pathlib import Path

from .esa_linked_child_certificates import RANGES, recombine_bounds, task_for
from .esa_linked_full_loss import ID as LAST, RESULT as LAST_REPORT
from .esa_linked_graph_cuts import FOLDER as BASE, ID as GRAPH, RESULT as GRAPH_REPORT, linked_values
from .esa_linked_graph_cuts import scaled_proposal, violated_cut
from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_saved_prediction_audit import endpoint
from .linked_monotone_support import upper_bound
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-linked-monotone-v1'
SCOPE = 'Certified maximizing faces for the eleven linked ESA calibration ranges'
PLAN = BASE+'ESA_LINKED_MONOTONE_PLAN.md'
RESULT = BASE+'esa-linked-monotone-result.json'
REQUEST = BASE+'esa-linked-monotone-qualification-v2.json'
REPORT = BASE+'esa-linked-monotone-tests-v2.xml'
TEST = 'analysis/tests/test_linked_monotone_support.py'
TESTS = (
    'test_monotone_upper_face_retains_the_true_maximum',
    'test_uncertain_derivative_is_retained_and_interior_maximum_is_enclosed',
    'test_recomputed_gradient_can_qualify_a_second_face',
    'test_original_graph_and_full_loss_reports_use_their_own_closure_layout',
)
REPORT_HASHES = {
    GRAPH_REPORT: '6f57bff0701f7ce99258b8663491a58e28777e5ecb876496a989a0fb6624c64f',
    LAST_REPORT: 'd5f231eafe7822be493499099b96777ae895c09af12bf77b4dc6ab503317894d',
}
WALL_S = 360
RECOVER = dict(RECOVERY_POLICY, maximum_wall_s=WALL_S)


def frozen_task(parent, model, index, count):
    return task_for(parent, model, index, bound_calls=count+1, bound_steps=4*count+3)


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


def checked_parent(report, completion, prefix, *, joint_report):
    if joint_report:
        return report['closures'][prefix] == completion
    return all(report[key] == completion[key] for key in ('manifest_sha256', 'summary_sha256'))


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the existing frozen calculation')
    reports = {}
    for name, expected in REPORT_HASHES.items():
        raw = (root/name).read_bytes()
        if digest(raw) != expected:
            raise ValueError('the exact closed certificate reports are required')
        reports[name] = json.loads(raw)
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    materials = dict(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    tasks = []
    with (closing(ClosedStudy(root, 'data/'+GRAPH)) as graph,
          closing(ClosedStudy(root, 'data/'+LAST)) as final):
        for study, report in ((graph, reports[GRAPH_REPORT]), (final, reports[LAST_REPORT])):
            if (not checked_parent(report, study.completion, study.prefix, joint_report=study is final)
                    or not study.summary['passed'] or len(study.tasks) != 11):
                raise ValueError('all eleven exact verified parents required')
        groups = ('cover', 'sensitivity', 'later-operator', 'earlier-linked-report', 'first-split')
        keys = [*groups, *(model+suffix for model in RANGES for suffix in ('', '-weights', '-settings', '-support'))]
        materials.update({key: final.input(key, raw=True) for key in keys})
        for identity, task in final.tasks.items():
            bound = final.envelope(identity)['result']
            if bound != reports[LAST_REPORT]['rows'][identity] or bound['excluded']:
                raise ValueError('all surviving outer ranges must remain in the cover')
            child = final.input(identity+'-child')
            child['prior'].update(upper=bound['upper'], witnesses=bound['witnesses'])
            region = final.input(identity+'-region')
            checks = final.artifact(identity, 'full-loss.json')['checks']
            region['rows'].extend([row['row'], row['limit']] for row in checks)
            saved = graph.artifact(identity, 'graph-cuts.json')
            count = sum(cut['name'] != 'training' for cut in saved['cuts'])
            if count != graph.envelope(identity)['result']['graphs_checked']:
                raise ValueError('all original graph proposals must be retained')
            materials[identity+'-child'] = encoded(child)
            materials[identity+'-region'] = encoded(region)
            materials[identity+'-original'] = encoded(saved)
            tasks.append(frozen_task(*(task['payload'][key] for key in ('parent', 'model', 'child')), count))
    inputs = dict(plan=PLAN, prior=LAST_REPORT, graph=GRAPH_REPORT, qualification=REQUEST, qualification_tests=REPORT)
    for key, value in materials.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=inputs, sources=sources, tasks=tasks, workers=2, threads=1, maximum_wall_s=WALL_S)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .esa_linked_joint_score import checked_score, score_objective
    from .esa_linked_training_support import load_projection_inputs
    from .ilvis0_coupled_map import StaticMap, restore_static_reference
    from .ilvis0_linked_directional import _linked_expression

    identity = task['identity']
    parent, model, index = (task['payload'][key] for key in ('parent', 'model', 'child'))

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    saved, region, frozen, original = [read(key) for key in
        (model+'-support', identity+'-region', identity+'-child', identity+'-original')]
    candidates = [row for row in original['cuts'] if row['name'] != 'training']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != frozen_task(parent, model, index, len(candidates)):
        raise ValueError('exact frozen range and archived directions required')
    cell = next(row for row in saved['ranges'] if row['identity'] == frozen['pair'])
    rows = [*cell['static'], *(row for row, _ in region['rows'])]
    limits = [*cell['limits'], *(value for _, value in region['rows'])]
    lo, hi = region['lower'], region['upper']
    child, prior = frozen['child'], frozen['prior']
    if len(lo) != 60 or len(hi) != 60 or len(cell['static']) != 270:
        raise ValueError('all 60 variables and original inequalities required')
    force, packet = saved['force'], saved['first_sample']
    reference = restore_static_reference(force['configuration'], packet['dv'], packet['dt'],
        lower=force['lower'], upper=force['upper'], center=force['center'], expected_report=saved['reference'])
    static = StaticMap(reference, expected_report=saved['reference'], numerical_allowance=saved['map_allowance'])
    child_lo, child_hi = child['lower'], child['upper']
    witnesses = [row for row in saved['points'] if all(a <= x <= b for a, x, b in
                 zip(child_lo, row['point'], child_hi, strict=True))]
    if len(witnesses) != prior['witnesses']:
        raise ValueError('the original witness membership must hold')
    center = np.asarray(force['center'])
    witness_points = [np.r_[np.asarray(row['point'])-center, linked_values(reference, row['point']), np.zeros(9)]
                      for row in witnesses]
    saved_cuts = []
    for candidate in candidates:
        context.charge(bound_calls=1, bound_steps=4)
        row = candidate['row']
        if len(row) != 60 or any(row[51:]):
            raise ValueError('the original physical graph row must retain its full size')
        weights = list(map(F, row[:51]))

        def expression(lower, upper):
            return _linked_expression(static, lower, upper, weights)

        calculation = upper_bound(expression, child_lo, child_hi)
        padding = F(static.numerical_allowance)*sum(abs(value) for value, cap in
                                                   zip(weights[27:], static.caps, strict=True) if cap)
        right = min(candidate['limit'], endpoint(F(calculation['exact_upper'])+padding, True))
        if any(violated_cut(row, right, point) for point in witness_points):
            raise ValueError('the tightened graph row excludes a saved witness')
        added = right < candidate['limit'] and violated_cut(row, right, original['trials'][candidate['iteration']]['point'])
        if added:
            rows.append(row)
            limits.append(right)
        saved_cuts.append(dict(name=candidate['name'], previous_limit=candidate['limit'], limit=right,
                               added=added, certificate=calculation))
    _, _, _, _, _, _, target, _ = load_projection_inputs(context, model)
    objective, allowance = score_objective(target+((F(0), F(0)),)*9, lo, hi)
    context.charge(bound_calls=1, bound_steps=3)
    proposal = scaled_proposal(lo, hi, rows, limits, objective)
    verified = checked_score(lo, hi, rows, limits, objective, proposal[1], allowance) if proposal is not None else None
    best = min(F(prior['upper']), verified) if verified is not None else F(prior['upper'])
    if any(best < F(row['score_lower']) for row in witnesses):
        raise ValueError('the tighter forecast upper bound lost a saved witness')
    context.save('monotone-cuts.json', dict(cuts=saved_cuts, exact_upper=str(best), objective=objective,
        coefficient_allowance=allowance, proposal=None if proposal is None else dict(
            point=proposal[0].tolist(), weights=proposal[1].tolist(), exact_upper=str(verified))))
    result = dict(identity=identity, model=model, parent=parent, child=index, excluded=False,
        previous_upper=prior['upper'], upper=endpoint(best, True), witnesses=len(witnesses),
        graphs_checked=len(saved_cuts), improved=sum(row['limit'] < row['previous_limit'] for row in saved_cuts),
        with_certified_face=sum(bool(row['certificate']['fixed']) for row in saved_cuts),
        added=sum(row['added'] for row in saved_cuts), passed=True, scientific_decision='abstain')
    context.save('child-certificate.json', result)
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
        previous = original.input('prior')
        dispositions = dict(previous['dispositions'])
        rows = {}
        for identity, origin in selected.items():
            if origin not in sources:
                sources[origin] = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
            source = sources[origin]
            envelope = source.envelope(identity)
            record = source.artifact(identity, 'child-certificate.json')
            if (envelope['result'] != record or envelope['charged'] != original.tasks[identity]['limits']
                    or record['previous_upper'] != dispositions[identity]['upper']):
                raise ValueError('the new bounds and their full charges must verify')
            rows[identity] = record
            dispositions[identity] = dict(previous_upper=record['previous_upper'], upper=record['upper'],
                                          excluded=False, status='certified')
        models = recombine_bounds(original, original.input('first-split'), dispositions, previous['candidate_bounds'])
        result = dict(rows=rows, complete=len(rows), candidate_bounds=models,
                      combined_upper=endpoint(sum(F(model['refined']) for model in models.values()), True),
                      nominal_separation=previous['nominal_separation'],
                      closures={key: study.completion for key, study in sources.items()})
    _write_equal(root/RESULT, encoded(result))
    return {key: result[key] for key in ('complete', 'combined_upper', 'candidate_bounds', 'nominal_separation')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    output = qualification(root, check=False) if action == 'request' else {
        'prepare': prepare, 'recover': recover, 'report': report}[action](root)
    print(json.dumps(output, sort_keys=True))
