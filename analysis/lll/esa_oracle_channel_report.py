# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and compare four sealed single-channel generated forecasts."""

import argparse
import hashlib
import json
import math
from pathlib import Path


def compare_channels(gyro,accel,full):
    values=[row['horizontal_rms_m'] for row in (gyro,accel,full)]
    if any(not isinstance(v,(int,float)) or not math.isfinite(v) or v<0
           for v in values) or values[0]==0 or values[1]==0:
        raise ValueError('complete positive single-channel scores required')
    return dict(gyro_to_accel_horizontal_rms_ratio=values[0]/values[1],
        full_to_gyro_horizontal_rms_ratio=values[2]/values[0],
        dominant_single_channel_horizontal=(
            'gyro' if values[0]>values[1] else
            'accel' if values[1]>values[0] else 'tie'),
        additive_error_assumption_made=False)


def build(root):
    import numpy as np
    from .airquantumgrav_observation_truth import receiver_samples
    from .esa_fit_adjusted_forecast_report import position_errors_neu,_metrics
    from .esa_oracle_clean_report import build as clean_build
    from .esa_oracle_channel_study import ID,SCOPE,LAWS,CHANNELS
    from .studies.closed import ClosedStudy

    root=Path(root).resolve();reference=clean_build(root)
    study=ClosedStudy(root,'data/'+ID)
    try:
        identities={law+'-'+channel for law in LAWS for channel in CHANNELS}
        if (study.completion['state']!='complete' or
                study.summary['completed']!=4 or
                study.manifest['scope']!=SCOPE or
                set(study.tasks)!=identities or set(study.rows)!=identities or
                any(study.manifest['sources'].get(name)!=hashlib.sha256(
                    (root/name).read_bytes()).hexdigest() for name in (
                        'analysis/lll/airquantumgrav_truth.py',
                        'analysis/lll/airquantumgrav_observation_truth.py',
                        'analysis/lll/esa_oracle_control.py'))):
            raise ValueError('complete source-matched channel control required')
        binding=study.input('parent-binding')
        if binding['clean_manifest_sha256']!=reference['study_manifest_sha256']:
            raise ValueError('channel control uses different clean parent')
        cases={}
        for law in LAWS:
            scores={}
            for channel in CHANNELS:
                identity=law+'-'+channel
                result=study.envelope(identity)['result']
                record=study.artifact(identity,'channel-forecast.json')
                if (result['passed'] is not True or
                        result['scientific_decision']!='abstain' or
                        result['law']!=law or result['channel']!=channel or
                        record['noise_law']!=law or
                        record['noisy_channel']!=channel or
                        record['future_receiver_positions_used_to_forecast'] is not False
                        or record['later_truth_used_for_scoring_only'] is not True
                        or record['original_reads']!=0 or record['protected_reads']!=0):
                    raise ValueError('unchanged sealed channel forecast required')
                times=np.asarray(record['times_s'],float)
                forecast=np.asarray(record['coordinates'],float)
                if (times.shape!=(900,) or forecast.shape!=(900,3) or
                        not np.array_equal(times,.5+np.arange(900.))):
                    raise ValueError('complete matched channel grid required')
                truth=receiver_samples('sphere_rotating',times[600:],
                    latitude_deg=55.,pattern='fast',removal=0.,sign=1,
                    height_profile='climb',gravity_model='inverse_square_height')
                score=_metrics(position_errors_neu(
                    forecast[600:],truth['coordinates']))
                if any(not math.isclose(score[key],record['future_metrics'][key],
                        rel_tol=1e-12,abs_tol=1e-9) or not math.isclose(
                        score[key],result['future_metrics'][key],
                        rel_tol=1e-12,abs_tol=1e-9)
                        for key in ('horizontal_rms_m','vertical_rms_m')):
                    raise ValueError('recomputed channel score differs')
                scores[channel]=score
            full=reference['cases'][law]['noisy_oracle']
            cases[law]=dict(single_channel=scores,full_noise=full,
                comparison=compare_channels(scores['gyro'],scores['accel'],full))
        return dict(version='esa-oracle-channel-report-v1',
            study='data/'+ID,
            study_manifest_sha256=study.completion['manifest_sha256'],
            study_summary_sha256=study.completion['summary_sha256'],
            clean_study_manifest_sha256=reference['study_manifest_sha256'],
            noisy_study_manifest_sha256=reference['noisy_study_manifest_sha256'],
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_oracle_channel_report.py').read_bytes()).hexdigest(),
            cases=cases,clean_future=reference['clean_future'],
            native_forecast_calls=4,original_reads=0,
            protected_confirmation_groups_opened=0,
            scientific_decision='abstain',uncertainty_calibrated=False)
    finally:study.close()


def publish(root):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();report=build(root)
    base=root/'docs/prediction-observed-development'
    atomic(base/'ORACLE_CHANNEL_REPORT.json',encoded(report))
    rows=[]
    for law in ('increment','point'):
        case=report['cases'][law]
        for label,score in (('gyro only',case['single_channel']['gyro']),
                            ('accelerometer only',case['single_channel']['accel']),
                            ('both',case['full_noise'])):
            rows.append('| {} | {} | {:.2f} | {:.2f} |'.format(law,label,
                score['horizontal_rms_m'],score['vertical_rms_m']))
    text=('# Which injected IMU channel drives the generated drift?\n\n'
        'Four frozen forecasts completed on the same two generated noise '
        'draws. Each kept one noisy IMU channel and replaced the other with '
        'its clean counterpart. All used the known initial state and sensor '
        'calibration; later truth only scored reports 600–899.\n\n'
        '| Error law | Noisy channel | Future horizontal RMS (m) | Future vertical RMS (m) |\n'
        '| --- | --- | ---: | ---: |\n'+'\n'.join(rows)+'\n\n'
        'On both fixed draws, the gyro channel dominates horizontal error. '
        'The full-noise error is not the sum of the two separate errors; '
        'the channels interact in propagation. This does not isolate white '
        'noise from changing bias, estimate a recorded ESA noise law, or '
        'qualify prediction coverage. The seven reserved ESA confirmation '
        'groups remain unopened.\n\n'
        'See the [clean forecast](ORACLE_CLEAN_REPORT.md), '
        '[full-noise forecasts](ORACLE_NOISY_REPORT.md), and '
        '[machine-readable scores](ORACLE_CHANNEL_REPORT.json).\n')
    atomic(base/'ORACLE_CHANNEL_REPORT.md',text.encode())
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv);report=publish(args.root)
    print(json.dumps({law:{channel:report['cases'][law]['single_channel'][
        channel]['horizontal_rms_m'] for channel in ('gyro','accel')}
        for law in ('increment','point')},sort_keys=True))


if __name__=='__main__':main()
