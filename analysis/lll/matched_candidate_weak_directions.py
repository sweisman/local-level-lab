# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only weakest training nuisance directions from sealed generated fits."""

import hashlib
import json
import statistics
from pathlib import Path

from .matched_candidate_generated_report import build as primary_report
from .matched_candidate_generated_study import recipe,tasks

PLAN='docs/prediction-observed-development/MATCHED_CANDIDATE_WEAK_DIRECTION_PLAN.md'


def build(root):
    import numpy as np
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    primary=primary_report(root)
    if primary['technical_passing']!=12 or primary['candidate_fits_converged']!=36:
        raise ValueError('complete matched candidate study required')
    selected={row['identity']:row['payload']['truth_model']
              for row in tasks(recipe())}
    study=ClosedStudy(root,primary['study'])
    try:
        cases={}
        for identity,model in sorted(selected.items()):
            fit=study.artifact(identity,'candidates/'+model+'/fit.json')
            local=fit['local_linearization']
            names=local['active_parameters']
            matrix=np.asarray(local['jacobian'],float)
            saved=np.asarray(fit['singular_values'],float)
            if (local.get('convention')!=
                    'whitened residual derivative by normalized parameter'
                    or names!=fit['active_parameters'] or len(names)!=26
                    or matrix.shape[1]!=26 or matrix.shape[0]<26
                    or not np.all(np.isfinite(matrix))
                    or saved.shape!=(26,) or np.any(saved<=0)):
                raise ValueError('complete saved whitened training Jacobian required')
            _,singular,vh=np.linalg.svd(matrix,full_matrices=False)
            if not np.allclose(singular,saved,rtol=1e-8,atol=1e-9):
                raise ValueError('independent SVD disagrees with saved singular values')
            absolute=np.abs(vh[-1])
            top=sorted(range(26),key=lambda i:-absolute[i])[:3]
            cases[identity]=dict(generating_and_fitted_model=model,
                                 weakest_to_strongest_ratio=float(singular[-1]/singular[0]),
                                 weakest_loading_magnitude={name:float(absolute[i])
                                                            for i,name in enumerate(names)},
                                 top_three=[names[i] for i in top])
        if len(cases)!=12:
            raise ValueError('exact correct-model fit set required')
        names=next(iter(cases.values()))['weakest_loading_magnitude']
        summary={name:dict(
            top_three_count=sum(name in row['top_three'] for row in cases.values()),
            median_absolute_loading=float(statistics.median(
                row['weakest_loading_magnitude'][name]
                for row in cases.values()))) for name in names}
        return dict(version='matched-candidate-weak-direction-audit-v1',
                    study=primary['study'],
                    manifest_sha256=primary['manifest_sha256'],
                    summary_sha256=primary['summary_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root/PLAN).read_bytes()).hexdigest(),
                    fits=12,
                    median_weakest_to_strongest_ratio=float(statistics.median(
                        row['weakest_to_strongest_ratio'] for row in cases.values())),
                    summary=summary,cases=cases,new_fits=0,original_reads=0,
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
        raise ValueError('fresh verified weak-direction report required')
    result=build(args.root)
    atomic(target,encoded(result))
    print(json.dumps(dict(fits=result['fits'])))


if __name__=='__main__':
    main()
