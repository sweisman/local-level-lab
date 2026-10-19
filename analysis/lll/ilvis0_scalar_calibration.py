# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local calibration ambiguity of scalar specific force, never a model verdict.

One seven-coordinate calibration is shared over the complete input history.
The tangent projection is unbounded and first order. It is not a bounded
nonlinear fit, confidence interval, or proof of identifiable model separation.
"""
import numpy as np


PARAMETERS=('gain_x','gain_y','gain_z','offset_x_mps2','offset_y_mps2',
            'offset_z_mps2','gravity_delta_mps2')


def analyze(body,force,limits,*,rcond=1e-10):
    """Project a zero-correction scalar residual against all calibration columns.

    body is the measured body-frame specific-force history; force is a
    candidate's declared required NED force at the base gravity. Both are in
    m/s². The caller supplies all seven positive symmetric calibration bounds.
    Gravity corrections increase downward gravity and subtract from force D.
    No receiver data, gyro, attitude, noise model or optimizer enters here.
    """
    body,force,limits=(np.asarray(value,float) for value in (body,force,limits))
    if (body.ndim!=2 or body.shape[1]!=3 or body.shape[0]==0
            or force.shape!=body.shape or not np.all(np.isfinite(body))
            or not np.all(np.isfinite(force))):
        raise ValueError('matching nonempty finite N by 3 force histories required')
    if (limits.shape!=(7,) or not np.all(np.isfinite(limits))
            or np.any(limits<=0.) or np.any(limits[:3]>=1.)):
        raise ValueError('seven positive finite bounds with gains below one required')
    if not np.isfinite(rcond) or not 0.<rcond<1.:
        raise ValueError('explicit finite relative rank tolerance between zero and one required')
    measured=np.linalg.norm(body,axis=1);required=np.linalg.norm(force,axis=1)
    if (not np.all(np.isfinite(measured)) or not np.all(np.isfinite(required))
            or np.any(measured<=np.finfo(float).tiny)
            or np.any(required<=np.finfo(float).tiny)):
        raise ValueError('nonzero representable force magnitudes required for derivatives')
    direction=body/measured[:,None]
    jacobian=np.column_stack((-direction*body,-direction,force[:,2]/required))*limits
    residual=measured-required
    u,singular,vt=np.linalg.svd(jacobian,full_matrices=False)
    retained=singular>rcond*singular[0]
    rank=int(np.sum(retained))
    coordinates=u[:,retained].T@residual
    step=-vt[retained].T@(coordinates/singular[retained])
    projected=residual-u[:,retained]@coordinates
    physical=step*limits
    feasible=bool(np.all(abs(step)<=1.))
    nonlinear=None
    if feasible:
        corrected=(body-physical[3:6])/(1.+physical[:3])
        target=force-np.array([0.,0.,physical[6]])
        actual=np.linalg.norm(corrected,axis=1)-np.linalg.norm(target,axis=1)
        nonlinear=float(np.linalg.norm(actual)/np.sqrt(len(actual)))
    return dict(parameters=PARAMETERS,scaled_jacobian=jacobian,singular_values=singular,
        rank=rank,relative_rank_tolerance=float(rcond),residual=residual,
        projected_residual=projected,linear_step_scaled=step,linear_step_physical=physical,
        linear_step_within_bounds=feasible,nonlinear_rms_at_linear_step_mps2=nonlinear,
        uncorrected_rms_mps2=float(np.linalg.norm(residual)/np.sqrt(len(residual))),
        projected_rms_mps2=float(np.linalg.norm(projected)/np.sqrt(len(projected))),
        nonlinear_identifiability_established=False,covariance_calibrated=False,
        scientific_decision='abstain')
