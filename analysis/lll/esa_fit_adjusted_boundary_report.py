# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only local profiles of active calibration bounds in generated ESA fits."""

import argparse
import hashlib
import json
from pathlib import Path


def profile_one_bound(residual,jacobian,*,active_index,free_indices,
                      normalized_value):
    """Linearized one-bound profile after projecting unconstrained columns.

    This is a tangent calculation at the saved fit, not a nonlinear refit or
    a confidence interval. Other active coordinates remain fixed at bounds.
    """
    import numpy as np

    r=np.asarray(residual,dtype=float)
    j=np.asarray(jacobian,dtype=float)
    free=list(free_indices)
    if (r.ndim!=1 or j.ndim!=2 or j.shape[0]!=len(r) or
            not 0<=active_index<j.shape[1] or
            len(set(free))!=len(free) or active_index in free or
            any(type(index) is not int or not 0<=index<j.shape[1]
                for index in free) or
            normalized_value not in (-1.,1.) or
            not np.all(np.isfinite(r)) or not np.all(np.isfinite(j))):
        raise ValueError('finite saved tangent and declared active bound required')
    column=j[:,active_index]
    if free:
        free_matrix=j[:,free]
        coefficients,_,rank,_=np.linalg.lstsq(
            free_matrix,np.column_stack((r,column)),rcond=1e-8)
        projected_r=r-free_matrix@coefficients[:,0]
        projected_j=column-free_matrix@coefficients[:,1]
    else:
        rank=0;projected_r=r;projected_j=column
    curvature=float(projected_j@projected_j)
    slope=float(2*projected_j@projected_r)
    estimable=bool(curvature>max(1e-20,1e-12*float(column@column)))
    step=float(-slope/(2*curvature)) if estimable else None
    gain=float(slope*slope/(4*curvature)) if estimable else None
    return dict(free_rank=int(rank),slope=slope,curvature=curvature,
        estimable=estimable,unbounded_step=step,
        local_cost_gain_if_unbounded=gain,
        unbounded_step_points_outside=(bool(step<0) if normalized_value==-1.
                                       else bool(step>0)) if estimable else None,
        nonlinear_refit_performed=False,scientific_decision='abstain')


def profile_active_set(residual,jacobian,*,active_indices,free_indices,
                       normalized_values):
    """Remove all active bounds in one local linear profile, keeping free
    nuisance directions projected out. The result is descriptive only.
    """
    import numpy as np

    r=np.asarray(residual,dtype=float)
    j=np.asarray(jacobian,dtype=float)
    active=list(active_indices);free=list(free_indices)
    values=list(normalized_values)
    if (r.ndim!=1 or j.ndim!=2 or j.shape[0]!=len(r) or
            not active or len(active)!=len(values) or
            len(set(active))!=len(active) or len(set(free))!=len(free) or
            set(active)&set(free) or
            any(type(index) is not int or not 0<=index<j.shape[1]
                for index in active+free) or
            any(value not in (-1.,1.) for value in values) or
            not np.all(np.isfinite(r)) or not np.all(np.isfinite(j))):
        raise ValueError('finite saved tangent and complete active set required')
    active_matrix=j[:,active]
    if free:
        free_matrix=j[:,free]
        coefficients,_,free_rank,_=np.linalg.lstsq(
            free_matrix,np.column_stack((r,active_matrix)),rcond=1e-8)
        residual_r=r-free_matrix@coefficients[:,0]
        residual_active=active_matrix-free_matrix@coefficients[:,1:]
    else:
        free_rank=0;residual_r=r;residual_active=active_matrix
    steps,_,active_rank,_=np.linalg.lstsq(
        residual_active,-residual_r,rcond=1e-8)
    fitted=residual_r+residual_active@steps
    gain=max(0.,float(residual_r@residual_r-fitted@fitted))
    identifiable=bool(active_rank==len(active))
    outside=(any(value+float(step)<-1. or value+float(step)>1.
                 for value,step in zip(values,steps,strict=True))
             if identifiable else None)
    return dict(free_rank=int(free_rank),
        active_rank_after_free_projection=int(active_rank),
        all_active_directions_estimable=identifiable,
        local_cost_gain_if_all_unbounded=gain,
        unbounded_steps=[float(value) for value in steps],
        unbounded_solution_outside_bounds=outside,
        nonlinear_refit_performed=False,scientific_decision='abstain')


