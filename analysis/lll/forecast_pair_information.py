# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ideal conditional Gaussian separation of sealed pairwise forecast paths."""

import argparse
from contextlib import closing
import gzip
from itertools import combinations
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import norm

from . import esa_changing_drift_transfer as full
from . import esa_no_snap_ablation as reduced
from .airquantumgrav_error_policy import reported_covariance
from .esa_joint_path_score import _ranges
from .forecast_smooth_error import decompose
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


FOLDER = full.FOLDER
PLAN = FOLDER + 'FORECAST_PAIR_INFORMATION_PLAN.md'
FREEZE = FOLDER + 'forecast-pair-information-freeze.json'
RESULT = FOLDER + 'forecast-pair-information-result.json'
ALPHA = .01
TARGET_POWER = .8


def ideal_comparison(squared_distance, *, alpha, target_power):
    """Simple Gaussian alternative with a known common covariance."""
    if (not math.isfinite(squared_distance) or squared_distance < 0
            or not 0 < alpha < target_power < 1):
        raise ValueError('finite squared distance and ordered probabilities required')
    z = norm.isf(alpha)
    distance = math.sqrt(squared_distance)
    required = z + norm.ppf(target_power)
    return dict(squared_distance=float(squared_distance), distance=distance,
                ideal_power=float(norm.cdf(distance - z)),
                largest_variance_multiplier_at_target_power=float(squared_distance / required**2))


def compare_paths(operator, times, first, second, *, training_epochs):
    """Compare two earlier-only paths under the same error assumptions."""
    a, b = np.asarray(first, float), np.asarray(second, float)
    if a.shape != b.shape:
        raise ValueError('matched future path coordinates required')
    split = decompose(operator, times, a - b, training_epochs=training_epochs)

    def describe(quantity):
        return ideal_comparison(quantity, alpha=ALPHA, target_power=TARGET_POWER)

    return dict(full=describe(split['total_squared_error']),
                after_cubic=describe(split['through_degree'][3]['remaining_squared_error']),
                after_degrees=[describe(part['remaining_squared_error'])
                               for part in split['through_degree'][:3]])


def _selection(rows, profile, law):
    selected = {}
    for model in full.MODELS:
        cell = [row for row in rows if (row['model'], row['profile'], row['law']) ==
                (model, profile, law)]
        if len(cell) != 2 or {row['start'] for row in cell} != {0, 1}:
            raise ValueError('same two sealed starts required for every model')
        eligible = [row for row in cell if row['converged']]
        if eligible and all(row['converged'] is not None for row in cell):
            best = min(eligible, key=lambda row: (row['training_cost'], row['start']))
            if best['passed']:
                selected[model] = best['identity']
    return selected


def _compute(matrix, receipts):
    origin = matrix.input('parent_identity')
    if origin['source_id'] != 'esa-99f1530c3eda4318' or matrix.manifest['scope'] != full.SCOPE:
        raise ValueError('opened ESA development recording required')
    training = json.loads(gzip.decompress(matrix.input('training', raw=True)))
    times = matrix.input('forecast_times')
    if len(training) != full.CUT or len(times) != full.CUT + full.LATER:
        raise ValueError('sealed 400/120 support required')
    before = np.linalg.cholesky(np.stack([reported_covariance(row) for row in training]))
    weights = (np.broadcast_to(np.eye(3)*full.POLICY['receiver_white_std_m'], (len(times), 3, 3)),
               np.concatenate((before, np.repeat(before[-1:], full.LATER, axis=0))))
    if any(receipt['anchor'] != full._coordinates(training[:1])[0].tolist()
           for receipt in receipts):
        raise ValueError('common earlier coordinate origin required')
    operators = {}
    for law, make, receipt in zip(('full', 'reduced'), (full.operator, reduced.no_snap_operator),
                                  receipts, strict=True):
        operators[law] = {weight: make(times, factor)
                          for weight, factor in zip(full.WEIGHTS, weights, strict=True)}
        if {key: op.configuration for key, op in operators[law].items()} != receipt['operator_configurations']:
            raise ValueError('sealed covariance configurations differ')

    rows = receipts[0]['rows']
    ready = {row['identity']: row['passed'] for row in rows}
    if (ready != {row['identity']: row['passed'] for row in receipts[1]['rows']}
            or ready != {identity: row['passed'] for identity, row in matrix.rows.items()}):
        raise ValueError('both saved paths must preserve every numerical disposition')
    saved = [{row['identity']: row for row in receipt['rows']} for receipt in receipts]
    outcomes = []
    for profile in (False, True):
        for law in full.LAWS:
            selected = _selection(rows, profile, law)
            arms = {}
            if len(selected) == len(full.MODELS):
                for (name, by_weight), paths in zip(operators.items(), saved, strict=True):
                    for weight, operator in by_weight.items():
                        centers = {model: paths[identity]['ranges'][weight]['center_m']
                                   for model, identity in selected.items()}
                        arms[f'{name}/{weight}'] = {f'{a}/{b}': compare_paths(
                            operator, times, centers[a], centers[b], training_epochs=full.CUT)
                            for a, b in combinations(full.MODELS, 2)}
            outcomes.append(dict(profile=profile, imu_law=law, selected=selected,
                                 complete=bool(arms), arms=arms))
    if sum(row['complete'] for row in outcomes) != 2:
        raise ValueError('original completeness count changed')
    return outcomes


def run(root, action):
    inputs = {name: (root / name).read_bytes() for source in (full, reduced)
              for name in (source.FREEZE, source.RANGES, source.SEAL)}
    receipts = [_ranges(inputs, source) for source in (full, reduced)]
    parents = json.loads(inputs[full.FREEZE])['parents']
    own = Path(__file__).relative_to(root).as_posix()
    config = encoded(dict(inputs={p: digest(data) for p, data in inputs.items()},
        sources={p: digest((root / p).read_bytes()) for p in source_closure(
            root, (own, PLAN, 'analysis/tests/test_forecast_pair_information.py'))},
        alpha=ALPHA, target_power=TARGET_POWER, fit_starts=0, operators=4, pair_comparisons=24,
        threads=1, later_receiver_reads=0, protected_reads=0, environment=runtime_environment()))
    if action == 'freeze':
        _write_equal(root / FREEZE, config)
        return dict(freeze_sha256=digest(config))
    if (root / FREEZE).read_bytes() != config:
        raise ValueError('pair information replay differs from frozen plan')
    with closing(ClosedStudy(root, 'data/' + full.ID)) as matrix:
        if matrix.completion != parents[0]:
            raise ValueError('closed fit matrix differs')
        results = _compute(matrix, receipts)
    payload = encoded(dict(freeze_sha256=digest(config), settings=results, fits=0,
        later_receiver_reads=0, protected_reads=0, calibrated=False, scientific_decision='abstain'))
    _write_equal(root / RESULT, payload)
    return dict(sha256=digest(payload), complete_settings=sum(row['complete'] for row in results))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
