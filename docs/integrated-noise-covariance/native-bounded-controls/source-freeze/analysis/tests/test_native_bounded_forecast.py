# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def fixture(profile=False,point_value=1.):
    import numpy as np
    from test_structured_native_training import error_fixture,make_problem,forecast_fixture
    op,_,_,_=error_fixture();problem=make_problem(None,observation_error=op.prefix(3),profile=profile)
    problem.requires_extended_training_difference=True;problem.frozen_error_model='sphere_rotating'
    point=np.full(len(problem.bounds.active),point_value)
    forecast=forecast_fixture(problem)
    forecast.update(training_coordinate_difference=np.full((3,3),1e-20),
        normalized_parameters=point.tolist(),frozen_error_model='sphere_rotating',
        error_training_configuration=problem.observation_error.configuration,
        training_residual_subtraction='native-before-binary64-cast')
    return problem,point,forecast,op


def call(problem,point,forecast,op,*,missing=False):
    import numpy as np
    from lll.ilvis0_bounded_error_forecast import diagnose_bounded_forecast
    from lll.ilvis0_bounded_prediction import known_scale
    return diagnose_bounded_forecast(problem,point,forecast,op,
        scale=known_scale(1.,source_id='exact-linear-software',covariance_id=op.configuration),
        training_remainder_radius=None if missing else 0.,future_remainder_bounds=None if missing else np.zeros(6),
        alpha_training=.01,alpha_prediction=.01,bound_margin=1e-6,
        parameter_scales=np.ones(len(point)),prediction_scales=np.ones(6),
        rank_rtol=1e-12,estimability_rtol=1e-10,estimability_atol=1e-12)


@pytest.mark.parametrize('profile',[False,True])
@pytest.mark.parametrize('point',[-1.,1.])
def test_native_bounded_diagnostic_retains_original_boundary_label_and_all_columns(profile,point):
    p,u,f,op=fixture(profile,point);r=call(p,u,f,op)
    assert r['linear_calibration']['status']=='active_bounds_unsupported'
    b=r['bounded_calibration'];assert b['supported'] and b['parameter_count']==26+int(profile)
    assert b['all_mean_columns_retained'] and b['nonlinear_coverage_established'] is False
    assert r['confidence_calibrated'] is False and r['later_observations_used'] is False


def test_native_bounded_diagnostic_retains_translated_box_for_unidentified_direction():
    import numpy as np
    p,u,f,op=fixture();f['jacobian'][9:,0]=2.
    r=call(p,u,f,op)['bounded_calibration']
    # Fitted u=+1 permits delta u in [-2,0], rather than [-1,1].
    assert np.all(r['lower']<f['coordinates'][3:].ravel()-4.)
    assert np.all(r['upper']>f['coordinates'][3:].ravel())


def test_native_bounded_diagnostic_missing_remainders_remain_unsupported():
    p,u,f,op=fixture();r=call(p,u,f,op,missing=True)
    assert r['bounded_calibration']['supported'] is False
    assert 'lower' not in r['bounded_calibration']
    assert r['linear_calibration']['status']=='active_bounds_unsupported'


def test_native_bounded_diagnostic_uses_before_cast_residual_sign():
    import numpy as np
    p,u,f,op=fixture();r=call(p,u,f,op)['bounded_calibration']
    _,state=op.apply_block(-f['training_coordinate_difference'].ravel(),first_epoch=0)
    fixed=op.conditional_marginals(state=state)
    center=(r['lower']+r['upper'])/2-f['coordinates'][3:].ravel()
    np.testing.assert_allclose(center,fixed['mean'].ravel(),atol=1e-12)


@pytest.mark.parametrize('bad',['point','model','configuration','before_cast','split','columns'])
def test_native_bounded_diagnostic_rejects_mixed_or_incomplete_native_artifacts(bad):
    p,u,f,op=fixture()
    if bad=='point':f['normalized_parameters'][0]=0.
    elif bad=='model':f['frozen_error_model']='flat_still'
    elif bad=='configuration':f['error_training_configuration']='other'
    elif bad=='before_cast':f.pop('training_coordinate_difference')
    elif bad=='split':f['training_epochs']=4
    else:f['active_parameters']=f['active_parameters'][:-1]
    with pytest.raises(ValueError):call(p,u,f,op)


def provider(factory,future):
    from lll.ilvis0_bounded_error_forecast import BoundedForecastErrorDiagnostic
    return BoundedForecastErrorDiagnostic(factory,target='physical_position',
        receiver_transform_policy='last-training-transform-v1',bound_margin=1e-6,
        rank_rtol=1e-12,estimability_rtol=1e-10,estimability_atol=1e-12,
        scale_value=1.,scale_source_id='declared-software-law',training_remainder_radius=0.,
        future_remainder_bounds=future,alpha_training=.01,alpha_prediction=.01)


@pytest.mark.parametrize('invalid_future',[False,True])
def test_bounded_native_protocol_extends_once_and_preflights_remainder_shape(monkeypatch,invalid_future):
    import numpy as np
    from lll.ilvis0_native_error_training import ErrorTrainingFactory
    p,u,f,op=fixture();factory=ErrorTrainingFactory.__new__(ErrorTrainingFactory);calls=[]
    def extend(problem,**kwargs):
        assert problem is p and not any('gps' in key or 'receiver' in key for key in kwargs if key!='receiver_transform_policy')
        assert kwargs['target']=='physical_position'
        calls.append(True);return op,{'controlled_operator':True}
    monkeypatch.setattr(factory,'extend',extend)
    diagnostic=provider(factory,np.zeros(5 if invalid_future else 6))
    run=lambda:diagnostic(p,u,f,theta=p.theta,dv=p.dv,dt=p.dt,
        times=np.array([.01,.025,.04,.045,.05]),reserve=lambda **w:pytest.fail('unexpected native work'))
    if invalid_future:
        with pytest.raises(ValueError):run()
        assert calls==[]
    else:
        r=run();assert calls==[True] and r['prediction_target']=='physical_position'
        assert r['bounded_calibration']['supported']