def build(root):
    import numpy as np
    from .esa_fit_adjusted_control_report import build as control_build
    from .esa_fit_adjusted_control_study import ID,LAWS
    from .studies.closed import ClosedStudy

    root=Path(root).resolve()
    control=control_build(root)
    study=ClosedStudy(root,'data/'+ID)
    try:
        if (study.completion['state']!='complete' or
                control['study_manifest_sha256']!=study.completion['manifest_sha256'] or
                set(study.tasks)!=set(LAWS)):
            raise ValueError('sealed matching generated control required')
        cases={}
        for truth in LAWS:
            fits={}
            for law in LAWS:
                fit=study.artifact(truth,law+'/fit.json')
                local=fit['local_linearization']
                parameters=fit['active_parameters']
                values=fit['normalized_parameters']
                residual=np.asarray(local['residual'],dtype=float)
                jacobian=np.asarray(local['jacobian'],dtype=float)
                bounds=fit['active_bounds']
                if (fit['converged'] is not True or
                        fit['stopping_rule_verified'] is not True or
                        control['cases'][truth]['candidates'][law]['status']!='bound_active' or
                        local.get('convention')!=
                            'whitened residual derivative by normalized parameter' or
                        local.get('active_parameters')!=parameters or
                        residual.shape!=(1800,) or
                        jacobian.shape!=(1800,26) or
                        len(parameters)!=26 or len(values)!=26 or
                        len(set(parameters))!=26 or
                        not bounds or any(name not in parameters for name in bounds) or
                        not np.all(np.isfinite(residual)) or
                        not np.all(np.isfinite(jacobian)) or
                        abs(float(residual@residual)-fit['residual_sum_squares'])>
                            max(1e-8,1e-10*fit['residual_sum_squares'])):
                    raise ValueError('complete consistent saved boundary tangent required')
                free=[index for index,name in enumerate(parameters)
                      if name not in bounds]
                profiles={name:profile_one_bound(residual,jacobian,
                    active_index=parameters.index(name),free_indices=free,
                    normalized_value=values[parameters.index(name)])
                    for name in bounds}
                joint=profile_active_set(residual,jacobian,
                    active_indices=[parameters.index(name) for name in bounds],
                    free_indices=free,
                    normalized_values=[values[parameters.index(name)]
                                       for name in bounds])
                fits[law]=dict(training_cost=fit['residual_sum_squares'],
                    evaluations=fit['evaluations'],active_bounds=profiles,
                    joint_active_profile=joint,
                    tangent_replay_verified=True,
                    scientific_decision='abstain')
            cases[truth]=fits
        return dict(version='esa-fit-adjusted-boundary-report-v1',
            study='data/'+ID,
            study_manifest_sha256=study.completion['manifest_sha256'],
            study_summary_sha256=study.completion['summary_sha256'],
            control_report_source_sha256=control['report_source_sha256'],
            report_source_sha256=hashlib.sha256((root/
                'analysis/lll/esa_fit_adjusted_boundary_report.py').read_bytes()
                ).hexdigest(),
            cases=cases,generated_recordings=2,attempted_fits=4,
            nonlinear_refit_performed=False,
            protected_confirmation_groups_opened=0,
            scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    result=build(args.root)
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({truth:{law:list(row['active_bounds'])
        for law,row in fits.items()} for truth,fits in result['cases'].items()},
        sort_keys=True))


if __name__=='__main__':
    main()
