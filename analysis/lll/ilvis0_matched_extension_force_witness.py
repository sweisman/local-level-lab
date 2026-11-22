# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay force gaps and fixed forecasts after one common GPS perturbation."""

import argparse
from contextlib import ExitStack, closing
import gzip
import io
import json
import math
from pathlib import Path

from . import ilvis0_matched_extension_force as force
from .ilvis0_gps_force_comparison import support as gps_support
from .ilvis0_matched_force_covariance import SHARED_SIGMA, TAU_S, WHITE_SIGMA, mean_gradient
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-matched-extension-force-witness-v1'
FOLDER = force.aligned.shared.FOLDER
PLAN = FOLDER+'MATCHED_EXTENSION_FORCE_WITNESS_PLAN.md'
REQUEST = FOLDER+'matched-extension-force-witness-qualification.json'
TEST_REPORT = FOLDER+'matched-extension-force-witness-tests.xml'
RESULT = FOLDER+'matched-extension-force-witness-result.json'
TEST = 'analysis/tests/test_ilvis0_matched_extension_force_witness.py'
TESTS = ('test_force_witness_keeps_the_training_gain_in_the_gap',
         'test_force_witness_uses_one_shared_local_shift_at_each_epoch')
SCOPE = 'one common GPS correction on the added IMU8 force and forecast comparisons'
SEGMENT = 'b365bdf39150ee6afc303ac1'
FORCE_SHA = '883f2f119ba52104992f8f46254d0816281b56a2fd48f6fe7c8946b90e704771'
FORECAST_SHA = '8531eaaff881b6a14db2a3299a3048e5d65b4f143e9fc8ce81d418b5036a1918'
MAX_GRADIENTS, MAX_STEPS, ENVELOPES, FORECAST_CHECKS = 96, 128, 12600, 12
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=4,
    bound_steps=MAX_GRADIENTS+MAX_STEPS+ENVELOPES*force.average.SUBDIVISIONS+FORECAST_CHECKS)
RECOVERY = dict(force.RECOVERY_POLICY, max_technical_interruptions=1, maximum_wall_s=600)


def force_deficit(row, gain):
    return row['measured_lower_mps2']/(1.+gain)-math.nextafter(row['required_upper_mps2'], math.inf)


def corrected_tracks(tracks, metrics, correction):
    return {name: coords + correction/metrics[name] for name, coords in tracks.items()}


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))


