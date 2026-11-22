# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check whether one whole-path error scale transfers between saved ESA windows."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path

from .esa_repeat_turn_execution import LAWS, LATER, TRAIN, WINDOWS
from .studies.artifacts import atomic, digest, encoded


BASE = 'docs/prediction-observed-development/'
EVIDENCE = BASE+'esa-repeat-turn-forecast-evidence/'
RESULT = BASE+'esa-repeat-turn-scale-diagnostic.json'
TRAINING_RESULT = BASE+'esa-repeat-turn-training-scale-diagnostic.json'
PROFILE_RESULT = BASE+'esa-repeat-turn-covariance-shape-diagnostic.json'
RELEASE_SHA = '6607441aa0ae1cf43ae263a39eb4240e552d447ffe7b4a5774995cd8fe96fd3e'
SCORES_SHA = 'ae1fa59746e4f57cb539595afbde23d71899a7fdde73af438976c82daf3d988e'
ARMS = ('native', 'steady', 'turn', 'both')


def score_change(energy, scale, coordinates):
    return .5*(energy/scale - energy + coordinates*math.log(scale))


def leave_one_out(energies, *, coordinates):
    from .esa_rolling_scale_transfer import transfer

    if len(energies) != 4:
        raise ValueError('exactly four development windows required')
    findings = []
    for window, energy in sorted(energies.items()):
        others = sorted(i for i in energies if i != window)
        training_energy = math.fsum(energies[i] for i in others) / len(others)
        fitted = transfer(training_energy, energy, coordinates=coordinates)
        scale = fitted['earlier_variance_multiplier']
        findings.append(dict(window=window, fitting_windows=others, variance_multiplier=scale,
            original_mean_squared_standardized_error=energy/coordinates,
            mean_squared_standardized_error=fitted['later_to_earlier_variance_ratio'],
            negative_log_score_change=score_change(energy, scale, coordinates)))
    return findings


def verified_scores(root):
    release_raw = (root/EVIDENCE/'receiver-release.json').read_bytes()
    score_raw = (root/EVIDENCE/'receiver-scores.json').read_bytes()
    if (digest(release_raw), digest(score_raw)) != (RELEASE_SHA, SCORES_SHA):
        raise ValueError('exact verified repeat-turn score and release receipts required')
    release, saved = map(json.loads, (release_raw, score_raw))
    selected = {(row['first_index'], row['law']): row for row in release['primary']}
    scores = saved['scores']
    if (saved['release_sha256'] != RELEASE_SHA or len(release['primary']) != 8
            or set(selected) != {(i, law) for i in WINDOWS for law in LAWS}
            or set(scores) != {row['identity'] for row in selected.values()}):
        raise ValueError('all eight bound primary forecasts required')
    for (index, law), row in selected.items():
        scored = scores[row['identity']]
        if (row['state'] != 'sealed' or scored['forecast_sha256'] != row['forecast_sha256']
                or scored['law'] != law or set(scored['scores']) != set(ARMS)):
            raise ValueError('saved path score differs from the released forecast')
    return release, selected, scores


def analyze(root):
    _, selected, scores = verified_scores(root)
    energies = {law: {arm: {} for arm in ARMS} for law in LAWS}
    for (index, law), row in selected.items():
        scored = scores[row['identity']]
        for arm in ARMS:
            energies[law][arm][index] = scored['scores'][arm]['quadratic']
    comparisons = {law: {arm: leave_one_out(windows, coordinates=3*LATER)
                         for arm, windows in arms.items()} for law, arms in energies.items()}
    return dict(version='esa-repeat-turn-leave-one-window-out-v1',
                release_sha256=RELEASE_SHA, scores_sha256=SCORES_SHA,
                retrospection='same development recording; one window omitted from each variance estimate',
                coordinates_per_window=3*LATER, comparisons=comparisons,
                aircraft_fits=0, original_reads=0, protected_reads=0, scientific_decision='abstain')


def training_scale(*, training_energy, training_coordinates, active_parameters,
                   forecast_energy, forecast_coordinates, fixed_native_variance):
    if (type(training_coordinates) is not int or type(active_parameters) is not int
            or not 0 <= active_parameters < training_coordinates
            or type(forecast_coordinates) is not int or forecast_coordinates < 1
            or not all(math.isfinite(x) for x in (training_energy, forecast_energy, fixed_native_variance))
            or training_energy <= 0. or forecast_energy < 0. or fixed_native_variance <= 0.):
        raise ValueError('valid fixed native variance and complete training and forecast energies required')
    result = dict(fixed_native_variance=fixed_native_variance,
                  reference_mean_squared_standardized_error=forecast_energy/forecast_coordinates)
    for name, count in (('training_only', training_coordinates),
                        ('subtract_fitted_parameters', training_coordinates-active_parameters)):
        variance = training_energy/count
        scale = variance/fixed_native_variance
        result[name] = dict(native_variance=variance, ratio_to_fixed_variance=scale,
            mean_squared_standardized_error=forecast_energy/(scale*forecast_coordinates),
            negative_log_score_change=score_change(forecast_energy, scale, forecast_coordinates))
    return result


