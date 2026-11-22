# SPDX-License-Identifier: AGPL-3.0-or-later
"""Decompose sealed future path error without changing its forecast."""

import argparse
from contextlib import ExitStack, closing
import json
import math
from pathlib import Path

import numpy as np

from . import esa_rolling_scale_transfer as transfer
from .airquantumgrav_error_policy import reported_covariance
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .state_space_covariance import LinearInnovations
from .studies.artifacts import ArchiveStore, digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


FOLDER = transfer.FOLDER
PLAN = FOLDER + 'FORECAST_SMOOTH_ERROR_PLAN.md'
FREEZE = FOLDER + 'forecast-smooth-error-freeze.json'
RESULT = FOLDER + 'forecast-smooth-error-result.json'
FULL, RULE = transfer.FULL, transfer.rule


def decompose(operator, times, conditioned_error, *, training_epochs):
    """Partition weighted later error using smooth physical-coordinate terms."""
    if (not isinstance(operator, LinearInnovations) or type(training_epochs) is not int
            or not 1 <= training_epochs < operator.epoch_count - 4):
        raise ValueError('complete operator and nonempty chronological split required')
    count, d = operator.epoch_count, operator.observation_dimension
    t = np.asarray(times, float)
    error = np.asarray(conditioned_error, float)
    if (t.shape != (count,) or error.shape != (count - training_epochs, d)
            or not np.isfinite(t).all() or not np.isfinite(error).all()
            or not (np.diff(t) > 0.0).all()):
        raise ValueError('finite ordered times and complete matched future errors required')
    delay = t[training_epochs:] - t[training_epochs]
    x = 2.0 * delay / delay[-1] - 1.0
    polynomials = np.polynomial.legendre.legvander(x, 3)
    design = np.kron(polynomials, np.eye(d))
    columns = np.column_stack((error.ravel(), design))
    _, checkpoint = operator.apply_block(
        np.zeros((training_epochs * d, columns.shape[1])), first_epoch=0)
    whitened, _ = operator.apply_block(columns, first_epoch=training_epochs, state=checkpoint)
    residual = whitened[:, 0]
    basis, r = np.linalg.qr(whitened[:, 1:], mode='reduced')
    if np.linalg.matrix_rank(r) != r.shape[1]:
        raise ValueError('smooth path terms must be numerically distinguishable')
    coefficients = basis.T @ residual
    total = float(residual @ residual)
    parts = []
    for degree in range(4):
        dimensions = (degree + 1) * d
        included = coefficients[:dimensions]
        remainder = residual - basis[:, :dimensions] @ included
        removed = float(included @ included)
        remaining = float(remainder @ remainder)
        if not math.isclose(removed + remaining, total, rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError('orthogonal score decomposition did not close')
        parts.append(dict(degree=degree, smooth_dimension=dimensions,
                          smooth_squared_error=removed, remaining_squared_error=remaining))
    return dict(total_squared_error=total, through_degree=parts, covariance_configuration=operator.configuration,
                forecast_changed=False, scientific_decision='abstain')


def _cut(study, cut, rows, expected):
    n = cut + FULL.LATER
    times = study.input('forecast_times')
    if len(times) != n or len(rows) != n or rows[:cut] != transfer._rows(study):
        raise ValueError('sealed forecast and receiver split differ')
    anchor = FULL._coordinates(rows[:1])[0]
    receiver = FULL._chart(FULL._coordinates(rows), anchor)
    fixed = np.broadcast_to(np.eye(3) * FULL.POLICY['receiver_white_std_m'], (n, 3, 3))
    weights = np.linalg.cholesky(np.asarray([reported_covariance(row) for row in rows[:cut]]))
    reported = np.concatenate((weights, np.repeat(weights[-1:], FULL.LATER, axis=0)))
    operators = {f'{law}/{weight}': maker(times, values)
                 for law, maker in zip(RULE.observed.LAWS, (FULL.operator, RULE.reduced.no_snap_operator),
                                       strict=True)
                 for weight, values in zip(FULL.WEIGHTS, (fixed, reported), strict=True)}
    if {key: op.configuration for key, op in operators.items()} != expected['operators']:
        raise ValueError('covariance identity differs from the sealed score')
    answer = {}
    for law in transfer.late_study.LAWS:
        forecast = study.artifact(law, 'forecast.json')
        if (study.envelope(law)['result']['passed'] is not True
                or forecast['prediction_receiver_positions_used'] is not False
                or forecast['times_s'] != times or forecast['training_epochs'] != cut
                or forecast['prediction_epochs'] != FULL.LATER):
            raise ValueError('closed earlier-only forecast required')
        path = FULL._chart(forecast['coordinates'], anchor)
        arm_results = {}
        for key, operator in operators.items():
            cond = FULL.condition(operator, path[:cut] - receiver[:cut], path[cut:])
            error = np.asarray(cond['center_m']) - receiver[cut:]
            info = decompose(operator, times, error, training_epochs=cut)
            if not math.isclose(info['total_squared_error'], expected['scores'][law][key],
                                rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError('did not reproduce the sealed score')
            arm_results[key] = info
        answer[law] = arm_results
    return answer


def run(root, action):
    paths = (transfer.EARLIER, transfer.RESULT, transfer.FREEZE)
    raw = {p: (root / p).read_bytes() for p in paths}
    early, result, base_freeze = (json.loads(raw[p]) for p in paths)
    if (result['earlier_sha256'] != digest(raw[transfer.EARLIER])
            or early['freeze_sha256'] != digest(raw[transfer.FREEZE])
            or result['freeze_sha256'] != early['freeze_sha256']):
        raise ValueError('scale transfer receipts differ')
    own = Path(__file__).relative_to(root).as_posix()
    config = encoded(dict(inputs={p: digest(data) for p, data in raw.items()},
        sources={p: digest((root / p).read_bytes()) for p in source_closure(
            root, (own, PLAN, 'analysis/tests/test_forecast_smooth_error.py'))},
        fit_starts=0, operators=8, decompositions=16, threads=1, protected_reads=0,
        environment=runtime_environment()))
    if action == 'freeze':
        _write_equal(root / FREEZE, config)
        return dict(freeze_sha256=digest(config))
    if (root / FREEZE).read_bytes() != config:
        raise ValueError('smooth error replay differs from frozen plan')
    with ExitStack() as stack:
        store = stack.enter_context(closing(ArchiveStore(root)))
        studies = [stack.enter_context(closing(ClosedStudy(root, 'data/' + module.ID, store=store)))
                   for module in (transfer.early_study, transfer.late_study)]
        if [study.completion for study in studies] != base_freeze['forecast_studies']:
            raise ValueError('closed forecast identities differ')
        parent = stack.enter_context(closing(ClosedStudy(root, FULL.PARENT, store=store)))
        if any(parent.completion[field] != base_freeze['parent'][field]
               for field in ('manifest_sha256', 'summary_sha256')):
            raise ValueError('sealed later scoring receiver source differs')
        positions = transfer._rows(parent)
        first = _cut(studies[0], transfer.EARLY_CUT,
                     positions[:transfer.EARLY_CUT + FULL.LATER], early)
        second = _cut(studies[1], FULL.CUT, positions[:FULL.CUT + FULL.LATER], result['later'])
    ratios = {}
    for law, arms in first.items():
        ratios[law] = {}
        for arm, info in arms.items():
            late = second[law][arm]
            ratios[law][arm] = dict(full=late['total_squared_error'] / info['total_squared_error'],
                remaining=[end['remaining_squared_error'] / start['remaining_squared_error']
                           for start, end in zip(info['through_degree'], late['through_degree'], strict=True)])
    payload = encoded(dict(freeze_sha256=digest(config), earlier=first, later=second,
                           later_to_earlier=ratios, fits=0, protected_reads=0,
                           scientific_decision='abstain'))
    _write_equal(root / RESULT, payload)
    return dict(sha256=digest(payload), ratios=ratios)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
