# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved receiver-only sensitivity to a height error common to both streams."""

from contextlib import closing
import csv
import gzip
import io
import json
from pathlib import Path
import platform

import numpy as np

from .ilvis0_receiver_force import DISC_WITH_FIELD, FIELD_MODELS, MATCHED_MODELS, evaluate
from .ilvis0_receiver_overlap import WEEK_MS, _time_index
from .ilvis0_receiver_window_pairs_study import IDENTITY, PARENT
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


AMPLITUDE_M = .10
PERIODS_S = (20., 60., 120.)
GRAVITY = 9.81
RADIUS = 6371000.
PAIRS = 11
TARGETS = 490
FIELDS = (('zero', 'sphere_still', 'flat_still'),
          ('specified', 'sphere_rotating', DISC_WITH_FIELD))
FOLDER = 'docs/ilvis0-measurement-contribution'
SOURCE = 'analysis/lll/ilvis0_shared_gps_error.py'
TESTS = 'analysis/tests/test_ilvis0_shared_gps_error.py'
PLAN = FOLDER + '/SHARED_GPS_ERROR_PLAN.md'
FREEZE = FOLDER + '/shared-gps-error-freeze.json'


def rate(model):
    return 7.292115e-5 if model in FIELD_MODELS else 0.


def quadratic_weights(offsets_s):
    """The equal-weight vertical specialization of LocalPolynomial, degree 2."""
    times = np.asarray(offsets_s, dtype=float)
    if (times.ndim != 1 or len(times) < 3 or not np.isfinite(times).all()
            or not times[0] <= 0 <= times[-1] or np.any(np.diff(times) <= 0.)):
        raise ValueError('ordered support bracketing the target required')
    scale = float(np.max(abs(times)))
    scaled = times/scale
    design = np.column_stack((np.ones(len(times)), scaled, .5*scaled**2))
    weights, _, rank, _ = np.linalg.lstsq(design.T, np.eye(3), rcond=None)
    if rank != 3:
        raise ValueError('quadratic receiver operator is rank deficient')
    return weights.T/np.array([[1.], [scale], [scale**2]])


def force_response(offsets_s, coordinates, periods_s):
    """Evaluate the vector response to equally timed cosine and sine components."""
    times = np.asarray(offsets_s, dtype=float)
    coordinates = np.asarray(coordinates, dtype=float)
    if coordinates.shape != (len(times), 3) or not np.isfinite(coordinates).all():
        raise ValueError('finite latitude, longitude and height at each saved epoch required')
    weights = quadratic_weights(times)
    jet = weights@coordinates

    def force(values, model):
        return evaluate(*values, model=model, background_rate_rads=rate(model),
                        gravity_mps2=GRAVITY, disc_radius_m=RADIUS)['specific_force_ned_mps2']

    nominal = {model: force(jet, model) for model in MATCHED_MODELS}
    phases = 2.*np.pi*np.arange(16)/16
    coefficients = np.vstack((np.cos(phases), np.sin(phases)))
    output = []
    for period in periods_s:
        phase = times*(2.*np.pi/period)
        derivative = weights@(AMPLITUDE_M*np.column_stack((np.cos(phase), np.sin(phase))))
        perturbed = np.broadcast_to(jet, (2, 3, 3)).copy()
        perturbed[:, :, 2] += derivative.T
        models, magnitudes = {}, {}
        for model, vector in nominal.items():
            response = np.column_stack([force(values, model)-vector for values in perturbed])
            models[model] = dict(nominal_force=vector, phase_response=response,
                                 maximum_vector_shift_mps2=float(np.linalg.norm(response, ord=2)))
            magnitudes[model] = np.linalg.norm(vector[:, None]+response@coefficients, axis=0)
        contrasts = {}
        for label, globe, disc in FIELDS:
            baseline = float(np.linalg.norm(nominal[globe])-np.linalg.norm(nominal[disc]))
            shifted = magnitudes[globe]-magnitudes[disc]
            contrasts[label] = dict(nominal=baseline, maximum_change=float(max(abs(shifted-baseline))),
                sampled_minimum=float(shifted.min()), sampled_maximum=float(shifted.max()),
                sampled_sign_reversal=bool((baseline > 0. > shifted.min())
                                           or (baseline < 0. < shifted.max())))
        output.append(dict(period_s=period, models=models, contrasts=contrasts,
                           maximum_height_acceleration_shift_mps2=float(np.linalg.norm(derivative[2]))))
    return output


def cancellation_residual(left, right, times, period):
    error = AMPLITUDE_M*np.sin(np.asarray(times, dtype=float)*(2.*np.pi/period))
    return float(np.max(abs(((left+error)-(right+error))-(left-right))))


