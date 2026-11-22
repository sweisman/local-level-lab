# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check continuous ESA scale compatibility and transfer to omitted pairs."""

import argparse
from contextlib import ExitStack, closing
import json
import math
from pathlib import Path

from .esa_axis_innovation_scale import ID as AXIS, RESULT as AXIS_REPORT, axis_score
from .esa_axis_scale_compatibility import ID as PARENT, RESULT as PRIOR, SCALE_RANGE, quadratic_interval
from .esa_motion_innovation_scale import BASE, LAWS, scorer
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-scale-reference-transfer-v1'
SCOPE = 'ESA 187 continuous minimax reference compatibility and omitted-pair transfer'
PLAN = BASE+'ESA_SCALE_REFERENCE_TRANSFER_PLAN.md'
RESULT = BASE+'esa-scale-reference-transfer-result.json'
REQUEST = BASE+'esa-scale-reference-transfer-qualification.json'
TEST_REPORT = BASE+'esa-scale-reference-transfer-tests.xml'
TEST = 'analysis/tests/test_esa_scale_reference_transfer.py'
TESTS = ('test_scale_score_gradient_agrees_with_correlated_likelihood_differences',
         'test_reference_fit_finds_compatible_setting_and_obeys_charge_limit')
REPORTS = {
    PRIOR: 'eb99b673e71c9c61fbc47c92d6489f4fae84e2409cca1028d461456af4642f36',
    AXIS_REPORT: '3a24ea4ef30ebdbe47170be87ba90557e49f90d577d3d9b152e40131412b42c4',
}
MAXIMUM = 96
STARTS = 2


class EvaluationLimit(Exception):
    """Finish the finite search with its best already charged point."""


def score_gradient(score, logs):
    import numpy as np
    from scipy.linalg import cho_factor, cho_solve

    scales = np.exp(logs)
    quiet, motion = scales[:3], scales[3:]
    weights = score.weight.reshape(-1, 3)
    variance = (quiet+weights*motion).ravel()
    sigma = np.sqrt(variance)
    scaled_error = score.y/sigma
    root = score.root/sigma[:, None]
    if root.shape[1]:
        gram = cho_factor(score.identity+root.T@root, lower=True, check_finite=False)
        scaled_error -= root@cho_solve(gram, root.T@scaled_error, check_finite=False)
    solution = scaled_error/sigma
    power = solution.reshape(-1, 3)**2
    gradient = -np.r_[quiet*power.sum(axis=0), motion*(weights*power).sum(axis=0)]
    return float(score.y@solution), gradient


def fit_reference(scores, start, *, maximum, reserve):
    import numpy as np
    from scipy.optimize import minimize

    start = np.asarray(start, dtype=float)
    if (not scores or start.shape != (6,) or maximum < 1 or not np.isfinite(start).all()
            or np.any((start < SCALE_RANGE[0]) | (start > SCALE_RANGE[1]))):
        raise ValueError('six in-range log scales and finite optimization work required')
    lower, upper = np.asarray([row.reference for row in scores]).T
    center, half_width = (lower+upper)/2., (upper-lower)/2.
    previous = None
    best = None
    evaluations = 0

    def at(logs):
        nonlocal previous, best, evaluations
        key = tuple(float(v) for v in logs)
        if previous is not None and key == previous[0]:
            return previous[1:]
        if evaluations >= maximum:
            raise EvaluationLimit
        reserve()
        evaluations += 1
        values, derivatives = zip(*(score_gradient(score, logs) for score in scores), strict=True)
        standardized = (np.asarray(values)-center)/half_width
        jac = np.asarray(derivatives)/half_width[:, None]
        if not np.isfinite(standardized).all() or not np.isfinite(jac).all():
            raise ValueError('finite reference offsets and derivatives required')
        candidate = (float(np.max(abs(standardized))), key)
        if best is None or candidate < best:
            best = candidate
        previous = key, standardized, jac
        return standardized, jac

    def constraint(value):
        deviation, _ = at(value[:6])
        return np.r_[value[-1]-deviation, value[-1]+deviation]

    def jacobian(value):
        _, gradient = at(value[:6])
        return np.c_[np.vstack((-gradient, gradient)), np.ones(2*len(scores))]

    at(start)
    try:
        result = minimize(lambda value: value[-1], np.r_[start, best[0]], method='SLSQP',
            jac=lambda _: np.r_[np.zeros(6), 1.], bounds=[SCALE_RANGE]*6+[(0., None)],
            constraints=[dict(type='ineq', fun=constraint, jac=jacobian)],
            options=dict(maxiter=maximum, ftol=1e-10))
        status = int(result.status)
    except EvaluationLimit:
        status = 'evaluation_limit'
    return dict(log_scales=best[1], deviation=best[0], evaluations=evaluations, status=status)


