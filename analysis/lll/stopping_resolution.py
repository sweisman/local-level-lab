# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed-point native probes using the unchanged bounded stopping correction."""
import math

FRACTIONS=(.5,.25,.125,-.125,-.25,-.5,-1.)
MAXIMUM_SWEEPS=10


def probe(fit,*,evaluate,physical_step,packet_count,epoch_count,reserve,save,save_bytes,check_continue):
    import io
    import numpy as np
    from .ilvis0_solver_position import verify_stability
    from .ilvis0_solver_refinement import projected_stationarity
    from .studies.artifacts import digest
    if (type(packet_count) is not int or packet_count<1 or type(epoch_count) is not int or epoch_count<2
            or not all(callable(v) for v in (evaluate,physical_step,reserve,save,save_bytes,check_continue))):
        raise ValueError('finite input support and explicit evaluation/evidence callbacks required')
    point=np.asarray(fit['normalized_parameters'],float);active=fit['active_parameters'];saved_cost=fit['residual_sum_squares']
    if (point.ndim!=1 or len(point) not in (26,27) or not isinstance(active,list) or len(active)!=len(point)
            or any(not isinstance(v,str) or not v for v in active) or len(set(active))!=len(active)
            or not np.all(np.isfinite(point)) or np.any(abs(point)>1) or type(fit.get('converged')) is not bool
            or type(saved_cost) not in (int,float) or not math.isfinite(saved_cost) or saved_cost<0):
        raise ValueError('complete finite feasible saved fit with every active column required')
    point=point.copy();records=[];anchor=None
    def sweep(u,*,kind,fraction=None,requested=None):
        nonlocal anchor
        check_continue();u=np.asarray(u,float).copy()
        if u.shape!=point.shape or not np.all(np.isfinite(u)) or np.any(abs(u)>1) or len(records)>=MAXIMUM_SWEEPS:
            raise ValueError('one feasible declared probe within its finite allowance required')
        reserve(native_calls=1,packet_visits=packet_count*epoch_count)
        r,j,b=evaluate(u.copy());r,j=(np.asarray(v,float).copy() for v in (r,j))
        if (r.shape!=(3*epoch_count,) or j.shape!=(len(r),len(point))
                or not np.all(np.isfinite(r)) or not np.all(np.isfinite(j))
                or not isinstance(b,(int,np.integer)) or not 0<=b<=epoch_count):
            raise ValueError('finite residual and complete native derivative columns required')
        if anchor is None:anchor=(r.copy(),j.copy())
        r0,j0=anchor;difference=np.asarray(physical_step(r-r0),float)
        if difference.shape!=(epoch_count,3) or not np.all(np.isfinite(difference)):
            raise ValueError('complete finite physical position differences required')
        predicted=r0+j0@(u-point);cost=float(r@r);initial=float(r0@r0);linear_cost=float(predicted@predicted)
        stationarity=projected_stationarity(u,r,j)[0]
        if not all(math.isfinite(v) for v in (cost,initial,linear_cost,stationarity)):
            raise ValueError('finite native and linearized probe summaries required')
        name=f'sweep-{len(records):02d}.npz';stream=io.BytesIO()
        np.savez_compressed(stream,point=u,residual=r,jacobian=j,position_delta_neu_m=difference)
        raw=stream.getvalue();save_bytes(name,raw)
        records.append(dict(index=len(records),kind=kind,fraction=fraction,artifact=name,artifact_sha256=digest(raw),
            cost=cost,linearized_cost=linear_cost,relative_cost_change=abs(cost-initial)/max(cost,initial,1.),
            linearized_relative_cost_change=abs(linear_cost-initial)/max(linear_cost,initial,1.),
            linearization_error_norm=float(np.linalg.norm(r-predicted)),stationarity=stationarity,
            normalized_parameter_step=float(np.linalg.norm(u-point)),
            clipped=bool(requested is not None and not np.array_equal(u,requested)),
            position_rms_neu_m=np.sqrt(np.mean(difference*difference,axis=0)).tolist(),
            position_max_abs_neu_m=np.max(abs(difference),axis=0).tolist(),packet_boundary_epochs=int(b)))
        return r,j,int(b)
    first=sweep(point,kind='baseline');second=sweep(point,kind='repeat');captured=[]
    def fresh(u,fresh=False):
        if not fresh or captured:raise ValueError('one unchanged shared fresh correction required')
        captured.append(np.asarray(u,float).copy())
        return sweep(u,kind='shared_correction',fraction=1.)
    check_continue()
    shared=verify_stability(point,first[0],first[1],fresh,physical_step)
    direction=None
    if captured:
        direction=captured[0]-point
        for fraction in FRACTIONS:
            requested=point+fraction*direction
            sweep(np.clip(requested,-1.,1.),kind='scaled_correction',fraction=fraction,requested=requested)
    expected=MAXIMUM_SWEEPS if captured else 2
    if len(records)!=expected:raise ValueError('fixed probe protocol and native accounting differ')
    output=dict(version='fixed-point-stopping-resolution-v1',active_parameters=active,
        saved_converged=fit['converged'],saved_cost=saved_cost,shared_probe=shared,
        correction_available=bool(captured),normalized_correction=direction.tolist() if direction is not None else None,
        residual_repeat_bitwise_equal=bool(np.array_equal(first[0],second[0])),
        derivative_repeat_bitwise_equal=bool(np.array_equal(first[1],second[1])),
        relative_saved_cost_difference=abs(records[0]['cost']-saved_cost)/max(records[0]['cost'],saved_cost,1.),
        packet_count=packet_count,epoch_count=epoch_count,native_calls=len(records),
        packet_query_visits=len(records)*packet_count*epoch_count,sweeps=records,
        all_columns_retained=True,optimizer_starts=0,labels_changed=False,
        passed=True,confidence_calibrated=False,scientific_decision='abstain')
    save('probe.json',output)
    return output
