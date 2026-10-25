# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent dense controls for a structured bounded-prediction adapter."""
import time
import pytest


@pytest.fixture(scope='module',autouse=True)
def finite_allowance():
    started=time.monotonic()
    yield
    assert time.monotonic()-started<120


def example(form='after_transition',p=3):
    import numpy as np
    from lll.state_space_covariance import LinearInnovations
    rows=[]
    for i in range(12):
        step=dict(transition=np.array([[.95,.03],[0.,.9]]),
            process_loading=np.array([[.03,0.],[.01,.04]]),
            observation=np.array([[1.,.2],[.1,1.]]),white_loading=np.eye(2)*.1)
        if form=='before_transition_shared_noise':step['observation_process_loading']=np.array([[.02,.01],[0.,.03]])
        rows.append(step)
    op=LinearInnovations(rows,epoch_count=12,state_dimension=2,observation_dimension=2,
        initial_loading=np.eye(2)*.2,maximum_bytes=100000,design_is_fixed=True,
        error_distribution='gaussian',observation_form=form)
    x=np.cos((np.arange(24)[:,None]+1)*(np.arange(p)[None,:]+1)/7.)
    return op,x,x[:16]@np.linspace(-.2,.3,p)+.01*np.sin(np.arange(16))


def arguments(op,x,y):
    import numpy as np
    from lll.ilvis0_bounded_prediction import known_scale
    return dict(operator=op,design=x,training_values=y,training_epochs=8,
        coefficient_bounds=np.tile([-1.,1.],(x.shape[1],1)),nominal_future=np.zeros(8),
        scale=known_scale(1.,source_id='declared-software-law',covariance_id=op.configuration),
        training_remainder_radius=0.,future_remainder_bounds=np.zeros(8),
        alpha_training=.01,alpha_prediction=.01,mean_design_is_fixed=True,
        rank_tolerance=1e-10,maximum_parameters=27,prediction_ids=[str(i) for i in range(8)])


@pytest.mark.parametrize('form',['after_transition','before_transition_shared_noise'])
def test_bounded_state_geometry_matches_independent_dense_conditional_blocks(form):
    import numpy as np
    from lll.bounded_state_prediction import geometry
    op,x,y=example(form);g=geometry(op,x,y,training_epochs=8)
    l=op.unwhiten(np.eye(24));c=l@l.T;k=np.linalg.solve(c[:16,:16],c[:16,16:]).T
    np.testing.assert_allclose(g['conditional_mean'],k@y,rtol=1e-12,atol=1e-13)
    np.testing.assert_allclose(g['contrasts'],x[16:]-k@x[:16],rtol=1e-12,atol=1e-13)
    np.testing.assert_allclose(g['conditional_variance'],np.diag(c[16:,16:]-k@c[:16,16:]),rtol=1e-12,atol=1e-13)
    np.testing.assert_allclose(g['training_response_norm'],np.linalg.norm(k@l[:16,:16],axis=1),rtol=1e-12,atol=1e-13)
    np.testing.assert_allclose(g['whitened_values'],np.linalg.solve(l[:16,:16],y),rtol=1e-12,atol=1e-13)


@pytest.mark.parametrize('bound',[-1.,0.,1.])
def test_bounded_state_prediction_keeps_exact_boundary_truth(bound):
    import numpy as np
    from lll.bounded_state_prediction import predict
    op,x,y=example(p=1);y=x[:16,0]*bound
    before=x.copy();old=y.copy();r=predict(**arguments(op,x,y))
    assert r['supported'] and r['parameter_count']==1
    assert np.all(r['lower']<=x[16:,0]*bound) and np.all(r['upper']>=x[16:,0]*bound)
    assert r['observational_coverage_calibrated'] is False
    np.testing.assert_array_equal(x,before);np.testing.assert_array_equal(y,old)


def test_bounded_state_prediction_preserves_unknown_future_affecting_parameter():
    import numpy as np
    from lll.bounded_state_prediction import predict
    op,x,y=example(p=2);x[:,1]=0.;x[16:,1]=2.
    r=predict(**arguments(op,x,y))
    assert r['supported'] and r['training_rank']==1 and r['parameter_count']==2
    assert np.all(r['upper']-r['lower']>=4.)


