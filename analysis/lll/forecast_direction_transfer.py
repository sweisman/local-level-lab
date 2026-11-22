# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check whether directions frozen on independent generated paths transfer."""

import argparse
from contextlib import closing
from itertools import combinations
import json
from pathlib import Path

import numpy as np

from . import matched_generated_joint_score as source
from .airquantumgrav_error_policy import reported_covariance
from .forecast_family_margin import coordinates
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


FULL, REDUCED = source.full, source.reduced
PLAN = FULL.FOLDER + 'FORECAST_DIRECTION_TRANSFER_PLAN.md'
FREEZE = FULL.FOLDER + 'forecast-direction-transfer-freeze.json'
RESULT = FULL.FOLDER + 'forecast-direction-transfer-result.json'


def donors_for(records, target, *, same_route):
    seeds = {row['seed'] for row in records}
    if len(seeds) != len(records) or len({row['identity'] for row in records}) != len(records):
        raise ValueError('distinct forecasts and disjoint underlying noise seeds required')
    return [row for row in records if row['identity'] != target['identity']
            and (row['latitude_deg'] == target['latitude_deg']) == same_route]


def _span(directions, *, tolerance):
    u, singular, _ = np.linalg.svd(directions.T, full_matrices=False)
    return u[:, singular > tolerance]


def retention(donor_contrasts, target_means):
    """Measure retained joint Gaussian information in the imported directions."""
    donor, target = np.asarray(donor_contrasts, float), np.asarray(target_means, float)
    if (target.ndim != 2 or target.shape[0] != 3 or target.shape[1] < 2
            or donor.ndim != 3 or not len(donor) or donor.shape[1:] != (2, target.shape[1])
            or not np.isfinite(donor).all() or not np.isfinite(target).all()):
        raise ValueError('full three-model reference and two directions per donor required')
    norm = np.linalg.norm(donor, axis=-1, keepdims=True)
    unit = np.divide(donor, norm, out=np.zeros_like(donor), where=norm > 0.0)
    frozen = _span(unit.mean(axis=0), tolerance=1e-10)
    contrast = target[1:] - target[0]
    own = _span(contrast, tolerance=1e-10 * np.linalg.norm(contrast))
    if own.shape[1] and frozen.shape[1] >= own.shape[1]:
        overlap = np.linalg.svd(frozen.T @ own, full_matrices=False, compute_uv=False)
        worst = float(min(overlap[-1] ** 2, 1.0))
    else:
        worst = 0.0
    fractions = []
    for i, j in combinations(range(3), 2):
        direction = target[j] - target[i]
        squared = float(direction @ direction)
        projected = frozen.T @ direction
        fractions.append(float(min(projected @ projected / squared, 1.0)) if squared > 0 else None)
    return dict(donor_rank=frozen.shape[1], target_rank=own.shape[1],
                worst_case_information_fraction=worst, pair_information_fractions=fractions)


def _paths(study, archived):
    identity = archived['identity']
    task = study.tasks[identity]['payload']
    if (task['truth_model'] != archived['truth_model']
            or study.envelope(identity)['result']['all_candidates_converged'] is not True):
        raise ValueError('same complete generated history required')
    cut, future = source.CUT, source.FUTURE
    earlier = study.artifact(identity, 'training-receiver.json')
    anchor = FULL._coordinates(earlier[:1])[0]
    measured = FULL._chart(FULL._coordinates(earlier), anchor)
    saved = {model: study.artifact(identity, f'candidates/{model}/forecast.json') for model in FULL.MODELS}
    times = np.asarray(saved[FULL.MODELS[0]]['times_s'], float)
    if (len(earlier) != cut or len(times) != cut + future
            or any(p['training_epochs'] != cut or p['prediction_epochs'] != future
                   or not np.array_equal(p['times_s'], times)
                   or p['prediction_receiver_positions_used'] is not False for p in saved.values())):
        raise ValueError('shared earlier-only forecast support required')
    cov = np.linalg.cholesky(np.asarray([reported_covariance(row) for row in earlier]))
    weights = (np.broadcast_to(np.eye(3) * FULL.POLICY['receiver_white_std_m'], (len(times), 3, 3)),
               np.concatenate((cov, np.repeat(cov[-1:], future, axis=0))))
    operators = {law: {weight: make(times, factor)
                      for weight, factor in zip(FULL.WEIGHTS, weights, strict=True)}
                 for law, make in zip(source.LAWS, (FULL.operator, REDUCED.no_snap_operator), strict=True)}
    centers = {}
    for model, fit in saved.items():
        path = FULL._chart(fit['coordinates'], anchor)
        centers[model] = {law: {weight: FULL.condition(op, path[:cut] - measured, path[cut:])['center_m']
                               for weight, op in arms.items()} for law, arms in operators.items()}
    if digest(encoded(centers)) != archived['earlier_only_centers_sha256']:
        raise ValueError('original earlier-only forecasts differ')
    return dict(identity=identity, seed=task['seed'], latitude_deg=task['latitude_deg'],
                truth_model=task['truth_model'], times=times, centers=centers, operators=operators)


