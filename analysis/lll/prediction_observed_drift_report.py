# SPDX-License-Identifier: AGPL-3.0-or-later
"""Describe sealed ESA development forecast errors without another fit."""
import argparse
import gzip
import hashlib
import json
import math
import statistics
from pathlib import Path


def summarize_drift(errors_neu_m, times_s, training_epochs):
    """Describe the later error's straight-line component, without correcting it."""
    rows = errors_neu_m
    times = times_s
    cut = training_epochs
    if (type(cut) is not int or cut < 2 or len(rows) - cut < 3 or
            len(times) != len(rows) or
            any(len(row) != 3 or any(not math.isfinite(value) for value in row)
                for row in rows) or
            any(not math.isfinite(value) for value in times) or
            any(right <= left for left, right in zip(times[:-1], times[1:]))):
        raise ValueError('finite three-axis errors and strictly increasing times required')
    later_time = times[cut:]
    tail_start = times[cut-1] - 120.
    tail_first = next(index for index in range(cut)
                      if times[index] >= tail_start)
    if cut-tail_first < 2:
        raise ValueError('at least two training-tail epochs required')
    tail_time = times[tail_first:cut]
    later_time_mean = statistics.fmean(later_time)
    centered_time = [value - later_time_mean for value in later_time]
    time_ss = sum(value*value for value in centered_time)
    tail_time_mean = statistics.fmean(tail_time)
    centered_tail_time = [value-tail_time_mean for value in tail_time]
    tail_time_ss = sum(value*value for value in centered_tail_time)
    axes = {}
    for axis, name in enumerate(('north', 'east', 'up')):
        training = [row[axis] for row in rows[:cut]]
        later = [row[axis] for row in rows[cut:]]
        tail = training[tail_first:]
        tail_mean = statistics.fmean(tail)
        tail_slope = sum(t*(value-tail_mean) for t, value in
                         zip(centered_tail_time, tail)) / tail_time_ss
        mean = statistics.fmean(later)
        centered = [value - mean for value in later]
        slope = sum(t*e for t, e in zip(centered_time, centered)) / time_ss
        total_ss = sum(value*value for value in centered)
        remainder_ss = sum((e - slope*t)**2 for t, e in
                           zip(centered_time, centered))
        axes[name] = dict(
            training_rms_m=math.sqrt(statistics.fmean(v*v for v in training)),
            later_rms_m=math.sqrt(statistics.fmean(v*v for v in later)),
            later_mean_m=mean,
            later_first_m=later[0], later_last_m=later[-1],
            training_tail_epochs=len(tail),
            training_tail_slope_m_per_min=60*tail_slope,
            training_tail_extrapolated_first_m=(
                tail_mean+tail_slope*(later_time[0]-tail_time_mean)),
            training_tail_extrapolated_last_m=(
                tail_mean+tail_slope*(later_time[-1]-tail_time_mean)),
            later_slope_m_per_min=60*slope,
            later_linear_explained_fraction=(
                max(0., min(1., 1. - remainder_ss/total_ss))
                if total_ss > 0 else None))
    return dict(training_epochs=cut, prediction_epochs=len(rows)-cut,
                prediction_duration_s=later_time[-1]-later_time[0],
                axes=axes, scientific_decision='abstain')


def summarize_motion(receiver_rows, training_epochs):
    """Describe receiver-reported motion near and after the saved split."""
    rows = receiver_rows
    cut = training_epochs
    if (type(cut) is not int or cut < 2 or len(rows)-cut < 3 or
            any(any(key not in row or not math.isfinite(row[key])
                    for key in ('time_s', 'north_mps', 'east_mps', 'up_mps'))
                for row in rows) or
            any(b['time_s'] <= a['time_s'] for a, b in
                zip(rows[:-1], rows[1:]))):
        raise ValueError('finite ordered receiver motion and split required')
    tail_start = rows[cut-1]['time_s']-120.
    first = next(index for index in range(cut)
                 if rows[index]['time_s'] >= tail_start)
    if cut-first < 2:
        raise ValueError('at least two training-tail receiver epochs required')
    result = dict(training_tail_epochs=cut-first,
                  prediction_epochs=len(rows)-cut)
    for name, part in (('training_tail', rows[first:cut]),
                       ('later', rows[cut:])):
        result[name+'_mean_speed_mps'] = statistics.fmean(
            math.hypot(row['north_mps'], row['east_mps']) for row in part)
        for axis in ('north', 'east', 'up'):
            result[name+'_mean_'+axis+'_mps'] = statistics.fmean(
                row[axis+'_mps'] for row in part)
    return result


