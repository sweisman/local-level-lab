# SPDX-License-Identifier: AGPL-3.0-or-later
"""Apply the frozen generated error range to sealed ESA development forecasts."""

import argparse
from contextlib import closing
import gzip
import json
from pathlib import Path

import numpy as np

from .airquantumgrav_error_policy import reported_covariance
from .airquantumgrav_geographic_report import error_metrics
from .esa_integrated_drift_v2_pilot import POLICY
from .esa_rolling_origin_400_model_matrix import ID, LAWS, MODELS, SCOPE, tasks
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_prediction_observed import accuracy_screen
from .integrated_drift_v2 import integrated_drift_v2_operator
from .models import radii
from .studies.artifacts import ArchiveStore, digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_CHANGING_DRIFT_TRANSFER_PLAN.md'
FREEZE = FOLDER+'esa-changing-drift-transfer-freeze.json'
RANGES = FOLDER+'esa-changing-drift-transfer-ranges.json.gz'
SEAL = FOLDER+'esa-changing-drift-transfer-range-seal.json'
RESULT = FOLDER+'esa-changing-drift-transfer-result.json'
GENERATED = FOLDER+'threshold-42-validation/'
PARENT = 'data/prediction-observed-development-continuation-v1-20261113'
CUT, LATER = 400, 120
THRESHOLD = 4.2
WEIGHTS = ('fixed_3cm', 'reported_earlier_covariance')


def operator(times, weight):
    times = np.asarray(times, float)
    return integrated_drift_v2_operator(times-times[0], origin_s=0.,
        acceleration_psd=POLICY['acceleration_psd'], jerk_psd=POLICY['jerk_psd'],
        snap_psd=POLICY['snap_psd'], receiver_random_walk_psd=POLICY['receiver_random_walk_psd'],
        initial_receiver_offset_std_m=POLICY['initial_receiver_offset_std_m'],
        initial_position_std_m=0., initial_velocity_std_mps=0.,
        initial_acceleration_std_mps2=0., initial_jerk_std_mps3=0.,
        receiver_loading=weight, maximum_bytes=8_000_000)


def condition(error, earlier, raw):
    earlier, raw = np.asarray(earlier, float), np.asarray(raw, float)
    if (earlier.ndim != 2 or earlier.shape[1] != 3 or raw.ndim != 2 or raw.shape[1] != 3
            or len(earlier)+len(raw) != error.epoch_count or not np.isfinite(raw).all()):
        raise ValueError('complete earlier residuals and later predicted coordinates required')
    _, state = error.apply_block(earlier.ravel(), first_epoch=0)
    distribution = error.conditional_marginals(state=state)
    sigma = np.sqrt(np.diagonal(distribution['covariance'], axis1=1, axis2=2))
    return dict(center_m=(raw-distribution['mean']).tolist(), sigma_m=sigma.tolist(),
                later_receiver_positions_used=False)


def _metrics(errors):
    metrics = error_metrics(errors.tolist())
    metrics.update(maximum_horizontal_m=float(np.max(np.linalg.norm(errors[:, :2], axis=1))),
                   maximum_absolute_up_m=float(np.max(abs(errors[:, 2]))))
    return dict(horizontal_rms_m=metrics['horizontal_rms_m'],
                height_rms_m=metrics['vertical_rms_m'], total_rms_m=metrics['total_rms_m'],
                descriptive_accuracy_passed=accuracy_screen(metrics)['passed'])


def score_range(forecast, observed, threshold):
    center, sigma = (np.asarray(forecast[key], float)[:len(observed)] for key in ('center_m', 'sigma_m'))
    error = center-np.asarray(observed, float)
    if sigma.shape != error.shape or not (np.isfinite(error).all() and np.all(sigma > 0.)):
        raise ValueError('complete finite receiver scores and positive range widths required')
    level = abs(error)/sigma
    return dict(**_metrics(error), contained=bool(np.all(level <= threshold)),
                maximum_absolute_standardized_error=float(level.max()),
                inside_coordinate_count=np.count_nonzero(level<=threshold, axis=0).tolist(),
                final_half_width_m=(threshold*sigma[-1]).tolist())


def compare_ranges(first, second, threshold):
    a, b = (np.asarray(item['center_m'], float) for item in (first, second))
    width = threshold*(np.asarray(first['sigma_m'])+np.asarray(second['sigma_m']))
    gap = abs(a-b)-width
    return dict(epochs_with_disjoint_axis_range=int(np.count_nonzero(np.any(gap > 0., axis=1))),
                maximum_axis_gap_m=max(0., float(gap.max())))


