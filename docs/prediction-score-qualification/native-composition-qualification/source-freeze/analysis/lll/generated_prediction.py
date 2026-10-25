# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared generated-data fitting/forecast orchestration with isolated scoring.

Input construction, fitting and later truth generation are explicit providers.
This component supplies no calibration truth, noise defaults or confidence law.
"""


def calculate(spec,r,*,material,train_and_forecast,kernel_factory,reserve,
              reserve_construction,save,truth,check_continue,training_error_factory=None,
              forecast_error_diagnostic=None):
    import numpy as np
    from lll.airquantumgrav_geographic_controls import position_errors
    from lll.airquantumgrav_scoring import sections
    from lll.studies.artifacts import digest,encoded
    times=np.asarray(material['times'],float);rows=material['training_rows'];cut=material['training_epochs']
    n=len(material['dt']);prefix=int(np.searchsorted(np.cumsum(material['dt']),
        times[cut-1]+r['limits']['time_offset'],side='left'))+1
    hashes=lambda:{k:digest(np.asarray(material[k],dtype='<f8').tobytes()) for k in ('theta','dv','dt','times')}
    initial_hashes=hashes();rows_hash=digest(encoded(rows))
    if (len(rows)!=cut or not 2<=cut<len(times) or prefix>n
            or any(initial_hashes[k]!=material['binding']['measured_raw_array_sha256'][k] for k in ('theta','dv','dt'))
            or rows_hash!=material['binding']['noisy_training_receiver_sha256']):
        raise ValueError('complete unchanged measured inputs required before initialization')
    anchor=float(rows[0]['height_m']);save('training-receiver.json',rows);check_continue()
    kernel,tangent,compilation=kernel_factory(anchor);save('compilation.json',compilation)
    binding=dict(full_array_sha256=initial_hashes,native_packets=n,training_prefix_packets=prefix,
        training_prefix_sha256={k:digest(np.asarray(material[k][:prefix],dtype='<f8').tobytes()) for k in ('theta','dv','dt')},
        training_epochs=cut,prediction_epochs=len(times)-cut,gravity_anchor_height_m=anchor,
        gravity_anchor_source='first_noisy_training_receiver_height',training_receiver_sha256=rows_hash,
        noise=material['binding'],original_reads=0,protected_reads=0)
    save('input-binding.json',binding);written=set()
    def save_fit(name,value):
        save(name,value)
        written.add(name)
    native_calls=0
    def reserve_fit(**work):
        nonlocal native_calls
        reserve(**work);native_calls+=work['native_calls']
    protocol_options={} if training_error_factory is None else dict(training_error_factory=training_error_factory)
    if forecast_error_diagnostic is not None:protocol_options['forecast_error_diagnostic']=forecast_error_diagnostic
    result=train_and_forecast(**{k:material[k] for k in ('theta','dv','dt')},times=times,
        training_rows=rows,time_origin_s=0.,model=spec['model'],profile=spec['profile'],policy_id=spec['policy_id'],
        start=spec['start'],limits=r['limits'],maximum_evaluations=r['maximum_evaluations'],
        maximum_interval_s=1.5/r['rate_hz'],kernel=kernel,tangent_kernel=tangent,
        reserve=reserve if training_error_factory is None else reserve_fit,save=save_fit,
        check_continue=check_continue,**protocol_options)
    if not {'fit.json','forecast.json'}<=written:raise ValueError('completed saved forecast required before later truth')
    if forecast_error_diagnostic is not None and 'forecast-error-diagnostic.json' not in written:
        raise ValueError('saved conditional forecast required before later truth')
    if forecast_error_diagnostic is not None and result['forecast_error_diagnostic']['prediction_target']!='physical_position':
        raise ValueError('physical truth scoring requires a physical-position prediction target')
    if hashes()!=initial_hashes or digest(encoded(rows))!=rows_hash:raise ValueError('measured inputs changed during fitting')
    forecast=result['forecast'];fit=result['fit'];active=fit['active_parameters'];jac=np.asarray(forecast['jacobian'])
    if (forecast['active_parameters']!=active or len(active)!=26+int(spec['profile'])
            or len(set(active))!=len(active) or jac.shape!=(len(times)*3,len(active)) or not np.all(np.isfinite(jac))
            or not result['all_columns_retained'] or result['true_initial_state_supplied'] or result['true_calibration_supplied']):
        raise ValueError('complete nuisance columns and measured-only initialization required')
    save('forecast-binding.json',dict(full_array_sha256=hashes(),jacobian_shape=list(jac.shape),
        jacobian_sha256=digest(np.asarray(jac,dtype='<f8').tobytes()),raw_arrays_unchanged=True))
    check_continue();reserve_construction(generated_samples=len(times));answer=truth(times)
    save('scoring-observations.json',{k:np.asarray(v).tolist() for k,v in answer.items()})
    errors=position_errors(forecast['coordinates'],answer,model=spec['model']);scored=sections(errors,cut)
    save('scores.json',dict(times_s=times.tolist(),errors_neu_m=errors.tolist(),**scored,
        score_reference='generated noiseless physical truth',later_receiver_noise_added=False))
    accurate=all(v['accuracy']['passed'] for v in scored.values())
    result_summary=dict(**spec,passed=bool(fit['converged'] and accurate),converged=fit['converged'],
        evaluations=fit['evaluations'],native_calls=fit['evaluations']+1 if training_error_factory is None else native_calls,
        training_cost=fit['residual_sum_squares'],
        training_epochs=cut,prediction_epochs=len(times)-cut,**scored,accuracy_all_sections=accurate,
        all_columns_retained=True,forecast_saved_before_scoring=True,true_initial_state_supplied=False,
        true_calibration_supplied=False,gravity_anchor_height_m=anchor,
        gravity_anchor_source='first_noisy_training_receiver_height',score_reference='generated noiseless physical truth',
        original_reads=0,protected_reads=0,observed_starts=0,confidence_calibrated=False,scientific_decision='abstain')
    if forecast_error_diagnostic is not None:
        diagnostic=result['forecast_error_diagnostic']
        if diagnostic['prediction_target']!='physical_position':
            raise ValueError('physical truth scoring requires a physical-position prediction target')
        fixed=np.asarray(diagnostic['fixed_parameters']['mean'],float)
        if fixed.shape!=(len(times)-cut,3) or not np.all(np.isfinite(fixed)):
            raise ValueError('complete finite fixed-calibration conditional forecast required')
        combined=np.vstack((forecast['coordinates'][:cut],fixed))
        conditional_errors=position_errors(combined,answer,model=spec['model'])
        conditional_scores=sections(conditional_errors,cut)
        save('conditional-scores.json',dict(times_s=times.tolist(),errors_neu_m=conditional_errors.tolist(),
            **conditional_scores,score_reference='generated noiseless physical truth',
            prediction_target='physical_position',parameter_uncertainty_included=False,
            confidence_calibrated=False,primary_raw_forecast_unchanged=True))
        result_summary['conditional_prediction']=conditional_scores['prediction']
        result_summary['linear_calibration_status']=diagnostic['linear_calibration']['status']
    return result_summary
