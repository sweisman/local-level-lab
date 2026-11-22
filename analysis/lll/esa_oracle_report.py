# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hash-checked, saved-only known-calibration forecast comparison."""

import argparse
import hashlib
import json
import math
from pathlib import Path


def compare_scores(oracle, fitted):
    values = (oracle['horizontal_rms_m'],oracle['vertical_rms_m'],
              fitted['horizontal_rms_m'],fitted['vertical_rms_m'])
    if any(not isinstance(v,(int,float)) or not math.isfinite(v) or v < 0
           for v in values) or fitted['horizontal_rms_m'] == 0:
        raise ValueError('complete finite matched forecast scores required')
    return dict(oracle_minus_fitted_horizontal_rms_m=values[0]-values[2],
                oracle_minus_fitted_vertical_rms_m=values[1]-values[3],
                oracle_to_fitted_horizontal_rms_ratio=values[0]/values[2],
                oracle_better_horizontal=values[0]<values[2])


def build(root):
    import numpy as np
    from .airquantumgrav_observation_truth import receiver_samples
    from .esa_fit_adjusted_forecast_report import (
        build as fitted_build, position_errors_neu, _metrics)
    from .esa_oracle_study import ID, SCOPE, LAWS
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    fitted = fitted_build(root)
    study = ClosedStudy(root,'data/'+ID)
    try:
        if (study.completion['state'] != 'complete' or
                study.summary['completed'] != 2 or
                study.manifest['scope'] != SCOPE or
                set(study.tasks) != set(LAWS) or
                set(study.rows) != set(LAWS) or
                any(study.manifest['sources'].get(name) != hashlib.sha256(
                    (root/name).read_bytes()).hexdigest() for name in (
                        'analysis/lll/airquantumgrav_truth.py',
                        'analysis/lll/airquantumgrav_observation_truth.py',
                        'analysis/lll/esa_oracle_control.py'))):
            raise ValueError('complete source-matched oracle study required')
        bindings = study.input('parent-binding')
        if (set(bindings) != set(LAWS) or any(bindings[law][
                'parent_manifest_sha256'] != fitted['study_manifest_sha256']
                for law in LAWS)):
            raise ValueError('matched sealed parent required')
        cases = {}
        for law in LAWS:
            result = study.envelope(law)['result']
            record = study.artifact(law,'oracle-forecast.json')
            if (result['passed'] is not True or
                    result['scientific_decision'] != 'abstain' or
                    result['law'] != law or
                    record['known_corrections_supplied_not_fitted'] is not True or
                    record['future_receiver_positions_used_to_forecast'] is not False or
                    record['later_truth_used_for_scoring_only'] is not True or
                    record['original_reads'] != 0 or
                    record['protected_reads'] != 0):
                raise ValueError('unchanged sealed no-refit forecast required')
            forecast = np.asarray(record['coordinates'],dtype=float)
            times = np.asarray(record['times_s'],dtype=float)
            if (forecast.shape != (900,3) or times.shape != (900,) or
                    not np.array_equal(times,.5+np.arange(900.))):
                raise ValueError('complete matched forecast times required')
            answer = receiver_samples('sphere_rotating',times[600:],
                latitude_deg=55.,pattern='fast',removal=0.,sign=1,
                height_profile='climb',gravity_model='inverse_square_height')
            oracle = _metrics(position_errors_neu(
                forecast[600:],answer['coordinates']))
            if any(not math.isclose(oracle[key],record['future_metrics'][key],
                    rel_tol=1e-12,abs_tol=1e-9) or not math.isclose(
                    oracle[key],result['future_metrics'][key],
                    rel_tol=1e-12,abs_tol=1e-9)
                    for key in ('horizontal_rms_m','vertical_rms_m')):
                raise ValueError('recomputed oracle score differs')
            matched = fitted['cases'][law]['candidates'][law]['full_future']
            cases[law] = dict(oracle=oracle,fitted=matched,
                              comparison=compare_scores(oracle,matched),
                              parent_input_sha256=bindings[law][
                                  'parent_input_sha256'])
        return dict(version='esa-oracle-noisy-report-v1',
            study='data/'+ID,
            study_manifest_sha256=study.completion['manifest_sha256'],
            study_summary_sha256=study.completion['summary_sha256'],
            fitted_report_source_sha256=fitted['report_source_sha256'],
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_oracle_report.py').read_bytes()).hexdigest(),
            cases=cases,generated_recordings=2,native_forecast_calls=2,
            observed_ESA_records_read=0,protected_confirmation_groups_opened=0,
            known_calibration_supplied=True,scientific_decision='abstain',
            uncertainty_calibrated=False)
    finally:
        study.close()


def publish(root):
    from .studies.artifacts import atomic,encoded
    root = Path(root).resolve()
    result = build(root)
    base = root/'docs/prediction-observed-development'
    atomic(base/'ORACLE_NOISY_REPORT.json',encoded(result))
    rows = []
    for law in ('increment','point'):
        case = result['cases'][law]
        rows.append('| {} | {:.2f} | {:.2f} | {:.2f} | {:.2f} |'.format(
            law,case['oracle']['horizontal_rms_m'],
            case['fitted']['horizontal_rms_m'],
            case['oracle']['vertical_rms_m'],
            case['fitted']['vertical_rms_m']))
    markdown = ('# Known calibration on the saved noisy streams\n\n'
        'Both frozen tasks completed. The same generated IMU measurements were '
        'forecast from the known initial state and sensor corrections, without '
        'fitting them to receiver positions. Future physical truth was used only '
        'for scoring reports 600–899.\n\n'
        '| Noise construction | Known calibration horizontal RMS (m) | Fitted horizontal RMS (m) | Known calibration vertical RMS (m) | Fitted vertical RMS (m) |\n'
        '| --- | ---: | ---: | ---: | ---: |\n' + '\n'.join(rows) + '\n\n'
        'Known calibration did not remove future drift in either generated '
        'stream. The fitted forecasts were more accurate on these two fixed '
        'draws, especially for point-rate noise. This control does not assign '
        'the drift to any one noise, timing or motion mechanism, establish '
        'calibrated prediction coverage, or decide an Earth model. The seven '
        'reserved ESA confirmation groups remain unopened.\n\n'
        'The [machine-readable report](ORACLE_NOISY_REPORT.json) records exact '
        'scores and source/evidence hashes.\n')
    atomic(base/'ORACLE_NOISY_REPORT.md',markdown.encode())
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    args = parser.parse_args(argv)
    print(json.dumps(publish(args.root),sort_keys=True))


if __name__ == '__main__':
    main()
