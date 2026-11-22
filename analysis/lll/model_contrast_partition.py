# SPDX-License-Identifier: AGPL-3.0-or-later
"""Partition saved joint prediction scores into contrast and common errors."""

import argparse
from contextlib import closing
from itertools import combinations
import json
from pathlib import Path

import numpy as np

from . import forecast_pair_information as pair_info
from . import joint_score_abstention as rule
from . import matched_generated_joint_score as generated
from .airquantumgrav_error_policy import reported_covariance
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


FULL, REDUCED = generated.full, generated.reduced
PLAN = FULL.FOLDER + 'MODEL_CONTRAST_PARTITION_PLAN.md'
FREEZE = FULL.FOLDER + 'model-contrast-partition-freeze.json'
RESULT = FULL.FOLDER + 'model-contrast-partition-result.json'


def partition(squared_distances, energies, *, coordinates):
    """Recover projections using only squared pair and observation distances."""
    distances, scores = np.asarray(squared_distances, float), np.asarray(energies, float)
    if (distances.shape != (3, 3) or scores.shape != (3,) or type(coordinates) is not int
            or coordinates < 3 or not np.isfinite(distances).all() or not np.isfinite(scores).all()
            or np.any(distances < 0.0) or np.any(scores < 0.0)
            or not np.array_equal(distances, distances.T) or np.any(distances.diagonal())):
        raise ValueError('nonnegative symmetric distances and finite complete three-model scores required')
    radius = distances[0, 1:]
    gram = (radius[:, None] + radius - distances[1:, 1:]) / 2
    eigenvalues, vectors = np.linalg.eigh(gram)
    tolerance = 1e-12 * max(1.0, float(np.max(distances)))
    if eigenvalues[0] < -tolerance:
        raise ValueError('distances do not define a Euclidean contrast')
    keep = eigenvalues > tolerance
    axes = vectors[:, keep]
    inner = (scores[0] + radius - scores[1:]) / 2
    projected = (axes.T @ inner) / np.sqrt(eigenvalues[keep])
    points = np.vstack((np.zeros(keep.sum()), axes * np.sqrt(eigenvalues[keep])))
    contrast = np.sum((points - projected) ** 2, axis=1)
    orthogonal = float(scores[0] - contrast[0])
    score_slack = 1e-8 * max(1.0, float(np.max(scores)), float(np.max(distances)))
    if orthogonal < -score_slack or np.any(abs(contrast + orthogonal - scores) > score_slack):
        raise ValueError('scores do not share the declared forecast geometry')
    orthogonal = max(0.0, orthogonal)
    rank = int(keep.sum())
    return dict(contrast_rank=rank, orthogonal_coordinates=coordinates - rank,
                orthogonal_squared_error=orthogonal,
                orthogonal_error_per_coordinate=orthogonal / (coordinates - rank),
                contrast_squared_errors=contrast.tolist(), total_squared_errors=scores.tolist())


def _distance_matrix(lookup):
    matrix = np.zeros((3, 3))
    for i, j in combinations(range(3), 2):
        matrix[i, j] = matrix[j, i] = lookup(FULL.MODELS[i], FULL.MODELS[j])
    return matrix


def _observed(result, pairs):
    rows = []
    for observed, forecasts in zip(result['settings'], pairs['settings'], strict=True):
        if ((observed['complete'], observed['profile'], observed['imu_law']) !=
                (forecasts['complete'], forecasts['profile'], forecasts['imu_law'])):
            raise ValueError('same matched ESA settings required')
        arms = {}
        for law, weights in observed['scores'].items():
            for weight, source in weights.items():
                arm = f'{law}/{weight}'
                distances = _distance_matrix(
                    lambda a, b: forecasts['arms'][arm][f'{a}/{b}']['full']['squared_distance'])
                arms[arm] = partition(distances, [source['scores'][m] for m in FULL.MODELS],
                                      coordinates=3 * FULL.LATER)
        rows.append(dict(profile=observed['profile'], imu_law=observed['imu_law'],
                         complete=observed['complete'], arms=arms))
    return rows


