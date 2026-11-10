# SPDX-License-Identifier: AGPL-3.0-or-later
"""Globe/disc refinement diagnostics, without new predictions or optimizer starts."""
import math

VERSION = 'ilvis0-globe-disc-refinement-v1'


def constant_bias_example(signal_rads, bias_bound_rads):
    """An additive constant gyro contrast can be absorbed by bounded constant bias.

    This algebraic control is not a flight fit or a statement that the real
    contrast is constant. Bias is per axis; an actual varying contrast needs
    independent geometry and a complete nonlinear profile.
    """
    signal=tuple(float(x) for x in signal_rads)
    if len(signal)!=3 or any(not math.isfinite(x) for x in signal) or not math.isfinite(bias_bound_rads) or bias_bound_rads<0:
        raise ValueError('finite three-vector and nonnegative bound required')
    bias=tuple(max(-bias_bound_rads,min(bias_bound_rads,x)) for x in signal)
    remaining=tuple(a-b for a,b in zip(signal,bias))
    return dict(signal_rads=signal,fitted_constant_bias_rads=bias,remaining_rads=remaining,
                fully_absorbed=all(x==0 for x in remaining),scope='constant additive contrast only')


def motion_scales(speed_mps, radius_m=6371000., gyro_bias_bound_dph=20., accel_bias_bound_mps2=.25):
    if not all(math.isfinite(x) and x>0 for x in (speed_mps,radius_m,gyro_bias_bound_dph,accel_bias_bound_mps2)):
        raise ValueError('positive finite scales required')
    curvature=speed_mps/radius_m*180/math.pi*3600
    centripetal=speed_mps*speed_mps/radius_m
    return dict(speed_mps=speed_mps,horizontal_curvature_dph=curvature,
                gyro_bound_to_curvature_ratio=gyro_bias_bound_dph/curvature,
                centripetal_acceleration_mps2=centripetal,
                accel_bound_to_centripetal_ratio=accel_bias_bound_mps2/centripetal,
                interpretation='conditional spherical scale comparison, not a measured signal or complete globe/disc contrast')


def globe_disc_profile(fits):
    """Globe is the union of the two preregistered globe candidates.

    Both globe optimizations and the disc optimization must be resolved before
    using their minima in a family comparison. Convergence is still local and
    covariance/bounds remain assumptions; no calibrated decision is emitted.
    """
    names=('sphere_rotating','sphere_still','flat_still')
    if len(fits)!=3 or {f.get('model') for f in fits}!=set(names):
        raise ValueError('exactly three distinct candidate fits required')
    rows={f['model']:f for f in fits}
    unresolved=[]
    for name in names:
        f=rows[name];stationarity=f.get('exact_projected_gradient_relative')
        if ('error' in f or not f.get('converged') or stationarity is None
                or not math.isfinite(stationarity) or stationarity>1e-4):unresolved.append(name)
    out=dict(version=VERSION,scientific_decision='abstain',calibrated=False,
             unresolved_optimizations=unresolved,globes=list(names[:2]),
             scope='local conditional profile costs, not a global optimum or hypothesis test')
    if unresolved:return dict(out,conditional_disc_minus_globe_cost=None)
    costs={name:rows[name].get('residual_sum_squares') for name in names}
    if any(not isinstance(x,(int,float)) or not math.isfinite(x) or x<0 for x in costs.values()):
        raise ValueError('finite nonnegative matched profile costs required')
    globe=min(costs['sphere_rotating'],costs['sphere_still'])
    return dict(out,conditional_disc_minus_globe_cost=costs['flat_still']-globe,
                globe_profile_cost=globe,disc_profile_cost=costs['flat_still'])
