# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only sensitivity of the sealed joint-score rule to a common variance."""

import argparse
import json
from pathlib import Path

from . import joint_score_abstention as rule
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


FOLDER = rule.full.FOLDER
PLAN = FOLDER + 'JOINT_SCORE_SCALE_WINDOW_PLAN.md'
FREEZE = FOLDER + 'joint-score-scale-window-freeze.json'
RESULT = FOLDER + 'joint-score-scale-window-result.json'
LABELS = ('globe', 'disc', 'specified', 'zero')


def _merge(intervals):
    merged = []
    for lo, hi, right_closed in sorted(intervals):
        if merged and lo <= merged[-1][1]:
            if (hi, right_closed) > tuple(merged[-1][1:]):
                merged[-1][1:] = [hi, right_closed]
        else:
            merged.append([lo, hi, right_closed])
    return merged


def _intersect(left, right):
    intersections = []
    for a, b, closed_b in left:
        for c, d, closed_d in right:
            lo, hi = max(a, c), min(b, d)
            closed = (b > hi or closed_b) and (d > hi or closed_d)
            if lo < hi or (lo == hi and closed):
                intersections.append([lo, hi, closed])
    return _merge(intersections)


def windows(scores, *, epochs, physical=None):
    """Invert the existing rule for all positive common variance multipliers."""
    baseline = rule.assess(scores, epochs=epochs, physical=physical)
    lower, upper = baseline['reference_band']
    if baseline['shape_reason'] == 'incomplete':
        return dict(status='incomplete')
    compatible = {model: min(arms.values()) / upper for model, arms in scores.items()}
    rotating, still, disc = rule.full.MODELS
    globe_at = min(compatible[rotating], compatible[still])
    result = {label: [] for label in LABELS}
    for model, arms in scores.items():
        families = [('disc', globe_at)] if model == disc else [
            ('globe', compatible[disc]),
            ('specified' if model == rotating else 'zero',
             min(compatible[disc], compatible[still if model == rotating else rotating]))]
        for arm, q in arms.items():
            if q == 0.0 or (physical is not None and not physical[model][arm]):
                continue
            lo, ceiling = q / upper, q / lower
            for label, competing in families:
                if lo < competing:
                    result[label].append([lo, min(ceiling, competing), ceiling < competing])
    return dict(status='complete', reference_band=baseline['reference_band'],
                compatible_from=compatible, at_unit_scale=baseline,
                windows={label: _merge(group) for label, group in result.items()})


def _observed(saved):
    observed = saved[rule.observed.OBSERVED]
    if observed['recording'] != 187:
        raise ValueError('only the designated development recording is allowed')
    prior = saved[rule.RESULT]['observed']
    by_law = {law: saved[path] for law, path in zip(
        rule.observed.LAWS, (rule.full.RESULT, rule.reduced.RESULT), strict=True)}
    by_identity = {law: {row['identity']: row for row in receipt['rows']}
                   for law, receipt in by_law.items()}
    rows = []
    for row, primary, prior_row in zip(observed['settings'], by_law['full']['matched_settings'],
                                       prior, strict=True):
        key = (row['profile'], row['imu_law'], row['complete'])
        if key != (primary['profile'], primary['law'], primary['complete']):
            raise ValueError('matched study settings differ')
        physical, scores = {}, {}
        if row['complete']:
            for model, identity in primary['primary'].items():
                scores[model] = {f'{law}/{weight}': arm['scores'][model]
                                 for law, arms in row['scores'].items()
                                 for weight, arm in arms.items()}
                physical[model] = {f'{law}/{weight}': by_identity[law][identity]['horizons'][
                    str(rule.full.LATER)]['ranges'][weight]['descriptive_accuracy_passed']
                    for law in rule.observed.LAWS for weight in rule.full.WEIGHTS}
        if rule.assess(scores, epochs=rule.full.LATER, physical=physical) != {
                k: v for k, v in prior_row.items() if k not in ('profile', 'imu_law')}:
            raise ValueError('unit-scale replay differs from the sealed verdict')
        rows.append(dict(profile=row['profile'], imu_law=row['imu_law'],
                         **windows(scores, epochs=rule.full.LATER, physical=physical)))
    complete = [row for row in rows if row['status'] == 'complete']
    if len(rows) != 4 or len(complete) != 2:
        raise ValueError('sealed four-setting denominator changed')
    return rows, {label: _intersect(complete[0]['windows'][label], complete[1]['windows'][label])
                  for label in LABELS}


def run(root, action):
    input_paths = (rule.FREEZE, rule.RESULT, rule.observed.OBSERVED,
                   rule.full.RESULT, rule.reduced.RESULT)
    raw = {path: (root / path).read_bytes() for path in input_paths}
    saved = {path: json.loads(value) for path, value in raw.items()}
    hashes = {path: digest(value) for path, value in raw.items()}
    if (saved[rule.RESULT]['freeze_sha256'] != hashes[rule.FREEZE]
            or any(saved[rule.FREEZE]['inputs'][path] != hashes[path] for path in input_paths[2:])):
        raise ValueError('sealed joint-score inputs changed')
    own = Path(__file__).relative_to(root).as_posix()
    sources = (own, PLAN, 'analysis/tests/test_joint_score_scale_window.py')
    from .studies.dependencies import source_closure
    frozen = encoded(dict(inputs=hashes, environment=runtime_environment(), threads=1,
                          sources={p: digest((root / p).read_bytes())
                                   for p in source_closure(root, sources)},
                          settings=4, maximum_complete_scale_windows=2,
                          fit_starts=0, native_calls=0, protected_reads=0))
    if action == 'freeze':
        _write_equal(root / FREEZE, frozen)
        return dict(freeze_sha256=digest(frozen))
    if (root / FREEZE).read_bytes() != frozen:
        raise ValueError('scale-window replay does not match the freeze')
    rows, shared = _observed(saved)
    payload = encoded(dict(freeze_sha256=digest(frozen), settings=rows,
                           both_complete_settings=shared, new_fits=0,
                           protected_reads=0, calibrated=False, scientific_decision='abstain'))
    _write_equal(root / RESULT, payload)
    return dict(sha256=digest(payload), both_complete_settings=shared)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
