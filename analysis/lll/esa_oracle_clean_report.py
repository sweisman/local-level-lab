# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the sealed long clean forecast against analytic future truth."""

import argparse
import hashlib
import json
import math
from pathlib import Path


def clean_to_noisy_ratios(clean,noisy):
    axes=(('horizontal','horizontal_rms_m'),('vertical','vertical_rms_m'))
    if any(not math.isfinite(clean[key]) or clean[key]<=0 or
           not math.isfinite(noisy[key]) or noisy[key]<0 for _,key in axes):
        raise ValueError('finite positive clean reference required')
    return {axis:noisy[key]/clean[key] for axis,key in axes}


def build(root):
    import numpy as np
    from .airquantumgrav_observation_truth import receiver_samples
    from .esa_fit_adjusted_forecast_report import position_errors_neu,_metrics
    from .esa_oracle_report import build as noisy_build
    from .esa_oracle_clean_study import ID,SCOPE
    from .studies.closed import ClosedStudy

    root=Path(root).resolve();noisy=noisy_build(root)
    study=ClosedStudy(root,'data/'+ID)
    try:
        if (study.completion['state']!='complete' or
                study.summary['completed']!=1 or
                study.manifest['scope']!=SCOPE or
                set(study.tasks)!={'clean'} or
                any(study.manifest['sources'].get(name)!=hashlib.sha256(
                    (root/name).read_bytes()).hexdigest() for name in (
                        'analysis/lll/airquantumgrav_truth.py',
                        'analysis/lll/airquantumgrav_observation_truth.py',
                        'analysis/lll/esa_oracle_control.py'))):
            raise ValueError('complete source-matched clean control required')
        result=study.envelope('clean')['result']
        record=study.artifact('clean','clean-forecast.json')
        if (result['passed'] is not True or result['scientific_decision']!='abstain'
                or record['known_corrections_supplied_not_fitted'] is not True
                or record['later_truth_used_for_scoring_only'] is not True
                or record['original_reads']!=0 or record['protected_reads']!=0):
            raise ValueError('sealed known-correction forecast required')
        times=np.asarray(record['times_s'],float)
        coordinates=np.asarray(record['coordinates'],float)
        if (times.shape!=(900,) or coordinates.shape!=(900,3) or
                not np.array_equal(times,.5+np.arange(900.))):
            raise ValueError('complete clean forecast grid required')
        truth=receiver_samples('sphere_rotating',times[600:],
            latitude_deg=55.,pattern='fast',removal=0.,sign=1,
            height_profile='climb',gravity_model='inverse_square_height')
        score=_metrics(position_errors_neu(
            coordinates[600:],truth['coordinates']))
        if any(not math.isclose(score[key],record['future_metrics'][key],
                rel_tol=1e-12,abs_tol=1e-9) or not math.isclose(
                score[key],result['future_metrics'][key],
                rel_tol=1e-12,abs_tol=1e-9)
                for key in ('horizontal_rms_m','vertical_rms_m')):
            raise ValueError('recomputed clean score differs')
        cases={law:dict(noisy_oracle=noisy['cases'][law]['oracle'],
                        noisy_to_clean_rms_ratio=clean_to_noisy_ratios(
                            score,noisy['cases'][law]['oracle']))
               for law in ('increment','point')}
        return dict(version='esa-oracle-clean-report-v1',study='data/'+ID,
            study_manifest_sha256=study.completion['manifest_sha256'],
            study_summary_sha256=study.completion['summary_sha256'],
            noisy_study_manifest_sha256=noisy['study_manifest_sha256'],
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_oracle_clean_report.py').read_bytes()).hexdigest(),
            clean_future=score,cases=cases,native_forecast_calls=1,
            original_reads=0,protected_confirmation_groups_opened=0,
            scientific_decision='abstain',uncertainty_calibrated=False)
    finally:
        study.close()


def publish(root):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();result=build(root)
    base=root/'docs/prediction-observed-development'
    atomic(base/'ORACLE_CLEAN_REPORT.json',encoded(result))
    clean=result['clean_future']
    rows=[]
    for law in ('increment','point'):
        score=result['cases'][law]['noisy_oracle']
        rows.append('| {} noise | {:.2f} | {:.2f} |'.format(
            law,score['horizontal_rms_m'],score['vertical_rms_m']))
    markdown=('# Long clean forecast control\n\n'
        'The single frozen 900-second clean task completed. Known sensor '
        'corrections and the true initial state were supplied; no parameters '
        'were fitted. Only reports 600–899 were scored against later analytic '
        'truth.\n\n'
        '| Stream | Future horizontal RMS (m) | Future vertical RMS (m) |\n'
        '| --- | ---: | ---: |\n'
        '| Clean | {:.3f} | {:.3f} |\n'.format(
            clean['horizontal_rms_m'],clean['vertical_rms_m'])+
        '\n'.join(rows)+'\n\n'
        'The long clean propagation is close to the analytic trajectory. '
        'The large drift in the two [noisy-stream controls](ORACLE_NOISY_REPORT.md) '
        'therefore appears only when random IMU errors are injected into this '
        'software setup. That does not identify which error component causes '
        'it or establish a measured ESA error law. The seven reserved ESA '
        'confirmation groups remain unopened.\n\n'
        'The [machine-readable report](ORACLE_CLEAN_REPORT.json) contains '
        'exact scores and evidence hashes.\n')
    atomic(base/'ORACLE_CLEAN_REPORT.md',markdown.encode())
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv)
    print(json.dumps(publish(args.root),sort_keys=True))


if __name__=='__main__':main()