def _position_rows(data):
    return list(csv.DictReader(io.StringIO(gzip.decompress(data).decode())))


def _study_ready(study):
    return (study.completion['state'] == 'complete' and study.summary['total'] == PAIRS
            and study.summary['completed'] == PAIRS and study.summary['passed'] is True)


def _detail(pair, side, target, tags, coordinates, maximum_gap_s, minimum_samples):
    common = dict(pair=pair, side=side, target_gps_s=target['target_gps_s'],
                  half_window_s=target[side+'_half_window_s'])
    half = common['half_window_s']
    if half is None:
        return [dict(common, state='original_abstention', samples=0)]
    target_ms = round(common['target_gps_s']*1000)
    seconds = (tags-target_ms)/1000.
    selected = abs(seconds) <= half
    times = seconds[selected]
    common['samples'] = len(times)
    if (len(times) < minimum_samples or not times[0] <= 0. <= times[-1]
            or times[0]+half > maximum_gap_s or half-times[-1] > maximum_gap_s
            or max(np.diff(times)) > maximum_gap_s):
        return [dict(common, state='incomplete_matched_support')]
    coordinates = coordinates[selected].copy()
    coordinates[:, 1] = np.unwrap(coordinates[:, 1])
    rows = []
    for record in force_response(times, coordinates, PERIODS_S):
        row = dict(common, state='evaluated', period_s=record['period_s'],
                   maximum_height_acceleration_shift_mps2=record['maximum_height_acceleration_shift_mps2'])
        row.update({f'{model}_maximum_vector_shift_mps2': data['maximum_vector_shift_mps2']
                    for model, data in record['models'].items()})
        for label, values in record['contrasts'].items():
            row.update({f'{label}_{key}': value for key, value in values.items()})
        rows.append(row)
    return rows


def build(root):
    rows, pair_cancellations, hashes = [], [], {}
    target_count = 0
    with closing(ClosedStudy(root, PARENT)) as overlap:
        with closing(ClosedStudy(root, 'data/'+IDENTITY, store=overlap.store)) as windows:
            if not (_study_ready(overlap) and _study_ready(windows)
                    and set(windows.tasks) == set(overlap.tasks)
                    and sum(windows.envelope(pair)['result']['targets']
                            for pair in windows.tasks) == TARGETS):
                raise ValueError('exact sealed set of receiver pairs and targets required')
            for pair, task in windows.tasks.items():
                prior = overlap.tasks[pair]
                for ledger in (overlap, windows):
                    if ledger.envelope(pair)['result']['passed'] is not True:
                        raise ValueError('saved pair did not pass the original integrity checks')
                details = windows.artifact(pair, 'pair-window-comparison.json')
                if (details['pair_id'] != pair or any(
                        details[side+'_task'] != task[side+'_task']
                        or prior[side+'_task'] != task[side+'_task'] for side in ('left', 'right'))
                        or len(details['target_details']) != windows.envelope(pair)['result']['targets']):
                    raise ValueError('saved targets and source binding differ')
                inputs = {}
                for side in ('left', 'right'):
                    key = prior[side+'_key']
                    data = overlap.input(key, raw=True)
                    if digest(data) != task[side+'_sha256']:
                        raise ValueError('changed receiver input')
                    hashes[key] = digest(data)
                    inputs[side] = _time_index(_position_rows(data))
                tags = np.array(sorted(inputs['left'].keys() & inputs['right'].keys()), dtype=np.int64)
                differences = _position_rows(overlap.artifact(pair, 'differences.csv.gz', raw=True))
                expected = np.array([int(d['gps_week'])*WEEK_MS+int(d['gps_milliseconds'])
                                     for d in differences], dtype=np.int64)
                if not np.array_equal(tags, expected) or len(tags) != details['matched_epochs']:
                    raise ValueError('exact recorded receiver matches changed')
                coordinates = {}
                for side, indexed in inputs.items():
                    positions = np.array([[float(indexed[tag][field]) for field in
                        ('latitude_deg', 'longitude_deg', 'ellipsoid_height_m')] for tag in tags])
                    positions[:, :2] = np.deg2rad(positions[:, :2])
                    coordinates[side] = positions
                left, right = coordinates['left'][:, 2], coordinates['right'][:, 2]
                if not np.array_equal(left-right, [float(d['difference_up_m']) for d in differences]):
                    raise ValueError('sealed paired-height difference changed')
                residual = max(cancellation_residual(left, right, (tags-tags[0])/1000., period)
                               for period in PERIODS_S)
                if residual > 1e-9:
                    raise ValueError('common-height perturbation failed cancellation check')
                pair_cancellations.append(dict(pair=pair, matched_epochs=len(tags), residual_m=residual))
                settings = task['support_policy']
                for target in details['target_details']:
                    target_count += 1
                    for side in ('left', 'right'):
                        rows.extend(_detail(pair, side, target, tags, coordinates[side],
                                            settings['maximum_gap_s'], settings['minimum_samples']))
            prior_receipts = {name: ledger.completion for name, ledger in
                              (('overlap', overlap), ('windows', windows))}
    scored = [row for row in rows if row['state'] == 'evaluated']
    windows_evaluated = len(scored)//len(PERIODS_S)
    states = dict(evaluated=windows_evaluated, **{state: sum(row['state'] == state for row in rows)
                  for state in ('original_abstention', 'incomplete_matched_support')})
    if sum(states.values()) != 2*TARGETS or target_count != TARGETS:
        raise ValueError('incomplete pair window accounting')
    aggregate = {}
    for period in PERIODS_S:
        subset = [row for row in scored if row['period_s'] == period]
        responses = [row['maximum_height_acceleration_shift_mps2'] for row in subset]
        aggregate[str(period)] = dict(
            height_acceleration_shift_median_mps2=float(np.median(responses)),
            height_acceleration_shift_maximum_mps2=max(responses),
            maximum_force_vector_shift_mps2=max(
                row[f'{model}_maximum_vector_shift_mps2'] for row in subset for model in MATCHED_MODELS),
            **{f'{label}_sign_reversals': sum(row[f'{label}_sampled_sign_reversal'] for row in subset)
               for label, _, _ in FIELDS},
            **{f'{label}_contrast_change_maximum_mps2': max(row[f'{label}_maximum_change'] for row in subset)
               for label, _, _ in FIELDS})
    return dict(
        pairs=len(pair_cancellations), targets=target_count, window_states=states,
        amplitude_m=AMPLITUDE_M, periods_s=list(PERIODS_S), mode='shared-height sensitivity only',
        polynomial_operators=windows_evaluated,
        force_predictions=windows_evaluated*len(MATCHED_MODELS)*(1+2*len(PERIODS_S)),
        observed_imu_fit_starts=0, imu_observations_used=False, absolute_error_established=False,
        archived_receipts=prior_receipts, receiver_inputs_sha256=hashes,
        pair_cancellation=pair_cancellations, summary=aggregate, scientific_decision='abstain'), rows


