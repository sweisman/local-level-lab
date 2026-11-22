# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-only recorded-IMU forecast with a declared bounded optimizer."""

import gzip
import json


def evaluate(task,context,*,preflight):
    import numpy as np
    from .ilvis0_exploratory import MODELS,load_kernel
    from .ilvis0_shape import instrument_limits,load_tangent
    from .ilvis0_prediction import training_inputs
    from .ilvis0_training_forecast import training_problem,fit_training
    from .ilvis0_forecast import native_forecast
    from .ilvis0_gps_sensitivity import assumptions,coordinate_covariance
    from .ilvis0_saved_prediction import summarize
    from .ilvis0_independent_scipy_adapter import fit_candidate as scipy_trf
    from .ilvis0_solver_trust_v2 import fit_candidate as trust_v2

    spec=task['payload']
    policy=json.loads(context.input_path('recipe').read_bytes())
    if (policy['model']!='sphere_rotating' or
            policy['maximum_evaluations']!=200 or
            policy['stopping']!='near_zero' or
            policy['maximum_interval_s']!=.0075 or
            spec['model']!=policy['model'] or
            spec['profile'] is not False or
            spec['clock']!='header_elapsed' or
            spec['solver'] not in ('trust_v2','scipy_trf')):
        raise ValueError('unchanged recorded model and calibration required')
    common=json.loads(gzip.decompress(context.input_path().read_bytes()))
    prefix=json.loads(context.input_path(
        spec['segment_id']+'-'+spec['origin']+'-training').read_bytes())
    times=np.asarray(common['times'],float)
    values=np.asarray(common['values'],float)
    training_gps=np.asarray(prefix['training_gps'],float)
    count=common['layout']['receiver_epochs']
    outer=common['layout']['training_epochs']
    cut=prefix['cut_epoch']
    expected_cut=count//3 if spec['origin']=='inner' else outer
    horizon=min(outer-count//3,count-outer)
    if (spec['origin'] not in ('inner','outer') or
            common['segment_id']!=spec['segment_id'] or
            prefix['segment_id']!=spec['segment_id'] or
            count!=len(times) or outer!=2*count//3 or
            common['layout']['native_packets']!=len(values) or
            cut!=expected_cut or prefix['horizon_epochs']!=horizon or
            training_gps.shape!=(cut,3) or
            values.ndim!=2 or values.shape[1]!=15):
        raise ValueError('unchanged split, receiver prefix and packet dimensions required')
    limits=instrument_limits(policy['gyro_offset_dph'])
    placeholder=np.zeros((count,3))
    placeholder[:cut]=training_gps
    t,gps,v=training_inputs(times,placeholder,values,
                            limits['time_offset'],cut=cut)
    assumption=next(item for item in assumptions()
                    if item.name==policy['training_weight'])
    blocks=np.tile(np.diag(np.square(policy['independent_neu_m'])),
                   (len(t),1,1))
    covariance=coordinate_covariance(t,gps[:,0],gps[:,2],
                                     blocks,assumption)
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
    kernel,kmeta=load_kernel(directory)
    tangent,tmeta=load_tangent(directory)
    for name,meta in (('ilvis0_native.c',kmeta),
                      ('ilvis0_tangent.cpp',tmeta)):
        if context.manifest['sources']['analysis/lll/'+name]!=meta['source_sha256']:
            raise ValueError('compiled native source differs from freeze')
    context.save('compilation.json',dict(value=kmeta,tangent=tmeta))
    model=MODELS[0]
    if model!=policy['model']:
        raise ValueError('original conditional physical model required')
    problem=training_problem(t,gps,theta=v[:,9:12],dv=v[:,12:15],dt=v[:,2],
        covariance=covariance,model=model,limits=limits,profile=False,
        clock='header_elapsed',maximum_interval_s=policy['maximum_interval_s'],
        kernel=kernel,tangent_kernel=tangent)
    columns=len(problem.bounds.active)
    start=(np.zeros(columns) if spec['start']==0 else
           np.where(np.arange(columns)%2,-.001,.001))
    provider=scipy_trf if spec['solver']=='scipy_trf' else trust_v2
    fit=fit_training(problem,model,start=start,
        maximum_evaluations=30 if preflight else policy['maximum_evaluations'],
        reserve=context.charge,stopping='ordinary',solver_provider=provider)
    context.save('fit.json',fit)
    query=times[:cut+horizon]
    forecast=native_forecast(problem,fit['normalized_parameters'],model,
        theta=values[:,9:12],dv=values[:,12:15],dt=values[:,2],
        times=query,maximum_interval_s=policy['maximum_interval_s'],
        reserve=context.charge)
    context.save('forecast.json',dict(coordinates=forecast['coordinates'].tolist(),
        times=query.tolist(),active_parameters=forecast['active_parameters'],
        training_epochs=cut,prediction_epochs=horizon,
        continuous_propagation_without_gps_reset=True,
        prediction_receiver_positions_used=False))
    scoring=json.loads(context.input_path(
        spec['segment_id']+'-'+spec['origin']+'-scoring').read_bytes())
    later=np.asarray(scoring['prediction_gps'],float)
    if (scoring['segment_id']!=spec['segment_id'] or
            later.shape!=(horizon,3)):
        raise ValueError('separate complete scoring positions required')
    observed=np.concatenate((training_gps,later))
    metric=np.column_stack((6378137.+observed[:,2],
        (6378137.+observed[:,2])*np.cos(observed[:,0]),
        np.ones(len(observed))))
    errors=(forecast['coordinates']-observed)*metric
    if not np.all(np.isfinite(errors)):
        raise ValueError('finite scored forecast errors required')
    rows=[dict(epoch=index,time_s=float(time),
        role='training' if index<cut else 'prediction',
        **{axis+'_direct_error_m':float(errors[index,j])
           for j,axis in enumerate(('north','east','up'))})
        for index,time in enumerate(query)]
    report=summarize(rows,training_epochs=cut,prediction_epochs=horizon)
    context.save('epochs.json',rows)
    context.save('scores.json',report)
    if len(forecast['active_parameters'])!=26:
        raise ValueError('all 26 active calibration directions required')
    return dict(passed=True,technical_completion_only=True,
        preflight_only=preflight,segment_id=spec['segment_id'],
        origin=spec['origin'],model=model,profile=False,
        clock='header_elapsed',solver=spec['solver'],start=spec['start'],
        converged=fit['converged'],training_cost=fit['residual_sum_squares'],
        evaluations=fit['evaluations'],all_active_columns_retained=True,
        training=report['training'],prediction=report['prediction'],
        confidence_calibrated=False,scientific_decision='abstain',
        original_labels_reclassified=0)
