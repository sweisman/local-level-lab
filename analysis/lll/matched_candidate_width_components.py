# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only affine calibration/future-noise width decomposition."""

import hashlib
import json
import math
from pathlib import Path

from .matched_candidate_case import MODELS
from .matched_candidate_generated_report import build as primary_report

PLAN='docs/prediction-observed-development/MATCHED_CANDIDATE_WIDTH_COMPONENT_PLAN.md'
EPOCHS=(1,10,20,40)


def case_components(study,identity):
    import numpy as np
    from scipy.stats import norm
    from .airquantumgrav_truth import A,E2

    earlier=study.artifact(identity,'training-receiver.json')[-1]
    phi=math.radians(earlier['latitude_deg']);h=earlier['height_m']
    factor=1-E2*math.sin(phi)**2
    scale=np.array([A*(1-E2)/factor**1.5+h,
                    (A/math.sqrt(factor)+h)*math.cos(phi),1.])
    if np.any(scale<=0):
        raise ValueError('positive earlier receiver metric required')
    result={}
    for model in MODELS:
        prefix='candidates/'+model+'/'
        bound=study.artifact(identity,prefix+'bounded-receiver.json')
        diagnostic=study.artifact(identity,prefix+'receiver-forecast-error-diagnostic.json')
        q=bound['prediction_epochs']
        alpha=.025/(3*q)
        if (q!=40 or bound.get('joint_future_coordinate_count')!=3*q
                or not math.isclose(bound.get('marginal_coverage_lower_bound',0),
                                    1-.025-alpha,rel_tol=0,abs_tol=1e-12)
                or bound.get('later_observations_used') is not False
                or bound.get('prediction_target')!='receiver_measurement'):
            raise ValueError('frozen whole-path receiver allowance required')
        lower=np.asarray(bound['lower'],float).reshape(q,3)
        upper=np.asarray(bound['upper'],float).reshape(q,3)
        covariance=np.asarray(diagnostic['fixed_parameters']['covariance'],float)
        if (lower.shape!=(q,3) or upper.shape!=lower.shape
                or covariance.shape!=(q,3,3)
                or any(not np.all(np.isfinite(v)) for v in
                       (lower,upper,covariance)) or np.any(lower>=upper)):
            raise ValueError('complete saved receiver bounds and covariance required')
        variance=np.diagonal(covariance,axis1=1,axis2=2)
        if np.any(variance<=0):
            raise ValueError('positive conditional future variance required')
        total=(upper-lower)/2
        future=norm.ppf(1-alpha/2)*np.sqrt(variance)
        calibration=total-future
        if np.any(calibration<-1e-10*np.maximum(1.,total)):
            raise ValueError('saved width contradicts affine component sum')
        calibration=np.maximum(calibration,0.)
        horizontal_total=np.linalg.norm(total[:,:2]*scale[:2],axis=1)
        horizontal_future=np.linalg.norm(future[:,:2]*scale[:2],axis=1)
        horizontal_calibration=np.linalg.norm(calibration[:,:2]*scale[:2],axis=1)
        if np.any(horizontal_total<=0):
            raise ValueError('positive horizontal range required')
        result[model]=dict(
            total_horizontal_halfwidth_m=horizontal_total.tolist(),
            future_noise_horizontal_radius_m=horizontal_future.tolist(),
            calibration_horizontal_allowance_m=horizontal_calibration.tolist(),
            calibration_to_total_horizontal_ratio=(horizontal_calibration/
                                                   horizontal_total).tolist(),
            component_sum_reproduces_saved_coordinate_width=True)
    return result


def build(root):
    import statistics
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    primary=primary_report(root)
    if primary['technical_passing']!=12 or primary['candidate_fits_converged']!=36:
        raise ValueError('complete numerically converged matrix required')
    study=ClosedStudy(root,primary['study'])
    try:
        cases={identity:case_components(study,identity)
               for identity in sorted(primary['cases'])}
        summary={}
        for model in MODELS:
            summary[model]={}
            for epoch in EPOCHS:
                index=epoch-1
                summary[model][str(epoch)]=dict(
                    median_calibration_share=float(statistics.median(
                        case[model]['calibration_to_total_horizontal_ratio'][index]
                        for case in cases.values())),
                    median_total_horizontal_halfwidth_m=float(statistics.median(
                        case[model]['total_horizontal_halfwidth_m'][index]
                        for case in cases.values())),
                    median_future_noise_horizontal_radius_m=float(statistics.median(
                        case[model]['future_noise_horizontal_radius_m'][index]
                        for case in cases.values())))
        return dict(version='matched-candidate-width-components-v1',
                    study=primary['study'],
                    manifest_sha256=primary['manifest_sha256'],
                    summary_sha256=primary['summary_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root/PLAN).read_bytes()).hexdigest(),
                    cases=cases,summary=summary,new_fits=0,original_reads=0,
                    protected_reads=0,scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic,encoded
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    target=Path(args.output)
    if target.exists():
        raise ValueError('fresh verified width report required')
    result=build(args.root)
    atomic(target,encoded(result))
    print(json.dumps(dict(cases=len(result['cases']),models=len(result['summary']))))


if __name__=='__main__':
    main()
