# SPDX-License-Identifier: AGPL-3.0-or-later
"""Development-only decision from calibrated, matched group forecast scores."""

import math
import re

from .flight_group_decision import DISC, ROTATING, STILL, assess
from .group_rank_calibration import calibrate_candidate


MODELS = (DISC, STILL, ROTATING)


def _group_evidence(record, protocol, settings, *, reference_model=None):
    if not isinstance(record, dict):
        raise ValueError('a group record is required')
    identity = record.get('group_id')
    cases = record.get('settings')
    if (not isinstance(identity, str) or not identity.strip()
            or record.get('protocol_sha256') != protocol
            or not isinstance(cases, dict) or set(cases).difference(settings)):
        raise ValueError('a named group with the frozen protocol and declared settings is required')

    models = MODELS if reference_model is None else (reference_model,)
    scores = dict.fromkeys(models, math.inf)
    adequate = dict.fromkeys(models, True)
    complete = len(cases) == len(settings)
    for results in cases.values():
        if not isinstance(results, dict) or set(results).difference(models):
            raise ValueError('only declared model scores are allowed')
        scored = {}
        for model, result in results.items():
            if result is None:
                continue
            if not isinstance(result, dict):
                raise ValueError('each available model requires a score and adequacy flag')
            value = result.get('score')
            passed = result.get('adequate')
            if (type(value) not in (int, float) or not math.isfinite(value)
                    or value < 0 or type(passed) is not bool):
                raise ValueError('finite nonnegative forecast score and boolean adequacy required')
            scored[model] = value
            adequate[model] &= passed
        if len(scored) != len(models):
            complete = False
            continue
        best = min(scored.values()) if reference_model is None else 0
        for model, value in scored.items():
            scores[model] = min(scores[model], value-best)
    if not complete:
        return identity, None, None
    return identity, scores, adequate


def _matched_inputs(query, calibration, protocol_sha256, settings, planned_draws, *, absolute_null=False):
    if not isinstance(protocol_sha256, str) or not re.fullmatch('[0-9a-f]{64}', protocol_sha256):
        raise ValueError('frozen protocol SHA-256 required')
    if (not isinstance(settings, (tuple, list)) or not settings
            or any(not isinstance(s, str) or not s.strip() for s in settings)
            or len(set(settings)) != len(settings)):
        raise ValueError('frozen, unique setting identifiers required')
    if isinstance(query, dict) and 'true_model' in query:
        raise ValueError('query group must be separate from known-truth calibration')

    identity, gaps, adequate = _group_evidence(query, protocol_sha256, settings)
    if (not isinstance(planned_draws, dict) or set(planned_draws) != set(MODELS)
            or any(not isinstance(cases, dict) or not cases for cases in planned_draws.values())):
        raise ValueError('predeclare a reference family for every true model')
    assignments = {}
    references = {model: {case: {} for case in planned_draws[model]} for model in MODELS}
    for model, cases in planned_draws.items():
        for scenario, draw_ids in cases.items():
            if not isinstance(draw_ids, (tuple, list)):
                raise ValueError('predeclare an ordered list of draw identities for each scenario')
            for draw_id in draw_ids:
                if (not isinstance(draw_id, str) or not draw_id.strip()
                        or draw_id == identity or draw_id in assignments):
                    raise ValueError('planned reference identities must be unique and disjoint from the query')
                assignments[draw_id] = model, scenario

    seen = set()
    for record in calibration:
        group_id = record.get('group_id') if isinstance(record, dict) else None
        assignment = assignments.get(group_id) if isinstance(group_id, str) else None
        if assignment is None or group_id in seen or record.get('true_model') != assignment[0]:
            raise ValueError('saved calibration requires unique identities with their declared truths')
        seen.add(group_id)
        truth, scenario = assignment
        _, group_scores, _ = _group_evidence(record, protocol_sha256, settings,
                                             reference_model=truth if absolute_null else None)
        references[truth][scenario][group_id] = group_scores[truth] if group_scores is not None else None

    return identity, gaps, adequate, references


def compare_group(query, calibration, *, protocol_sha256, settings, planned_draws, alpha,
                  absolute_null=False):
    """Compare one new group with disjoint, known-truth calibration groups.

    The protocol hash binds the upstream settings, group formation, scores and
    population. It identifies those assumptions but cannot establish that the
    scores are exchangeable. Every output retains a scientific abstention.

    With absolute_null, each reference contains only the generating model's
    losses. The minimum matched gap on the query is at most its minimum own
    loss. Ranking that gap against reference own losses conservatively bounds
    the exchangeable rank based on own losses on both sides.
    """
    if type(alpha) not in (int, float) or not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError('fixed probability strictly between zero and one required')
    if type(absolute_null) is not bool:
        raise ValueError('absolute null selection must be explicit')
    identity, gaps, adequate, references = _matched_inputs(
        query, calibration, protocol_sha256, settings, planned_draws, absolute_null=absolute_null)
    ranks = {}
    for model in MODELS:
        target = dict.fromkeys(planned_draws[model], None if gaps is None else gaps[model])
        ranks[model] = calibrate_candidate(planned_draws[model], references[model], target,
                                           target_id=identity)
    counts = {model: sum(row['planned_draws'] for row in ranks[model]['by_scenario'].values())
              for model in MODELS}
    unavailable = {model: sum(row['unavailable_draws'] for row in ranks[model]['by_scenario'].values())
                   for model in MODELS}

    version = 'prediction-group-absolute-null-v1' if absolute_null else 'prediction-group-decision-v1'
    result = dict(version=version, group_id=identity,
                  protocol_sha256=protocol_sha256, settings=list(settings), alpha=alpha,
                  scores=gaps, ranks=ranks, p_values=dict.fromkeys(MODELS),
                  calibration_counts=counts, unavailable_calibration=unavailable,
                  retained_models=list(MODELS), shape='abstain', field='abstain',
                  cohort_row={'status': 'abstain'}, scientific_decision='abstain')
    if gaps is None:
        return dict(result, status='incomplete_query')
    if not all(counts.values()):
        return dict(result, status='missing_calibration_stratum')

    p_values = {model: ranks[model]['p_value'] for model in MODELS}
    retained = [model for model in MODELS if p_values[model] > alpha]
    cohort_row = dict(status='complete', p_values=p_values,
                      adequate=[model for model in MODELS if adequate[model]])
    decision = assess([identity], {identity: cohort_row}, minimum_groups=1, alpha=alpha)
    return dict(result, status='scored', p_values=p_values, retained_models=retained,
                cohort_row=cohort_row, shape=decision['shape'], field=decision['field'])


def compare_group_work(query, sealed_calibration, *, protocol_sha256, settings, planned_draws,
                       group_count, minimum_groups, alpha):
    """Build a cohort work row using the same scores and adequacy as the final test."""
    from .group_rank_work import candidate_rank_work

    identity, gaps, adequate, references = _matched_inputs(
        query, sealed_calibration, protocol_sha256, settings, planned_draws)
    if gaps is None or not all(any(plan.values()) for plan in planned_draws.values()):
        raise ValueError('complete sealed target and a frozen reference population for each model required')
    ranks = {model: candidate_rank_work(planned_draws[model], references[model],
                dict.fromkeys(planned_draws[model], gaps[model]), target_id=identity,
                group_count=group_count, minimum_groups=minimum_groups, alpha=alpha)
             for model in MODELS}
    return dict(status='complete', ranks=ranks, adequate=[model for model in MODELS if adequate[model]])