def _coordinates(rows):
    points = np.array([[r['latitude_deg'], r['longitude_deg'], r['height_m']] for r in rows])
    points[:, :2] = np.deg2rad(points[:, :2])
    return points


def _chart(points, anchor):
    latitude, _, altitude = anchor
    north, prime = radii(latitude)
    scale = np.array([north+altitude, (prime+altitude)*np.cos(latitude), 1.])
    delta = np.asarray(points, float)-anchor
    delta[:, 1] = np.arctan2(np.sin(delta[:, 1]), np.cos(delta[:, 1]))
    if not np.isfinite(delta).all() or not np.all(scale > 0.):
        raise ValueError('finite coordinates and earlier local metric required')
    return delta*scale


def _ranges(study, rows, times, task_rows):
    base = _coordinates(rows)
    fixed = np.broadcast_to(np.eye(3)*POLICY['receiver_white_std_m'], (CUT+LATER, 3, 3))
    earlier_weight = np.linalg.cholesky(np.asarray([reported_covariance(r) for r in rows]))
    reported = np.concatenate((earlier_weight, np.repeat(earlier_weight[-1:], LATER, axis=0)))
    operators = {key: operator(times, matrix) for key, matrix in zip(WEIGHTS, (fixed, reported), strict=True)}
    results = []
    for row in task_rows:
        identity = row['identity']
        if row['converged'] is True:
            fit = study.artifact(identity, 'fit.json')
            cost = fit['gaussian_training_score']['negative_log_likelihood']
            if not np.isfinite(cost) or fit['converged'] is not True or fit['model'] != row['model']:
                raise ValueError('unchanged converged training selection required')
            row = dict(row, training_cost=cost)
        if not row['passed']:
            results.append(row)
            continue
        raw = study.artifact(identity, 'forecast.json', raw=True)
        forecast = json.loads(raw)
        if (digest(raw) != row['forecast_sha256'] or forecast['times_s'] != times
                or forecast['training_epochs'] != CUT or forecast['prediction_epochs'] != LATER
                or np.shape(forecast['coordinates']) != (CUT+LATER, 3)
                or forecast['prediction_receiver_positions_used'] is not False
                or row['converged'] is not True):
            raise ValueError('unchanged earlier-only passing forecasts required')
        path = _chart(forecast['coordinates'], base[0])
        training = path[:CUT]-_chart(base, base[0])
        ranges = {name: condition(error, training, path[CUT:]) for name, error in operators.items()}
        results.append(dict(row, raw_future_m=path[CUT:].tolist(), ranges=ranges))
    return dict(anchor=base[0].tolist(), rows=results,
                operator_configurations={key: v.configuration for key, v in operators.items()},
                later_receiver_positions_used=False)


def _scores(saved, later):
    observed = _chart(_coordinates(later), saved['anchor'])
    rows = []
    for row in saved['rows']:
        record = {key: value for key, value in row.items() if key not in ('ranges', 'raw_future_m')}
        if row['passed']:
            forecasts = row['ranges']
            record.update(horizons={str(count): dict(raw=_metrics(
                np.asarray(row['raw_future_m'])[:count]-observed[:count]),
                ranges={key: score_range(value, observed[:count], THRESHOLD)
                        for key, value in forecasts.items()}) for count in (60, LATER)})
        rows.append(record)

    settings = []
    for profile in (False, True):
        for law in LAWS:
            group = [r for r in saved['rows'] if r['profile'] is profile and r['law'] == law]
            primary = {}
            for model in MODELS:
                candidates = [r for r in group if r['model']==model]
                if all(r['converged'] is not None for r in candidates):
                    converged = [r for r in candidates if r['converged']]
                    if converged:
                        chosen = min(converged, key=lambda r: (r['training_cost'], r['start']))
                        if chosen['passed']:
                            primary[model] = chosen
            complete = len(primary) == len(MODELS)
            comparisons = {}
            if complete:
                pairs = (('specified_globe_disc', MODELS[0], MODELS[2]),
                         ('zero_globe_disc', MODELS[1], MODELS[2]),
                         ('within_globe', MODELS[0], MODELS[1]))
                comparisons = {key: {label: compare_ranges(primary[a]['ranges'][key],
                                  primary[b]['ranges'][key], THRESHOLD) for label, a, b in pairs}
                               for key in WEIGHTS}
            settings.append(dict(profile=profile, law=law, complete=complete,
                primary={model: item['identity'] for model, item in primary.items()}, ranges=comparisons))
    return dict(rows=rows, matched_settings=settings, receiver_epochs=LATER,
                original_reads=0, fit_starts=0, protected_reads=0,
                aircraft_coverage_established=False, scientific_decision='abstain')