def _transfer(records, target):
    groups = {name: donors_for(records, target, same_route=same)
              for name, same in (('same_route', True), ('other_route', False))}
    if (len(groups['same_route']) != 5 or len(groups['other_route']) != 6
            or any(not np.allclose(r['times'] - r['times'][source.CUT],
                                   target['times'] - target['times'][source.CUT],
                                   rtol=0.0, atol=1e-9) for r in records)):
        raise ValueError('predeclared donor counts and same relative time support required')
    results = {}
    for law, arms in target['operators'].items():
        for weight, operator in arms.items():
            def means(record):
                return np.asarray([record['centers'][model][law][weight] for model in FULL.MODELS])

            target_paths = means(target)
            answers = {}
            for name, members in groups.items():
                donor_paths = np.asarray([means(row) for row in members])
                differences = donor_paths[:, 1:] - donor_paths[:, :1]
                paths = np.concatenate((target_paths - target_paths[0],
                                        differences.reshape(-1, source.FUTURE, 3)))
                projected = coordinates(operator, target['times'], paths, training_epochs=source.CUT)
                answers[name] = {metric: retention(value[3:].reshape(len(members), 2, -1), value[:3])
                                 for metric, value in projected.items()}
            results[f'{law}/{weight}'] = answers
    return dict(identity=target['identity'], truth_model=target['truth_model'],
                donors={k: [row['identity'] for row in seq] for k, seq in groups.items()}, arms=results)


def run(root, action):
    paths = (source.FREEZE, source.RESULT)
    raw = {path: (root / path).read_bytes() for path in paths}
    earlier, scores = (json.loads(raw[p]) for p in paths)
    if scores['freeze_sha256'] != digest(raw[source.FREEZE]):
        raise ValueError('sealed generated forecast inventory required')
    own = Path(__file__).relative_to(root).as_posix()
    config = encoded(dict(inputs={p: digest(b) for p, b in raw.items()},
        sources={p: digest((root / p).read_bytes()) for p in source_closure(
            root, (own, PLAN, 'analysis/tests/test_forecast_direction_transfer.py'))},
        operators=48, direction_comparisons=192, threads=1, fits=0, new_draws=0,
        later_receiver_reads=0, protected_reads=0, environment=runtime_environment()))
    if action == 'freeze':
        _write_equal(root / FREEZE, config)
        return dict(freeze_sha256=digest(config))
    if (root / FREEZE).read_bytes() != config:
        raise ValueError('same frozen direction-transfer inputs required')
    with closing(ClosedStudy(root, 'data/' + source.parent.ID)) as study:
        if (study.completion != earlier['parent'] or len(scores['rows']) != 12
                or set(study.tasks) != {row['identity'] for row in scores['rows']}):
            raise ValueError('same completed twelve-case control required')
        references = [_paths(study, row) for row in scores['rows']]
        result = [_transfer(references, target) for target in references]
    payload = encoded(dict(freeze_sha256=digest(config), rows=result, fits=0, new_draws=0,
                            later_receiver_reads=0, protected_reads=0, scientific_decision='abstain'))
    _write_equal(root / RESULT, payload)
    return dict(sha256=digest(payload), cases=len(result), comparisons=192)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
