# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit saved structured-error predictions without fits or regenerated truth."""


def check_case(spec,result,saved,*,r):
    import math
    import numpy as np
    from .structured_noisy_training import case_recipe
    from .airquantumgrav_noisy_report import check_case as original_check
    from .airquantumgrav_training_report import saved_position_errors
    from .airquantumgrav_scoring import sections
    from .airquantumgrav_truth import A,E2,DISC_RADIUS
    from .studies.artifacts import encoded
    law=spec['law'];base={k:v for k,v in spec.items() if k!='law'};configured=case_recipe(r,law)
    fit=saved['fit.json'];binding=saved['input-binding.json'];ops=saved['native-operation-summary.json']
    cut=2*r['queries']//3;n=round(r['duration_s']*r['rate_hz']);prefix=binding['training_prefix_packets']
    fit_calls=fit['evaluations']+1;fit_work=fit['evaluations']*prefix*cut+n*r['queries']
    if (result['law']!=law or ops['fit_forecast_calls']!=fit_calls
            or not 1<=ops['bridge_calls']<=prefix+cut+n+r['queries']
            or ops['native_calls']!=ops['bridge_calls']+fit_calls or result['native_calls']!=ops['native_calls']
            or ops['packet_visits']!=ops['bridge_calls']+fit_work):
        raise ValueError('saved covariance, fit/forecast and complete native accounting differ')
    # Reuse the frozen protocol checks for the explicitly separated fit/forecast
    # portion. Keep the original full-operation result unchanged in the evidence.
    checked=original_check(base,dict(result,native_calls=fit_calls),saved,r=configured,
        operations=dict(value=0,tangent=fit_calls,packet_visits=fit_work))
    forecast=saved['forecast.json'];diag=saved['forecast-error-diagnostic.json'];conditional=saved['conditional-scores.json']
    operator=saved['training-error-operator.json'];extended=diag['error_operator']
    score=fit['gaussian_training_score'];rows=3*cut;rss=fit['residual_sum_squares'];logdet=operator['error_log_determinant']
    expected=.5*(rss+logdet+rows*math.log(2*math.pi))
    expected_law='recorded_increments' if law=='increment' else 'linear_rate_points'
    if (score['row_count']!=rows or score['residual_sum_squares']!=rss or score['log_determinant']!=logdet
            or not math.isclose(score['negative_log_likelihood'],expected,rel_tol=1e-13,abs_tol=1e-10)
            or score['model_comparison_calibrated'] or diag['prediction_target']!='physical_position'
            or diag['later_observations_used'] or diag['confidence_calibrated']
            or extended['later_receiver_fields_used'] or extended['receiver_observation_epochs']!=cut
            or extended['receiver_transform_policy']!=r['receiver_transform_policy']
            or extended['training_operator_configuration']!=operator['operator_configuration']
            or forecast['error_training_configuration']!=operator['operator_configuration']
            or forecast['normalized_parameters']!=fit['normalized_parameters']
            or forecast['frozen_error_model']!=base['model']
            or forecast['training_residual_subtraction']!='native-before-binary64-cast'
            or diag['raw_coordinates']!=forecast['coordinates']
            or any(item['model']!=base['model'] or item['source_law']!=expected_law
                or item['weights_depend_on_fitted_residuals'] or not item['weights_frozen_during_optimization']
                or item['anchor_normalized_point']!=[0.]*(26+int(base['profile'])) for item in (operator,extended))
            or any(operator['input_sha256'][key]!=binding['training_prefix_sha256'][key] for key in ('theta','dv','dt'))
            or any(extended['input_sha256'][key]!=binding['full_array_sha256'][key] for key in ('theta','dv','dt','times'))):
        raise ValueError('training normalization, prediction target or saved fitted-point binding differs')
    linear=diag['linear_calibration'];status=linear['status']
    if status not in ('estimable','unidentifiable','active_bounds_unsupported','linear_step_outside_bounds'):
        raise ValueError('unsupported calibration diagnostic status')
    if status!='estimable' and ('covariance' in linear or linear['parameter_uncertainty_included']):
        raise ValueError('unsupported calibration was assigned finite unrestricted uncertainty')
    combined=forecast['coordinates'][:cut]+diag['fixed_parameters']['mean']
    errors=saved_position_errors(combined,saved['scoring-observations.json'],model=base['model'],
        constants=dict(A=A,E2=E2,DISC_RADIUS=DISC_RADIUS))
    if not np.allclose(errors,conditional['errors_neu_m'],rtol=0,atol=1e-7):
        raise ValueError('independent conditional physical errors differ')
    calculated=sections(conditional['errors_neu_m'],cut)
    if (conditional['prediction_target']!='physical_position' or conditional['confidence_calibrated']
            or not conditional['primary_raw_forecast_unchanged']
            or any(encoded(calculated[k])!=encoded(conditional[k]) for k in calculated)
            or encoded(result['conditional_prediction'])!=encoded(calculated['prediction'])
            or result['linear_calibration_status']!=status):
        raise ValueError('conditional forecast scores or abstention labels differ')
    return dict(checked,law=law,native_calls=ops['native_calls'],conditional_prediction=calculated['prediction'],
        linear_calibration_status=status,confidence_calibrated=False)
