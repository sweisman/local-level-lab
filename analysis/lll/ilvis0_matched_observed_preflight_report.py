# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay held-out position scores without refitting the observed preflight."""

from contextlib import closing
import csv
import io
import json
from pathlib import Path

import numpy as np

from .ilvis0_gps_sensitivity import assumptions, coordinate_covariance
from .ilvis0_matched_observed_preflight import FOLDER, ID, TRACKS, recipe, tasks
from .ilvis0_solver_position import physical_metric
from .ilvis0_wide_tangent import derive
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


def build(root):
    rows = []
    training_metrics = {}
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        frozen = study.input('input_receipt')
        expected = {item['identity']: item for item in tasks(frozen['recordings'])}
        policy = study.input('recipe')
        if (set(expected) != set(study.tasks) or policy != recipe()
                or study.summary['total'] != 8):
            raise ValueError('unchanged eight-case recorded preflight required')
        for path, sha in study.manifest['sources'].items():
            study.read('source-freeze/'+path, sha, raw=True)
        cpp = 'analysis/lll/ilvis0_tangent.cpp'
        cpp_sha = study.manifest['sources'][cpp]
        wide_sha = digest(derive(study.read('source-freeze/'+cpp, cpp_sha, raw=True),
                                 expected_sha256=cpp_sha))
        covariance_law = next(item for item in assumptions() if item.name == policy['weighting'])
        for identity, item in expected.items():
            task = {key: value for key, value in study.tasks[identity].items()
                    if key not in ('index', 'shard')}
            if item != task:
                raise ValueError('changed recorded preflight task')
            row = dict(identity=identity, segment_id=task['segment_id'], model=task['model'],
                       state='missing', technical_pass=False, converged=False,
                       training_evaluations=None, prefix_difference_m=None, reason=None,
                       training_cost=None, projected_stationarity=None, stopping_probe=None,
                       trial_evaluations=None, rejected_only_trial_evaluations=None)
            for track in TRACKS:
                row.update({f'{track}_{axis}_rms_m': None for axis in ('horizontal', 'height')})
            rows.append(row)
            if identity not in study.rows:
                continue
            envelope = study.envelope(identity)
            result = envelope['result']
            row.update(state=envelope['status'], reason=result.get('reason'))
            if result.get('forecast_saved_before_scoring') is not True:
                if result['passed']:
                    raise ValueError('missing saved forecast under reported pass')
                continue
            fit = study.artifact(identity, 'fit.json')
            compilation = study.artifact(identity, 'compilation.json')
            if (compilation['value']['source_sha256'] != study.manifest['sources']['analysis/lll/ilvis0_native.c']
                    or compilation['tangent']['source_sha256'] != cpp_sha
                    or compilation['wide']['source_sha256'] != wide_sha
                    or compilation['wide']['original_source_sha256'] != cpp_sha
                    or compilation['wide']['internal_mantissa_bits'] <= 53):
                raise ValueError('compiled forecast identity differs from frozen native sources')
            forecast = study.artifact(identity, 'forecast.json')
            segment = task['segment_id']
            scoring = study.input(segment+'-scoring')
            query = study.input(segment+'-queries')
            positions = np.asarray(forecast['coordinates'], float)
            cut, later = task['training_epochs'], task['scoring_epochs']
            recorded_difference = np.asarray(forecast['training_coordinate_difference'], float)
            if (positions.shape != (cut+later, 3) or not np.isfinite(positions).all()
                    or recorded_difference.shape != (cut, 3) or not np.isfinite(recorded_difference).all()
                    or forecast['training_epochs'] != cut
                    or forecast['later_positions_used']
                    or fit['prediction_receiver_positions_used_in_training']
                    or forecast['query_times_s'] != query['query_times_s']
                    or forecast['query_times_s'][cut:] != scoring['query_times_s']
                    or fit['model'] != task['model']
                    or result['training_evaluations'] != fit['evaluations']
                    or result['converged'] != fit['converged']
                    or fit['evaluations']+1 != envelope['charged']['native_calls']
                    or envelope['charged']['packet_visits'] != fit['evaluations']*task['training_packets']*cut
                        + task['full_packets']*(cut+later)
                    or result['observed_fit_starts'] != 1
                    or result['passed'] != (result['prefix_difference_m'] <= policy['maximum_prefix_difference_m'])):
                raise ValueError('saved fit, forecast or accounting differs')
            if segment not in training_metrics:
                train = study.input(segment+'-training')
                gps = np.asarray(train['coordinates']['onboard'], float)
                blocks = np.tile(np.diag(np.square(policy['independent_neu_m'])), (cut, 1, 1))
                queries = query['query_times_s'][:cut]
                if queries != train['query_times_s']:
                    raise ValueError('training queries differ from prepared positions')
                covariance = coordinate_covariance(np.asarray(queries), gps[:, 0],
                                                   gps[:, 2], blocks, covariance_law)
                training_metrics[segment] = np.linalg.cholesky(covariance), physical_metric(gps)
            factor, metric = training_metrics[segment]
            fitted = factor @ np.asarray(fit['local_linearization']['residual'], float)
            difference = (recorded_difference-fitted.reshape((cut, 3)))*metric
            prefix = float(np.linalg.norm(difference, axis=1).max())
            if not np.isclose(prefix, result['prefix_difference_m'], rtol=1e-12, atol=1e-12):
                raise ValueError('saved training-prefix error does not replay')
            for track in TRACKS:
                reference = np.asarray(scoring['coordinates'][track], float)
                if reference.shape != (later, 3):
                    raise ValueError('saved scoring receiver epochs differ')
                residual = (positions[cut:]-reference)*physical_metric(reference)
                scores = dict(horizontal=float(np.sqrt(np.mean(np.sum(residual[:, :2]**2, axis=1)))),
                              height=float(np.sqrt(np.mean(residual[:, 2]**2))))
                for axis, score in scores.items():
                    if not np.isclose(score, result['heldout_rms_by_gps_stream'][track][axis+'_rms_m'],
                                      rtol=1e-12, atol=1e-12):
                        raise ValueError('held-out position score does not replay')
                    row[f'{track}_{axis}_rms_m'] = score
            evaluations = {entry['evaluation'] for entry in fit['evaluation_trace']}
            trials = {entry['evaluation'] for entry in fit['step_history']}
            accepted = {entry['evaluation'] for entry in fit['step_history'] if entry['accepted']}
            ordinary = {entry['evaluation'] for entry in fit['evaluation_trace'] if not entry['fresh']}
            if evaluations != set(range(1, fit['evaluations']+1)) or not trials <= ordinary:
                raise ValueError('trial history differs from charged training evaluations')
            row.update(technical_pass=result['passed'], converged=fit['converged'],
                       training_evaluations=fit['evaluations'],
                       prefix_difference_m=prefix, training_cost=fit['residual_sum_squares'],
                       projected_stationarity=fit['exact_projected_gradient_relative'],
                       stopping_probe=fit['stability_probe']['reason'], reason=fit.get('message'),
                       trial_evaluations=len(trials), rejected_only_trial_evaluations=len(trials-accepted))
        receipt = dict(study.completion, charged=study.summary['charged'],
                       completed=study.summary['completed'], total=8,
                       preflight_technical_passes=sum(row['technical_pass'] for row in rows),
                       numerical_stops=sum(row['converged'] for row in rows),
                       observed_recordings=len(frozen['recordings']), qualified_coverage=False,
                       scientific_decision='abstain')
    return receipt, rows


def publish(root):
    receipt, rows = build(root)
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    payload = stream.getvalue().encode()
    receipt.update(reporter_sha256=digest(Path(__file__).read_bytes()), output_sha256=digest(payload))
    folder = Path(root)/FOLDER
    for name, raw in [('matched-observed-preflight-fits.csv', payload),
                      ('matched-observed-preflight-receipt.json', encoded(receipt))]:
        path = folder/name
        if path.is_file() and path.read_bytes() != raw:
            raise ValueError('sealed recorded preflight report differs')
        if not path.is_file():
            atomic(path, raw)
    return receipt


if __name__ == '__main__':
    print(json.dumps(publish(Path.cwd()), sort_keys=True))
