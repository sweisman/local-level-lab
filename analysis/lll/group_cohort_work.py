# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check whether remaining reference draws can change a frozen cohort decision."""

from itertools import product

from .flight_group_decision import (
    LABELS, MODELS, _decision_from_passes, _probability, _within_group, assess,
)


def _bounds(row):
    ranks = row.get('ranks')
    if (set(row) != {'status', 'ranks', 'adequate'} or not isinstance(ranks, dict)
            or set(ranks) != MODELS):
        raise ValueError('explicit adequacy and rank bounds for every candidate required')
    limits = {}
    pending = 0
    for model, rank in ranks.items():
        lower, upper = rank.get('p_value_min'), rank.get('p_value_max')
        count = rank.get('pending_draws')
        if (not _probability(lower) or not _probability(upper) or lower > upper
                or type(count) is not int or count < 0 or (count == 0 and lower != upper)):
            raise ValueError('ordered rank bounds and a nonnegative pending draw count required')
        limits[model] = lower, upper
        pending += count
    return limits, pending


def _ballots(row, limits, multiplier, alpha):
    # Within-group tests use only maxima and the adequacy flags. Each rank
    # can therefore contribute just two distinct decisions at the cutoff.
    options = [(lo, hi) if multiplier * float(lo) <= alpha < multiplier * float(hi) else (hi,)
               for lo, hi in limits.values()]
    ballots = set()
    for values in product(*options):
        group = dict(row, p_values=dict(zip(limits, values, strict=True)))
        evidence = _within_group(group)
        ballots.add(tuple(int(multiplier * float(evidence[label]) <= alpha) for label in LABELS))
    return ballots


def _reachable_decisions(ballots, minimum):
    # Track attainable count vectors. A label that can no longer reach
    # minimum is represented by -1. A passing label needs no further count.
    remaining = [sum(any(vote[i] for vote in group) for group in ballots)
                 for i in range(len(LABELS))]
    reachable = {(0,) * len(LABELS)}
    for group in ballots:
        for i in range(len(LABELS)):
            remaining[i] -= any(vote[i] for vote in group)
        reachable = {tuple(min(minimum, count + bit)
                           if count >= 0 and count + bit + future >= minimum else -1
                           for count, bit, future in zip(vector, vote, remaining, strict=True))
                     for vector in reachable for vote in group}
    return {_decision_from_passes(dict(zip(LABELS, (n == minimum for n in counts), strict=True)))
            for counts in reachable}


def _work_state(groups, rows):
    if set(rows) != set(groups):
        raise ValueError('one sealed target assessment or terminal status for each frozen group required')
    bounds, upper = {}, {}
    pending = 0
    for group, row in rows.items():
        if row.get('status') != 'complete':
            upper[group] = row
            continue
        limits, count = _bounds(row)
        bounds[group] = limits
        upper[group] = dict(status='complete', adequate=row['adequate'],
                            p_values={model: hi for model, (_, hi) in limits.items()})
        pending += count
    return bounds, upper, pending


def _result(possible, pending, conservative):
    return dict(possible_decisions=[dict(shape=shape, field=field) for shape, field in sorted(possible)],
                decision_fixed=len(possible) == 1, shape_fixed=len({shape for shape, _ in possible}) == 1,
                field_fixed=len({field for _, field in possible}) == 1, pending_draw_slots=pending,
                conservative=conservative, scientific_decision='abstain')


def cohort_rank_work(group_ids, rows, *, minimum_groups, alpha):
    """Find possible shape and field decisions with sealed targets and adequacy.

    Complete rows supply each candidate's `candidate_rank_work` result in
    `ranks` and the fixed `adequate` list. Every other row must be explicitly
    terminal. No future target or adequacy result may enter after this check.

    A candidate's interval allows either attainable cutoff outcome. Treating
    these outcomes independently gives a superset when references are shared.
    A single outcome in that superset fixes both decisions. The reported
    conservative assessment still counts unfinished draws as unavailable.
    """
    groups = tuple(group_ids)
    bounds, upper, pending = _work_state(groups, rows)
    conservative = assess(groups, upper, minimum_groups=minimum_groups, alpha=alpha)
    multiplier = len(groups) - minimum_groups + 1
    ballots = [_ballots(upper[group], bounds[group], multiplier, alpha) if group in bounds
               else {(0,) * len(LABELS)} for group in groups]
    possible = _reachable_decisions(ballots, minimum_groups)
    return _result(possible, pending, conservative)


def _shared_rejections(model, scores, rows, multiplier, alpha):
    """A common calibration pool rejects a suffix of targets ordered by score."""
    order = sorted(scores, key=lambda group: scores[group][model])
    possible = []
    for split in range(len(order)+1):
        lower = order[split-1] if split else None
        higher = order[split] if split < len(order) else None
        if lower is not None and multiplier*rows[lower]['ranks'][model]['p_value_max'] <= alpha:
            continue
        if higher is not None and (scores[higher][model] == 0.
                or multiplier*rows[higher]['ranks'][model]['p_value_min'] > alpha):
            continue
        if lower is not None and higher is not None and scores[lower][model] == scores[higher][model]:
            continue
        possible.append(frozenset(order[split:]))
    if not possible:
        raise ValueError('shared reference ranks must allow at least one attainable rejection set')
    return possible


def _shared_cohort_rank_work(group_ids, rows, scores, *, minimum_groups, alpha):
    """Preserve rank dependence from common reference scores across targets.

    Call with rows built from one common calibration plan and the draft scores
    used to build those rows. A model's target score must be the same across
    its reference scenarios. Its draw identities must be disjoint from other
    models' identities. Unknown relations across distinct draws are ignored.
    """
    groups = tuple(group_ids)
    _, upper, pending = _work_state(groups, rows)
    conservative = assess(groups, upper, minimum_groups=minimum_groups, alpha=alpha)
    if set(scores) != {group for group, row in rows.items() if row['status'] == 'complete'}:
        raise ValueError('the same sealed queries must supply scores and calibrated work rows')
    multiplier = len(groups)-minimum_groups+1
    models = tuple(sorted(MODELS))
    suffixes = [_shared_rejections(model, scores, rows, multiplier, alpha) for model in models]
    possible = set()
    for rejected in product(*suffixes):
        votes = {}
        for group in groups:
            row = rows[group]
            if group in scores:
                # Only the threshold side matters for the decision. These
                # binary inputs are never returned as calibrated p-values.
                row = dict(status='complete', adequate=row['adequate'],
                           p_values={model: float(group not in subset)
                                     for model, subset in zip(models, rejected, strict=True)})
            votes[group] = _within_group(row)
        possible.add(_decision_from_passes({
            label: sum(value[label] == 0. for value in votes.values()) >= minimum_groups for label in LABELS}))
    if (conservative['shape'], conservative['field']) not in possible:
        raise ValueError('the all-unavailable reference completion must remain attainable')
    output = _result(possible, pending, conservative)
    output['pending_reference_draws'] = (sum(row['pending_draws'] for row in rows[next(iter(scores))]['ranks'].values())
                                         if scores else 0)
    return output
