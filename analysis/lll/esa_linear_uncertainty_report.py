# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score sealed ESA local-calibration moments on already opened later GPS."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from .esa_conditional_forecast_report import (HISTORICAL,SCORING_SHA256,TASK,
    score_paths)
from .esa_conditional_coverage_report import describe_coverage


STUDY='data/esa-linear-uncertainty-development-v3-20261115'
MANIFEST_SHA256='0d89b2d2af9b8546cef9bf33c6e222e2a19214137f87805a1b6241f10dc55092'


def compare_coverage(fixed_mean,fixed_cov,local_mean,local_cov,receiver):
    return dict(fixed=describe_coverage(fixed_mean,receiver,fixed_cov),
                local=describe_coverage(local_mean,receiver,local_cov,
                    parameter_uncertainty_included=True))


def build(root):
    import numpy as np
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    study=ClosedStudy(root,STUDY);historical=ClosedStudy(root,HISTORICAL)
    try:
        if (study.completion['state']!='complete' or
                study.completion['manifest_sha256']!=MANIFEST_SHA256 or
                study.summary['completed']!=1 or study.summary['total']!=1 or
                study.rows[TASK]['passed'] is not True or
                historical.manifest['inputs']['scoring']['sha256']!=SCORING_SHA256):
            raise ValueError('exact sealed local-calibration study and scoring input required')
        linear=study.artifact(TASK,'linear-uncertainty.json')
        fixed=study.artifact(TASK,'conditional-forecast.json')
        tangent=study.artifact(TASK,'fitted-tangent-replay.json')
        prefix=study.artifact(TASK,'prefix-replay.json')
        if (linear['status']!='estimable' or linear['training_rank']!=26 or
                linear['parameter_count']!=26 or
                linear['parameter_step_inside_bounds'] is not True or
                linear['parameter_uncertainty_included'] is not True or
                linear['later_observations_used'] is not False or
                linear['scientific_decision']!='abstain' or
                tangent['training_jacobian_replayed'] is not True or
                tangent['maximum_position_difference_m']>1e-4 or
                prefix['replay_passed'] is not True or
                fixed['training_epochs']!=800 or fixed['prediction_epochs']!=400 or
                fixed['later_receiver_values_used'] is not False):
            raise ValueError('complete early-only local calibration result required')
        rows=json.loads(gzip.decompress(historical.input('scoring',raw=True)))
        if len(rows)!=1200:raise ValueError('complete later receiver rows required')
        receiver=np.asarray([[math.radians(row['latitude_deg']),
            math.radians(row['longitude_deg']),row['height_m']] for row in rows])
        coverage=compare_coverage(fixed['conditional_receiver_mean'],
            fixed['conditional_receiver_covariance'],linear['receiver_mean'],
            linear['receiver_covariance'],receiver[800:])
        scores=score_paths(fixed['raw_coordinates'],linear['receiver_mean'],receiver,
            training_epochs=800)
        return dict(version='esa-local-linear-uncertainty-development-report-v1',
            study=STUDY,manifest_sha256=MANIFEST_SHA256,
            scoring_sha256=SCORING_SHA256,
            reporter_sha256=hashlib.sha256((root/'analysis/lll/esa_linear_uncertainty_report.py')
                .read_bytes()).hexdigest(),
            coverage_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_conditional_coverage_report.py').read_bytes()).hexdigest(),
            fitted_tangent_replay=tangent,training_prefix_replay_passed=True,
            training_rank=26,parameter_count=26,parameter_step_inside_bounds=True,
            scores=scores,coverage=coverage,
            local_linear_only=True,observed_error_law_calibrated=False,
            later_receiver_used_for_fit=False,protected_confirmation_groups_opened=0,
            scientific_decision='abstain')
    finally:
        historical.close();study.close()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv);report=build(args.root)
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(coverage=report['coverage'],
        local_scores=report['scores']['conditional']),sort_keys=True))


if __name__=='__main__':main()
