# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-calibration second-moment benchmark, not an aircraft decision rule."""


def summarize(operator,*,training_epochs,nominal_position_scales,accuracy_limits):
    import numpy as np
    from .state_space_covariance import LinearInnovations
    if (not isinstance(operator,LinearInnovations) or operator.observation_dimension!=3
            or type(training_epochs) is not int or not 1<=training_epochs<operator.epoch_count):
        raise ValueError('three-coordinate fixed-error operator and nonempty split required')
    future=operator.epoch_count-training_epochs;units=np.asarray(nominal_position_scales,float)
    if (units.shape!=(future,3) or not np.all(np.isfinite(units)) or np.any(units<=0)
            or not isinstance(accuracy_limits,dict)
            or set(accuracy_limits)!=set(('horizontal_rms_m','vertical_rms_m'))
            or any(type(v) not in (int,float) or not np.isfinite(v) or v<=0 for v in accuracy_limits.values())):
        raise ValueError('complete positive nominal metric and declared RMS screens required')
    # For this fixed Gaussian law the conditional covariance depends on the
    # earlier observation layout, not its realized residual values. Zero values
    # merely construct the required checkpoint; no later observations enter.
    _,state=operator.apply_block(np.zeros(3*training_epochs),first_epoch=0)
    conditional=operator.conditional_marginals(state=state)
    variance=np.diagonal(conditional['covariance'],axis1=1,axis2=2)*units**2
    if not np.all(np.isfinite(variance)) or np.any(variance<0):raise ValueError('finite nonnegative physical second moments required')
    horizontal=float(np.mean(variance[:,:2].sum(axis=1)));vertical=float(np.mean(variance[:,2]))
    return dict(training_epochs=training_epochs,prediction_epochs=future,
        horizontal_expected_squared_rms_m2=horizontal,vertical_expected_squared_rms_m2=vertical,
        sqrt_expected_horizontal_squared_rms_m=float(np.sqrt(horizontal)),
        sqrt_expected_vertical_squared_rms_m=float(np.sqrt(vertical)),
        endpoint_standard_deviation_neu_m=np.sqrt(variance[-1]).tolist(),
        marginal_variance_neu_m2=variance.tolist(),accuracy_limits=dict(accuracy_limits),
        descriptive_second_moment_exceeds_screen=dict(horizontal=horizontal>accuracy_limits['horizontal_rms_m']**2,
            vertical=vertical>accuracy_limits['vertical_rms_m']**2),
        error_operator_configuration=operator.configuration,known_calibration_benchmark=True,
        covariance_conditioned_on_earlier_layout=True,earlier_residual_values_used=False,
        is_expected_realized_rms=False,calibration_uncertainty_included=False,
        nonlinear_coverage_established=False,error_law_calibrated=False,confidence_calibrated=False,
        scientific_decision='abstain')
