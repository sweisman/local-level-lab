# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check finite rank resolution of the archived simulator reference scores."""

import argparse
import csv
from fractions import Fraction
import io
import json
import math
from pathlib import Path

from .group_rank_calibration import minimum_draws
from .ilvis0_matched_observed_inputs import _write_equal
from .prediction_receiver_references import ATTEMPT_COMPLETION, FOLDER, KEYS, ORIGINAL, RESULT, summarize
from .studies.artifacts import digest, encoded


ALPHA = Fraction(1, 20)
GROUPS = 7
PLAN = FOLDER+'REFERENCE_RESOLUTION_PLAN.md'
OUTPUT = FOLDER+'reference-resolution.json'
COST_LEDGER = 'docs/prediction-calibration-host-20261030/results.csv'
COST_LEDGER_SHA = 'ca1dc5a0bde85e0136da3b44ba27fe208764a747f51c57d3614d76cd81e02937'


def rank_resolution(planned, scores):
    if (type(planned) is not int or not 0 < planned or len(scores) > planned
            or any(isinstance(v, bool) or not math.isfinite(v) or v < 0 for v in scores)):
        raise ValueError('finite nonnegative available losses and a positive planned count are required')
    missing = planned-len(scores)
    order = sorted(scores, reverse=True)
    rules = []
    for minimum in range(1, GROUPS+1):
        cutoff = ALPHA/(GROUPS-minimum+1)
        tail = math.floor(cutoff*(planned+1))-1-missing
        reachable = tail >= 0
        rules.append(dict(minimum_groups=minimum, cutoff=str(cutoff), reachable=reachable,
            maximum_available_tail_count=tail if reachable else None,
            strictly_above_m=order[tail] if reachable else None,
            minimum_planned_if_missing_fixed=minimum_draws(GROUPS, minimum, alpha=float(ALPHA),
                                                          unavailable=missing)))
    return dict(planned=planned, available=len(scores), unavailable=missing,
                smallest_p_value=str(Fraction(missing+1, planned+1)), rules=rules)


def verify_earlier_choices(cost_rows, replay_rows):
    choices = {}
    for row in cost_rows:
        if (row['role'] != 'calibration' or row['profile'] not in ('True', 'False')
                or row['complete'] != 'True' or row['converged'] != 'True'):
            raise ValueError('complete earlier-only cost ledger required')
        case = (int(row['draw_seed']), row['model'], row['law'], row['profile'] == 'True')
        cost = float(row['training_cost'])
        if not math.isfinite(cost) or cost < 0.:
            raise ValueError('the original training losses must be finite and nonnegative')
        choices.setdefault(case, []).append((cost, int(row['start']), row['identity']))
    for row in replay_rows:
        case = (row['seed'], *(row[key] for key in KEYS))
        candidates = choices.get(case, ())
        if (len(candidates) != 2 or {start for _, start, _ in candidates} != {0, 1}
                or min(candidates) != (row['earlier_cost'], row['start'], row['identity'])):
            raise ValueError('the earlier-cost choice differs from the original ledger')


def evidence(root):
    raw = (root/RESULT).read_bytes()
    saved = json.loads(raw)
    if (saved['parent'] != ORIGINAL or saved['first_attempt'] != ATTEMPT_COMPLETION
            or len(saved['seeds']) != 299 or len(set(saved['seeds'])) != 299
            or saved['aircraft_calibrated'] or saved['scientific_decision'] != 'abstain'
            or any(saved[key] != 0 for key in ('new_fits', 'reserved_reads', 'validation_cases'))):
        raise ValueError('the sealed calibration-only replay is required')
    rows = saved['records']
    summaries = summarize(saved['seeds'], rows)
    if summaries != saved['scenario_summaries']:
        raise ValueError('the saved reference counts and scores differ')
    costs = (root/COST_LEDGER).read_bytes()
    if digest(costs) != COST_LEDGER_SHA:
        raise ValueError('the original training-cost ledger hash differs')
    verify_earlier_choices(csv.DictReader(io.StringIO(costs.decode())), rows)
    scenarios = []
    for case in summaries:
        scores = [row['forecast_to_receiver_3d_rms_m'] for row in rows
                  if all(row[key] == case[key] for key in KEYS)]
        scenarios.append({key: case[key] for key in KEYS} | rank_resolution(len(saved['seeds']), scores))
    return dict(version='simulator-reference-resolution-v1', input_sha256=digest(raw),
                training_cost_ledger_sha256=COST_LEDGER_SHA, verified_earlier_cost_choices=len(rows),
                plan_sha256=digest((root/PLAN).read_bytes()), source_sha256=digest(Path(__file__).read_bytes()),
                group_count=GROUPS, illustrative_allowance=str(ALPHA), scenarios=scenarios,
                reachable_in_every_scenario=[k for k in range(1, GROUPS+1)
                    if all(row['rules'][k-1]['reachable'] for row in scenarios)],
                no_operational_threshold=True, new_fits=0, protected_reads=0, scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('release', 'check'))
    args = parser.parse_args()
    root = Path.cwd()
    result = evidence(root)
    raw = encoded(result)
    if args.action == 'release':
        _write_equal(root/OUTPUT, raw)
    elif (root/OUTPUT).read_bytes() != raw:
        raise ValueError('the saved reference resolution differs')
    print(json.dumps(dict(scenarios=len(result['scenarios']),
        reachable_in_every_scenario=result['reachable_in_every_scenario']), sort_keys=True))


if __name__ == '__main__':
    main()
