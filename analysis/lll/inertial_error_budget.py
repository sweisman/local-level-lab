# SPDX-License-Identifier: AGPL-3.0-or-later
"""Analytic local-level white-noise example, separate from flight inference.

Perfect initial state, constant gravity, small angles and no future aiding.
These kernels describe a stated stochastic model, not measured archive errors.
"""
import itertools
import math


def level_position_covariance(t,u,*,gyro_white,accel_white,gravity):
    """Per-axis position covariance at two times since perfect initialization.

    ``gyro_white`` has units rad/sqrt(s); ``accel_white`` has m/s/sqrt(s).
    Angular noise tilts gravity into the two horizontal axes. Force noise is
    isotropic. The independent drivers give zero cross-axis covariance here.
    """
    values=(t,u,gyro_white,accel_white,gravity)
    if not all(math.isfinite(x) for x in values) or min(values[:4])<0 or gravity<=0:
        raise ValueError('finite nonnegative times/noise and positive gravity required')
    m=min(t,u);d=abs(t-u)
    # Integrate after substituting w=m-s. All polynomial terms are positive,
    # avoiding cancellation when t and u are close.
    try:
        gyro=gravity**2*gyro_white**2/4*(m**5/5+d*m**4/2+d*d*m**3/3)
        force=accel_white**2*(m**3/3+d*m*m/2)
        horizontal=gyro+force
    except OverflowError as error:raise ValueError('unrepresentable level covariance') from error
    if not math.isfinite(horizontal) or not math.isfinite(force):raise ValueError('unrepresentable level covariance')
    return dict(north_east_m2=horizontal,up_m2=force)


def level_error_budget(times,*,gyro_white,accel_white,gravity):
    """Marginal error scales; sqrt(E[mean squared error]) is not E[sample RMS]."""
    times=list(itertools.islice(iter(times),2049))
    if (not 1<=len(times)<=2048 or not all(math.isfinite(t) and t>=0 for t in times)
            or any(b<=a for a,b in zip(times,times[1:]))):
        raise ValueError('one to 2048 finite ordered query horizons required')
    values=[level_position_covariance(t,t,gyro_white=gyro_white,accel_white=accel_white,gravity=gravity) for t in times]
    return dict(query_epochs=len(times),last_horizon_s=times[-1],
        gyro_white_rads_per_sqrt_s=gyro_white,accel_white_mps_per_sqrt_s=accel_white,gravity_mps2=gravity,
        endpoint_per_horizontal_axis_sd_m=math.sqrt(values[-1]['north_east_m2']),
        endpoint_vertical_sd_m=math.sqrt(values[-1]['up_m2']),
        sqrt_expected_mean_horizontal_squared_error_m=math.sqrt(math.fsum(2*v['north_east_m2'] for v in values)/len(values)),
        assumptions=dict(perfect_initial_state=True,constant_local_gravity=True,small_angles=True,
            continuous_independent_white_drivers=True,independent_axes=True,no_future_position_aiding=True,
            no_bias_drift_or_receiver_error=True),
        measured_instrument_noise=False,universal_estimator_lower_bound=False,
        scientific_decision='abstain')


def level_innovations(times,*,gyro_white,accel_white,gravity,receiver_loading,maximum_bytes):
    """Eight-state exact covariance for the declared constant-level example.

    Continuous process noise is integrated analytically over each actual time
    interval. This example is not a flight observation/error model.
    """
    import numpy as np
    from lll.state_space_covariance import LinearInnovations
    t=np.array(times,dtype=float,copy=True)
    if (t.ndim!=1 or not 1<=len(t)<=100000 or not np.all(np.isfinite(t)) or t[0]<0
            or np.any(np.diff(t)<=0)):raise ValueError('bounded nonnegative strictly ordered horizons required')
    level_position_covariance(0.,0.,gyro_white=gyro_white,accel_white=accel_white,gravity=gravity)
    receiver=np.array(receiver_loading,dtype=float,copy=True)
    if receiver.shape!=(3,3) or not np.all(np.isfinite(receiver)):raise ValueError('finite three-axis receiver loading required')
    observation=np.zeros((3,8));observation[0,2]=observation[1,5]=observation[2,7]=1.
    shape=np.array([[1.,0.,0.],[.5,1/math.sqrt(12),0.],[1/6,math.sqrt(3)/12,1/math.sqrt(720)]])
    def steps():
        previous=0.
        for time in t:
            dt=float(time-previous);previous=float(time);f=np.eye(8);b=np.zeros((8,12))
            force=accel_white*math.sqrt(dt)*np.array([[1.,0.],[dt/2,dt/math.sqrt(12)]])
            gyro=gyro_white*math.sqrt(dt)*np.array([1.,gravity*dt,gravity*dt*dt])[:,None]*shape
            for axis,start in enumerate((0,3)):
                f[start+1,start]=gravity*dt;f[start+2,start]=gravity*dt*dt/2;f[start+2,start+1]=dt
                b[start:start+3,3*axis:3*axis+3]=gyro
                b[start+1:start+3,6+2*axis:8+2*axis]=force
            f[7,6]=dt;b[6:8,10:12]=force
            yield dict(transition=f,process_loading=b,observation=observation,white_loading=receiver)
    return LinearInnovations(steps(),epoch_count=len(t),state_dimension=8,observation_dimension=3,
        initial_loading=None,maximum_bytes=maximum_bytes,design_is_fixed=True,error_distribution='gaussian')