def run(root, action):
    with closing(ArchiveStore(root)) as store:
        matrix = ClosedStudy(root, 'data/'+ID, store=store)
        parent = ClosedStudy(root, PARENT, store=store)
        binding, origin = matrix.input('saved-input-binding'), matrix.input('parent_identity')
        rows = json.loads(gzip.decompress(matrix.input('training', raw=True)))
        times = matrix.input('forecast_times')
        declared = tasks()
        if (matrix.manifest['scope'] != SCOPE or set(matrix.rows) != {t['identity'] for t in declared}
                or origin['source_id'] != 'esa-99f1530c3eda4318' or binding['source_id'] != origin['source_id']
                or any(origin[k]!=parent.completion[k] for k in ('manifest_sha256', 'summary_sha256'))
                or len(rows) != CUT or len(times) != CUT+LATER
                or [r['time_s']-binding['time_origin_s'] for r in rows] != times[:CUT]):
            raise ValueError('same sealed development recording and split required')
        task_rows = []
        for task in declared:
            identity = task['identity']
            envelope = matrix.envelope(identity)
            outcome = envelope['result']
            spec = task['payload']
            if (matrix.tasks[identity]['payload'] != spec
                    or any(outcome.get(key) != value for key, value in spec.items())
                    or outcome.get('later_receiver_positions_used') is not False):
                raise ValueError('sealed task or observation boundary differs')
            passed = outcome['passed']
            forecast_sha = envelope['artifacts'][f'artifacts/{identity}/forecast.json'] if passed else None
            task_rows.append(dict(identity=identity, **spec, passed=passed,
                converged=outcome.get('numerical_converged'),
                original_status=matrix.rows[identity]['status'], forecast_sha256=forecast_sha))
        inputs = {name: (root/name).read_bytes() for name in (GENERATED+'policy.json', GENERATED+'RESULT.json')}
        policy, report = (json.loads(data) for data in inputs.values())
        if (report['generated_gate_passed'] is not True or report['threshold_z'] != THRESHOLD
                or report['policy_sha256'] != digest(inputs[GENERATED+'policy.json'])
                or policy['generated_case_policy_sha256'] != digest(encoded(POLICY))):
            raise ValueError('same generated reference law required')
        seeds = (Path(__file__).relative_to(root).as_posix(), PLAN,
                 'analysis/tests/test_esa_changing_drift_transfer.py')
        freeze = encoded(dict(sources={p:digest((root/p).read_bytes()) for p in source_closure(root, seeds)},
            generated={p:digest(raw) for p, raw in inputs.items()}, parents=[matrix.completion, parent.completion],
            earlier={key:matrix.manifest['inputs'][key]['sha256'] for key in ('training', 'forecast_times')},
            tasks=task_rows, threshold=THRESHOLD, operator_count=2, maximum_case_scores=48,
            fit_starts=0, threads=1, environment=runtime_environment()))
        if action == 'freeze':
            _write_equal(root/FREEZE, freeze)
            return dict(freeze_sha256=digest(freeze))
        if (root/FREEZE).read_bytes() != freeze:
            raise ValueError('changed source or study freeze')
        if action == 'condition':
            ranges = _ranges(matrix, rows, times, task_rows)
            raw = gzip.compress(encoded(dict(ranges, freeze_sha256=digest(freeze))), mtime=0)
            _write_equal(root/RANGES, raw)
            seal = dict(freeze_sha256=digest(freeze), ranges_sha256=digest(raw), later_receiver_reads=0)
            _write_equal(root/SEAL, encoded(seal))
            return seal

        seal, raw = json.loads((root/SEAL).read_bytes()), (root/RANGES).read_bytes()
        if seal != dict(freeze_sha256=digest(freeze), ranges_sha256=digest(raw), later_receiver_reads=0):
            raise ValueError('seal the earlier-only ranges before scoring')
        saved = json.loads(gzip.decompress(raw))
        all_rows = json.loads(gzip.decompress(parent.input('training', raw=True)))
        later = all_rows[CUT:CUT+LATER]
        if (all_rows[:CUT] != rows or len(all_rows) != 800
                or [r['time_s']-binding['time_origin_s'] for r in later] != times[CUT:]):
            raise ValueError('unchanged later development support required')
        result = _scores(saved, later)
        content = encoded(dict(result, **seal, later_receiver_sha256=digest(encoded(later))))
        _write_equal(root/RESULT, content)
        return dict(tasks=len(result['rows']), passing=sum(r['passed'] for r in result['rows']),
                    scored_settings=sum(r['complete'] for r in result['matched_settings']),
                    sha256=digest(content))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'condition', 'score'))
    print(run(Path.cwd(), parser.parse_args().action))
