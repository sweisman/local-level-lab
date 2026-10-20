# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generated native cover with a fixed common-error expansion at every epoch.

Future truth and the known-control shared error are unavailable until training
constraints and the future envelope have been emitted. All 33 columns remain.
"""
import numpy as np
from . import ilvis0_orientation_cover as cover,ilvis0_shared_envelope as joint
from .ilvis0_training_box import contract

NOISE_M=.001
ARITHMETIC_M=1e-5


def evaluate(task,case,*,reference,native,bound,emit):
    config=case['configuration'];truth=np.asarray(case['truth'],float)
    train=np.asarray(task['training_times'],float);future=float(task['future_time'])
    sector=cover.sector(task['sector']);lo=sector['lower'];hi=sector['upper'];center=sector['center']
    if (truth.shape!=(27,) or not np.all(np.isfinite(truth)) or not np.array_equal(center,reference.center)
            or not np.array_equal(lo,reference.lower) or not np.array_equal(hi,reference.upper)):
        raise ValueError('full fixed sector/reference and known-control vector required')
    scale=np.array([6371000.,6371000.*np.cos(config['initial_c'][0]),1.])
    training_truth,_=native(train,truth)
    nominal,jac=native(np.r_[train,future],center)
    reports=[bound(t,lo,hi,nominal[i]) for i,t in enumerate(train)]
    before=bound(future,lo,hi,nominal[-1])
    observed=training_truth+(.5*NOISE_M*np.sin(np.arange(len(train)*3).reshape(len(train),3)+.2))/scale
    region=joint.training(times=train,observations=observed,native_values=nominal[:-1],native_jacobians=jac[:-1],
        reports=reports,reference=reference,physical_lower=lo,physical_upper=hi,coordinate_scale=scale,
        origin=config['initial_c'],noise_allowance=np.full((len(train),3),NOISE_M),arithmetic_allowance=ARITHMETIC_M)
    emit('training',dict(times_s=train,observations=observed,nominal=nominal[:-1],jacobian=jac[:-1],
        region=region.report(),reference=reference.report(),sector=sector,parameter_count=33))
    contraction=contract(region.lower,region.upper,region.design,region.target_lower,region.target_upper,maximum_passes=8)
    truth_in_sector=bool(np.all(lo<=truth) and np.all(truth<=hi))
    common=dict(identity=task['identity'],kind=task['kind'],case_key=f"case-{task['model']}-{int(task['profile'])}-{task['packets']}",
        task=task,sector=sector,parameter_count=33,physical_parameter_count=27,shared_error_count=6,
        shared_binding=reference.binding,contraction=contraction,truth_in_sector=truth_in_sector,
        original_reads=0,optimizer_starts=0,floating_point_enclosure_verified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
    if contraction['empty']:
        return dict(common,passed=not truth_in_sector,excluded=True,known_truth_retained=not truth_in_sector,
            exclusion='outward_necessary_constraint_contradiction')
    left=contraction['lower'];right=contraction['upper']
    report=bound(future,left[:27],right[:27],nominal[-1])
    envelope=joint.future(region,time=future,native_value=nominal[-1],native_jacobian=jac[-1],
        report=report,reference=reference,lower=left,upper=right)
    emit('future',dict(time_s=future,nominal=nominal[-1],jacobian=jac[-1],fixed_center=center,
        lower=left,upper=right,reference=reference.report(),bound=report.report(),envelope=envelope,parameter_count=33))
    # Only now may either future truth or the oracle shared-error vector be read.
    actual,_=native([future],truth);future_truth=(actual[0]-np.asarray(config['initial_c']))*scale
    retained=True;gamma=None
    if truth_in_sector:
        gamma=reference.normalized_values_at(truth);extended=np.r_[truth,gamma]
        retained=bool(np.all(left<=extended) and np.all(extended<=right))
    contained=bool(np.all(envelope['lower']<=future_truth) and np.all(future_truth<=envelope['upper']))
    return dict(common,passed=retained and (contained or not truth_in_sector),excluded=False,
        known_truth_retained=retained,known_shared_error=gamma,future_truth_evaluated_after_bounds=True,
        future_truth_m=future_truth,future_lower_m=envelope['lower'],future_upper_m=envelope['upper'],
        future_center=center,future_remainder_before_m=before.unshared_remainder*scale,
        future_remainder_after_m=report.unshared_remainder*scale,certificates=envelope['certificates'])
