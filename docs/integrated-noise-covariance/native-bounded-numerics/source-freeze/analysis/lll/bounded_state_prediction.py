# SPDX-License-Identifier: AGPL-3.0-or-later
"""Structured error geometry for the existing bounded prediction envelopes.

This adapter does not estimate an archive error law or certify nonlinear
remainders. It accepts no later observations and never deletes nuisance columns.
"""


def geometry(operator,design,training_values,*,training_epochs):
    import numpy as np
    from .state_space_covariance import LinearInnovations
    if (not isinstance(operator,LinearInnovations) or type(training_epochs) is not int
            or not 1<=training_epochs<operator.epoch_count):
        raise ValueError('declared structured operator and nonempty chronological split required')
    d=operator.observation_dimension;k=operator.state_dimension
    n=d*operator.epoch_count;m=d*training_epochs
    x=np.asarray(design,dtype=float);y=np.asarray(training_values,dtype=float)
    if (x.ndim!=2 or x.shape[0]!=n or not 1<=x.shape[1]<=27
            or y.shape!=(m,) or not np.all(np.isfinite(x)) or not np.all(np.isfinite(y))):
        raise ValueError('complete mean design and earlier values only required')
    a,_=operator.apply_block(x[:m],first_epoch=0)
    b,checkpoint=operator.apply_block(y,first_epoch=0)
    future=operator.conditional_marginals(state=checkpoint)
    # Only N x p design storage is needed; never an N x N projection.
    padded=np.zeros((n,x.shape[1]));padded[:m]=a
    contrast=x[m:]-operator.unwhiten(padded)[m:]
    # Square root of the response to earlier independent innovations. Future
    # innovations are not included in this root; conditional_marginals carries
    # their separate uncertainty. QR avoids covariance subtraction/cancellation.
    root=np.zeros((k,k))
    for i in range(training_epochs):
        joined=np.hstack((operator._transition[i]@root,operator._gain[i]@operator._lower[i]))
        root=np.linalg.qr(joined.T,mode='reduced')[1].T
    response=np.empty((operator.epoch_count-training_epochs,d))
    for local,i in enumerate(range(training_epochs,operator.epoch_count)):
        response[local]=np.linalg.norm(operator._observation[i]@root,axis=1)
        root=operator._transition[i]@root
    variance=np.diagonal(future['covariance'],axis1=1,axis2=2).ravel().copy()
    values=dict(whitened_design=a,whitened_values=b,conditional_mean=future['mean'].ravel(),
        conditional_variance=variance,contrasts=contrast,training_response_norm=response.ravel())
    if any(not np.all(np.isfinite(v)) for v in values.values()):raise ValueError('unrepresentable structured prediction geometry')
    return values


def predict(*,operator,design,training_values,training_epochs,coefficient_bounds,nominal_future,
            scale,training_remainder_radius,future_remainder_bounds,alpha_training,alpha_prediction,
            mean_design_is_fixed,rank_tolerance,maximum_parameters,prediction_ids):
    """Outer coordinate bounds under supplied Gaussian/mean-remainder assumptions.

    Coefficient bounds are relative to the supplied linearization intercept.
    They must include every active mean parameter, including any null direction.
    A zero remainder is justified for exact linear controls; it cannot be inferred
    from a small residual, a numerical stopping check or point-forecast accuracy.
    """
    import numpy as np
    from .state_space_covariance import LinearInnovations
    from .ilvis0_bounded_prediction import Region,predict as envelope
    if (not isinstance(operator,LinearInnovations) or type(maximum_parameters) is not int
            or not 1<=maximum_parameters<=27 or type(mean_design_is_fixed) is not bool
            or type(training_epochs) is not int or not 1<=training_epochs<operator.epoch_count):
        raise ValueError('explicit operator, split, design origin and finite parameter allowance required')
    x=np.asarray(design,dtype=float);bounds=np.asarray(coefficient_bounds,dtype=float)
    n=operator.epoch_count*operator.observation_dimension;m=training_epochs*operator.observation_dimension
    nominal=np.asarray(nominal_future,dtype=float);ids=tuple(prediction_ids)
    if (x.ndim!=2 or x.shape[0]!=n or not 1<=x.shape[1]<=maximum_parameters
            or bounds.shape!=(x.shape[1],2) or not np.all(np.isfinite(bounds)) or np.any(bounds[:,0]>bounds[:,1])
            or nominal.shape!=(n-m,) or not np.all(np.isfinite(nominal))
            or len(ids)!=n-m or len(set(ids))!=len(ids)):
        raise ValueError('complete finite mean design, coefficient box and unique future coordinates required')
    g=geometry(operator,x,training_values,training_epochs=training_epochs)
    region=Region(g['whitened_values'],g['whitened_design'],bounds,scale=scale,
        covariance_id=operator.configuration,remainder_radius=training_remainder_radius,alpha=alpha_training,
        rank_tolerance=rank_tolerance,design_is_fixed=mean_design_is_fixed)
    result=envelope(region,nominal+g['conditional_mean'],g['contrasts'],
        conditional_variance=g['conditional_variance'],training_response_norm=g['training_response_norm'],
        future_remainder_bounds=future_remainder_bounds,alpha=alpha_prediction,prediction_ids=ids)
    result.update(uncertainty_scope='bounded linear mean and supplied Gaussian law with explicit remainder bounds',
        all_mean_columns_retained=True,later_observations_used=False,
        nonlinear_coverage_established=False,error_law_calibrated=False)
    return result
