# SPDX-License-Identifier: AGPL-3.0-or-later
"""Certified projection margins between finite families of sealed forecasts."""

import argparse
from contextlib import ExitStack, closing
import gzip
from itertools import combinations
import json
import math
from pathlib import Path

import numpy as np

from . import esa_alternate_training_refit as refit
from . import forecast_pair_information as pairs
from .airquantumgrav_error_policy import reported_covariance
from .esa_joint_path_score import _ranges
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .state_space_covariance import LinearInnovations
from .studies.artifacts import ArchiveStore, digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


FULL, REDUCED = pairs.full, pairs.reduced
PLAN = FULL.FOLDER + 'FORECAST_FAMILY_MARGIN_PLAN.md'
FREEZE = FULL.FOLDER + 'forecast-family-margin-freeze.json'
RESULT = FULL.FOLDER + 'forecast-family-margin-result.json'


def coordinates(operator, times, paths, *, training_epochs):
    """Express entire conditional paths in the two declared score metrics."""
    if (not isinstance(operator, LinearInnovations) or type(training_epochs) is not int
            or not 1 <= training_epochs < operator.epoch_count - 4):
        raise ValueError('fixed operator and supported chronological split required')
    n, d = operator.epoch_count, operator.observation_dimension
    t, array = np.asarray(times, float), np.asarray(paths, float)
    if (t.shape != (n,) or array.ndim != 3 or not 2 <= len(array) <= 40
            or array.shape[1:] != (n - training_epochs, d) or not np.isfinite(array).all()
            or not np.isfinite(t).all() or not (np.diff(t) > 0.0).all()):
        raise ValueError('complete finite paths on the same chronological support required')
    elapsed = t[training_epochs:] - t[training_epochs]
    polys = np.polynomial.legendre.legvander(2.0 * elapsed / elapsed[-1] - 1.0, 3)
    basis = np.kron(polys, np.eye(d))
    changes = (array - array[0]).reshape(len(array), -1).T
    columns = np.column_stack((changes, basis))
    _, checkpoint = operator.apply_block(
        np.zeros((training_epochs * d, columns.shape[1])), first_epoch=0)
    values, _ = operator.apply_block(columns, first_epoch=training_epochs, state=checkpoint)
    full = values[:, :len(array)]
    q, r = np.linalg.qr(values[:, len(array):], mode='reduced')
    if np.linalg.matrix_rank(r) != r.shape[1]:
        raise ValueError('smooth error terms must be numerically distinguishable')
    return dict(full=full.T, after_cubic=(full - q @ (q.T @ full)).T)


def margin(first, second):
    """Lower bound on distance between two convex hulls from one direction."""
    a, b = np.asarray(first, float), np.asarray(second, float)
    if (a.ndim != 2 or b.ndim != 2 or not len(a) or not len(b) or not a.shape[1]
            or a.shape[1] != b.shape[1] or not np.isfinite(a).all() or not np.isfinite(b).all()):
        raise ValueError('finite matched forecast families required')
    delta = b[0] - a[0]
    baseline = float(np.linalg.norm(delta))
    result = dict(baseline_distance=baseline, separating_direction_found=False,
                  signed_margin=None, lower_bound_on_distance=0.0)
    if baseline == 0.0:
        return result
    if not math.isfinite(baseline):
        raise ValueError('unrepresentable baseline distance')
    direction = delta / baseline
    first_proj, second_proj = (a - a[0]) @ direction, (b - a[0]) @ direction
    intervals = [[float(values.min()), float(values.max())]
                 for values in (first_proj, second_proj)]
    signed = intervals[1][0] - intervals[0][1]
    result.update(first_projection_interval=intervals[0], second_projection_interval=intervals[1],
                  signed_margin=signed, separating_direction_found=signed > 0.0,
                  lower_bound_on_distance=max(signed, 0.0))
    return result


def _alt_paths(alternate, training, times, anchor):
    if alternate.manifest['scope'] != refit.SCOPE or alternate.completion['state'] != 'complete':
        raise ValueError('closed alternate training study required')
    specs = {task['identity']: task['payload'] for task in refit.tasks()}
    if set(alternate.rows) != set(specs) or set(alternate.tasks) != set(specs):
        raise ValueError('all six original alternate fits required')
    material = alternate.input('alternate-material-binding')
    earlier = {}
    for source in refit.SOURCES:
        key = 'training_' + source
        raw = alternate.input(key, raw=True)
        rows = json.loads(gzip.decompress(raw))
        metadata = material['sources'][key]
        if (len(rows) != FULL.CUT or digest(raw) != metadata['staged_sha256']
                or digest(encoded(rows)) != metadata['training_rows_sha256']):
            raise ValueError('alternate training rows differ from the frozen refit')
        for original, changed in zip(training, rows, strict=True):
            if set(original) != set(changed) or any(original[k] != changed[k] for k in original
                    if k not in ('latitude_deg', 'longitude_deg', 'height_m')):
                raise ValueError('only receiver position may differ between fits')
        earlier[source] = FULL._chart(FULL._coordinates(rows), anchor)
    saved = {}
    for identity, spec in specs.items():
        outcome = alternate.envelope(identity)['result']
        forecast = alternate.artifact(identity, 'forecast.json')
        if (alternate.tasks[identity]['payload'] != spec or outcome['passed'] is not True
                or outcome['later_receiver_positions_used'] is not False or forecast['times_s'] != times
                or forecast['training_epochs'] != FULL.CUT or forecast['prediction_epochs'] != FULL.LATER
                or forecast['prediction_receiver_positions_used'] is not False):
            raise ValueError('exact earlier-only alternate forecasts required')
        saved[spec['source'], spec['model']] = FULL._chart(forecast['coordinates'], anchor)
    return earlier, saved


