# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check one archived calibration seed for receiver-target replay without fitting."""

import argparse
from contextlib import closing
import math
from pathlib import Path

from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


PARENT = 'data/prediction-calibration-host-20261030'
FOLDER = 'docs/prediction-receiver-replay/'
SEED = 281474977610656
FIT_COUNT = 24
TRAINING_EPOCHS = 79
FORECAST_EPOCHS = 40
GENERATOR_SOURCES = (
    'analysis/lll/airquantumgrav_error_policy.py',
    'analysis/lll/airquantumgrav_weighted_controls.py',
    'analysis/lll/measurement_noise.py',
)


def receiver_path(times, truth, training, binding, *, seed):
    """Extend the seeded error process only after binding the earlier observations."""
    import numpy as np
    from .airquantumgrav_error_policy import build
    from .airquantumgrav_weighted_controls import fixture_rows
    from .measurement_noise import receiver_errors

    cut = TRAINING_EPOCHS
    count = cut + FORECAST_EPOCHS
    if (times.shape != (count,) or truth.shape != (count, 3)
            or not np.isfinite(truth).all() or len(training) != cut
            or binding['training_epochs'] != cut or binding['prediction_epochs'] != count-cut):
        raise ValueError('complete original query support and split required')
    noise = binding['noise']
    policy = noise['receiver_policy']['policy_id']
    training_hash = digest(encoded(training))
    if (noise['settings']['seed'] != seed or policy != 'reported-short-v1'
            or noise['later_receiver_positions_generated'] is not False
            or training_hash != binding['training_receiver_sha256']
            or training_hash != noise['noisy_training_receiver_sha256']
            or digest(times.astype('<f8').tobytes()) != binding['full_array_sha256']['times']):
        raise ValueError('saved seed, receiver prefix or time support differs')
    clean = fixture_rows(truth[:cut], times[:cut])
    weights = build(clean, policy_id=policy)
    if weights.source_sha256 != noise['receiver_covariance_source_sha256']:
        raise ValueError('original receiver covariance source differs')
    transforms = np.concatenate((
        weights.transforms, np.repeat(weights.transforms[-1:], count-cut, axis=0)))
    errors = receiver_errors(times, weights.spec, seed=seed,
                             maximum_epochs=count, transforms=transforms)
    reconstructed = [
        dict(row, latitude_deg=row['latitude_deg'] + math.degrees(error[0]),
             longitude_deg=row['longitude_deg'] + math.degrees(error[1]),
             height_m=row['height_m'] + error[2])
        for row, error in zip(clean, errors[:cut], strict=True)
    ]
    if (digest(errors[:cut].astype('<f8').tobytes()) != noise['receiver_coordinate_noise_sha256']
            or digest(encoded(reconstructed)) != training_hash):
        raise ValueError('seeded receiver noise or training positions did not reproduce')
    return truth[cut:] + errors[cut:]


def replay_case(study, identity):
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors

    task = study.tasks[identity]['payload']['case']
    forecast = study.artifact(identity, 'forecast.json')
    fit = study.artifact(identity, 'fit.json')
    if (study.rows[identity]['status'] != 'complete' or not fit['converged']
            or forecast['normalized_parameters'] != fit['normalized_parameters']
            or forecast['active_parameters'] != fit['active_parameters']
            or forecast['frozen_error_model'] != task['model']
            or forecast['training_epochs'] != TRAINING_EPOCHS
            or forecast['prediction_epochs'] != FORECAST_EPOCHS
            or forecast['prediction_receiver_positions_used'] is not False):
        raise ValueError('sealed, converged, earlier-only forecast required')
    times = np.asarray(forecast['times_s'], dtype=float)
    truth = np.asarray(study.artifact(identity, 'scoring-observations.json')['coordinates'])
    measured = receiver_path(
        times, truth, study.artifact(identity, 'training-receiver.json'),
        study.artifact(identity, 'input-binding.json'), seed=SEED)
    later = truth[TRAINING_EPOCHS:]
    predicted = forecast['coordinates'][TRAINING_EPOCHS:]
    rms = lambda error: float(np.sqrt(np.mean(np.sum(error**2, axis=1))))
    return dict(
        identity=identity, model=task['model'], input_law=task['law'],
        fits_own_generating_model=True, training_prefix_verified=True,
        receiver_sha256=digest(measured.astype('<f8').tobytes()),
        forecast_to_truth_3d_rms_m=rms(receiver_errors(predicted, later)),
        forecast_to_receiver_3d_rms_m=rms(receiver_errors(predicted, measured)),
        receiver_to_truth_3d_rms_m=rms(receiver_errors(measured, later)),
    )


def run(root, action):
    root = Path(root).resolve()
    with closing(ClosedStudy(root, PARENT)) as study:
        recipe = study.input('recipe')
        if (recipe['role'] != 'calibration' or recipe['seeds'][0] != SEED
                or len(recipe['seeds']) != 299 or study.completion['state'] != 'complete'
                or study.summary['completed'] != 299 * FIT_COUNT):
            raise ValueError('original complete calibration archive required')
        cases = sorted(identity for identity, task in study.tasks.items()
                       if task['payload']['draw_seed'] == SEED)
        if len(cases) != FIT_COUNT:
            raise ValueError('exact seed-family scope required')
        for name in GENERATOR_SOURCES:
            if digest((root/name).read_bytes()) != study.manifest['sources'][name]:
                raise ValueError(f'original receiver generator source differs: {name}')
        own = Path(__file__).relative_to(root).as_posix()
        sources = source_closure(root, (own, FOLDER+'README.md'))
        freeze = encoded(dict(
            source_sha256={name:digest((root/name).read_bytes()) for name in sources},
            parent=study.completion, seed=SEED, cases=cases,
            training_epochs=TRAINING_EPOCHS, forecast_epochs=FORECAST_EPOCHS,
            max_replays=FIT_COUNT, new_fits=0, new_seeds=0, threads=1,
            validation_cases=0, original_reads=0, protected_reads=0,
            environment=runtime_environment()))
        path = root/FOLDER/'freeze.json'
        if action == 'freeze':
            _write_equal(path, freeze)
            return dict(freeze_sha256=digest(freeze), cases=len(cases))
        if path.read_bytes() != freeze:
            raise ValueError('unchanged replay scope, sources and environment required')
        records = [replay_case(study, identity) for identity in cases]
    result = dict(freeze_sha256=digest(freeze), records=records, cases=len(records),
                  original_reads=0, validation_cases=0, protected_reads=0,
                  new_fits=0, new_seeds=0, calibrated=False, scientific_decision='abstain')
    _write_equal(root/FOLDER/'result.json', encoded(result))
    return {key:value for key,value in result.items() if key != 'records'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    print(run(args.root, args.action))


if __name__ == '__main__':
    main()
