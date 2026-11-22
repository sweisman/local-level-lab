# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the observed scope of the selective-precision solver evidence."""
import argparse
import hashlib
from itertools import product
import json
import math
from pathlib import Path

from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded


FOLDER = Path('docs/mixed-tangent-hybrid')
OUTPUT = FOLDER/'esa-dispatch-scope-v1.json'
INPUTS = {
    'observed-dispatch-fresh-result.json': '781bb1eae88ee8761bcfa800baf82c21cb470d3836f39e19b7ddb06674429d41',
    'esa-dispatch-accuracy.json': '629ea00554cc714bf929407f2b9c08c065eb35240560339ff0661321d9246ed5',
    'esa-full-fit-timing-result.json': 'fcc8c04d1c8624b82b467cbb302143ae147109f587699fda49420b6f0f3bd6d4',
    'esa-short-fit-timing-result.json': '13515bed6a7c3d38dff64d75ff0f3ecb87912aa484a4947bd6b63210967284df',
}
MODELS = ('sphere_rotating', 'sphere_still')
POLICIES = ('reported-short-v1', 'reported-persistent-v1')
METHODS = ('wide', 'selective')
HORIZONS = ('120', '240', '400')
LIMITS = dict(horizontal_rms_m=10., maximum_absolute_up_m=150., maximum_horizontal_m=50., vertical_rms_m=30.)
TOLERANCE_M = .01


def check_horizon(row, expected_limits, tolerance):
    screen, values = row['limits'], row['score']
    if (screen['limits'] != expected_limits or screen['calibrated_goodness_of_fit']
            or screen['scientific_decision'] != 'abstain'):
        raise ValueError('the original uncalibrated accuracy limits are required')
    checks, margins = {}, {}
    for name, limit in expected_limits.items():
        value = values[name]
        if not math.isfinite(value) or value < 0:
            raise ValueError('nonnegative finite errors required')
        checks[name] = value <= limit
        margins[name] = abs(value-limit)
    if checks != screen['checks'] or all(checks.values()) is not screen['passed']:
        raise ValueError('saved accuracy flag differs from the original limits')
    if min(margins.values()) <= tolerance:
        raise ValueError('an accuracy result is within the solver tolerance of a limit')
    return checks, margins


def timing_ratios(rows, *, ordered):
    rows = list(rows)
    if len(rows) != 2:
        raise ValueError('the two frozen timing pairs are required')
    cases, ratios = set(), []
    for row in rows:
        wide, selective = (row['timing'][name]['fit_cpu_ns'] for name in METHODS)
        case = row['spec']
        key = (case['model'], case['profile'], case['policy_id'], case['start'])
        if (not row['passed'] or not row['equivalent'] or row['later_positions_read'] != 0
                or min(wide, selective) <= 0 or key in cases or case['model'] not in MODELS
                or not math.isclose(wide/selective, row['fit_cpu_ratio'], rel_tol=1e-12)):
            raise ValueError('the sealed timing comparisons must reproduce')
        cases.add(key)
        ratios.append(wide/selective)
    if min(ratios) <= 1 or sum(ratios)/2 < 1.25:
        raise ValueError('the predeclared speed condition did not pass')
    if ordered and {tuple(row['order']) for row in rows} != {METHODS, METHODS[::-1]}:
        raise ValueError('the whole-fit timing used both calculation orders')
    return ratios


