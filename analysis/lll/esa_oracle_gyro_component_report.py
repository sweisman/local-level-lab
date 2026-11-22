# SPDX-License-Identifier: AGPL-3.0-or-later
"""Recompute saved future errors for the sealed gyro white/bias forecasts."""

import argparse
import hashlib
import json
import math
from pathlib import Path


def compare_components(white, bias, gyro):
    values = [row['horizontal_rms_m'] for row in (white, bias, gyro)]
    if any(not isinstance(value, (int, float)) or
           not math.isfinite(value) or value < 0 for value in values):
        raise ValueError('finite nonnegative future errors required')
    return dict(larger_single_component=(
        'white' if values[0] > values[1] else
        'bias' if values[1] > values[0] else 'tie'),
        white_to_bias_horizontal_rms_ratio=(
            values[0] / values[1] if values[1] else None),
        combined_gyro_horizontal_rms_m=values[2],
        additive_error_assumption_made=False)


def horizontal_alignment(white_errors, bias_errors):
    import numpy as np
    white = np.asarray(white_errors, float)
    bias = np.asarray(bias_errors, float)
    if (white.shape != bias.shape or white.ndim != 2 or
            white.shape[1] != 3 or not np.all(np.isfinite(white)) or
            not np.all(np.isfinite(bias))):
        raise ValueError('matched finite north/east/up errors required')
    a, b = white[:, :2], bias[:, :2]
    energy_a, energy_b = float(np.sum(a*a)), float(np.sum(b*b))
    if energy_a <= 0 or energy_b <= 0:
        raise ValueError('nonzero horizontal errors required')
    return float(np.sum(a*b) / math.sqrt(energy_a*energy_b))


def build(root):
    import numpy as np
    from .airquantumgrav_observation_truth import receiver_samples
    from .esa_fit_adjusted_forecast_report import position_errors_neu, _metrics
    from .esa_oracle_channel_report import build as channel_build
    from .esa_oracle_gyro_component_study import ID, SCOPE, LAWS, COMPONENTS
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    channel = channel_build(root)
    study = ClosedStudy(root, 'data/' + ID)
    try:
        identities = {law + '-' + component for law in LAWS
                      for component in COMPONENTS}
        if (study.completion['state'] != 'complete' or
                study.summary['completed'] != 4 or
                study.manifest['scope'] != SCOPE or
                set(study.tasks) != identities or set(study.rows) != identities or
                any(study.manifest['sources'].get(name) != hashlib.sha256(
                    (root / name).read_bytes()).hexdigest() for name in (
                        'analysis/lll/airquantumgrav_truth.py',
                        'analysis/lll/airquantumgrav_observation_truth.py',
                        'analysis/lll/esa_oracle_control.py'))):
            raise ValueError('complete source-matched gyro component study required')
        binding = study.input('binding')
        if binding['channel_manifest_sha256'] != channel['study_manifest_sha256']:
            raise ValueError('gyro component parent differs')
        cases = {}
        for law in LAWS:
            scores, errors_by_component = {}, {}
            for component in COMPONENTS:
                identity = law + '-' + component
                result = study.envelope(identity)['result']
                record = study.artifact(identity, 'component-forecast.json')
                if (result['passed'] is not True or
                        result['scientific_decision'] != 'abstain' or
                        result['law'] != law or
                        result['gyro_component'] != component or
                        record['law'] != law or
                        record['gyro_component'] != component or
                        record['future_receiver_positions_used_to_forecast'] is not False or
                        record['later_truth_used_for_scoring_only'] is not True or
                        record['original_reads'] != 0 or
                        record['protected_reads'] != 0):
                    raise ValueError('unchanged sealed component result required')
                times = np.asarray(record['times_s'], float)
                forecast = np.asarray(record['coordinates'], float)
                if (times.shape != (900,) or forecast.shape != (900, 3) or
                        not np.array_equal(times, .5 + np.arange(900.))):
                    raise ValueError('complete matched component grid required')
                truth = receiver_samples('sphere_rotating', times[600:],
                    latitude_deg=55., pattern='fast', removal=0., sign=1,
                    height_profile='climb', gravity_model='inverse_square_height')
                errors = position_errors_neu(
                    forecast[600:], truth['coordinates'])
                score = _metrics(errors)
                if any(not math.isclose(score[key], source[key],
                        rel_tol=1e-12, abs_tol=1e-9)
                        for source in (record['future_metrics'],
                                       result['future_metrics'])
                        for key in ('horizontal_rms_m', 'vertical_rms_m')):
                    raise ValueError('recomputed component score differs')
                scores[component] = score
                errors_by_component[component] = errors
            gyro = channel['cases'][law]['single_channel']['gyro']
            cases[law] = dict(components=scores, both_gyro_components=gyro,
                comparison=compare_components(scores['white'], scores['bias'], gyro),
                white_bias_horizontal_error_cosine=horizontal_alignment(
                    errors_by_component['white'], errors_by_component['bias']))
        return dict(version='esa-oracle-gyro-component-report-v1',
            study='data/' + ID,
            study_manifest_sha256=study.completion['manifest_sha256'],
            study_summary_sha256=study.completion['summary_sha256'],
            channel_study_manifest_sha256=channel['study_manifest_sha256'],
            report_source_sha256=hashlib.sha256((root /
                'analysis/lll/esa_oracle_gyro_component_report.py').read_bytes()).hexdigest(),
            cases=cases, native_forecast_calls=4, original_reads=0,
            protected_confirmation_groups_opened=0,
            scientific_decision='abstain', uncertainty_calibrated=False)
    finally:
        study.close()


