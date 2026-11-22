# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only time profile of candidate separation versus receiver range."""

import hashlib
import json
from itertools import combinations
from pathlib import Path

from .matched_candidate_case import MODELS
from .matched_candidate_generated_report import build as primary_report

PLAN='docs/prediction-observed-development/MATCHED_CANDIDATE_HORIZON_PLAN.md'
EPOCHS=(1,10,20,40)


def profile_case(study,identity):
    import math
    import numpy as np
    from .airquantumgrav_truth import A,E2
    from .ilvis0_precision_value import longitude_residual

    earlier=study.artifact(identity,'training-receiver.json')[-1]
    phi=math.radians(earlier['latitude_deg']);h=earlier['height_m']
    factor=1-E2*math.sin(phi)**2
    scale=np.array([A*(1-E2)/factor**1.5+h,
                    (A/math.sqrt(factor)+h)*math.cos(phi),1.])
    if np.any(scale<=0):
        raise ValueError('positive fixed earlier receiver metric required')
    values={};grid=None
    for model in MODELS:
        path='candidates/'+model+'/'
        bound=study.artifact(identity,path+'bounded-receiver.json')
        diagnostic=study.artifact(identity,path+'receiver-forecast-error-diagnostic.json')
        forecast=study.artifact(identity,path+'forecast.json')
        m=bound['training_epochs'];q=bound['prediction_epochs']
        if q!=40 or len(forecast['times_s'])!=m+q:
            raise ValueError('exact frozen 40-epoch future required')
        future=forecast['times_s'][m:]
        if grid is None:grid=future
        elif future!=grid:raise ValueError('matched future receiver times required')
        lower=np.asarray(bound['lower'],float).reshape(q,3)
        upper=np.asarray(bound['upper'],float).reshape(q,3)
        center=np.asarray(diagnostic['fixed_parameters']['mean'],float)
        if (bound.get('prediction_target')!='receiver_measurement'
                or bound.get('later_observations_used') is not False
                or center.shape!=(q,3) or lower.shape!=center.shape
                or upper.shape!=center.shape or np.any(lower>=upper)
                or any(not np.all(np.isfinite(v))
                       for v in (center,lower,upper))):
            raise ValueError('complete earlier-only matched receiver range required')
        values[model]=(lower,upper,center)
    pairs={}
    for left,right in combinations(MODELS,2):
        lo_a,hi_a,center_a=values[left]
        lo_b,hi_b,center_b=values[right]
        difference=center_a-center_b
        difference[:,1]=longitude_residual(difference[:,1])
        horizontal=np.linalg.norm(difference[:,:2]*scale[:2],axis=1)
        halfwidth=((hi_a-lo_a)+(hi_b-lo_b))*scale/2
        combined=np.linalg.norm(halfwidth[:,:2],axis=1)
        if np.any(combined<=0):
            raise ValueError('positive combined horizontal range required')
        ratio=horizontal/combined
        disjoint=np.any(np.maximum(lo_a,lo_b)>np.minimum(hi_a,hi_b),axis=1)
        pairs[left+'__'+right]=dict(
            center_horizontal_separation_m=horizontal.tolist(),
            combined_horizontal_halfwidth_m=combined.tolist(),
            center_separation_to_halfwidth_ratio=ratio.tolist(),
            coordinate_ranges_disjoint=disjoint.tolist())
    return dict(earlier_metric='last training receiver position',
                future_times_s=grid,pairs=pairs)


def build(root):
    import statistics
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    primary=primary_report(root)
    if primary['technical_passing']!=12 or primary['candidate_fits_converged']!=36:
        raise ValueError('complete numerically converged matched matrix required')
    study=ClosedStudy(root,primary['study'])
    try:
        cases={identity:profile_case(study,identity)
               for identity in sorted(primary['cases'])}
        pair_names=tuple(next(iter(cases.values()))['pairs'])
        summary={}
        for pair in pair_names:
            horizons={}
            for epoch in EPOCHS:
                rows=[case['pairs'][pair] for case in cases.values()]
                index=epoch-1
                horizons[str(epoch)]=dict(
                    median_center_separation_m=float(statistics.median(
                        row['center_horizontal_separation_m'][index] for row in rows)),
                    median_combined_halfwidth_m=float(statistics.median(
                        row['combined_horizontal_halfwidth_m'][index] for row in rows)),
                    median_separation_to_halfwidth_ratio=float(statistics.median(
                        row['center_separation_to_halfwidth_ratio'][index] for row in rows)),
                    disjoint_recordings=sum(row['coordinate_ranges_disjoint'][index]
                                            for row in rows))
            summary[pair]=horizons
        return dict(version='matched-candidate-horizon-audit-v1',
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
    output=Path(args.output)
    if output.exists():
        raise ValueError('fresh verified horizon report required')
    result=build(args.root)
    atomic(output,encoded(result))
    print(json.dumps(dict(cases=len(result['cases']),pairs=len(result['summary']))))


if __name__=='__main__':
    main()
