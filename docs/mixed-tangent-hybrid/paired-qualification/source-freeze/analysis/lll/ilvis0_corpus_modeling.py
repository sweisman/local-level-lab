# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite conditional corpus extension, preserving optimizer and instrument failures."""
import math
import numpy as np
from scipy.optimize import least_squares

from . import applanix as ap, ilvis0 as il, ilvis0_followup as follow
from . import ilvis0_installation as installation, ilvis0_forward as forward
from . import ilvis0_exploratory as explore, ilvis0_estimator as estimator

VERSION='ilvis0-conditional-corpus-v1'
SCALES={6:(installation.ANGLE_SCALE,installation.VELOCITY_SCALE),
        8:(2.**-18,2.**-14),21:(2.**-28,.3048*2.**-21)}


def bounded_fit(problem,model,*,maximum_evaluations=200,start=None):
    """Broyden updates economize finite differences; final exact Jacobian checks stationarity.

    Every actual residual prediction counts. Approximate Jacobians never establish
    convergence: final freshly differenced projected gradient must also be small.
    Reserve two Jacobian steps plus three recorded-data diagnostic predictions.
    """
    n=len(problem.bounds.active);point=np.zeros(n) if start is None else np.asarray(start,float)
    problem.bounds.decode(point)
    if maximum_evaluations<3*n+6 or maximum_evaluations>200:raise ValueError('insufficient explicit evaluation budget')
    calls=0;best=None;last=None;jac=None;anchor=None;accepted=0
    fit_limit=maximum_evaluations-2*n-4
    def evaluate(u,limit=fit_limit):
        nonlocal calls,best,last
        if calls>=limit:raise estimator.EvaluationLimit('bounded corpus evaluation limit')
        calls+=1;r=problem.residual(u,model);last=(u.copy(),r.copy())
        cost=float(r@r)
        if best is None or cost<best[0]:best=(cost,u.copy(),r.copy())
        return r
    def exact(u,base,limit):
        matrix=np.empty((len(base),n))
        for i in range(n):
            step=1e-4 if u[i]<=1-1e-4 else -1e-4
            shifted=u.copy();shifted[i]+=step
            matrix[:,i]=(evaluate(shifted,limit)-base)/step
        return matrix
    def derivative(u):
        nonlocal jac,anchor,accepted
        base=last[1].copy() if last is not None and np.array_equal(last[0],u) else evaluate(u)
        # Two refreshes leave enough iterations for the strongly nonlinear initial yaw.
        if jac is None or (accepted==12 and calls+n<fit_limit):
            jac=exact(u,base,fit_limit);accepted=0
        elif anchor is not None:
            delta=u-anchor[0];den=float(delta@delta)
            if den>1e-24:jac=jac+np.outer(base-anchor[1]-jac@delta,delta)/den
        anchor=(u.copy(),base.copy());accepted+=1
        return jac.copy()
    success=False;message='evaluation budget exhausted'
    try:
        sol=least_squares(evaluate,point,jac=derivative,bounds=(-1.,1.),method='trf',x_scale=1.,
            ftol=1e-7,xtol=1e-7,gtol=1e-7,max_nfev=fit_limit)
        success=bool(sol.success);message=str(sol.message)
    except estimator.EvaluationLimit as error:message=str(error)
    cost,point,residual=best
    matrix=exact(point,residual,maximum_evaluations-3)
    coarse=np.empty_like(matrix)
    for i in range(n):
        step=2e-4 if point[i]<=1-2e-4 else -2e-4
        shifted=point.copy();shifted[i]+=step
        coarse[:,i]=(evaluate(shifted,maximum_evaluations-3)-residual)/step
    gradient=matrix.T@residual;projected=gradient.copy()
    projected[(point<=-1+1e-6)&(gradient>0)]=0
    projected[(point>=1-1e-6)&(gradient<0)]=0
    scale=np.maximum(np.linalg.norm(matrix,axis=0),1.)*max(np.linalg.norm(residual),1.)
    stationarity=float(np.max(abs(projected)/scale)) if n else 0.
    disagreement=float(np.linalg.norm(matrix-coarse,ord=2))
    singular=np.linalg.svd(matrix,compute_uv=False);cutoff=max(float(singular[0])*1e-7,3*disagreement)
    return dict(version=VERSION,model=model,parameters=problem.bounds.decode(point),normalized_parameters=point.tolist(),
        active_parameters=list(problem.bounds.active),residual_sum_squares=cost,evaluations=calls,maximum_evaluations=maximum_evaluations,
        solver_reported_success=success,converged=success and stationarity<=1e-4,
        exact_projected_gradient_relative=stationarity,stationarity_tolerance=1e-4,message=message,
        singular_values=singular.tolist(),nuisance_rank=int(np.sum(singular>cutoff)),
        derivative_step_disagreement_norm=disagreement,active_bounds=[name for name,u in zip(problem.bounds.active,point) if abs(u)>=.999],
        processing_independence_established=False,calibration_bounds_supported=False,
        covariance_calibrated=False,scientific_eligible=False,scientific_decision='abstain')