def publish(root):
    from .studies.artifacts import atomic, encoded
    root = Path(root).resolve()
    report = build(root)
    base = root / 'docs/prediction-observed-development'
    atomic(base / 'ORACLE_GYRO_COMPONENT_REPORT.json', encoded(report))
    rows = []
    for law in ('increment', 'point'):
        case = report['cases'][law]
        for label, score in (('white gyro noise', case['components']['white']),
                             ('changing gyro bias', case['components']['bias']),
                             ('both gyro components', case['both_gyro_components'])):
            rows.append('| {} | {} | {:.2f} | {:.2f} |'.format(
                law, label, score['horizontal_rms_m'], score['vertical_rms_m']))
    cosines = ', '.join('{}: {:.3f}'.format(law, report['cases'][law][
        'white_bias_horizontal_error_cosine']) for law in ('increment', 'point'))
    page = ('# Which gyro error component drives the generated drift?\n\n'
        'Four sealed forecasts separately retained the original white gyro '
        'noise or changing gyro bias. Accelerometer increments, initial state '
        'and calibration were kept exact. The increment law adds errors to '
        'each sample interval; the point law adds errors to sampled rates '
        'before they are integrated. Later truth scored the future '
        'predictions; it did not enter them.\n\n'
        '| Error law | Gyro error | Future horizontal RMS (m) | Future vertical RMS (m) |\n'
        '| --- | --- | ---: | ---: |\n' + '\n'.join(rows) + '\n\n'
        'The signed horizontal error directions have white/bias cosine '
        + cosines + '. A negative value means their separate errors tend to '
        'oppose each other over the future interval. These are two fixed '
        'synthetic noise draws. The combined error need not equal the sum '
        'of the separate errors. This comparison does not '
        'identify the error process in a recorded aircraft IMU or qualify '
        'prediction uncertainty. No reserved confirmation group was opened.\n\n'
        'See the [full channel comparison](ORACLE_CHANNEL_REPORT.md) and '
        '[machine-readable scores](ORACLE_GYRO_COMPONENT_REPORT.json).\n')
    atomic(base / 'ORACLE_GYRO_COMPONENT_REPORT.md', page.encode())
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    report = publish(args.root)
    print(json.dumps({law: report['cases'][law]['comparison']
                      for law in ('increment', 'point')}, sort_keys=True))


if __name__ == '__main__':
    main()
