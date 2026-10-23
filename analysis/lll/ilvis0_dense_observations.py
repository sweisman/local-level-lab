# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reproducible generated errors for the declared dense prediction controls.

This uses the existing structured covariance factor; it does not estimate an
instrument's noise or qualify nonlinear trajectory coverage. Forecast workers
must seal their forecasts before calling complete_noise. The training API draws
no future innovations and accepts no future measurements or fitted residuals.
"""
from lll.studies.artifacts import digest,encoded,reports_equal


def plan():
    return dict(version='ilvis0-dense-noise-v1',entropy=20261023,bit_generator='PCG64DXSM',
        laws=[[10,1e-12],[10,1e-10],[300,1e-12],[300,1e-10]],
        training_times_s=list(map(float,range(2,291))),future_times_s=list(map(float,range(292,439))),
        clock_s=.25,roles=dict(training=0,future=1),scale=1.,fitted_mean_parameters=0,
        error_law_is_device_estimate=False)


def stream_spec(model,profile,law_index,role):
    if (type(model) is not int or model not in range(3) or type(profile) is not bool
            or type(law_index) is not int or law_index not in range(4)
            or type(role) is not int or role not in (0,1)):
        raise ValueError('registered model, processing case, law and stream role required')
    p=plan()
    return dict(entropy=p['entropy'],spawn_key=[2*model+int(profile),law_index,role],bit_generator=p['bit_generator'])


def _innovations(model,profile,law_index,role,count):
    import numpy as np
    spec=stream_spec(model,profile,law_index,role)
    rng=np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence(spec['entropy'],spawn_key=tuple(spec['spawn_key']))))
    values=rng.standard_normal(count)
    return values,dict(spec,values=count,sha256=digest(values.astype('<f8').tobytes()))


def _transform(times,innovations,*,law_index,clock_s):
    import numpy as np
    from lll.ilvis0_receiver_distance import receiver_spec,joint_operator
    if type(law_index) is not int or law_index not in range(4) or clock_s!=plan()['clock_s']:
        raise ValueError('fixed declared law and generated-truth clock required')
    tau,q=plan()['laws'][law_index]
    op=joint_operator(np.asarray(times,float)+clock_s,receiver_spec(tau),q)
    return dict(error_m=op.unwhiten(innovations).reshape(-1,3).tolist(),operator_id=op.configuration,
        mean_parameters_fitted=0,observational_coverage_qualified=False)


def training_noise(*,model,profile,law_index):
    """Draw only earlier errors; later observations cannot enter this interface."""
    stream_spec(model,profile,law_index,0)  # Reject unknown identities before numerical imports.
    from lll.ilvis0_summary_error_controls import recipe
    p=plan();times=p['training_times_s'];z,stream=_innovations(model,profile,law_index,0,3*len(times))
    value=_transform(times,z,law_index=law_index,clock_s=p['clock_s'])
    return dict(version=p['version'],model=model,profile=profile,law_index=law_index,
        times_s=times,clock_s=p['clock_s'],error_m=value['error_m'],operator_id=value['operator_id'],
        training_stream=stream,plan_sha256=digest(encoded(p)),error_recipe_sha256=digest(encoded(recipe())),
        future_innovations_drawn=False,mean_parameters_fitted=0,error_law_is_device_estimate=False,
        observational_coverage_qualified=False)


def complete_noise(earlier):
    """Release later errors after the caller has verified a closed forecast.

    This is a generated-data utility, not an authorization gate. The worker is
    responsible for verifying its forecast receipt before invoking it. Exact
    replay rejects a changed earlier realization and preserves its complete
    correlation with later errors; separate innovation streams do not mean
    independent position-error processes.
    """
    import numpy as np
    keys={k:earlier[k] for k in ('model','profile','law_index')}
    check=training_noise(**keys)
    if not reports_equal(earlier,check):raise ValueError('recorded training realization or premise changed')
    p=plan();a=p['training_times_s'];b=p['future_times_s']
    train,_=_innovations(**keys,role=0,count=3*len(a));future,stream=_innovations(**keys,role=1,count=3*len(b))
    full=_transform(a+b,np.r_[train,future],law_index=keys['law_index'],clock_s=p['clock_s'])
    if not np.array_equal(np.asarray(full['error_m'][:len(a)]),np.asarray(earlier['error_m'])):
        raise ValueError('future process changed its earlier training prefix')
    return dict(version=p['version'],**keys,times_s=b,future_error_m=full['error_m'][len(a):],
        full_operator_id=full['operator_id'],training_record_sha256=digest(encoded(earlier)),
        training_stream=earlier['training_stream'],future_stream=stream,training_prefix_bitwise_equal=True,
        mean_parameters_fitted=0,error_law_is_device_estimate=False,observational_coverage_qualified=False)