def _compare(matrix, alternate, ranges, baseline_info):
    training = json.loads(gzip.decompress(matrix.input('training', raw=True)))
    times = matrix.input('forecast_times')
    origin = matrix.input('parent_identity')
    if (alternate.input('parent_identity') != origin or origin['source_id'] != 'esa-99f1530c3eda4318'
            or alternate.input('forecast_times') != times or len(training) != FULL.CUT
            or len(times) != FULL.CUT + FULL.LATER):
        raise ValueError('same recording and 400/120 periods required')
    anchor = FULL._coordinates(training[:1])[0]
    earlier, paths = _alt_paths(alternate, training, times, anchor)
    reported = np.linalg.cholesky(np.asarray([reported_covariance(row) for row in training]))
    weights = (np.broadcast_to(np.eye(3) * FULL.POLICY['receiver_white_std_m'], (len(times), 3, 3)),
               np.concatenate((reported, np.repeat(reported[-1:], FULL.LATER, axis=0))))
    sources = ('air1', *refit.SOURCES)
    answers = {}
    for name, maker, receipt in zip(('full', 'reduced'), (FULL.operator, REDUCED.no_snap_operator),
                                    ranges, strict=True):
        available = {row['identity']: row for row in receipt['rows']}
        if (receipt['anchor'] != anchor.tolist()
                or pairs._selection(receipt['rows'], True, 'increment') != baseline_info['selected']
                or any(identity != f'{model}-1-increment-0'
                       for model, identity in baseline_info['selected'].items())):
            raise ValueError('same sealed baseline refit starts required')
        for weight, factor in zip(FULL.WEIGHTS, weights, strict=True):
            operator = maker(times, factor)
            key = f'{name}/{weight}'
            if operator.configuration != receipt['operator_configurations'][weight]:
                raise ValueError('earlier weighting or covariance law changed')
            centers = []
            for model in FULL.MODELS:
                base = available[baseline_info['selected'][model]]['ranges'][weight]['center_m']
                centers.append(base)
                for source in refit.SOURCES:
                    path = paths[source, model]
                    centers.append(FULL.condition(operator, path[:FULL.CUT] - earlier[source],
                                                  path[FULL.CUT:])['center_m'])
            by_metric = coordinates(operator, times, centers, training_epochs=FULL.CUT)
            arms = {}
            for metric, values in by_metric.items():
                blocks = dict(zip(FULL.MODELS, values.reshape(len(FULL.MODELS), len(sources), -1), strict=True))
                for a, b in combinations(FULL.MODELS, 2):
                    contrast = f'{a}/{b}'
                    item = margin(blocks[a], blocks[b])
                    reference = baseline_info['arms'][key][contrast][metric]['distance']
                    if not math.isclose(item['baseline_distance'], reference, rel_tol=1e-9, abs_tol=1e-9):
                        raise ValueError('original sealed contrast did not replay')
                    arms.setdefault(contrast, {})[metric] = item
            answers[key] = arms
    return answers


def run(root, action):
    inputs = {name: (root / name).read_bytes() for source in (FULL, REDUCED)
              for name in (source.FREEZE, source.RANGES, source.SEAL)}
    inputs.update({name: (root / name).read_bytes() for name in (pairs.RESULT, pairs.FREEZE)})
    base = json.loads(inputs[pairs.RESULT])
    if base['freeze_sha256'] != digest(inputs[pairs.FREEZE]):
        raise ValueError('sealed baseline contrast study required')
    ranges = [_ranges(inputs, item) for item in (FULL, REDUCED)]
    baseline = next(row for row in base['settings'] if row['profile'] and row['imu_law'] == 'increment')
    with ExitStack() as stack:
        store = stack.enter_context(closing(ArchiveStore(root)))
        matrix, alternate = [stack.enter_context(closing(ClosedStudy(root, 'data/' + identity, store=store)))
                             for identity in (FULL.ID, refit.ID)]
        if matrix.completion != json.loads(inputs[FULL.FREEZE])['parents'][0]:
            raise ValueError('original fit matrix differs')
        own = Path(__file__).relative_to(root).as_posix()
        config = encoded(dict(inputs={p: digest(data) for p, data in inputs.items()},
            sources={p: digest((root / p).read_bytes()) for p in source_closure(
                root, (own, PLAN, 'analysis/tests/test_forecast_family_margin.py'))},
            study_completions=[matrix.completion, alternate.completion], fit_starts=0,
            operators=4, pair_margins=24, threads=1, later_receiver_reads=0,
            protected_reads=0, environment=runtime_environment()))
        if action == 'freeze':
            _write_equal(root / FREEZE, config)
            return dict(freeze_sha256=digest(config))
        if (root / FREEZE).read_bytes() != config:
            raise ValueError('forecast-family comparison differs from frozen plan')
        answer = _compare(matrix, alternate, ranges, baseline)
    payload = encoded(dict(freeze_sha256=digest(config), arms=answer,
                           training_sources=('air1', *refit.SOURCES), later_receiver_reads=0,
                           fits=0, protected_reads=0, calibrated=False, scientific_decision='abstain'))
    _write_equal(root / RESULT, payload)
    return dict(sha256=digest(payload), margins=sum(len(pairs) * 2 for pairs in answer.values()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