def extract(path,context,*,maximum_seconds=600):
    """Select complete raw/GPS-supported geometry before inspecting any model residual.

    Motion is modeled rather than screened for steady cruise. This does NOT replace
    the earlier level-flight gate. Unusable packets split runs; frames never repaired.
    """
    if not context['timing']['accepted']:raise ValueError('unsupported UTC mapping')
    types=set(context['inspection']['imu_types'])
    if len(types)!=1 or int(next(iter(types))) not in SCALES:raise ValueError('unsupported/mixed IMU configuration')
    kind=int(next(iter(types)));angle_scale,velocity_scale=SCALES[kind]
    leap=context['timing']['gps_minus_utc_s'];runs=[];current=[];previous=None;signature=None;setting=None
    nmea=ap.NMEA();fixes={};excluded=0
    with il.open_source(path) as original:
        stream=follow.HashedReader(original)
        for frame in ap.frames(stream):
            if frame.tag=='$MSG' and frame.group in (1,20):
                s=installation.installation_message(frame)
                setting=np.array(s['imu_to_aircraft_rotation']) if s['usable'] else None
                signature=frame.packet[10:-4].hex()
            if frame.tag!='$GRP':continue
            if frame.group==10001:
                header=ap.time_header(frame);packet_time=follow.utc_tag(header,leap)
                for sentence in nmea.feed(ap.group10001(frame)[1]):
                    if not sentence['valid']:continue
                    f=sentence['fields']
                    if not f[0].endswith('GGA') or int(f[6]) not in (1,2,4,5) or not f[9] or not f[11]:continue
                    if f[10]!='M' or f[12]!='M':raise ValueError('unsupported GPS height units')
                    sod=follow.utc_sod(f[1]);epoch=math.floor(packet_time/86400)*86400+sod
                    if epoch-packet_time>43200:epoch-=86400
                    if packet_time-epoch>43200:epoch+=86400
                    if abs(epoch-packet_time)>2:continue
                    coords=(math.radians(ap.coordinate(f[2],f[3])),math.radians(ap.coordinate(f[4],f[5])),float(f[9])+float(f[11]))
                    if not all(math.isfinite(x) for x in coords):raise ValueError('nonfinite receiver position')
                    if epoch in fixes and fixes[epoch]!=coords:raise ValueError('conflicting receiver epoch')
                    fixes[epoch]=coords
            if frame.group!=4:continue
            row=ap.group4(frame);t=follow.utc_tag(row,leap)
            dt=None if previous is None else t-previous[0]
            valid=(dt is not None and .0025<=dt<=.0075 and row['imu_type']==kind and row['rate_code']==2
                   and not row['data_status'] and not row['imu_status'])
            continuous=previous is not None and previous[1]==signature and previous[2]==row['time_types']
            if not valid or not continuous:
                if current:runs.append(current);current=[]
            valid=valid and continuous
            if valid:
                raw=np.array([row[k] for k in ap.RAW_FIELDS],dtype=np.int64)
                mount=np.eye(3) if setting is None else setting
                current.append((frame.offset,t,dt,*raw,*(mount@raw[3:]*angle_scale),*(mount@raw[:3]*velocity_scale)))
            else:excluded+=1
            previous=(t,signature,row['time_types'])
    if current:runs.append(current)
    if stream.digest.hexdigest()!=context['inspection']['source_sha256']:raise ValueError('original hash mismatch')
    # GPS gaps split potential geometry. No smoothing/interpolated observation is created.
    groups=[]
    for t in sorted(fixes):
        if not groups or t-groups[-1][-1]>2:groups.append([])
        groups[-1].append(t)
    candidates=[]
    for r in runs:
        begin=r[0][1]-r[0][2];end=r[-1][1]
        for g in groups:
            first=max(begin,g[0]-.2);last=min(end,g[-1]+.2,first+maximum_seconds)
            if last-first>=60:candidates.append((last-first,first,last,r,g))
    if not candidates:raise ValueError('no complete >=60s native/GPS-supported geometry')
    _,begin,end,rows,group=min(candidates,key=lambda x:(-x[0],x[1]))
    values=np.array([r for r in rows if r[1]-r[2]>=begin-1e-9 and r[1]<=end+1e-9],float)
    start=values[0,1]-values[0,2];duration=min(float(np.sum(values[:,2])),len(values)*.005)
    epochs=[t for t in group if .2<t-start<duration-.2]
    if len(epochs)<58:raise ValueError('insufficient actual receiver epochs')
    times=np.array(epochs)-start;gps=np.array([fixes[t] for t in epochs])
    provenance=dict(source_sha256=stream.digest.hexdigest(),source_bytes=stream.size,imu_type=kind,
        angle_scale_rad_per_count=angle_scale,velocity_scale_mps_per_count=velocity_scale,
        scale_status='explicit empirical conversion hypothesis; no configuration promotion',
        native_packets=len(values),receiver_epochs=len(times),duration_nominal_s=len(values)*.005,
        first_packet_offset=int(values[0,0]),last_packet_offset=int(values[-1,0]),
        first_interval_start_utc_s=start,duration_header_s=float(np.sum(values[:,2])),
        excluded_status_timing_packets=excluded,group1_observations_used=False,
        selection='longest <=600s complete native/GPS-supported run, earliest tie; no gyro residual',
        steady_level_flight_established=False,recorded_installation_used=setting is not None)
    return values,times,gps,provenance


def initialize(times,gps,values,model):
    mask=times<=times[0]+10
    seed_coordinates=gps.copy();seed_coordinates[:,1]=np.unwrap(seed_coordinates[:,1])
    coefficients=np.array([np.polyfit(times[mask],seed_coordinates[mask,i],1) for i in range(3)])
    c=coefficients[:,1];rate=coefficients[:,0]
    v=forward.coordinate_kinematics(model,c[0],c[2],rate,6371000.)['velocity_ned_mps']
    force=np.mean(values[:min(2000,len(values)),12:15],axis=0)/.005
    unit=force/np.linalg.norm(force);down=np.array([0.,0.,-1.]);dot=float(unit@down)
    if dot<-.999999:tilt=np.diag([1.,-1.,-1.])
    else:
        k=forward.skew(np.cross(unit,down));tilt=np.eye(3)+k+k@k/(1+dot)
    rotation=installation.rotation([0,0,math.degrees(math.atan2(v[1],v[0]))])@tilt
    return dict(latitude_rad=c[0],longitude_rad=c[1],height_m=c[2],velocity_ned_mps=v,
                attitude_body_to_ned=rotation),float(np.linalg.norm(force))
