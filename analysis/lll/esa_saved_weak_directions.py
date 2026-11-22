# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only weak directions in the opened ESA development matrix."""

import hashlib
import json
import statistics
from pathlib import Path

STUDY='data/esa-rolling-origin-400-model-matrix-20261118'
PLAN='docs/prediction-observed-development/ESA_SAVED_WEAK_DIRECTION_PLAN.md'
GENERATED='docs/prediction-observed-development/matched-candidates-weak-directions.json'


def build(root):
    import numpy as np
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    generated=json.loads((root/GENERATED).read_bytes())
    if (generated.get('fits')!=12 or generated.get('new_fits')!=0
            or generated.get('scientific_decision')!='abstain'):
        raise ValueError('sealed generated comparison report required')
    study=ClosedStudy(root,STUDY)
    try:
        if study.completion['state'] not in ('complete','terminal') or len(study.tasks)!=24:
            raise ValueError('exact sealed opened ESA development matrix required')
        rows={};converged=[]
        for identity,task in sorted(study.tasks.items()):
            payload=task['payload']
            if (payload['model'] not in ('sphere_rotating','sphere_still','flat_still')
                    or type(payload['profile']) is not bool
                    or payload['law'] not in ('increment','point')
                    or payload['start'] not in (0,1)):
                raise ValueError('unchanged ESA development candidate identity required')
            status=study.rows[identity]['status']
            if status!='complete':
                rows[identity]=dict(status=status,numerical_converged=False,
                                    candidate_model=payload['model'],
                                    profile=payload['profile'])
                continue
            fit=study.artifact(identity,'fit.json')
            row=dict(status='complete',
                     numerical_converged=fit.get('converged') is True,
                     candidate_model=payload['model'],profile=payload['profile'],
                     input_law=payload['law'],start=payload['start'])
            if row['numerical_converged']:
                local=fit['local_linearization']
                names=local['active_parameters']
                matrix=np.asarray(local['jacobian'],float)
                saved=np.asarray(fit['singular_values'],float)
                p=len(names)
                if (local.get('convention')!=
                        'whitened residual derivative by normalized parameter'
                        or names!=fit['active_parameters'] or p!=26+int(payload['profile'])
                        or matrix.ndim!=2 or matrix.shape[1]!=p
                        or matrix.shape[0]<p or not np.all(np.isfinite(matrix))
                        or saved.shape!=(p,) or np.any(saved<=0)):
                    raise ValueError('complete saved ESA local training Jacobian required')
                _,singular,vh=np.linalg.svd(matrix,full_matrices=False)
                if not np.allclose(singular,saved,rtol=1e-8,atol=1e-9):
                    raise ValueError('ESA saved singular values fail independent SVD')
                absolute=np.abs(vh[-1]);top=sorted(range(p),key=lambda i:-absolute[i])[:3]
                normalized=dict(zip(names,fit['normalized_parameters'],strict=True))
                row.update(weakest_to_strongest_ratio=float(singular[-1]/singular[0]),
                           weakest_loading_magnitude={name:float(absolute[i])
                                                      for i,name in enumerate(names)},
                           top_three=[names[i] for i in top],
                           near_bound={name:abs(normalized[name])>=.99
                                       for name in names})
                converged.append(row)
            rows[identity]=row
        if len(rows)!=24 or len(converged)!=20:
            raise ValueError('unchanged 24-task, 20-converged ESA development result required')
        groups={}
        for model in ('sphere_rotating','sphere_still','flat_still'):
            for profile in (False,True):
                key=model+'-profile-'+str(int(profile))
                group=[row for row in converged if row['candidate_model']==model
                       and row['profile'] is profile]
                groups[key]=dict(converged=len(group),
                                 gyro_bias_z_top_three=sum('gyro_bias_z' in row['top_three']
                                                           for row in group),
                                 gyro_bias_z_top_one=sum(row['top_three'][0]=='gyro_bias_z'
                                                         for row in group),
                                 median_weakest_to_strongest_ratio=(
                                     float(statistics.median(
                                         row['weakest_to_strongest_ratio']
                                         for row in group)) if group else None))
        return dict(version='esa-saved-weak-direction-comparison-v1',
                    study=STUDY,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    generated_report_sha256=hashlib.sha256(
                        (root/GENERATED).read_bytes()).hexdigest(),
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root/PLAN).read_bytes()).hexdigest(),
                    tasks_total=24,numerical_converged=20,
                    gyro_bias_z_top_three=sum('gyro_bias_z' in row['top_three']
                                              for row in converged),
                    gyro_bias_z_top_one=sum(row['top_three'][0]=='gyro_bias_z'
                                            for row in converged),
                    median_weakest_to_strongest_ratio=float(statistics.median(
                        row['weakest_to_strongest_ratio'] for row in converged)),
                    groups=groups,cases=rows,new_fits=0,
                    reserved_esa_group_reads=0,
                    scientific_decision='abstain')
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
        raise ValueError('fresh verified ESA weak-direction report required')
    result=build(args.root)
    atomic(target,encoded(result))
    print(json.dumps({key:result[key] for key in
                      ('tasks_total','numerical_converged',
                       'gyro_bias_z_top_three','gyro_bias_z_top_one')}))


if __name__=='__main__':
    main()