def analyze_training(root):
    from .esa_repeat_turn_execution_v2 import ID
    from .esa_repeat_turn_scoring import NATIVE_VARIANCE
    from .studies.closed import ClosedStudy

    release, selected, scores = verified_scores(root)
    run = 'data/'+ID
    findings = []
    with closing(ClosedStudy(root, EVIDENCE+'runtime')) as study:
        if (study.completion['manifest_sha256'] != release['manifest_sha256']
                or digest(encoded(study.completion)) != release['closures'][run]
                or release['recovery_sha256'] is not None
                or study.summary['completed'] != 16 or study.summary['passed'] is not True):
            raise ValueError('exact completed repeat-turn archive required')
        for (index, law), row in selected.items():
            identity = row['identity']
            envelope = study.envelope(identity)
            fit = study.artifact(identity, 'fit.json')
            proof = study.artifact(identity, 'training-prefix-replay.json')
            metric = fit['gaussian_training_score']
            if (envelope['result_sha256'] != release['outcomes'][identity]['result_sha256']
                    or fit['converged'] is not True or proof['replay_passed'] is not True
                    or metric['row_count'] != 3*TRAIN or len(fit['active_parameters']) != 27
                    or metric['residual_sum_squares'] != row['training_cost']):
                raise ValueError('archived training energy differs from its released fit')
            energy = scores[identity]['scores']['native']['quadratic']
            result = training_scale(training_energy=metric['residual_sum_squares'],
                training_coordinates=metric['row_count'], active_parameters=len(fit['active_parameters']),
                forecast_energy=energy, forecast_coordinates=3*LATER, fixed_native_variance=NATIVE_VARIANCE[law])
            findings.append(dict(window=index, law=law, identity=identity,
                training_energy=metric['residual_sum_squares'], forecast_native_energy=energy, **result))
    return dict(version='esa-repeat-turn-training-scale-v1', release_sha256=RELEASE_SHA,
                scores_sha256=SCORES_SHA, rows=findings, aircraft_fits=0, original_reads=0,
                protected_reads=0, scientific_decision='abstain')


def profile_variance(*, energy, negative_log_score, coordinates):
    if (type(coordinates) is not int or coordinates < 1 or not math.isfinite(energy)
            or energy <= 0. or not math.isfinite(negative_log_score)):
        raise ValueError('positive energy and finite Gaussian score required')
    scale = energy/coordinates
    return dict(variance_multiplier=scale, profiled_negative_log_score=
                negative_log_score+score_change(energy, scale, coordinates))


def analyze_shape(root):
    _, selected, scores = verified_scores(root)
    rows = []
    for (index, law), row in selected.items():
        identity = row['identity']
        arms = {name: profile_variance(energy=details['quadratic'],
                    negative_log_score=details['negative_log_score'], coordinates=3*LATER)
                for name, details in scores[identity]['scores'].items()}
        native = arms['native']['profiled_negative_log_score']
        changes = {name: arm['profiled_negative_log_score']-native for name, arm in arms.items()}
        rows.append(dict(window=index, law=law, identity=identity, arms=arms,
                         change_from_native=changes, best_arm=min(ARMS, key=changes.__getitem__)))
    return dict(version='esa-repeat-turn-profiled-shape-v1', release_sha256=RELEASE_SHA,
                scores_sha256=SCORES_SHA, rows=rows, scale_fitted_on_scored_window=True,
                aircraft_fits=0, original_reads=0, protected_reads=0, scientific_decision='abstain')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--training', action='store_true', help='use each matching archived training prefix')
    mode.add_argument('--profile', action='store_true', help='remove uniform scale when comparing covariance shapes')
    args = parser.parse_args()
    root = Path.cwd()
    if args.training:
        results, target, count = analyze_training(root), TRAINING_RESULT, 8
    elif args.profile:
        results, target, count = analyze_shape(root), PROFILE_RESULT, 32
    else:
        results, target, count = analyze(root), RESULT, 32
    raw = encoded(results)
    path = root/target
    if path.is_file():
        if path.read_bytes() != raw:
            raise ValueError('saved scale diagnostic differs from regenerated evidence')
    else:
        atomic(path, raw)
    print(json.dumps(dict(results=target, sha256=digest(raw), comparisons=count), sort_keys=True))
