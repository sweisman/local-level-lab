# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only error scales over shorter withheld prediction horizons."""

import argparse
import hashlib
import json
from pathlib import Path

HORIZONS=(1,5,10,30,60,120,300)


def prefix_scales(variance, horizons=HORIZONS):
    import numpy as np
    value=np.asarray(variance,dtype=float)
    if (value.ndim!=2 or value.shape[1]!=3 or not len(value) or
            not np.all(np.isfinite(value)) or np.any(value<0) or
            not horizons or any(type(n) is not int or not 1<=n<=len(value)
                                for n in horizons) or
            tuple(sorted(set(horizons)))!=tuple(horizons)):
        raise ValueError('finite future three-axis variances and ordered horizons required')
    return {str(n):dict(horizontal_rms_scale_m=float(np.sqrt(
                np.mean(value[:n,:2].sum(axis=1)))),
            vertical_rms_scale_m=float(np.sqrt(np.mean(value[:n,2]))),
            final_epoch_horizontal_scale_m=float(np.sqrt(value[n-1,:2].sum())))
            for n in horizons}


def long_training_crosscheck(row):
    if (row['version']!='same-operator-conditioning-comparison-v1' or
            row['training_epochs']!=800 or row['later_epochs']!=400 or
            row['realized_noise_used'] is not False or
            row['fitted_calibration_used'] is not False):
        raise ValueError('800 earlier and 400 future fixed-parameter epochs required')
    values=row['conditioned']['later_variance_neu_m2']
    scales=prefix_scales(values,(120,400))
    if abs(scales['400']['horizontal_rms_scale_m']-
           row['conditioned']['horizontal_rms_scale_m'])>1e-8:
        raise ValueError('saved 400-epoch scale differs')
    return scales['120']


def build(root):
    from .esa_oracle_matched_scale_report import build as matched_build
    from .esa_oracle_matched_scale_study import ID,LAWS
    from .studies.closed import ClosedStudy
    root=Path(root).resolve();matched=matched_build(root)
    study=ClosedStudy(root,'data/'+ID)
    try:
        if study.completion['manifest_sha256']!=matched['study_manifest_sha256']:
            raise ValueError('different sealed matched-scale study')
        cases={}
        for law in LAWS:
            row=study.artifact(law,'variance-comparison.json')
            if (row['version']!='same-operator-conditioning-comparison-v1' or
                    row['training_epochs']!=600 or row['later_epochs']!=300 or
                    row['realized_noise_used'] is not False or
                    row['fitted_calibration_used'] is not False):
                raise ValueError('complete matched fixed-parameter covariance required')
            variants={key:prefix_scales(row[key]['later_variance_neu_m2'])
                      for key in ('unconditional','conditioned')}
            for key in variants:
                if abs(variants[key]['300']['horizontal_rms_scale_m']-
                       row[key]['horizontal_rms_scale_m'])>1e-8:
                    raise ValueError('saved full-horizon scale differs')
            cases[law]=variants
        long_study=ClosedStudy(root,'data/noise-conditioning-comparison-20261111')
        try:
            if (long_study.completion['state']!='complete' or
                    long_study.rows['increment-1200-conditioning']['passed'] is not True):
                raise ValueError('complete 800-epoch generated comparison required')
            long_scale=long_training_crosscheck(long_study.artifact(
                'increment-1200-conditioning','variance-comparison.json'))
            long_manifest=long_study.completion['manifest_sha256']
        finally:long_study.close()
        return dict(version='esa-oracle-horizon-report-v1',
            source_study='data/'+ID,
            source_manifest_sha256=matched['study_manifest_sha256'],
            source_summary_sha256=matched['study_summary_sha256'],
            long_training_source_study='data/noise-conditioning-comparison-20261111',
            long_training_manifest_sha256=long_manifest,
            long_training_120_s=long_scale,
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_oracle_horizon_report.py').read_bytes()).hexdigest(),
            horizons_s=list(HORIZONS),cases=cases,
            original_reads=0,protected_confirmation_groups_opened=0,
            native_calls=0,random_draws=0,fitted_calibration_used=False,
            confidence_calibrated=False,scientific_decision='abstain')
    finally:study.close()


def publish(root):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve();result=build(root)
    base=root/'docs/prediction-observed-development'
    atomic(base/'ORACLE_HORIZON_REPORT.json',encoded(result))
    rows=[]
    for horizon in HORIZONS:
        n=str(horizon);increment=result['cases']['increment']
        point=result['cases']['point']
        rows.append('| {} | {:.2f} | {:.2f} | {:.2f} | {:.2f} |'.format(
            horizon,
            increment['unconditional'][n]['horizontal_rms_scale_m'],
            increment['conditioned'][n]['horizontal_rms_scale_m'],
            point['unconditional'][n]['horizontal_rms_scale_m'],
            point['conditioned'][n]['horizontal_rms_scale_m']))
    page=('# How forecast error grows with the withheld interval\n\n'
        'This saved-only calculation uses the two declared synthetic IMU error '
        'laws on the same 900-second generated aircraft path. There is no new '
        'fit or simulated draw. The table shows expected horizontal RMS scale '
        'over the first part of the final 300 seconds. “With updates” means '
        'the linear Gaussian calculation conditions on all 600 earlier '
        'one-second receiver reports. It does not use a receiver report from '
        'the withheld interval. Calibration and initial state are known.\n\n'
        '| Withheld seconds | Increment: no updates (m) | Increment: earlier updates (m) | Point-rate: no updates (m) | Point-rate: earlier updates (m) |\n'
        '| ---: | ---: | ---: | ---: | ---: |\n'+
        '\n'.join(rows)+'\n\n'
        'A separate sealed generated study used 800 earlier receiver reports '
        'and the same increment-error law on a different aircraft path. Its '
        'expected horizontal RMS scale over the next 120 seconds is '
        '{:.2f} m, versus {:.2f} m above with 600 earlier reports. This '
        'cross-check uses saved covariances and no new draws or fits.\n\n'
        'Earlier receiver updates sharply reduce the synthetic uncertainty. '
        'Long open-loop accuracy is therefore a different requirement from '
        'testing a model against positions throughout a recording. These are '
        'linearized scales under assumed synthetic error laws, not observed '
        'aircraft coverage or a reason to revise a completed gate. A separate '
        'protocol must preselect any shorter withheld horizon and test '
        'physical adequacy and coverage before using real-flight results. '
        'The seven ESA confirmation groups remain closed.\n\n'
        '[Exact values and hashes](ORACLE_HORIZON_REPORT.json) · '
        '[Matched 300-second comparison](ORACLE_MATCHED_SCALE_REPORT.md).\n').format(
            result['long_training_120_s']['horizontal_rms_scale_m'],
            result['cases']['increment']['conditioned']['120']['horizontal_rms_scale_m'])
    atomic(base/'ORACLE_HORIZON_REPORT.md',page.encode())
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv)
    result=publish(args.root)
    print(json.dumps({law:result['cases'][law]['conditioned']['300']
                      for law in ('increment','point')},sort_keys=True))


if __name__=='__main__':main()