def request(root):
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=force.aligned.shared.runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def prepare(root):
    import numpy as np

    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('retain the existing correction study allowance')
    environment, deps = force.aligned.shared.runtime_environment(), sources(root)
    qualification, tests = checked(root, REQUEST, sources=deps, environment=environment,
                                   required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, force.aligned.gps.RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    choices = ((force.ID, force.RESULT, FORCE_SHA), (force.forecast.ID, force.forecast.RECEIPT, FORECAST_SHA))
    with ExitStack() as stack:
        studies, reports = [], []
        for identity, path, expected in choices:
            raw = (root/path).read_bytes()
            if digest(raw) != expected:
                raise ValueError('unchanged force and forecast comparison reports are required')
            study = stack.enter_context(closing(ClosedStudy(root, 'data/'+identity,
                store=studies[0].store if studies else None)))
            report = json.loads(raw)
            if not study.summary['passed'] or any(report[key] != value for key, value in study.completion.items()):
                raise ValueError('each parent comparison must be sealed and verified')
            studies.append(study)
            reports.append(report)
        scalar, fitted = studies
        gains = {model: row['training_gain'] for model, row in scalar.artifact(SEGMENT, 'summary.json')['by_model'].items()}
        windows = scalar.artifact(SEGMENT, 'windows.json.gz', raw=True)
        training, later = (fitted.input(SEGMENT+'-'+name) for name in ('training', 'scoring'))
        trajectories = {model: fitted.artifact(SEGMENT+'-'+model, 'forecast.json')
                        for model in force.average.MATCHED_MODELS}
        packets = np.load(io.BytesIO(gzip.decompress(fitted.input(SEGMENT+'-packets', raw=True))), allow_pickle=False)
        before, = [row for row in reports[1]['comparisons'] if row['segment_id'] == SEGMENT]
        if packets.shape != (117080, 15) or len(training['query_times_s']) != 390 or len(later['query_times_s']) != 195:
            raise ValueError('the recorded IMU8 window and training split must remain fixed')
        recorded = dict(gains=gains, elapsed=packets[:, 2].tolist(), training=training, later=later,
            forecasts=trajectories, prior_ranks={k: before[k] for k in ('shape_by_field', 'globe_field')})
    inputs = dict(plan=PLAN, force_receipt=force.RESULT, forecast_receipt=force.forecast.RECEIPT)
    staged = dict(qualification=qualification, qualification_tests=tests, recovery=recovery,
        recovery_tests=recovery_tests, recovery_policy=encoded(RECOVERY), force_windows=windows,
        recorded=gzip.compress(encoded(recorded), mtime=0))
    for key, raw in staged.items():
        path = f'data/{ID}-inputs/{key}'
        force.aligned.shared._write_equal(root/path, raw)
        inputs[key] = path
    task = dict(identity=SEGMENT, input_key='recorded', limits=LIMITS)
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, tasks=[task], sources=deps,
        adapter=Path(__file__).relative_to(root).as_posix(), workers=1, threads=1, maximum_wall_s=300.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def _problem(recorded, details):
    import numpy as np

    average = force.average
    training, later = recorded['training'], recorded['later']
    times = np.array(training['query_times_s']+later['query_times_s'])
    tags = np.array(training['gps_tags_ms']+later['gps_tags_ms'])
    cut = len(training['query_times_s'])
    elapsed = np.asarray(recorded['elapsed'])
    ends = dict(zip(average.support.CLOCKS, (np.cumsum(np.full(len(elapsed), .005)), np.cumsum(elapsed)), strict=True))
    coords = {key: np.array(training['coordinates'][key]+later['coordinates'][key]) for key in average.TRACKS}
    by_window = {}
    for index, window in enumerate(details['windows']):
        tag = window['gps_millisecond_tag']
        if tags[index] != tag:
            raise ValueError('force windows changed their target order')
        if window['state'] != 'supported':
            continue
        state, start, stop = gps_support(tags, tag, average.support.HALF_WINDOW_S)
        if (state != 'evaluated' or not start <= index < stop or start < cut < stop
                or window['side'] != ('training' if stop <= cut else 'later')):
            raise ValueError('force windows must stay on their original side of the cut')
        packets = slice(window['packet_first'], window['packet_stop'])
        intervals = {key: average.checked_interval(value, packets, (times[start], times[stop-1]),
                     average.support.TIME_OFFSET_S, times[index]) for key, value in ends.items()}
        by_window[tag] = (slice(start, stop), average.quadratic_weights((tags[start:stop]-tag)/1000.), intervals)
    return times, cut, coords, by_window


def evaluate(task, context):
    import numpy as np

    from .ilvis0_error_model import Spec
    from .ilvis0_shared_force_witness import project_witness
    from .ilvis0_solver_position import physical_metric
    from .ilvis0_structured_force_projection import covariance_action

    if context.manifest['scope'] != SCOPE or task['identity'] != SEGMENT or task['limits'] != LIMITS:
        raise ValueError('only the fixed IMU8 correction comparison is authorized')
    raw = lambda path: json.loads(gzip.decompress(path.read_bytes()))
    recorded = raw(context.input_path())
    details = raw(context.input_path('force_windows'))
    times, cut, tracks, windows = _problem(recorded, details)
    rows = details['comparisons']
    if len(rows) != ENVELOPES:
        raise ValueError('all original sealed inequalities are required')
    gains = recorded['gains']
    active = [row for row in rows if force_deficit(row, gains[row['model']]) > 0.]
    if len(active) != 79 or len(active) > MAX_GRADIENTS:
        raise ValueError('the saved positive force deficits must be preserved')
    metrics = {key: physical_metric(coords) for key, coords in tracks.items()}
    shared = np.diag(np.square(SHARED_SIGMA))
    law = Spec(np.diag(np.square(WHITE_SIGMA)), ((TAU_S, shared),), shared, shared, times[0], times[-1]-times[0])
    average = force.average

    def material(row, coordinates):
        model, track = row['model'], row['gps_stream']
        support, weights, intervals = windows[row['gps_millisecond_tag']]
        local = coordinates[track][support].copy()
        local[:, 1] = np.unwrap(local[:, 1])
        settings = dict(model=model, background_rate_rads=average.rate(model),
                        gravity_mps2=average.GRAVITY, disc_radius_m=average.RADIUS)
        return track, support, weights, weights @ local, intervals[row['clock']], settings

    context.charge(bound_calls=1, bound_steps=MAX_GRADIENTS)
    matrix = np.zeros((len(active), len(times), 3))
    proposal, variances = [], []
    for index, row in enumerate(active):
        track, support, weights, jet, interval, settings = material(row, tracks)
        derivative = mean_gradient(jet, interval, **settings)
        matrix[index, support] = (weights.T @ derivative)/metrics[track][support]
        moved = covariance_action(times, law, matrix[index, :, :, None])[:, :, 0]
        variances.append(float(np.sum(matrix[index]*moved)))
        proposal.append(force_deficit(row, gains[row['model']])+1e-5)
    context.charge(bound_calls=1, bound_steps=MAX_STEPS)
    witness = project_witness(times, law, matrix.reshape(len(active), -1), proposal,
                              np.sqrt(variances), maximum_steps=MAX_STEPS)
    correction = witness.pop('error_m').reshape((-1, 3))
    changed = corrected_tracks(tracks, metrics, correction)
    context.charge(bound_calls=1, bound_steps=ENVELOPES*average.SUBDIVISIONS)
    gaps = []
    offset = average.support.TIME_OFFSET_S
    for row in rows:
        _, _, _, jet, interval, settings = material(row, changed)
        lower, upper = average.bound_average(jet, interval, offset_bounds_s=(-offset, offset),
                                             subdivisions=average.SUBDIVISIONS, **settings)
        model = row['model']
        measured = row['measured_lower_mps2']/(1.+gains[model])
        gaps.append(dict(model=model, track=row['gps_stream'], clock=row['clock'], side=row['side'],
            gps_millisecond_tag=row['gps_millisecond_tag'], before_mps2=force_deficit(row, gains[model]),
            after_mps2=measured-math.nextafter(upper, math.inf),
            stronger_mps2=measured-math.nextafter(lower, math.inf)))
    context.charge(bound_calls=1, bound_steps=FORECAST_CHECKS)
    scores = {}
    if len(recorded['forecasts'])*len(changed) != FORECAST_CHECKS:
        raise ValueError('every original forecast and GPS track must be scored')
    for model, path in recorded['forecasts'].items():
        if path['query_times_s'] != times.tolist() or path['training_epochs'] != cut or path['later_positions_used']:
            raise ValueError('the original saved forecast and split are required')
        predicted = np.asarray(path['coordinates'][cut:])
        scores[model] = dict(heldout_rms_by_gps_stream={})
        for key, coords in changed.items():
            error = (predicted-coords[cut:])*physical_metric(coords[cut:])
            scores[model]['heldout_rms_by_gps_stream'][key] = dict(
                horizontal_rms_m=float(np.sqrt(np.mean(np.sum(error[:, :2]**2, axis=1)))),
                height_rms_m=float(np.sqrt(np.mean(error[:, 2]**2))))
    changed_scores = force.forecast.compare_shapes(scores)
    result = dict(passed=True, initial_gaps=len(active), remaining_gaps=sum(row['after_mps2'] > 0. for row in gaps),
        remaining_stronger_gaps=sum(row['stronger_mps2'] > 0. for row in gaps),
        maximum_position_correction_m=float(np.linalg.norm(correction, axis=1).max()),
        rankings_preserved=all(changed_scores[key] == value for key, value in recorded['prior_ranks'].items()),
        recomputed_forecast_scores=changed_scores, projection=witness, scientific_decision='abstain')
    context.save('receiver-correction.json', dict(times_s=times.tolist(), local_neu_m=correction.tolist()))
    context.save_bytes('inequalities.json.gz', gzip.compress(encoded(gaps), mtime=0))
    context.save_bytes('comparison.json', encoded(result))
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(SEGMENT)
        result = envelope['result']
        if result['passed']:
            if result != study.artifact(SEGMENT, 'comparison.json') or envelope['charged'] != LIMITS:
                raise ValueError('comparison does not match the sealed result and charges')
            study.artifact(SEGMENT, 'receiver-correction.json', raw=True)
            study.artifact(SEGMENT, 'inequalities.json.gz', raw=True)
        raw = encoded(dict(study.completion, result=result, charged=envelope['charged'], new_fits=0))
    force.aligned.shared._write_equal(root/RESULT, raw)
    return dict(result_sha256=digest(raw), passed=result['passed'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    print(json.dumps({'request': request, 'prepare': prepare, 'report': report}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
