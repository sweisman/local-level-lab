# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only width and overlap audit for sealed generated candidate bounds."""

import hashlib
import json
from itertools import combinations
from pathlib import Path

from .matched_candidate_case import MODELS
from .matched_candidate_generated_report import build as primary_report


def case_widths(study,identity):
    import math
    import numpy as np
    from .airquantumgrav_truth import A,E2
    from .ilvis0_precision_value import longitude_residual
    earlier=study.artifact(identity,'training-receiver.json')
    last=earlier[-1]
    phi=math.radians(last['latitude_deg']);height=last['height_m']
    q=1-E2*math.sin(phi)**2
    scale=np.array([A*(1-E2)/q**1.5+height,
                    (A/math.sqrt(q)+height)*math.cos(phi),1.])
    if np.any(scale<=0):
        raise ValueError('positive fixed training-coordinate metric required')
    candidates={};full={}
    for model in MODELS:
        prefix='candidates/'+model+'/'
        bound=study.artifact(identity,prefix+'bounded-receiver.json')
        diagnostic=study.artifact(identity,prefix+'receiver-forecast-error-diagnostic.json')
        future=bound['prediction_epochs']
        lower=np.asarray(bound['lower'],float).reshape(future,3)
        upper=np.asarray(bound['upper'],float).reshape(future,3)
        center=np.asarray(diagnostic['fixed_parameters']['mean'],float)
        if (center.shape!=(future,3) or lower.shape!=center.shape
                or upper.shape!=center.shape
                or any(not np.all(np.isfinite(v)) for v in (center,lower,upper))
                or np.any(lower>=upper)
                or bound.get('prediction_target')!='receiver_measurement'
                or bound.get('later_observations_used') is not False):
            raise ValueError('complete unchanged receiver candidate range required')
        width=(upper-lower)*scale
        candidates[model]=dict(
            mean_full_horizontal_width_m=float(np.mean(
                np.linalg.norm(width[:,:2],axis=1))),
            maximum_full_horizontal_width_m=float(np.max(
                np.linalg.norm(width[:,:2],axis=1))),
            mean_full_vertical_width_m=float(np.mean(width[:,2])))
        full[model]=(lower,upper,center)
    pairs={}
    for left,right in combinations(MODELS,2):
        lo_a,hi_a,center_a=full[left];lo_b,hi_b,center_b=full[right]
        difference=center_a-center_b
        difference[:,1]=longitude_residual(difference[:,1])
        horizontal=np.linalg.norm(difference[:,:2]*scale[:2],axis=1)
        gap=np.maximum(0.,np.maximum(lo_a-hi_b,lo_b-hi_a))*scale
        separated=np.any(gap>0.,axis=1)
        pairs[left+'__'+right]=dict(
            median_center_horizontal_separation_m=float(np.median(horizontal)),
            maximum_center_horizontal_separation_m=float(np.max(horizontal)),
            epochs_with_disjoint_coordinate_ranges=int(np.count_nonzero(separated)),
            future_epochs=len(separated),
            entire_path_ranges_have_nonempty_coordinate_intersection=
                bool(not np.any(separated)),
            maximum_coordinate_gap_m=float(np.max(gap)))
    return dict(metric='fixed at last earlier receiver position',
                candidates=candidates,pairs=pairs)


def build(root,*,preflight=False):
    from .studies.closed import ClosedStudy
    from .studies.artifacts import encoded
    primary=primary_report(root,preflight=preflight)
    root=Path(root).resolve()
    study=ClosedStudy(root,primary['study'])
    try:
        cases={identity:case_widths(study,identity)
               for identity,row in primary['cases'].items()
               if row['technical_passed']}
        return dict(version='matched-candidate-range-audit-v1',
                    study=primary['study'],
                    manifest_sha256=primary['manifest_sha256'],
                    summary_sha256=primary['summary_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    primary_report_sha256=hashlib.sha256(encoded(primary)).hexdigest(),
                    cases=cases,new_fits=0,original_reads=0,protected_reads=0,
                    scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic,encoded
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    parser.add_argument('--preflight',action='store_true')
    args=parser.parse_args(argv)
    target=Path(args.output)
    if target.exists():
        raise ValueError('fresh verified range audit required')
    result=build(args.root,preflight=args.preflight)
    atomic(target,encoded(result))
    print(json.dumps(dict(cases=len(result['cases']))))


if __name__=='__main__':
    main()
