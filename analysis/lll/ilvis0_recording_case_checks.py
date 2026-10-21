# SPDX-License-Identifier: AGPL-3.0-or-later
"""Callback-driven acceptance calculation, extracted without changing qualified limits."""

def evaluate_case(task,case,*,native,bound):
    import numpy as np
    config=case["configuration"]
    center=np.array(case["center"]);lo=np.array(case["lower"]);hi=np.array(case["upper"])
    scale=np.array(case["coordinate_scale"])
    calls=0;bounds=0;n=len(case["dt"])
    value,jac=native(center);report,reference=bound(center,lo,hi)
    maximum=float(np.max(abs(value-report.center)*scale));passed=maximum<=1e-6;extra={};probes=[]
    augmented=report.design(jac,reference)
    if augmented.shape!=(3,51) or not np.array_equal(augmented[:,:27],jac):raise ValueError('a physical or common column disappeared')
    if task['kind']=='tangent':
        errors=[];step=.002
        for axis in range(27):
            delta=np.zeros(27);delta[axis]=step
            left=bound(center-delta,center-delta,center-delta)[0].center
            right=bound(center+delta,center+delta,center+delta)[0].center
            errors.append(((right-left)/(2*step)-jac[:,axis])*scale)
        error=float(np.max(abs(np.array(errors))));passed=passed and error<=2e-5
        extra=dict(tangent_errors_m_per_normalized_parameter=errors,maximum_tangent_error=error,tangent_columns=27)
    else:
        for point in (lo,hi,center+.7*(hi-center)):
            actual,_=native(point)
            gamma=np.r_[reference.normalized_values_at(point)]
            error=abs((actual-value-augmented@np.r_[point-center,gamma])*scale)
            inside=bool(np.all(abs(gamma)<=1+1e-11));contained=bool(np.all(error<=report.unshared_remainder*scale+1e-5))
            passed=passed and inside and contained
            probes.append(dict(point=point,normalized_common_errors=gamma,common_inside_bound=inside,factored_taylor_error_m=error,contained=contained))
        if task['kind']=='stationary':
            known=float(np.max(abs(report.center-config['initial_c'])*scale));passed=passed and known<=1e-6
            extra['independent_pose_error_m']=known
    return dict(identity=task['identity'],kind=task['kind'],passed=bool(passed),physical_parameter_count=27,enclosure_parameter_count=51,
        maximum_center_error_m=maximum,
        bound=report.report(),reference=reference.report(),previous_reference=reference.parent.report(),probes=probes,
        native_jacobian=jac,augmented_design=augmented,coordinate_scale=scale,**extra,
        original_reads=0,optimizer_starts=0,floating_point_enclosure_verified=False,observational_coverage_qualified=False,scientific_decision='abstain')

