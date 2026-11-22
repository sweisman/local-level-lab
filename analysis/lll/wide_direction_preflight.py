# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check wider externally chosen contrast spaces on disjoint saved routes."""

import argparse
from contextlib import ExitStack, closing
from itertools import combinations
import json
from pathlib import Path

import numpy as np
from scipy.stats import chi2, ncx2

from . import forecast_direction_transfer as transfer
from . import forecast_pair_information as pairs
from . import joint_score_abstention as rule
from .airquantumgrav_error_policy import reported_covariance
from .forecast_family_margin import coordinates
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import ArchiveStore, digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


FULL, SOURCE = transfer.FULL, transfer.source
PLAN = FULL.FOLDER + 'WIDE_DIRECTION_PREFLIGHT_PLAN.md'
FREEZE = FULL.FOLDER + 'wide-direction-preflight-freeze.json'
RESULT = FULL.FOLDER + 'wide-direction-preflight-result.json'
WIDTHS = (2, 4, 8, 12, 24)
ALPHA, POWER = .01, .8


def evaluate_spaces(directions, means, *, widths, alpha):
    """Evaluate power of a fixed projected quadratic score for each pair."""
    donor, target = np.asarray(directions, float), np.asarray(means, float)
    widths = tuple(widths)
    if (donor.ndim != 2 or not len(donor) or not donor.shape[1]
            or target.shape != (3, donor.shape[1]) or not np.isfinite(donor).all()
            or not np.isfinite(target).all() or not widths or len(set(widths)) != len(widths)
            or any(type(k) is not int or k < 1 for k in widths) or not 0.0 < alpha < 1.0):
        raise ValueError('complete contrasts, finite declared widths and valid size required')
    norm = np.linalg.norm(donor, axis=1, keepdims=True)
    unit = np.divide(donor, norm, out=np.zeros_like(donor), where=norm > 0)
    _, singular, axes = np.linalg.svd(unit, full_matrices=False)
    rank = int(np.count_nonzero(singular > 1e-10 * singular[0]))
    actual = np.asarray([target[b] - target[a] for a, b in combinations(range(3), 2)])
    whole = np.sum(actual ** 2, axis=1)
    out = {}
    for width in widths:
        kept = min(width, rank)
        projected = np.sum((actual @ axes[:kept].T) ** 2, axis=1)
        limit = chi2.isf(alpha, kept) if kept else None
        out[str(width)] = dict(actual_rank=kept, pairs=[
            dict(full_squared_distance=float(d), retained_squared_distance=float(k),
                 fraction=float(min(k / d, 1.0)) if d > 0.0 else None,
                 ideal_power=float(ncx2.sf(limit, kept, k)) if kept else None)
            for d, k in zip(whole, projected, strict=True)])
    return out


def _target(study, identity):
    payload = study.tasks[identity]['payload']
    cut, later = SOURCE.CUT, SOURCE.FUTURE
    receiver = study.artifact(identity, 'training-receiver.json')
    binding = study.artifact(identity, 'input-binding.json')
    if (study.envelope(identity)['result']['all_candidates_converged'] is not True
            or len(receiver) != cut or digest(encoded(receiver)) != binding['earlier_receiver_sha256']
            or binding['same_measurements_for_all_candidates'] is not True):
        raise ValueError('verified earlier-only matched route receiver input required')
    forecasts = {model: study.artifact(identity, f'candidates/{model}/forecast.json')
                 for model in FULL.MODELS}
    times = np.asarray(forecasts[FULL.MODELS[0]]['times_s'], float)
    if (len(times) != cut + later
            or any(p['training_epochs'] != cut or p['prediction_epochs'] != later
                   or not np.array_equal(p['times_s'], times)
                   or p['prediction_receiver_positions_used'] is not False for p in forecasts.values())):
        raise ValueError('matched sealed target forecast support required')
    coordinates_raw = FULL._coordinates(receiver)
    anchor = coordinates_raw[0]
    earlier = FULL._chart(coordinates_raw, anchor)
    raw_paths = {m: FULL._chart(f['coordinates'], anchor) for m, f in forecasts.items()}
    cov = np.linalg.cholesky(np.asarray([reported_covariance(row) for row in receiver]))
    weights = (np.broadcast_to(np.eye(3)*FULL.POLICY['receiver_white_std_m'], (len(times), 3, 3)),
               np.concatenate((cov, np.repeat(cov[-1:], later, axis=0))))
    arms = {}
    for law, make in zip(SOURCE.LAWS, (FULL.operator, transfer.REDUCED.no_snap_operator), strict=True):
        for name, weight in zip(FULL.WEIGHTS, weights, strict=True):
            operator = make(times, weight)
            means = [FULL.condition(operator, path[:cut] - earlier, path[cut:])['center_m']
                     for path in raw_paths.values()]
            arms[law, name] = operator, np.asarray(means)
    return dict(identity=identity, route=payload['route'], seed=payload['seed'], times=times, arms=arms)


