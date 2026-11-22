# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reconstruct a saved bounded stability candidate without native calls."""

import math
import hashlib
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import lsq_linear

from .ilvis0_solver_refinement import POLICY

VERSION='ilvis0-saved-bounded-correction-v1'
STUDY='data/ilvis0-remaining-prediction-transfer-20261118'
MANIFEST_SHA256='3cc9a72f3c3f3fa10c3f867fe31443fecfb7ee320dcb3567692d0af678c2863e'
FROZEN_SOLVER_SHA256='442dd52979f4db0973a29c7553ab5b0f02ba90e847dbea2f7db99735ade1db0f'


def reconstruct(fit):
    local=fit.get('local_linearization',{})
    probe=fit.get('stability_probe',{})
    point=np.asarray(local.get('normalized_parameters'),float)
    residual=np.asarray(local.get('residual'),float)
    jacobian=np.asarray(local.get('jacobian'),float)
    if (point.ndim!=1 or not len(point) or residual.ndim!=1 or not len(residual)
            or jacobian.shape!=(len(residual),len(point))
            or not all(np.all(np.isfinite(a)) for a in (point,residual,jacobian))
            or np.any(abs(point)>1.) or not isinstance(probe,dict)
            or probe.get('reason')!='fresh_position_probe_not_stable'):
        raise ValueError('complete saved nonpassing bounded probe required')
    cost=float(residual@residual)
    if not math.isclose(cost,fit.get('residual_sum_squares',float('nan')),
                        rel_tol=1e-10,abs_tol=1e-10):
        raise ValueError('saved residual cost differs')
    correction=lsq_linear(jacobian,-residual,bounds=(-1-point,1-point),
        method='bvls',tol=POLICY['stability_probe_linear_tolerance'],
        max_iter=POLICY['stability_probe_linear_maximum_iterations'])
    if not correction.success or not np.all(np.isfinite(correction.x)):
        raise ValueError('saved bounded correction did not solve')
    candidate=np.clip(point+correction.x,-1.,1.)
    predicted=residual+jacobian@correction.x
    predicted_cost=float(predicted@predicted)
    change=abs(predicted_cost-cost)/max(predicted_cost,cost,1.)
    step=float(np.linalg.norm(predicted-residual)/max(np.linalg.norm(residual),1.))
    distance=float(np.linalg.norm(candidate-point))
    for key,value in (('predicted_cost_change',change),
                      ('predicted_residual_step',step),
                      ('normalized_parameter_step',distance)):
        saved=probe.get(key)
        if (not isinstance(saved,(int,float)) or not math.isfinite(saved)
                or not math.isclose(value,saved,rel_tol=1e-6,abs_tol=1e-10)):
            raise ValueError('reconstructed bounded probe differs from saved receipt: '+key)
    return dict(version=VERSION,candidate_parameters=candidate.tolist(),
                predicted_cost_change=change,predicted_residual_step=step,
                normalized_parameter_step=distance,native_calls=0,
                forecast_computed=False,scientific_decision='abstain')


def build(root='.'):
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    study=ClosedStudy(root,STUDY)
    try:
        frozen=study.manifest['sources'].get('analysis/lll/ilvis0_solver_refinement.py')
        current=hashlib.sha256((root/'analysis/lll/ilvis0_solver_refinement.py').read_bytes()).hexdigest()
        packages=study.manifest['environment']['packages']
        if (study.completion['manifest_sha256']!=MANIFEST_SHA256
                or study.completion['state'] not in ('complete','terminal')
                or len(study.tasks)!=80 or frozen!=current or current!=FROZEN_SOLVER_SHA256
                or packages!={'numpy':np.__version__,'scipy':scipy.__version__}):
            raise ValueError('exact sealed solver and numerical environment required')
        candidates=[]
        for identity in study.tasks:
            fit=study.artifact(identity,'fit.json')
            if fit['stability_probe']['reason']=='fresh_position_probe_not_stable':
                candidate=reconstruct(fit)
                candidate['identity']=identity
                candidates.append(candidate)
        if len(candidates)!=49:
            raise ValueError('saved failed-probe population differs')
        return dict(version=VERSION,study=STUDY,manifest_sha256=MANIFEST_SHA256,
                    completion_summary_sha256=study.completion['summary_sha256'],
                    solver_source_sha256=frozen,
                    audit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    packages=packages,starts=80,reconstructed_candidates=len(candidates),
                    candidates=candidates,native_calls=0,original_reads=0,
                    withheld_positions_read=0,refits=0,forecast_computed=False,
                    failures_reclassified=False,scientific_decision='abstain')
    finally:
        study.close()


def publish(root='.'):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve()
    report=build(root)
    target=root/'docs/prediction-group-transfer/remaining-correction-candidates.json'
    atomic(target,encoded(report))
    return report


if __name__=='__main__':
    report=publish()
    print({key:report[key] for key in ('starts','reconstructed_candidates',
                                      'native_calls','forecast_computed')})
