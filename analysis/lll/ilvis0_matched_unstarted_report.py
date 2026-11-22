# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and compare the four saved forecasts after the IMU21 continuation."""

from contextlib import ExitStack, closing
from pathlib import Path

from .ilvis0_matched_unstarted_recovery import ARCHIVE, CAMPAIGN, IDENTITY, MANIFEST, SUMMARY, WORKSPACE
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


STAGE = WORKSPACE+'/'+CAMPAIGN+'/stage-000'
STAGE_MANIFEST = '954480490d2e1bd8a68a962be1418f73eb11fbd3c694b36ee8975ec2002b20a5'
STAGE_SUMMARY = '87f139e21d4b6a0ced87c2b968d18202860c60c22c234df0d4d6eaf18550434a'
CONTINUATION_SHA = '9a1f88a3fc4a84ccbe67ad88734d6e1d7e6e014d7ea96f65124b7e5c5db3c64a'
RESULT = 'docs/ilvis0-measurement-contribution/matched-unstarted-disc-result.json'
MODELS = ('sphere_rotating', 'sphere_still', 'flat_geographic_field', 'flat_still')


def forecast_scores(study, identity, scoring, query, training, policy):
    import numpy as np

    from .ilvis0_gps_sensitivity import assumptions, coordinate_covariance
    from .ilvis0_solver_position import physical_metric

    task = study.tasks[identity]
    envelope = study.envelope(identity)
    charges, saved = envelope['charged'], envelope['result']
    fit = study.artifact(identity, 'fit.json')
    forecast = study.artifact(identity, 'forecast.json')
    cut, later = task['training_epochs'], task['scoring_epochs']
    coordinates = np.asarray(forecast['coordinates'], float)
    recorded = np.asarray(forecast['training_coordinate_difference'], float)
    model = task['model']
    epochs = query['query_times_s']
    if (saved['passed'] is not True or fit['converged'] is not True or fit['stability_probe']['passed'] is not True
            or not saved['forecast_saved_before_scoring'] or forecast['later_positions_used']
            or fit['prediction_receiver_positions_used_in_training'] or model != fit['model']
            or saved['training_evaluations'] != fit['evaluations'] or fit['evaluations'] > 30
            or charges['native_calls'] != fit['evaluations']+1
            or charges['packet_visits'] != fit['evaluations']*task['training_packets']*cut
                + task['full_packets']*(cut+later)
            or epochs != forecast['query_times_s'] or epochs[:cut] != training['query_times_s']
            or epochs[cut:] != scoring['query_times_s'] or forecast['training_epochs'] != cut
            or coordinates.shape != (cut+later, 3) or recorded.shape != (cut, 3)
            or not np.isfinite(coordinates).all() or not np.isfinite(recorded).all()):
        raise ValueError('sealed stopped fit, withheld forecast or charges differ: '+identity)
    observed = np.asarray(training['coordinates']['onboard'])
    law = next(item for item in assumptions() if item.name == policy['weighting'])
    blocks = np.tile(np.diag(np.square(policy['independent_neu_m'])), (cut, 1, 1))
    covariance = coordinate_covariance(np.asarray(epochs[:cut]), observed[:, 0], observed[:, 2], blocks, law)
    original = np.linalg.cholesky(covariance) @ np.asarray(fit['local_linearization']['residual'])
    prefix_error = float(np.linalg.norm((recorded-original.reshape(cut, 3))*physical_metric(observed), axis=1).max())
    if (prefix_error > policy['maximum_prefix_difference_m']
            or not np.isclose(prefix_error, saved['prefix_difference_m'], atol=1e-12, rtol=1e-12)):
        raise ValueError('saved training prefix did not verify')
    scores = {}
    for stream, rows in scoring['coordinates'].items():
        receiver = np.asarray(rows, float)
        error = (coordinates[cut:]-receiver)*physical_metric(receiver)
        horizontal = float(np.sqrt(np.mean(np.sum(error[:, :2]**2, axis=1))))
        height = float(np.sqrt(np.mean(error[:, 2]**2)))
        original = saved['heldout_rms_by_gps_stream'][stream]
        if not np.allclose([horizontal, height], [original['horizontal_rms_m'], original['height_rms_m']],
                           rtol=1e-12, atol=1e-12):
            raise ValueError('recorded position scores did not reproduce')
        scores[stream] = dict(horizontal_rms_m=horizontal, height_rms_m=height,
                              total_rms_m=float(np.hypot(horizontal, height)))
    return dict(model=model, training_evaluations=fit['evaluations'], prefix_error_m=prefix_error,
                scores=scores, native_calls=charges['native_calls'])


def report(root):
    segment = IDENTITY.removesuffix('-flat_still')
    with ExitStack() as stack:
        parent = stack.enter_context(closing(ClosedStudy(root, ARCHIVE)))
        stage = stack.enter_context(closing(ClosedStudy(root, STAGE, store=parent.store)))
        if ((parent.completion['manifest_sha256'], parent.completion['summary_sha256']) != (MANIFEST, SUMMARY)
                or (stage.completion['manifest_sha256'], stage.completion['summary_sha256']) != (STAGE_MANIFEST, STAGE_SUMMARY)
                or digest(stage.read('completion.json', raw=True)) != CONTINUATION_SHA
                or set(stage.rows) != {IDENTITY} or IDENTITY in parent.rows
                or stage.manifest['environment'] != parent.manifest['environment']
                or any(stage.manifest['sources'].get(name) != sha for name, sha in parent.manifest['sources'].items())
                or any(stage.manifest['inputs'][name]['sha256'] != row['sha256']
                       for name, row in parent.manifest['inputs'].items())
                or any(stage.tasks[IDENTITY][name] != value for name, value in parent.tasks[IDENTITY].items()
                       if name not in ('index', 'shard'))):
            raise ValueError('exact original and continued observations and charges required')
        scoring, queries, training = (parent.input(segment+'-'+name)
                                      for name in ('scoring', 'queries', 'training'))
        policy = parent.input('recipe')
        results = [forecast_scores(stage if model == 'flat_still' else parent,
                    segment+'-'+model, scoring, queries, training, policy) for model in MODELS]
        result = dict(segment_id=segment, source_manifest_sha256=MANIFEST,
            continuation_manifest_sha256=STAGE_MANIFEST, continuation_completion_sha256=CONTINUATION_SHA,
            completed_original=parent.summary['completed'], later_epochs=len(scoring['query_times_s']),
            fits=results, scientific_decision='abstain')
    path = root/RESULT
    raw = encoded(result)
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('the four saved forecast comparisons differ')
    print(digest(raw))


if __name__ == '__main__':
    report(Path.cwd())