def ou_level_dynamics(dt,*,gyro_white,accel_white,gyro_bias_sd,accel_bias_sd,
                      gyro_bias_tau_s,accel_bias_tau_s,gravity):
    """Exact continuous-linear transition/diffusion for a thirteen-state example.

    Positive drivers give full-rank process covariance. A failed factorization
    is rejected, with no zero-variance replacement or eigenvalue clipping.
    """
    parameters=(gyro_white,accel_white,gyro_bias_sd,accel_bias_sd,gyro_bias_tau_s,accel_bias_tau_s,gravity)
    if not math.isfinite(dt) or dt<0 or not all(math.isfinite(v) and v>0 for v in parameters):
        raise ValueError('nonnegative interval and positive finite declared noise/dynamics required')
    import numpy as np
    from scipy.linalg import expm
    from lll.ilvis0_error_model import factor
    if dt==0:return np.eye(13),np.zeros((13,0))
    a=np.zeros((13,13));diffusion=np.zeros((13,13))
    for start in (0,5):
        a[start,start+3]=1.;a[start+1,start]=gravity;a[start+1,start+4]=1.;a[start+2,start+1]=1.
        a[start+3,start+3]=-1/gyro_bias_tau_s;a[start+4,start+4]=-1/accel_bias_tau_s
        diffusion[start,start]=gyro_white**2;diffusion[start+1,start+1]=accel_white**2
        diffusion[start+3,start+3]=2*gyro_bias_sd**2/gyro_bias_tau_s
        diffusion[start+4,start+4]=2*accel_bias_sd**2/accel_bias_tau_s
    a[10,12]=1.;a[11,10]=1.;a[12,12]=-1/accel_bias_tau_s
    diffusion[10,10]=accel_white**2;diffusion[12,12]=2*accel_bias_sd**2/accel_bias_tau_s
    block=np.zeros((26,26));block[:13,:13]=a;block[:13,13:]=diffusion;block[13:,13:]=-a.T
    exponential=expm(block*dt);transition=exponential[:13,:13].copy()
    covariance=exponential[:13,13:]@transition.T
    if not np.all(np.isfinite(transition)):raise ValueError('unrepresentable continuous transition')
    return transition,factor((covariance+covariance.T)/2)


def ou_level_innovations(times,*,gyro_white,accel_white,gyro_bias_sd,accel_bias_sd,
                         gyro_bias_tau_s,accel_bias_tau_s,gravity,receiver_loading,maximum_bytes):
    """White plus stationary changing-bias example; no aircraft-error calibration."""
    import numpy as np
    from functools import lru_cache
    from lll.state_space_covariance import LinearInnovations
    t=np.array(times,dtype=float,copy=True)
    if (t.ndim!=1 or not 1<=len(t)<=100000 or not np.all(np.isfinite(t)) or t[0]<0
            or np.any(np.diff(t)<=0)):raise ValueError('bounded nonnegative strictly ordered horizons required')
    parameters=dict(gyro_white=gyro_white,accel_white=accel_white,gyro_bias_sd=gyro_bias_sd,
        accel_bias_sd=accel_bias_sd,gyro_bias_tau_s=gyro_bias_tau_s,accel_bias_tau_s=accel_bias_tau_s,gravity=gravity)
    ou_level_dynamics(0.,**parameters)  # Validate without calculating an exponential.
    receiver=np.array(receiver_loading,dtype=float,copy=True)
    if receiver.shape!=(3,3) or not np.all(np.isfinite(receiver)):raise ValueError('finite three-axis receiver loading required')
    observation=np.zeros((3,13));observation[0,2]=observation[1,7]=observation[2,11]=1.
    initial=np.zeros((13,5))
    for column,(row,sd) in enumerate(((3,gyro_bias_sd),(4,accel_bias_sd),(8,gyro_bias_sd),
            (9,accel_bias_sd),(12,accel_bias_sd))):initial[row,column]=sd
    @lru_cache(maxsize=16)
    def dynamics(dt):return ou_level_dynamics(dt,**parameters)
    def steps():
        previous=0.
        for time in t:
            dt=float(time-previous);previous=float(time);transition,loading=dynamics(dt)
            yield dict(transition=transition,process_loading=loading,observation=observation,white_loading=receiver)
    return LinearInnovations(steps(),epoch_count=len(t),state_dimension=13,observation_dimension=3,
        initial_loading=initial,maximum_bytes=maximum_bytes,design_is_fixed=True,error_distribution='gaussian')