def training_handoff_discrepancy_m(forecast, receiver, native_difference):
    """Compare saved native training differences with forecast-minus-receiver."""
    import numpy as np
    from .airquantumgrav_scoring import receiver_errors
    from .models import radii

    f, g, d = (np.asarray(value, dtype=float)
               for value in (forecast, receiver, native_difference))
    if (g.ndim != 2 or not len(g) or g.shape[1:] != (3,) or
            f.shape != g.shape or d.shape != g.shape or
            not all(np.all(np.isfinite(value)) for value in (f, g, d))):
        raise ValueError('aligned finite three-axis training values required')
    rm, rn = radii(g[:, 0])
    scale = np.column_stack((rm+g[:, 2],
                             (rn+g[:, 2])*np.cos(g[:, 0]),
                             np.ones(len(g))))
    return float(np.max(np.abs(receiver_errors(f, g)-d*scale)))


def receiver_reference(times_s, receiver_coordinates, training_epochs):
    """Score fixed receiver-only rules after forecasting from training rows."""
    import numpy as np
    from .airquantumgrav_geographic_report import error_metrics
    from .airquantumgrav_scoring import receiver_errors
    from .receiver_only_forecast import forecast as linear_forecast
    from .receiver_only_geodesic import forecast_geodesic

    times = np.asarray(times_s, dtype=float)
    receiver = np.asarray(receiver_coordinates, dtype=float)
    cut = training_epochs
    if (type(cut) is not int or cut < 30 or
            receiver.shape != (len(times), 3) or len(times)-cut < 1 or
            not np.all(np.isfinite(times)) or
            not np.all(np.isfinite(receiver)) or
            np.any(np.diff(times) <= 0)):
        raise ValueError('aligned earlier and later receiver positions required')
    result = {}
    for name, rule in (('linear', linear_forecast),
                       ('geodesic', forecast_geodesic)):
        forecast = rule(times[:cut], receiver[:cut], times[cut:])
        if (forecast['later_positions_used'] is not False or
                forecast['imu_samples_used'] != 0):
            raise ValueError('receiver rule used a later position or IMU')
        error = receiver_errors(forecast['coordinates'], receiver[cut:])
        metrics = error_metrics(error.tolist())
        metrics.update(
            maximum_horizontal_m=float(np.max(np.linalg.norm(
                error[:, :2], axis=1))),
            maximum_absolute_up_m=float(np.max(np.abs(error[:, 2]))),
            north_east_up_velocity_mps=(
                forecast['north_east_up_velocity_mps'].tolist()),
            training_window_points=forecast['training_window_points'],
            later_positions_used_for_forecast=False,
            imu_samples_used=0)
        result[name] = metrics
    return result


def compare_generated_reference(rows, *, observed_training_m, observed_later_m):
    """Compare physical error scales from a fixed generated matrix and observation."""
    if (len(rows) != 24 or
            not all(row.get('converged') is True for row in rows) or
            any(not math.isfinite(value) or value < 0 for value in
                (observed_training_m, observed_later_m))):
        raise ValueError('24 converged generated cases and finite observed errors required')
    result = dict(generated_cases=24, observed_training_horizontal_rms_m=observed_training_m,
                  observed_later_horizontal_rms_m=observed_later_m)
    for section, key in (('training', 'training_horizontal_rms_m'),
                         ('prediction', 'later_horizontal_rms_m')):
        values = [row[section]['horizontal_rms_m'] for row in rows]
        passed = [row[section]['accuracy']['passed'] for row in rows]
        if (any(not math.isfinite(value) or value < 0 for value in values) or
                any(type(flag) is not bool for flag in passed)):
            raise ValueError('finite generated scores and explicit accuracy flags required')
        result[key] = dict(minimum=min(values), median=statistics.median(values),
                           maximum=max(values))
        result[('training' if section == 'training' else 'later')+
               '_accuracy_passed'] = sum(passed)
    result['observed_training_exceeds_generated_max'] = (
        observed_training_m > result['training_horizontal_rms_m']['maximum'])
    result['observed_later_exceeds_generated_max'] = (
        observed_later_m > result['later_horizontal_rms_m']['maximum'])
    return result