def _generated_case(study, row):
    identity = row['identity']
    if (study.tasks[identity]['payload']['truth_model'] != row['truth_model']
            or study.envelope(identity)['result']['all_candidates_converged'] is not True):
        raise ValueError('same completed known-model case required')
    cut, future = generated.CUT, generated.FUTURE
    training = study.artifact(identity, 'training-receiver.json')
    paths = {model: study.artifact(identity, f'candidates/{model}/forecast.json')
             for model in FULL.MODELS}
    times = paths[FULL.MODELS[0]]['times_s']
    if (len(training) != cut or len(times) != cut + future
            or any(p['training_epochs'] != cut or p['prediction_epochs'] != future
                   or p['times_s'] != times or p['prediction_receiver_positions_used'] is not False
                   for p in paths.values())):
        raise ValueError('common earlier-only forecast support required')
    early = FULL._coordinates(training)
    anchor = early[0]
    gps = FULL._chart(early, anchor)
    cov = np.linalg.cholesky(np.asarray([reported_covariance(r) for r in training]))
    weights = (np.broadcast_to(np.eye(3) * FULL.POLICY['receiver_white_std_m'], (len(times), 3, 3)),
               np.concatenate((cov, np.repeat(cov[-1:], future, axis=0))))
    operators = {law: {weight: make(times, factor)
                      for weight, factor in zip(FULL.WEIGHTS, weights, strict=True)}
                 for law, make in zip(generated.LAWS, (FULL.operator, REDUCED.no_snap_operator), strict=True)}
    centers = {}
    for model, forecast in paths.items():
        path = FULL._chart(forecast['coordinates'], anchor)
        centers[model] = {law: {weight: FULL.condition(
            operator, path[:cut] - gps, path[cut:])['center_m']
            for weight, operator in matched.items()} for law, matched in operators.items()}
    if digest(encoded(centers)) != row['earlier_only_centers_sha256']:
        raise ValueError('earlier-only generated forecast centers differ')
    arms = {}
    for law, matched in operators.items():
        for weight, operator in matched.items():
            means = {model: np.asarray(center[law][weight], float) for model, center in centers.items()}
            distances = _distance_matrix(lambda a, b: generated.joint_score(
                operator, cut, means[a] - means[b], horizons=(future,))[
                    str(future)]['squared_standardized_error'])
            scores = [row['scores'][law][weight]['models'][model]['squared_standardized_error']
                      for model in FULL.MODELS]
            arms[f'{law}/{weight}'] = partition(distances, scores, coordinates=3 * future)
    return dict(identity=identity, truth_model=row['truth_model'], arms=arms)


def run(root, action):
    inputs = {path: (root / path).read_bytes() for path in (
        generated.FREEZE, generated.RESULT, pair_info.FREEZE, pair_info.RESULT,
        rule.FREEZE, rule.observed.OBSERVED)}
    sources = {path: json.loads(raw) for path, raw in inputs.items()}
    if (sources[generated.RESULT]['freeze_sha256'] != digest(inputs[generated.FREEZE])
            or sources[pair_info.RESULT]['freeze_sha256'] != digest(inputs[pair_info.FREEZE])
            or sources[rule.FREEZE]['inputs'][rule.observed.OBSERVED] != digest(inputs[rule.observed.OBSERVED])):
        raise ValueError('verified parent score receipts required')
    own = Path(__file__).relative_to(root).as_posix()
    config = encoded(dict(inputs={p: digest(b) for p, b in inputs.items()},
        sources={p: digest((root / p).read_bytes()) for p in source_closure(
            root, (own, PLAN, 'analysis/tests/test_model_contrast_partition.py'))},
        fits=0, operators=48, pair_distances=144, partitions=56, threads=1,
        later_receiver_reads=0, protected_reads=0, environment=runtime_environment()))
    if action == 'freeze':
        _write_equal(root / FREEZE, config)
        return dict(freeze_sha256=digest(config))
    if (root / FREEZE).read_bytes() != config:
        raise ValueError('same frozen score partition required')
    saved = sources[generated.RESULT]['rows']
    with closing(ClosedStudy(root, 'data/' + generated.parent.ID)) as study:
        if (study.completion != sources[generated.FREEZE]['parent']
                or len(saved) != 12 or {r['identity'] for r in saved} != set(study.tasks)):
            raise ValueError('unchanged twelve-case reference required')
        controls = [_generated_case(study, row) for row in saved]
    observed = sources[rule.observed.OBSERVED]
    if observed['recording'] != 187:
        raise ValueError('only the opened ESA recording is supported')
    actual = _observed(observed, sources[pair_info.RESULT])
    if len(actual) != 4 or sum(r['complete'] for r in actual) != 2:
        raise ValueError('preserve all four development settings')
    payload = encoded(dict(freeze_sha256=digest(config), generated=controls, observed=actual,
                            model_order=FULL.MODELS, later_receiver_reads=0, fits=0,
                            protected_reads=0, calibrated=False, scientific_decision='abstain'))
    _write_equal(root / RESULT, payload)
    return dict(sha256=digest(payload), partitions=sum(len(r['arms']) for r in controls + actual))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
