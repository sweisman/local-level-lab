# SPDX-License-Identifier: AGPL-3.0-or-later
"""Post-fit generated receiver-target scoring with an unchanged earlier prefix."""


def score(times, physical_truth, training_rows, binding, diagnostic, bound):
    """Draw later receiver errors only after the target bound is already saved.

    This is a generated software check. Its intervals are not calibrated for
    observed aircraft or for a population of routes and noise laws.
    """
    import math
    import numpy as np
    from .airquantumgrav_error_policy import build
    from .airquantumgrav_weighted_controls import fixture_rows
    from .ilvis0_solver_position import physical_metric
    from .measurement_noise import receiver_errors
    from .ilvis0_precision_value import longitude_residual

    t=np.asarray(times,dtype=float)
    truth=np.asarray(physical_truth,dtype=float)
    if (t.ndim!=1 or truth.shape!=(len(t),3) or len(t)<4
            or not np.all(np.isfinite(t)) or np.any(np.diff(t)<=0)
            or not np.all(np.isfinite(truth))):
        raise ValueError('complete ordered generated physical truth required')
    if (not isinstance(training_rows,list) or not isinstance(binding,dict)
            or not isinstance(diagnostic,dict) or not isinstance(bound,dict)
            or diagnostic.get('prediction_target')!='receiver_measurement'
            or bound.get('prediction_target')!='receiver_measurement'
            or diagnostic.get('later_observations_used') is not False
            or bound.get('later_observations_used') is not False):
        raise ValueError('saved earlier-only receiver target required')
    m=bound.get('training_epochs')
    if (type(m) is not int or not 2<=m<len(t)
            or bound.get('prediction_epochs')!=len(t)-m or len(training_rows)!=m):
        raise ValueError('matching earlier and later epochs required')
    noise=binding.get('noise',{})
    settings=noise.get('settings',{})
    policy=noise.get('receiver_policy',{}).get('policy_id')
    seed=settings.get('seed')
    if type(seed) is not int or policy!='reported-short-v1':
        raise ValueError('unchanged declared receiver seed and policy required')
    clean=fixture_rows(truth[:m],t[:m])
    weights=build(clean,policy_id=policy)
    if weights.source_sha256!=noise.get('receiver_covariance_source_sha256'):
        raise ValueError('earlier receiver covariance source changed')
    transforms=np.concatenate((weights.transforms,
                               np.repeat(weights.transforms[-1][None],len(t)-m,axis=0)))
    errors=receiver_errors(t,weights.spec,seed=seed,maximum_epochs=len(t),
                           transforms=transforms)
    for i,(row,base,error) in enumerate(zip(training_rows,clean,errors[:m],strict=True)):
        expected=(base['latitude_deg']+math.degrees(error[0]),
                  base['longitude_deg']+math.degrees(error[1]),
                  base['height_m']+error[2])
        actual=tuple(row[k] for k in ('latitude_deg','longitude_deg','height_m'))
        if (np.any(np.abs(np.asarray(actual)-expected)>
                   np.array([1e-11,1e-11,1e-7]))
                or row.get('time_s')!=base['time_s']):
            raise ValueError(f'earlier receiver prefix changed at epoch {i}')
    observed=truth[m:]+errors[m:]
    center=np.asarray(diagnostic.get('fixed_parameters',{}).get('mean'),float)
    lower=np.asarray(bound.get('lower'),float)
    upper=np.asarray(bound.get('upper'),float)
    q=len(t)-m
    if (center.shape!=(q,3) or lower.shape!=(3*q,) or upper.shape!=(3*q,)
            or any(not np.all(np.isfinite(a)) for a in (center,lower,upper))):
        raise ValueError('complete saved receiver forecast and envelope required')
    lower=lower.reshape(q,3);upper=upper.reshape(q,3)
    if np.any(lower>upper):
        raise ValueError('ordered saved receiver envelope required')
    contains=(lower<=observed)&(observed<=upper)
    metric=physical_metric(observed)
    difference=center-observed
    difference[:,1]=longitude_residual(difference[:,1])
    error_m=difference*metric
    width=(upper-lower)*metric
    horizontal=np.linalg.norm(error_m[:,:2],axis=1)
    horizontal_width=np.linalg.norm(width[:,:2],axis=1)
    return dict(training_prefix_reproduced=True,
                prediction_target='receiver_measurement',
                future_epochs=q,
                all_later_coordinates_contained=bool(np.all(contains)),
                contained_coordinates=int(np.count_nonzero(contains)),
                total_coordinates=3*q,
                point_horizontal_rms_m=float(np.sqrt(np.mean(horizontal**2))),
                point_vertical_rms_m=float(np.sqrt(np.mean(error_m[:,2]**2))),
                mean_full_width_horizontal_m=float(np.mean(horizontal_width)),
                mean_full_width_vertical_m=float(np.mean(width[:,2])),
                empirical_coverage_calibrated=False,
                observed_aircraft_coverage_established=False,
                scientific_decision='abstain')