def _evaluate(donors, target):
    if (target['seed'] in {row['seed'] for row in donors}
            or len({row['seed'] for row in donors}) != 12
            or any(not np.allclose(row['times'] - row['times'][SOURCE.CUT],
                                   target['times'] - target['times'][SOURCE.CUT],
                                   rtol=0.0, atol=1e-9) for row in donors)):
        raise ValueError('independent donor seeds and common time support required')
    rows = {}
    for (law, weight), (op, means) in target['arms'].items():
        paths = np.asarray([[d['centers'][m][law][weight] for m in FULL.MODELS] for d in donors])
        diff = (paths[:, 1:] - paths[:, :1]).reshape(-1, SOURCE.FUTURE, 3)
        all_vectors = np.concatenate((means - means[0], diff))
        projected = coordinates(op, target['times'], all_vectors, training_epochs=SOURCE.CUT)
        answers = {}
        for metric, values in projected.items():
            widths = evaluate_spaces(values[3:], values[:3], widths=WIDTHS, alpha=ALPHA)
            oracle = [pairs.ideal_comparison(pair['full_squared_distance'], alpha=ALPHA,
                                             target_power=POWER)['ideal_power']
                      for pair in widths[str(WIDTHS[0])]['pairs']]
            answers[metric] = dict(widths=widths, oracle_pair_power=oracle)
        rows[f'{law}/{weight}'] = answers
    return dict(identity=target['identity'], route=target['route'], arms=rows)


def run(root, action):
    paths = (SOURCE.FREEZE, SOURCE.RESULT, rule.FREEZE, rule.ROUTE_RESULT)
    raw = {path: (root / path).read_bytes() for path in paths}
    source, scores, reference, route = (json.loads(raw[path]) for path in paths)
    if (scores['freeze_sha256'] != digest(raw[SOURCE.FREEZE])
            or reference['inputs'][rule.ROUTE_RESULT] != digest(raw[rule.ROUTE_RESULT])
            or len(scores['rows']) != 12 or route['candidate_fits_converged'] != 6):
        raise ValueError('same sealed donors and separate route controls required')
    own = Path(__file__).relative_to(root).as_posix()
    config = encoded(dict(inputs={p: digest(b) for p, b in raw.items()},
        sources={p: digest((root / p).read_bytes()) for p in source_closure(
            root, (own, PLAN, 'analysis/tests/test_wide_direction_preflight.py'))},
        widths=WIDTHS, alpha=ALPHA, target_power=POWER, operators=56, comparisons=80,
        fits=0, later_receiver_reads=0, protected_reads=0, threads=1, environment=runtime_environment()))
    if action == 'freeze':
        _write_equal(root / FREEZE, config)
        return dict(freeze_sha256=digest(config))
    if (root / FREEZE).read_bytes() != config:
        raise ValueError('same frozen wider direction checks required')
    with ExitStack() as stack:
        store = stack.enter_context(closing(ArchiveStore(root)))
        donor, target = [stack.enter_context(closing(ClosedStudy(root, 'data/' + ref.ID, store=store)))
                         for ref in (SOURCE.parent, rule.routes)]
        if (donor.completion != source['parent'] or target.completion != reference['route_completion']
                or target.manifest['scope'] != rule.routes.SCOPE
                or set(target.tasks) != set(target.rows) or set(target.rows) != set(route['cases'])
                or set(target.rows) != {'straight-level', 'turning-level'}):
            raise ValueError('original source-bound physical paths differ')
        cases = [transfer._paths(donor, row) for row in scores['rows']]
        rows = [_evaluate(cases, _target(target, identity)) for identity in sorted(target.rows)]
    payload = encoded(dict(freeze_sha256=digest(config), routes=rows, widths=WIDTHS,
            pair_order=[(a, b) for a, b in combinations(FULL.MODELS, 2)],
            target_routes_share_one_seed=True, later_receiver_reads=0, protected_reads=0,
            fits=0, scientific_decision='abstain'))
    _write_equal(root / RESULT, payload)
    return dict(sha256=digest(payload), routes=len(rows), comparisons=80)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
