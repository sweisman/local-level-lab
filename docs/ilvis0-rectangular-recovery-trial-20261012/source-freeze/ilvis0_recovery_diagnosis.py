# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only diagnosis of sealed recovery results; no native integrations or fits."""
import hashlib
import json
import math
from pathlib import Path

VERSION = 'ilvis0-recovery-saved-diagnosis-v1'


def load_completed(directory):
    directory = Path(directory)
    completion_path = directory/'completion.json'
    if not completion_path.exists():
        raise ValueError('completed study required')
    completion = json.loads(completion_path.read_text())
    if completion.get('state') != 'complete':
        raise ValueError('completed study required')
    expected = dict(completion['journal_hashes'], **{
        'manifest.json': completion['manifest_sha256'],
        'summary.json': completion['summary_sha256']})
    inputs = {}
    for name, digest in expected.items():
        raw = (directory/name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(f'input hash mismatch: {name}')
        inputs[name] = raw
    summary = json.loads(inputs['summary.json'])
    if summary.get('state') != 'complete':
        raise ValueError('completed summary required')
    starts = [json.loads(line) for line in inputs['starts.jsonl'].splitlines()]
    sweeps = [json.loads(line) for line in inputs['sweeps.jsonl'].splitlines()]
    for rows, key in ((starts, 'starts'), (sweeps, 'native_sweeps')):
        if len(rows) != completion[key] or len(rows) != summary[key]:
            raise ValueError('charged journal count mismatch')
        if [r['number'] for r in rows] != list(range(1, len(rows)+1)):
            raise ValueError('journal sequence mismatch')
    identities = [r['identity'] for r in starts]
    if len(set(identities)) != len(identities) or set(identities) != set(summary['results']):
        raise ValueError('charged result identities mismatch')
    if any(r['identity'] not in identities for r in sweeps):
        raise ValueError('uncharged sweep identity')
    return summary, expected


def _finite(value, nonnegative=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or
            not math.isfinite(value) or nonnegative and value < 0):
        raise ValueError('invalid saved diagnostic')
    return value


def inspect_fit(identity, fit):
    segment, case, model, role = identity.split('::')
    names = fit['active_parameters']
    if not names or len(set(names)) != len(names):
        raise ValueError('invalid saved parameters')
    vectors = [fit[k] for k in ('normalized_parameters', 'gradient', 'projected_gradient',
                               'scaled_projected_gradient', 'singular_values')]
    if any(len(v) != len(names) for v in vectors):
        raise ValueError('saved diagnostic dimensions disagree')
    for vector in vectors:
        for value in vector:
            _finite(value)
    point, gradient, projected, scaled, singular = vectors
    if any(abs(u) > 1 for u in point):
        raise ValueError('saved point outside bounds')
    if any(v < 0 for v in singular) or any(a < b for a, b in zip(singular, singular[1:])):
        raise ValueError('invalid singular spectrum')
    for u, g, p, s in zip(point, gradient, projected, scaled):
        blocked = u <= -1+1e-6 and g > 0 or u >= 1-1e-6 and g < 0
        if (not math.isclose(p, 0. if blocked else g, rel_tol=1e-10, abs_tol=1e-15)
                or p*s < 0 or p == 0 and s != 0):
            raise ValueError('invalid saved gradient projection')
    stationarity = _finite(fit['exact_projected_gradient_relative'], True)
    if not math.isclose(stationarity, max(abs(x) for x in scaled), rel_tol=1e-10, abs_tol=1e-15):
        raise ValueError('saved stationarity disagrees with gradient')
    tolerance = _finite(fit['stationarity_tolerance'], True)
    evaluations, maximum = fit['evaluations'], fit['maximum_evaluations']
    if (tolerance <= 0 or type(evaluations) is not int or type(maximum) is not int
            or not 1 <= evaluations <= maximum):
        raise ValueError('invalid evaluation allowance or tolerance')
    probe = fit.get('stability_probe') or {}
    for key in ('predicted_cost_change', 'predicted_residual_step', 'actual_cost_change',
                'actual_residual_step', 'fresh_stationarity'):
        if key in probe:
            _finite(probe[key], True)
    stationarity_passed = stationarity <= tolerance
    if fit['converged'] and (not stationarity_passed or not fit['stability_verified']):
        raise ValueError('saved convergence disagrees with required checks')
    exhausted = 'allowance exhausted' in fit['message'] or 'maximum number of function evaluations' in fit['message']
    category = ('passed' if fit['converged'] else 'budget_exhausted' if exhausted else
                'early_stationarity_failure' if not stationarity_passed else 'early_stability_failure')
    index = max(range(len(names)), key=lambda i: abs(scaled[i]))
    cost = _finite(fit['residual_sum_squares'], True)
    reference = _finite(fit['reference_cost'], True)
    history = fit.get('accepted_step_history', [])
    return dict(identity=identity, segment_id=segment, case_id=case, model=model, role=role,
                converged=bool(fit['converged']), failure_class=category,
                evaluations=evaluations, maximum_evaluations=maximum,
                stationarity_passed=stationarity_passed, stationarity_ratio=stationarity/tolerance,
                stability_verified=bool(fit['stability_verified']), probe_reason=probe.get('reason'),
                callback_probe_disagreement=bool(fit['converged'] and not probe.get('passed', False)),
                predicted_cost_change_ratio=(probe['predicted_cost_change']/1e-8
                                             if 'predicted_cost_change' in probe else None),
                predicted_residual_step_ratio=(probe['predicted_residual_step']/1e-6
                                               if 'predicted_residual_step' in probe else None),
                jacobian_condition_ratio=singular[0]/singular[-1] if singular[-1] else None,
                dominant_parameter=names[index], dominant_normalized_value=point[index],
                dominant_bound_distance=1-abs(point[index]),
                relative_cost_change_from_reference=(cost-reference)/max(reference, 1.),
                cost=cost, reference_cost=reference, accepted_callbacks=len(history),
                stable_accepted_iterations=fit.get('stable_accepted_iterations', 0),
                last_callback_cost=history[-1]['cost'] if history else None,
                stopping_message=fit['message'], scientific_decision='abstain')
