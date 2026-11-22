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

    conservative = assess(groups, upper, minimum_groups=minimum_groups, alpha=alpha)
    multiplier = len(groups) - minimum_groups + 1
    ballots = [_ballots(upper[group], bounds[group], multiplier, alpha) if group in bounds
               else {(0,) * len(LABELS)} for group in groups]
    possible = _reachable_decisions(ballots, minimum_groups)
    return dict(possible_decisions=[dict(shape=shape, field=field) for shape, field in sorted(possible)],
                decision_fixed=len(possible) == 1, shape_fixed=len({shape for shape, _ in possible}) == 1,
                field_fixed=len({field for _, field in possible}) == 1, pending_draw_slots=pending,
                conservative=conservative, scientific_decision='abstain')