def task_for(law, pair):
    donors = 8 if pair is None else 6
    scored = 8-donors
    identity = f'all-{law}' if pair is None else f'{pair[0]}-{law}'
    return dict(identity=identity, input_key='design', payload=dict(law=law, pair=pair),
        limits=dict(native_calls=0, packet_visits=0, bound_calls=8+STARTS*MAXIMUM+1+int(bool(scored)),
                    bound_steps=16+STARTS*MAXIMUM*donors+2*(donors+scored)))


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('use the existing frozen reference-transfer study')
    reports = {}
    for name, expected in REPORTS.items():
        value = (root/name).read_bytes()
        if digest(value) != expected:
            raise ValueError('archived covariance study report changed')
        reports[name] = json.loads(value)
    deps, environment = sources(root), runtime_environment()
    qualification, tests = checked(root, REQUEST, sources=deps, environment=environment,
                                   required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    staged = dict(qualification=qualification, qualification_tests=tests, recovery=recovery,
        recovery_tests=recovery_tests, recovery_policy=encoded(dict(RECOVERY_POLICY, maximum_wall_s=240)))
    with ExitStack() as stack:
        parent = stack.enter_context(closing(ClosedStudy(root, 'data/'+PARENT)))
        axis = stack.enter_context(closing(ClosedStudy(root, 'data/'+AXIS, store=parent.store)))
        for study, name in ((parent, PRIOR), (axis, AXIS_REPORT)):
            if (not study.summary['passed']
                    or any(reports[name][key] != value for key, value in study.completion.items())):
                raise ValueError('both saved studies must be complete and verified')
        design = parent.input('design')
        windows = [i for pair in design['pairs'] for i in pair]
        names = ['design', *(f'observed-{index}' for index in windows)]
        names.extend(f'forecast-{index}-{law}' for index in windows for law in LAWS)
        staged.update({name: parent.input(name, raw=True) for name in names})
        tasks = [task_for(law, pair) for law in LAWS for pair in [None, *design['pairs']]]
        for task in tasks:
            name = task['identity']
            law, pair = task['payload']['law'], task['payload']['pair']
            if pair is None:
                raw = parent.artifact(law, 'compatibility.json', raw=True)
                if json.loads(raw) not in reports[PRIOR]['laws']:
                    raise ValueError('retained box cover differs from published results')
                staged[name+'-cover'] = raw
                fits = [entry['selected']['axis_motion']['log_scales'] for entry in reports[AXIS_REPORT]['folds']
                        if entry['law'] == law]
                if len(fits) != 4:
                    raise ValueError('all four saved covariance scale fits are required')
                staged[name+'-settings'] = encoded(fits)
            else:
                raw = axis.artifact(name, 'axis-scale.json', raw=True)
                if json.loads(raw) not in reports[AXIS_REPORT]['folds']:
                    raise ValueError('this fold must use its own predecessor scales')
                staged[name+'-settings'] = raw
    inputs = dict(plan=PLAN, prior=PRIOR, axis_report=AXIS_REPORT)
    for key, raw in staged.items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, raw)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, tasks=tasks, sources=deps,
        adapter=Path(__file__).relative_to(root).as_posix(), workers=2, threads=1, maximum_wall_s=180.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def checked_scores(context, scores, logs):
    context.charge(bound_calls=1, bound_steps=2*len(scores))
    rows = {}
    for index, score in scores.items():
        lo, hi = quadratic_interval(score, logs)
        result = axis_score(score, logs)
        if not lo <= result['quadratic'] <= hi:
            raise ValueError('the archived likelihood falls outside the score enclosure')
        rows[str(index)] = dict(result, enclosed=bool(score.reference[0] <= lo <= hi <= score.reference[1]),
                               interval=[lo, hi])
    return rows