@pytest.mark.parametrize('missing',['training','future'])
def test_bounded_state_prediction_withholds_unsupported_nonlinear_remainders(missing):
    from lll.bounded_state_prediction import predict
    op,x,y=example();a=arguments(op,x,y)
    a['training_remainder_radius' if missing=='training' else 'future_remainder_bounds']=None
    r=predict(**a)
    assert r['supported'] is False and 'lower' not in r and 'upper' not in r


def test_bounded_state_prediction_retains_all_27_columns_under_rank_deficiency():
    from lll.bounded_state_prediction import predict
    op,x,y=example(p=27);r=predict(**arguments(op,x,y))
    assert r['supported'] and r['parameter_count']==27 and r['training_rank']<=16


@pytest.mark.parametrize('bad',['later_values','missing_bound','missing_column','invalid_split','nonfinite'])
def test_bounded_state_prediction_rejects_hidden_later_values_and_incomplete_layout(bad):
    import numpy as np
    from lll.bounded_state_prediction import predict
    op,x,y=example();a=arguments(op,x,y)
    if bad=='later_values':a['training_values']=np.r_[y,np.ones(8)]
    elif bad=='missing_bound':a['coefficient_bounds']=a['coefficient_bounds'][:-1]
    elif bad=='missing_column':a['design']=x[:-1]
    elif bad=='invalid_split':a['training_epochs']=12
    else:a['design'][0,0]=float('nan')
    with pytest.raises(ValueError):predict(**a)


def test_bounded_state_prediction_is_invariant_to_parameter_units():
    import numpy as np
    from lll.bounded_state_prediction import predict
    op,x,y=example();a=arguments(op,x,y);first=predict(**a)
    units=np.array([.1,10.,2.]);a['design']=x*units
    a['coefficient_bounds']=a['coefficient_bounds']/units[:,None]
    second=predict(**a)
    np.testing.assert_allclose(first['lower'],second['lower'],rtol=2e-10,atol=1e-10)
    np.testing.assert_allclose(first['upper'],second['upper'],rtol=2e-10,atol=1e-10)


@pytest.mark.parametrize('fixed',[False,True])
@pytest.mark.parametrize('form',['after_transition','before_transition_shared_noise'])
def test_bounded_state_envelopes_match_independent_dense_adapter(fixed,form):
    import numpy as np
    from lll.bounded_state_prediction import predict
    from lll.ilvis0_bounded_prediction import Region,predict as envelope
    op,x,y=example(form);a=arguments(op,x,y);a['mean_design_is_fixed']=fixed
    a['training_remainder_radius']=.03;a['future_remainder_bounds']=np.linspace(.01,.02,8)
    got=predict(**a)
    l=op.unwhiten(np.eye(24));c=l@l.T
    k=np.linalg.solve(c[:16,:16],c[:16,16:]).T
    factor=np.linalg.cholesky(c[:16,:16])
    region=Region(np.linalg.solve(factor,y),np.linalg.solve(factor,x[:16]),a['coefficient_bounds'],
        scale=a['scale'],covariance_id=op.configuration,remainder_radius=.03,
        alpha=.01,rank_tolerance=1e-10,design_is_fixed=fixed)
    expected=envelope(region,k@y,x[16:]-k@x[:16],
        conditional_variance=np.diag(c[16:,16:]-k@c[:16,16:]),
        training_response_norm=np.linalg.norm(k@factor,axis=1),
        future_remainder_bounds=a['future_remainder_bounds'],alpha=.01,prediction_ids=a['prediction_ids'])
    assert got['supported'] and got['nominal_failure_probability_bound']==.02
    for key in ('lower','upper','conditional_noise_half_width','deterministic_remainder_half_width'):
        np.testing.assert_allclose(got[key],expected[key],rtol=2e-11,atol=2e-12)


def test_bounded_state_prediction_rejects_scale_from_another_covariance():
    from lll.bounded_state_prediction import predict
    from lll.ilvis0_bounded_prediction import known_scale
    op,x,y=example();a=arguments(op,x,y)
    a['scale']=known_scale(1.,source_id='software',covariance_id='other')
    with pytest.raises(ValueError):predict(**a)