def frozen_configuration(root):
    from .studies.dependencies import source_closure

    root = Path(root).resolve()
    return dict(
        sources_sha256={path: digest((root/path).read_bytes())
                        for path in source_closure(root, (SOURCE, TESTS, PLAN))},
        parents={name: digest((root/name/'completion.json').read_bytes())
                 for name in (PARENT, 'data/'+IDENTITY)},
        python=platform.python_version(), numpy=np.__version__, machine=platform.machine(),
        threads=1, pairs=PAIRS, targets=TARGETS, polynomial_budget=2*TARGETS,
        force_prediction_budget=2*TARGETS*len(MATCHED_MODELS)*(1+2*len(PERIODS_S)),
        amplitude_m=AMPLITUDE_M, periods_s=PERIODS_S, imu_fit_budget=0)


def publish(root):
    root = Path(root).resolve()
    freeze = (root/FREEZE).read_bytes()
    if freeze != encoded(frozen_configuration(root)):
        raise ValueError('shared-height diagnostic differs from its frozen configuration')
    receipt, rows = build(root)
    fields = list(dict.fromkeys(name for row in rows for name in row))
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    csv_bytes = stream.getvalue().encode()
    receipt['output_sha256'] = digest(csv_bytes)
    receipt['freeze_sha256'] = digest(freeze)
    folder = root/FOLDER
    for name, data in [('shared-gps-error-windows.csv', csv_bytes),
                       ('shared-gps-error-receipt.json', encoded(receipt))]:
        target = folder/name
        if target.is_file() and target.read_bytes() != data:
            raise ValueError('saved shared-height diagnostic changed: '+name)
        if not target.is_file():
            atomic(target, data)
    return receipt


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    args = parser.parse_args()
    if args.action == 'freeze':
        raw = encoded(frozen_configuration('.'))
        path = Path(FREEZE)
        if path.is_file() and path.read_bytes() != raw:
            raise ValueError('existing shared-height configuration differs')
        if not path.is_file():
            atomic(path, raw)
        print(digest(raw))
    else:
        report = publish('.')
        print(json.dumps({key: report[key] for key in
            ('pairs', 'targets', 'window_states', 'force_predictions', 'summary')}, sort_keys=True))