def evaluate(task, context):
    import numpy as np

    law, pair = (task['payload'][key] for key in ('law', 'pair'))
    declared = {k: v for k,v in task.items() if k not in ('index', 'shard')}
    design = json.loads(context.input_path('design').read_bytes())
    if (context.manifest['scope'] != SCOPE or law not in LAWS or declared != task_for(law, pair)
            or (pair is not None and pair not in design['pairs'])):
        raise ValueError('exact frozen in-sample or omitted-pair study required')
    name = task['identity']
    original = json.loads(context.input_path(name+'-settings').read_bytes())
    indices = [i for group in design['pairs'] for i in group]
    donors = [i for i in indices if pair is None or i not in pair]
    baseline = {}
    if pair is None:
        cover = json.loads(context.input_path(name+'-cover').read_bytes())
        if cover['quiet']['status'] != 'witness' or cover['full']['status'] != 'unresolved':
            raise ValueError('an archived steady setting and open full cover are required')
        median = np.median(original, axis=0).tolist()
        starts = [cover['quiet']['witness']+median[3:], median]
    else:
        if original['law'] != law or original['pair'] != pair or original['fitting'] != donors:
            raise ValueError('omitted outcomes cannot supply the scale starting points')
        quiet = original['selected']['axis_quiet']['log_scales']
        starts = [original['selected']['axis_motion']['log_scales'], quiet[:3]+[quiet[3]]*3]
        baseline = {str(row['index']): row['scores']['axis_quiet'] for row in original['heldout']}

    def read(index):
        return scorer(context, index, law, design['scores'][f'{index}-{law}'])

    training = {i: read(i) for i in donors}
    trials = [fit_reference(list(training.values()), start, maximum=MAXIMUM,
        reserve=lambda: context.charge(bound_calls=1, bound_steps=len(donors))) for start in starts]
    selected = min(trials, key=lambda record: (record['deviation'], record['log_scales']))
    logs = selected['log_scales']
    fitted = checked_scores(context, training, logs)
    compatible = all(row['enclosed'] for row in fitted.values())
    if pair is None and compatible and not any(all(a <= x <= b for (a,b), x in zip(box, logs, strict=True))
                                               for _,box in cover['full']['open']):
        raise ValueError('verified setting was excluded by the archived interval check')
    heldout = {} if pair is None else checked_scores(context, {i: read(i) for i in pair}, logs)
    result = dict(law=law, pair=pair, fitting=donors, starts=starts, trials=trials, selected=selected,
                  compatible=compatible, fitted=fitted, heldout=heldout, prior_heldout=baseline,
                  passed=True, scientific_decision='abstain')
    context.save('reference-transfer.json', result)
    return result


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if len(study.rows) != 10 or study.manifest['scope'] != SCOPE:
            raise ValueError('all continuous scale tasks must seal')
        rows = []
        for identity in study.rows:
            envelope = study.envelope(identity)
            row = envelope['result']
            if row['passed']:
                fits = sum(v['evaluations'] for v in row['trials'])
                charges = dict(native_calls=0, packet_visits=0, bound_calls=9+fits+int(bool(row['heldout'])),
                               bound_steps=32+fits*len(row['fitting']))
                if row != study.artifact(identity, 'reference-transfer.json') or envelope['charged'] != charges:
                    raise ValueError('sealed scale-transfer calculation or charges differ')
            rows.append(row)
        transfers = {}
        for law in LAWS:
            folds = [r for r in rows if r['passed'] and r['law'] == law and r['pair'] is not None]
            targets = [score for fold in folds for score in fold['heldout'].values()]
            prior = [score for fold in folds for score in fold['prior_heldout'].values()]
            total, earlier = [math.fsum(row['negative_log_score'] for row in items) for items in (targets, prior)]
            passed = sum(row['enclosed'] for row in targets)
            transfers[law] = dict(windows=len(targets), inside_reference=passed, log_score=total,
                previous_log_score=earlier, clears_development_screen=passed == 8 and total < earlier)
        value = dict(study.completion, rows=rows, transfers=transfers, charged=study.summary['charged'],
                     new_fits=0, scientific_decision='abstain')
    raw = encoded(value)
    _write_equal(root/RESULT, raw)
    return dict(result_sha256=digest(raw), compatibility={r['law']: r['compatible'] for r in rows
        if r['passed'] and r['pair'] is None}, transfers=transfers)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    print(json.dumps({'request': request, 'prepare': prepare, 'report': report}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
