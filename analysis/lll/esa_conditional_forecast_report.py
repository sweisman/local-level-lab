# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score a sealed earlier-conditioned ESA forecast against later GPS reports."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path


STUDY = 'data/esa-conditional-forecast-development-v3-20261114'
PARENT = 'data/esa-rate-refit-development-v2-20261114'
HISTORICAL = 'docs/esa-observed-wide-pilot'
TASK = 'single-pass-receiver-conditional'
MANIFEST_SHA256 = '17fd7ee56d1ed40fcef39061a4e7ba0706bd93e8d04b9f0998b0db94dc128ea7'
SCORING_SHA256 = '5cce2704433e7dece8eec336882692e15194d6c882d8e2bd7efa67265a172c2b'


def score_paths(raw, conditioned, receiver, *, training_epochs):
    """Score only the preselected later rows, with unchanged earlier support."""
    import numpy as np
    from .airquantumgrav_geographic_report import error_metrics
    from .airquantumgrav_scoring import receiver_errors

    raw,conditioned,receiver = (np.asarray(value,dtype=float)
                                for value in (raw,conditioned,receiver))
    if (raw.ndim != 2 or raw.shape != receiver.shape or raw.shape[1:] != (3,) or
            type(training_epochs) is not int or not 1 < training_epochs < len(raw) or
            conditioned.shape != (len(raw)-training_epochs,3) or
            not all(np.all(np.isfinite(value)) for value in (raw,conditioned,receiver))):
        raise ValueError('complete finite raw, conditional and later receiver routes required')
    later_raw = raw[training_epochs:]
    later_receiver = receiver[training_epochs:]
    def metrics(route,reference):
        errors=receiver_errors(route,reference)
        result=error_metrics(errors.tolist())
        result['maximum_horizontal_m']=float(np.max(np.linalg.norm(errors[:,:2],axis=1)))
        result['maximum_absolute_up_m']=float(np.max(np.abs(errors[:,2])))
        return result
    return dict(prediction_epochs=len(later_raw),
        raw=metrics(later_raw,later_receiver),
        conditional=metrics(conditioned,later_receiver),
        adjustment=metrics(conditioned,later_raw))


def build(root):
    import numpy as np
    from .ilvis0_prediction_observed import accuracy_screen
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    studies = [ClosedStudy(root,STUDY)]
    try:
        studies.extend([ClosedStudy(root,PARENT),ClosedStudy(root,HISTORICAL)])
        study,parent,historical = studies
        if (not MANIFEST_SHA256 or study.completion['manifest_sha256'] != MANIFEST_SHA256 or
                study.completion['state'] != 'complete' or
                study.summary['completed'] != 1 or study.summary['total'] != 1 or
                study.rows[TASK]['passed'] is not True or
                parent.completion['manifest_sha256'] !=
                'fabb0ef004ce452a7a0b0a14ac71c307b350d3b9b4d25ca8bc8545598f75c2ba' or
                historical.manifest['inputs']['scoring']['sha256'] != SCORING_SHA256):
            raise ValueError('exact sealed conditional study and scoring rows required')
        saved = study.artifact(TASK,'conditional-forecast.json')
        if (saved['training_epochs'] != 800 or saved['prediction_epochs'] != 400 or
                saved['optimization_performed'] is not False or
                saved['later_receiver_values_used'] is not False or
                saved['fixed_calibration_only'] is not True or
                saved['scientific_decision'] != 'abstain' or
                saved['linear_calibration_status'] not in (
                    'estimable','active_bounds_unsupported','no_active_calibration',
                    'linear_step_outside_bounds','unidentifiable','not_evaluated') or
                len(saved['times_s']) != 1200 or
                np.asarray(saved['conditional_receiver_covariance']).shape != (400,3,3)):
            raise ValueError('complete fixed-parameter conditional forecast required')
        rows = json.loads(gzip.decompress(historical.input('scoring',raw=True)))
        if len(rows) != 1200:
            raise ValueError('complete later receiver rows required')
        receiver = np.asarray([[math.radians(row['latitude_deg']),
            math.radians(row['longitude_deg']),row['height_m']] for row in rows])
        scores = score_paths(saved['raw_coordinates'],
            saved['conditional_receiver_mean'],receiver,training_epochs=800)
        return dict(version='esa-conditional-forecast-report-v1',study=STUDY,
            manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            scoring_sha256=SCORING_SHA256,
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_conditional_forecast_report.py').read_bytes()).hexdigest(),
            scores=scores,raw_accuracy_screen=accuracy_screen(scores['raw']),
            conditional_accuracy_screen=accuracy_screen(scores['conditional']),
            training_epochs=800,prediction_epochs=400,
            linear_calibration_status=saved['linear_calibration_status'],
            fixed_calibration_only=True,confidence_calibrated=False,
            observation_error_law_calibrated=False,
            later_receiver_values_used_for_forecast=False,
            protected_confirmation_groups_opened=0,
            scientific_decision='abstain')
    finally:
        for study in reversed(studies):
            study.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args = parser.parse_args(argv)
    result = build(args.root)
    path = Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(scores=result['scores'],
        conditional_passed=result['conditional_accuracy_screen']['passed']),sort_keys=True))


if __name__ == '__main__':
    main()