def audit(root):
    reports = []
    for filename, expected in INPUTS.items():
        raw = (root/FOLDER/filename).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('saved dispatch evidence digest differs: '+filename)
        reports.append(json.loads(raw))
    paired, accuracy, full, short = reports
    settings = tuple(product(MODELS, (False, True), POLICIES))
    groups = {(r['model'], r['profile'], r['policy_id']): r for r in paired['groups']}
    pairs = {(r['model'], r['profile'], r['policy_id'], r['start']): r for r in paired['pairs']}
    scored = {(*r['group'], r['start'], r['method']): r for r in accuracy['scores']}
    if (set(groups) != set(settings) or len(groups) != len(paired['groups'])
            or set(pairs) != {(*s, i) for s in settings for i in (0, 1)} or len(pairs) != len(paired['pairs'])
            or set(scored) != {(*p, m) for p in pairs for m in METHODS} or len(scored) != len(accuracy['scores'])
            or paired['protected_reads'] or paired['forecast_positions_decoded'] or not paired['equivalent_on_window']
            or accuracy['development_recordings'] != 1 or accuracy['calibrated_coverage']
            or accuracy['protected_reads'] or accuracy['scientific_decision'] != 'abstain' or not accuracy['passed']):
        raise ValueError('the original complete one-window comparison is required')

    minimum_margin = math.inf
    maximum_score_change = 0.
    counts = dict.fromkeys(HORIZONS, 0)
    max_path = 0.
    for setting in settings:
        record = groups[setting]
        rule = record['rule']
        spread = max(rule[k] for k in ('reference_within_maximum_m', 'candidate_within_maximum_m', 'cross_start_maximum_m'))
        if (not record['equivalent'] or not rule['all_fits_pass'] or not rule['same_start_costs_agree']
                or rule['reference_near_ties'] != [0, 1] or rule['candidate_near_ties'] != [0, 1]
                or not 0. <= spread <= TOLERANCE_M or rule['forecast_tolerance_m'] != TOLERANCE_M):
            raise ValueError('all four saved paths must belong to the one-centimetre equivalence set')
        max_path = max(max_path, spread)
        members = []
        for start, method in product((0, 1), METHODS):
            pair = pairs[(*setting, start)]
            fit, row = pair['fits'][method], scored[(*setting, start, method)]
            primary = rule['reference_primary' if method == 'wide' else 'candidate_primary']
            if (not pair['passed'] or not all(fit[k] for k in ('passed', 'converged', 'all_columns_retained'))
                    or row['key'] != pair['identity']+'-'+method or row['training_cost'] != fit['training_cost']
                    or row['primary'] != (start == primary) or set(row['horizons']) != set(HORIZONS)):
                raise ValueError('the saved forecast metrics must bind the original fit and start')
            members.append(row['horizons'])
        for horizon in HORIZONS:
            checks = []
            for member in members:
                outcome, margins = check_horizon(member[horizon], LIMITS, TOLERANCE_M)
                checks.append(outcome)
                minimum_margin = min(minimum_margin, *margins.values())
            values = [[member[horizon]['score'][k] for member in members] for k in LIMITS]
            delta = max(max(column)-min(column) for column in values)
            maximum_score_change = max(maximum_score_change, delta)
            if any(check != checks[0] for check in checks[1:]) or delta > TOLERANCE_M:
                raise ValueError('an accuracy screen differs within the equivalent solver starts')
            counts[horizon] += all(checks[0].values())
    if not full['passed'] or not short['speed_gate_passed']:
        raise ValueError('both original timing studies must retain their passing verdicts')
    return dict(version=1, evidence=INPUTS, development_recording=187, validation_recordings=0,
                settings=len(settings), paths=len(scored), criteria_checked=len(scored)*len(HORIZONS)*len(LIMITS),
                maximum_path_spread_m=max_path, maximum_accuracy_metric_spread_m=maximum_score_change,
                minimum_limit_margin_m=minimum_margin, settings_passing=counts, recorded_models=list(MODELS),
                short_speed_ratios=timing_ratios(short['pairs'], ordered=False),
                full_speed_ratios=timing_ratios(full['fits'].values(), ordered=True),
                observed_method_for_untested_inputs='wide', calibrated_coverage=False, scientific_decision='abstain')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('release', 'check'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = audit(root)
    if action == 'release':
        _write_equal(root/OUTPUT, encoded(result))
    elif (root/OUTPUT).read_bytes() != encoded(result):
        raise ValueError('the solver evidence scope receipt differs')
    print(json.dumps(result, sort_keys=True))
