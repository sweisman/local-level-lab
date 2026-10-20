# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generated sector experiment with explicit training/prediction dependencies.

Callers supply charged native/bound callbacks and immutable evidence emission.
The actual future truth is evaluated only after constraints, center and bounds
have been fixed and emitted. No archive inputs or fitted thresholds enter here.
"""
import numpy as np
from . import ilvis0_orientation_cover as cover
from .ilvis0_training_box import contract

NOISE_M=.001
ARITHMETIC_M=1e-5


def evaluate(task,case,*,native,bound,emit):
    config=case['configuration'];truth=np.asarray(case['truth'],float)
    train=np.asarray(task['training_times'],float);future=float(task['future_time'])
    if truth.shape!=(27,) or not np.all(np.isfinite(truth)):raise ValueError('full known generated parameter vector required')
    sector=cover.sector(task['sector']);lo=sector['lower'];hi=sector['upper'];center=sector['center']
    scale=np.array([6371000.,6371000.*np.cos(config['initial_c'][0]),1.])
    training_truth,_=native(train,truth)
    nominal,jac=native(np.r_[train,future],center)
    remainders=np.array([bound(t,lo,hi,center,p) for t,p in zip(train,nominal[:-1])])
    before_remainder=bound(future,lo,hi,center,nominal[-1])
    observed=training_truth+(.5*NOISE_M*np.sin(np.arange(len(train)*3).reshape(len(train),3)+.2))/scale
    matrix=(jac[:-1]*scale[None,:,None]).reshape(-1,27)
    difference=((observed-nominal[:-1])*scale).ravel();allowance=(remainders+NOISE_M+ARITHMETIC_M).ravel()
    constraints=cover.training_constraints(matrix,difference,allowance,center)
    emit('training',dict(times_s=train,observations=observed,nominal=nominal[:-1],jacobian=jac[:-1],
        difference_m=difference,allowance_m=allowance,remainders_m=remainders,constraints=constraints,
        sector=sector,coordinate_scale=scale,parameter_count=27))
    contraction=contract(lo,hi,matrix,constraints['lower'],constraints['upper'],maximum_passes=8)
    truth_in_sector=bool(np.all(lo<=truth) and np.all(truth<=hi))
    common=dict(identity=task['identity'],kind=task['kind'],case_key=f"case-{task['model']}-{int(task['profile'])}-{task['packets']}",
        task=task,sector=sector,parameter_count=27,contraction=contraction,truth_in_sector=truth_in_sector,
        original_reads=0,optimizer_starts=0,floating_point_enclosure_verified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
    if contraction['empty']:
        return dict(common,passed=not truth_in_sector,excluded=True,known_truth_retained=not truth_in_sector,
            exclusion='outward_necessary_constraint_contradiction')
    left=contraction['lower'];right=contraction['upper'];chosen=left+(right-left)/2.
    prediction,derivative=native([future],chosen)
    remainder=bound(future,left,right,chosen,prediction[0])
    coordinate=(prediction[0]-np.asarray(config['initial_c']))*scale;jfuture=derivative[0]*scale[:,None]
    envelope=cover.future_envelope(coordinate,jfuture,chosen,left,right,constraints,remainder,arithmetic_allowance=ARITHMETIC_M)
    if np.any(envelope['lower']>envelope['upper']):raise ValueError('contradictory certified support requires diagnosis')
    emit('future',dict(time_s=future,nominal_position_m=coordinate,jacobian_m=jfuture,chosen_center=chosen,
        lower=left,upper=right,remainder_m=remainder,coordinate_scale=scale,envelope=envelope,parameter_count=27))
    retained=not truth_in_sector or bool(np.all(left<=truth) and np.all(truth<=right))
    actual,_=native([future],truth);future_truth=(actual[0]-np.asarray(config['initial_c']))*scale
    contained=bool(np.all(envelope['lower']<=future_truth) and np.all(future_truth<=envelope['upper']))
    return dict(common,passed=retained and (contained or not truth_in_sector),excluded=False,
        known_truth_retained=retained,future_truth_evaluated_after_bounds=True,future_truth_m=future_truth,
        future_lower_m=envelope['lower'],future_upper_m=envelope['upper'],future_center=chosen,
        future_remainder_before_m=before_remainder,future_remainder_after_m=remainder,certificates=envelope['certificates'])
