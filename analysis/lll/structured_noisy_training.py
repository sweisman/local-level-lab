# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared noisy calibration experiment using the existing study lifecycle."""
import math

SCOPE='generated structured-error training and withheld physical prediction; no original/protected inputs'


def recipe():
    from .airquantumgrav_training_controls import recipe as base
    from .airquantumgrav_noisy_inputs import noise_settings,rate_point_noise_settings
    return dict(base(),version='structured-noisy-training-v1',duration_s=120.,queries=119,
        latitudes_deg=[55.],input_laws=['increment','point'],policies=['reported-short-v1'],
        noise_by_law=dict(increment=noise_settings(),point=rate_point_noise_settings()),
        workers=4,threads=1,maximum_wall_s=7200.,gravity_model='inverse_square_height',height_profile='climb',
        prediction_target='physical_position',receiver_transform_policy='last-training-transform-v1',
        covariance_anchor_policy='normalized-midpoint-v1',bound_margin=1e-6,
        rank_rtol=1e-10,estimability_rtol=1e-8,estimability_atol=1e-10)


def case_recipe(r,law):
    if law not in r['input_laws']:raise ValueError('declared source-specific input law required')
    return dict(r,noise=r['noise_by_law'][law])


def limits(r,law):
    from .airquantumgrav_noisy_inputs import construction_limits
    n=round(r['duration_s']*r['rate_hz']);cut=2*r['queries']//3
    last=r['query_start_s']+(cut-1)*r['query_step_s']
    prefix=math.ceil((last+r['limits']['time_offset'])*r['rate_hz'])+2
    bridge=prefix+cut+n+r['queries']
    work=dict(native_calls=bridge+r['maximum_evaluations']+1,
        packet_visits=bridge+r['maximum_evaluations']*prefix*cut+n*r['queries'],bound_calls=0,bound_steps=0)
    construction=construction_limits(case_recipe(r,law));construction['generated_samples']+=r['queries']
    return work,construction


def tasks(r=None):
    import itertools
    r=recipe() if r is None else r;result=[]
    for law,model,profile,start in itertools.product(r['input_laws'],r['models'],r['profiles'],range(r['starts'])):
        result.append(dict(identity=f'{law}-{model}-{int(profile)}-{start}',input_key='recipe',native_kind='tangent',
            payload=dict(law=law,model=model,latitude_deg=55.,profile=profile,start=start,policy_id='reported-short-v1'),
            limits=limits(r,law)[0]))
    return result


def calculate(spec,r,*,kernel_factory,noise_kernel,reserve,reserve_construction,save,check_continue,training_provider=None):
    from .airquantumgrav_noisy_inputs import construct,error_law
    from .airquantumgrav_prediction import train_and_forecast
    from .airquantumgrav_training_controls import _spec
    from .airquantumgrav_observation_truth import receiver_samples
    from .ilvis0_native_error_training import ErrorTrainingFactory,ForecastErrorDiagnostic
    from .generated_prediction import calculate as generated
    if training_provider is not None and not callable(training_provider):
        raise ValueError('explicit training protocol provider required')
    protocol=train_and_forecast if training_provider is None else training_provider
    law=spec['law'];base={k:v for k,v in spec.items() if k!='law'};configured=case_recipe(r,law)
    material=construct(base,configured,reserve=reserve_construction)
    anchor=material['training_rows'][0]['height_m']
    factory=ErrorTrainingFactory(noise=error_law(configured['noise']),noise_kernel=noise_kernel,
        gravity_anchor_height_m=anchor,maximum_packets=len(material['dt']),maximum_queries=len(material['times']),
        maximum_bytes=64*1024**2,anchor_policy=r['covariance_anchor_policy'])
    diagnostic=ForecastErrorDiagnostic(factory,target=r['prediction_target'],
        receiver_transform_policy=r['receiver_transform_policy'],bound_margin=r['bound_margin'],
        rank_rtol=r['rank_rtol'],estimability_rtol=r['estimability_rtol'],estimability_atol=r['estimability_atol'])
    arguments,sign=_spec({k:v for k,v in base.items() if k!='policy_id'})
    written=set();binding={};operations=dict(bridge_calls=0,fit_forecast_calls=0,native_calls=0,packet_visits=0)
    def saving(name,value):
        save(name,value);written.add(name)
        if name=='input-binding.json':binding.update(value)
    def charge(**work):
        if set(work)!={'native_calls','packet_visits'} or work['native_calls']!=1:
            raise ValueError('one complete native operation reservation required')
        reserve(**work);operations['native_calls']+=1;operations['packet_visits']+=work['packet_visits']
        operations['bridge_calls' if work['packet_visits']==1 else 'fit_forecast_calls']+=1
    def truth(times):
        if not {'forecast.json','forecast-error-diagnostic.json'}<=written:
            raise ValueError('both forecasts must be saved before later truth')
        return receiver_samples(times=times,sign=sign,**arguments,height_profile=r['height_profile'],
            gravity_model=r['gravity_model'])
    result=generated(base,configured,material=material,train_and_forecast=protocol,kernel_factory=kernel_factory,
        reserve=charge,reserve_construction=reserve_construction,save=saving,truth=truth,check_continue=check_continue,
        training_error_factory=factory,forecast_error_diagnostic=diagnostic)
    if result['native_calls']!=operations['native_calls']:
        raise ValueError('full native construction and fitting counts differ')
    save('native-operation-summary.json',operations)
    return dict(result,law=law)
