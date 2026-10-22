# SPDX-License-Identifier: AGPL-3.0-or-later
"""Staged necessary constraints with one fixed native calibration reference.

No future observation is accepted. Bounds conditioned on earlier training are
used only while retaining the complete earlier region. Error-law validity and
whole-program numerical enclosure remain supplied, unqualified assumptions.
"""
from fractions import Fraction as F

import numpy as np


def _typed(region):
    from .ilvis0_transform_envelope import TrainingRegion
    return TrainingRegion(region['times_s'],region['design'],region['target_lower'],region['target_upper'],
        region['inequality_design'],region['inequality_upper'],region['lower'],region['upper'],region['center'],
        region['coordinate_scale'],region['origin'],region['binding'],region['source_id'],region['force_source_id'],
        region['arithmetic_allowance'])


def predict(*,training_times,observations,noise_allowance,stage_sizes,future_time,reference,lower,upper,
            coordinate_scale,origin,native,bound,reserve,save,arithmetic_allowance=1e-5):
    from . import ilvis0_transform_envelope as joint
    from .ilvis0_direct_interface import bridge
    from .ilvis0_directional_acceleration import DirectionalAcceleration
    from .ilvis0_conditioned_acceleration import ConditionedAcceleration
    from .ilvis0_acceleration_projection import project
    from .ilvis0_staged_training import merge_epochs
    from .ilvis0_sharded_native import plain
    from .ilvis0_training_remainder_audit import scaled_design
    from .ilvis0_saved_prediction_audit import support,endpoint
    times=np.array(training_times,float,copy=True);count=len(times)
    observed=np.array(observations,float,copy=True);noise=np.array(noise_allowance,float,copy=True)
    if (times.ndim!=1 or not 1<=count<=32 or not np.all(np.isfinite(times)) or times[0]<0.
            or np.any(np.diff(times)<=0.) or observed.shape!=(count,3) or noise.shape!=(count,3)
            or not np.all(np.isfinite(observed)) or not np.all(np.isfinite(noise)) or np.any(noise<0.)
            or not 1<=len(stage_sizes)<=8 or any(type(v) is not int or v<1 for v in stage_sizes)
            or sum(stage_sizes)!=count or not np.isfinite(future_time) or future_time<=times[-1]):
        raise ValueError('finite ordered training data, explicit allowances/stages and a later prediction required')
    def store(name,value):save(name,plain(value))
    center=reference.parent.center
    reserve(physical_proofs=1);proof=DirectionalAcceleration(reference,lower,upper)
    store('physical-proof.json',proof.report());region=None;first=0
    for ordinal,size in enumerate(stage_sizes,1):
        last=first+size; values=[];jacobians=[];reports=[]
        for index in range(first,last):
            time_s=float(times[index]);value,jac=native(time_s,center)
            raw=bound(time_s,proof)
            report=bridge(raw,reference,proof,value,coordinate_scale)
            values.append(value);jacobians.append(jac);reports.append(report)
            store(f'training-bound-{index+1:02d}.json',report.report())
        fresh=joint.training(times=times[first:last],observations=observed[first:last],native_values=values,
            native_jacobians=jacobians,reports=reports,reference=reference,physical_lower=lower,physical_upper=upper,
            coordinate_scale=coordinate_scale,origin=origin,noise_allowance=noise[first:last],
            arithmetic_allowance=arithmetic_allowance)
        fresh=plain(fresh.report());region=fresh if region is None else merge_epochs(region,fresh)
        store(f'stage-{ordinal:02d}-region.json',region)
        bundle=dict(training=dict(region=region),reference=reference.report(),lower=region['lower'],upper=region['upper'])
        reserve(training_proofs=1)
        certificate=project(**bundle,reserve=lambda p,s:reserve(lp_proposals=p,exact_supports=s))
        proof=ConditionedAcceleration(bundle,certificate,reserve=lambda s:reserve(exact_supports=s))
        store(f'stage-{ordinal:02d}-conditioning-input.json',bundle)
        store(f'stage-{ordinal:02d}-certificate.json',certificate)
        store(f'stage-{ordinal:02d}-proof.json',proof.report())
        first=last
    value,jac=native(float(future_time),center)
    raw=bound(float(future_time),proof);report=bridge(raw,reference,proof,value,coordinate_scale)
    store('future-bound.json',report.report())
    reserve(lp_proposals=6,exact_supports=12)
    future=joint.future(_typed(region),time=float(future_time),native_value=value,native_jacobian=jac,
                        report=report,reference=reference)
    store('future.json',future)
    reserve(exact_supports=6);matrix=scaled_design(jac,report.report(),region['coordinate_scale'])
    args=(region['lower'],region['upper'],region['inequality_design'],region['inequality_upper'])
    for axis,(row,unit) in enumerate(zip(matrix,region['coordinate_scale'],strict=True)):
        certificate=future['certificates'][axis]
        high=support(*args,row,certificate['upper_multipliers'])
        low=support(*args,[-v for v in row],certificate['lower_multipliers'])
        if high!=F(certificate['upper']) or low!=F(certificate['negated_lower']):
            raise ValueError('staged future certificate changed')
        shift=(F(float(value[axis]))-F(region['origin'][axis]))*F(unit)
        shift-=sum((F(v)*F(c) for v,c in zip(row,region['center'],strict=True)),F(0))
        radius=F(float(report.unshared_remainder[axis]))*F(unit)+F(region['arithmetic_allowance'])
        if (endpoint(shift-low-radius,False)!=future['lower'][axis]
                or endpoint(shift+high+radius,True)!=future['upper'][axis]):
            raise ValueError('staged future outward endpoint changed')
    audit=dict(passed=True,exact_supports_checked=6,all_prior_rows_preserved=True,parameter_count=51)
    store('independent-audit.json',audit)
    return plain(dict(region=region,future=future,independent_audit=audit,future_time_s=future_time,
        physical_parameter_count=27,parameter_count=51,future_observations_used=False,
        recording_length_usefulness_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain'))