def build(root):
    """Bind the completed continuation and reopen only its saved inputs."""
    from .airquantumgrav_scoring import receiver_errors
    from .prediction_observed_continuation_report import summarize
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy
    import numpy as np

    root = Path(root).resolve()
    study = ClosedStudy(root,
                        'data/prediction-observed-development-continuation-v1-20261113')
    try:
        if (study.completion['manifest_sha256'] !=
                '2dbbd77362e7d21cad709f0a1001173ac99b44c3ea30e7021b6ce513de1e9788'
                or study.completion['summary_sha256'] !=
                '1add15ded2e8c72e204dee11086833ebaea9b6c4c0a8e69d1fa82be4f2b5bc6d'):
            raise ValueError('unexpected sealed continuation identity')
        identity = 'esa-187-no-refit'
        verified = summarize(study, identity=identity,
                             group_id='esa-99f1530c3eda4318',
                             training_epochs=800, prediction_epochs=400)
        rows = json.loads(gzip.decompress(study.input('scoring', raw=True)))
        training = json.loads(gzip.decompress(study.input('training', raw=True)))
        score = study.artifact(identity, 'withheld-receiver-score.json')
        if (len(rows) != 1200 or len(training) != 800 or
                encoded(rows[:800]) != encoded(training) or
                digest(encoded(rows)) != score['withheld_receiver_sha256']):
            raise ValueError('saved receiver rows disagree with sealed score')
        receiver = np.asarray([[math.radians(row['latitude_deg']),
                                math.radians(row['longitude_deg']), row['height_m']]
                               for row in rows], dtype=float)
        laws = {}
        for law in ('increment', 'point'):
            forecast = study.input('saved-'+law+'-forecast')
            if (forecast['training_epochs'] != 800 or
                    forecast['prediction_epochs'] != 400 or
                    forecast['frozen_error_model'] != 'sphere_rotating' or
                    len(forecast['times_s']) != 1200 or
                    len(forecast['coordinates']) != 1200):
                raise ValueError('saved forecast split or law changed')
            times = forecast['times_s']
            origin = rows[0]['time_s'] - times[0]
            if any(not math.isclose(row['time_s']-origin, t,
                                    rel_tol=0., abs_tol=1e-6)
                   for row, t in zip(rows, times)):
                raise ValueError('saved forecast and receiver times disagree')
            errors = receiver_errors(forecast['coordinates'], receiver)
            report = summarize_drift(errors.tolist(), times, 800)
            report['training_handoff_max_discrepancy_m'] = (
                training_handoff_discrepancy_m(
                    forecast['coordinates'][:800], receiver[:800],
                    forecast['training_coordinate_difference']))
            for section, key in (('training', 'training_rms_m'),
                                 ('prediction', 'later_rms_m')):
                observed = score['candidate_receiver_sections'][law][section]['rms_neu_m']
                if any(not math.isclose(report['axes'][axis][key], observed[index],
                                        rel_tol=1e-9, abs_tol=1e-7)
                       for index, axis in enumerate(('north', 'east', 'up'))):
                    raise ValueError('recomputed error disagrees with sealed score')
            laws[law] = report
        generated = ClosedStudy(root, 'docs/esa-noisy-prediction')
        try:
            if (generated.completion['manifest_sha256'] !=
                    'bbcab9c01d94ba36269cda087cf8cf4629df6c559174b136ad5b1e2fdbde9f7f'
                    or generated.completion['summary_sha256'] !=
                    '5eeacd812ae7d3678068175d116ff24d36ee597be2ffdfc8967e5e9f89123699'
                    or generated.summary['total'] != 24 or
                    generated.summary['completed'] != 24):
                raise ValueError('unexpected sealed generated ESA matrix')
            generated_rows = [generated.envelope(identity)['result']
                              for identity in generated.tasks]
            generated_reference = compare_generated_reference(
                generated_rows,
                observed_training_m=score['candidate_receiver_sections'][
                    'increment']['training']['horizontal_rms_m'],
                observed_later_m=score['candidate_receiver_sections'][
                    'increment']['prediction']['horizontal_rms_m'])
            generated_reference.update(
                study=generated.prefix,
                manifest_sha256=generated.completion['manifest_sha256'],
                summary_sha256=generated.completion['summary_sha256'],
                synthetic_noise_is_measured_hardware=False)
        finally:
            generated.close()
        return dict(source_study=study.prefix,
                    manifest_sha256=verified['manifest_sha256'],
                    summary_sha256=verified['summary_sha256'],
                    scoring_sha256=study.manifest['inputs']['scoring']['sha256'],
                    reporter_sha256=hashlib.sha256(
                        (root/'analysis/lll/prediction_observed_drift_report.py').read_bytes()
                    ).hexdigest(),
                    receiver_reference_plan_sha256=hashlib.sha256(
                        (root/'docs/prediction-observed-development/RECEIVER_REFERENCE_PLAN.md').read_bytes()
                    ).hexdigest(),
                    receiver_reference_source_sha256={name: hashlib.sha256(
                        (root/'analysis/lll'/name).read_bytes()).hexdigest()
                        for name in ('receiver_only_forecast.py',
                                     'receiver_only_geodesic.py')},
                    laws=laws, receiver_motion=summarize_motion(rows, 800),
                    receiver_reference=receiver_reference(
                        study.input('saved-increment-forecast')['times_s'],
                        receiver, 800),
                    generated_reference=generated_reference,
                    native_calls=0, refits=0,
                    protected_reads=0, scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    result = build(args.root)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({law: result['laws'][law]['axes']['east']
                      for law in ('increment', 'point')}, sort_keys=True))


if __name__ == '__main__':
    main()
