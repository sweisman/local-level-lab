# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small independent Cartesian 3-D physical controls; no archive inputs or fits.

Exact rotating-body force integrals generate measurements. An independent midpoint
reconstruction is checked against the existing Python strapdown primitive. This is
not end-to-end qualification of the nonlinear geographic/native archive fitter.
"""
import math
import numpy as np

from . import ilvis0_forward as forward

VERSION='ilvis0-coupled-cartesian-controls-v1'


def skew(value):
    x,y,z=value
    return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])


def coefficients(angle):
    square=angle*angle
    if angle<.01:
        return 1-square/6+square*square/120,.5-square/24+square*square/720,1/6-square/120+square*square/5040
    return math.sin(angle)/angle,(1-math.cos(angle))/square,(angle-math.sin(angle))/(angle*square)


def rotation(value):
    value=np.asarray(value,float)
    if value.shape!=(3,) or not np.all(np.isfinite(value)): raise ValueError('finite rotation vector required')
    a,b,_=coefficients(float(np.linalg.norm(value))); k=skew(value)
    return np.eye(3)+a*k+b*k@k


def force_integral(theta,body_force,period):
    # Integral exp(-[omega] t) dt, independent of the production midpoint formula.
    _,b,c=coefficients(float(np.linalg.norm(theta))); k=skew(theta)
    return period*(np.eye(3)-b*k+c*k@k)@body_force


def fixture(near_boundary=False):
    period=.005; packets_per_leg=400
    rates=np.repeat(np.array([[.012,-.008,.010],[-.010,.015,.008],[.006,-.012,-.010],
        [-.005,-.007,.016],[.015,.011,-.006],[-.008,.006,.012]]),packets_per_leg,axis=0)
    acceleration=np.repeat(np.array([[.03,-.02,.01],[-.02,.04,-.005],[.01,-.03,.003],
        [-.04,.01,-.002],[.02,.02,.004],[.015,-.025,-.004]]),packets_per_leg,axis=0)
    gravity=np.array([0.,0.,9.81+(.0499 if near_boundary else .002)])
    calibration=dict(gyro_gain=np.array([.0199,-.0198,.0197] if near_boundary else [.002,-.003,.005]),
        gyro_bias=np.radians([.99,-.98,.97] if near_boundary else [.2,-.3,.1])/3600,
        accel_gain=np.array([.149,-.149,.149] if near_boundary else [.0003,-.0002,.0005]),
        accel_bias=np.array([.249,-.249,.249] if near_boundary else [.015,-.02,.025]))
    initial=rotation([.02,-.01,.015]); mount=rotation([.012,-.006,.009])
    c=initial.copy(); v=np.array([220.,30.,.1]); p=np.zeros(3)
    attitudes=[c.copy()]; velocities=[v.copy()]; positions=[p.copy()]; theta=[]; dv=[]
    for w,a in zip(rates,acceleration):
        angle=w*period; increment=force_integral(angle,c.T@(a-gravity),period)
        theta.append(angle); dv.append(increment)
        p=p+v*period+a*period**2/2; v=v+a*period; c=c@rotation(angle)
        attitudes.append(c.copy()); velocities.append(v.copy()); positions.append(p.copy())
    theta=np.array(theta); dv=np.array(dv)
    return dict(period_s=period,rates=rates,acceleration=acceleration,gravity=gravity,
        calibration=calibration,mount_sensor_to_body=mount,initial_attitude=initial,
        truth_attitudes=np.array(attitudes),truth_velocities=np.array(velocities),truth_positions=np.array(positions),
        true_theta=theta,true_dv=dv,
        logged_theta=(theta@mount)*(1+calibration['gyro_gain'])+period*calibration['gyro_bias'],
        logged_dv=(dv@mount)*(1+calibration['accel_gain'])+period*calibration['accel_bias'])


def correct(fixture,calibration,period):
    if not math.isfinite(period) or period<=0: raise ValueError('positive finite clock period required')
    for name in ('gyro_gain','gyro_bias','accel_gain','accel_bias'):
        value=np.asarray(calibration[name],float)
        if value.shape!=(3,) or not np.all(np.isfinite(value)) or name.endswith('gain') and np.any(value<=-1):
            raise ValueError('invalid calibration')
    mount=fixture['mount_sensor_to_body']
    theta=((fixture['logged_theta']-period*calibration['gyro_bias'])/(1+calibration['gyro_gain']))@mount.T
    dv=((fixture['logged_dv']-period*calibration['accel_bias'])/(1+calibration['accel_gain']))@mount.T
    return theta,dv


def reconstruct(f,period,calibration,initial_velocity,gravity,check_primitive=False):
    theta,dv=correct(f,calibration,period)
    c=f['initial_attitude'].copy(); v=np.array(initial_velocity,float); p=np.zeros(3)
    rows=[]; primitive_difference=0.
    for i,(angle,increment) in enumerate(zip(theta,dv)):
        middle=c@rotation(angle/2)
        new_v=v+middle@increment+gravity*period
        delta_p=(v+new_v)*period/2
        new_c=c@rotation(angle)
        if check_primitive:
            other_c,other_v,other_delta=forward.local_step(c,v,angle,increment,period,np.zeros(3),np.zeros(3),gravity)
            primitive_difference=max(primitive_difference,float(np.max(abs(other_c-new_c))),
                float(np.max(abs(other_v-new_v))),float(np.max(abs(other_delta-delta_p))))
        c,v,p=new_c,new_v,p+delta_p
        error=p-f['truth_positions'][i+1]; relative=c.T@f['truth_attitudes'][i+1]
        sine=np.linalg.norm([relative[2,1]-relative[1,2],relative[0,2]-relative[2,0],relative[1,0]-relative[0,1]])/2
        attitude_error=math.atan2(sine,(np.trace(relative)-1)/2)
        rows.append(dict(time_by_packet_index_s=(i+1)*f['period_s'],
            north_error_m=float(error[0]),east_error_m=float(error[1]),down_error_m=float(error[2]),
            attitude_error_rad=attitude_error,velocity_error_mps=float(np.linalg.norm(v-f['truth_velocities'][i+1]))))
    errors=np.array([[r[k] for k in ('north_error_m','east_error_m','down_error_m')] for r in rows])
    return dict(maximum_position_error_m=float(np.max(np.linalg.norm(errors,axis=1))),
        maximum_horizontal_error_m=float(np.max(np.linalg.norm(errors[:,:2],axis=1))),
        maximum_vertical_error_m=float(np.max(abs(errors[:,2]))),
        maximum_attitude_error_rad=max(r['attitude_error_rad'] for r in rows),
        maximum_velocity_error_mps=max(r['velocity_error_mps'] for r in rows),
        primitive_max_difference=primitive_difference,trace=rows)


def recover_calibration(f):
    # Known physical trajectory and mount supply the reference rates for this control.
    period=f['period_s']; mount=f['mount_sensor_to_body']; rows=[]
    for kind,truth,observed in (('gyro',f['true_theta'],f['logged_theta']),('accel',f['true_dv'],f['logged_dv'])):
        rates=truth@mount/period; measured=observed/period
        for axis in range(3):
            design=np.column_stack((rates[:,axis],np.ones(len(rates))))
            scaled=design/np.linalg.norm(design,axis=0)
            singular=np.linalg.svd(scaled,compute_uv=False)
            rank=int(np.sum(singular>singular[0]*1e-12))
            if rank!=2: raise ValueError('known control lacks calibration excitation')
            ls=np.linalg.lstsq(design,measured[:,axis],rcond=None)[0]
            q,r=np.linalg.qr(design,mode='reduced'); qr=np.linalg.solve(r,q.T@measured[:,axis])
            expected=np.array([1+f['calibration'][kind+'_gain'][axis],f['calibration'][kind+'_bias'][axis]])
            rows.append(dict(channel=kind,axis='xyz'[axis],rank=rank,
                normalized_condition_ratio=float(singular[0]/singular[-1]),
                maximum_gain_error=float(max(abs(ls[0]-expected[0]),abs(qr[0]-expected[0]))),
                maximum_bias_error=float(max(abs(ls[1]-expected[1]),abs(qr[1]-expected[1]))),
                methods_max_difference=float(np.max(abs(ls-qr)))))
    return dict(channels=rows,maximum_gain_error=max(r['maximum_gain_error'] for r in rows),
        maximum_bias_error=max(r['maximum_bias_error'] for r in rows),
        reference_attitude_velocity_mount_clock_known=True,nonlinear_solver_qualified=False)


def run_control(near_boundary=False):
    f=fixture(near_boundary); scale=1.00005; period=f['period_s']; original=f['calibration']
    compensated=dict(gyro_gain=original['gyro_gain'],gyro_bias=original['gyro_bias']/scale,
        accel_gain=scale*(1+original['accel_gain'])-1,accel_bias=original['accel_bias']/scale)
    configurations=(('correct_clock',period,original,f['truth_velocities'][0],f['gravity']),
        ('wrong_clock',period*scale,original,f['truth_velocities'][0],f['gravity']),
        ('coupled_compensation',period*scale,compensated,f['truth_velocities'][0]/scale,f['gravity']/scale**2))
    results={name:reconstruct(f,dt,cal,v,g,check_primitive=name=='correct_clock')
        for name,dt,cal,v,g in configurations}
    recovery=recover_calibration(f)
    # Evaluate the independent piecewise-quadratic path at external physical time,
    # rather than associating receiver observations only by packet index.
    external_times=np.arange(1,len(f['rates'])+1)*period
    shifted_times=external_times/scale
    index=np.minimum(np.floor(shifted_times/period).astype(int),len(f['rates'])-1)
    remainder=shifted_times-index*period
    alternative_path=(f['truth_positions'][index]+f['truth_velocities'][index]*remainder[:,None]+
        f['acceleration'][index]*remainder[:,None]**2/2)
    external_error=float(np.max(np.linalg.norm(alternative_path-f['truth_positions'][1:],axis=1)))
    good=results['correct_clock']; bad=results['wrong_clock']; paired=results['coupled_compensation']
    passed=(good['maximum_position_error_m']<5e-4 and bad['maximum_position_error_m']>.01 and
        paired['maximum_position_error_m']<5e-4 and paired['maximum_attitude_error_rad']<1e-9 and
        good['primitive_max_difference']<1e-9 and recovery['maximum_gain_error']<1e-8 and
        recovery['maximum_bias_error']<1e-9 and external_error>.01)
    return dict(version=VERSION,control='near_boundary' if near_boundary else 'interior',
        duration_s=len(f['rates'])*period,packets=len(f['rates']),clock_scale=scale,
        external_time_max_position_error_m=external_error,
        external_time_trace=[dict(time_by_packet_index_s=float(t),north_error_m=float(e[0]),
            east_error_m=float(e[1]),down_error_m=float(e[2])) for t,e in
            zip(external_times,alternative_path-f['truth_positions'][1:])],
        **results,calibration_recovery=recovery,production_primitive_max_difference=good['primitive_max_difference'],
        coupled_parameter_changes=dict(gravity_down_mps2=float(f['gravity'][2]*(scale**-2-1)),
            initial_velocity_mps=(f['truth_velocities'][0]*(1/scale-1)).tolist(),
            accel_gain_fraction=(compensated['accel_gain']-original['accel_gain']).tolist()),
        passed=bool(passed),observed_fit_starts=0,native_predictions=0,
        python_primitive_steps=len(f['rates']),independent_midpoint_steps=3*len(f['rates']),
        epoch_association='Known packet index; no independently time-tagged receiver stream',
        full_archival_solver_qualified=False,scientific_decision='abstain')
