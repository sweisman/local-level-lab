# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


@pytest.fixture(scope='session')
def prediction_work():
    import time
    return dict(started=time.monotonic(),cases=0)


@pytest.fixture(autouse=True)
def finite_prediction_allowance(prediction_work):
    import time
    prediction_work['cases']+=1
    assert prediction_work['cases']<=16 and time.monotonic()-prediction_work['started']<120
    yield
    assert time.monotonic()-prediction_work['started']<120


def example(p,cutoff):
    import numpy as np
    from lll.state_space_covariance import LinearInnovations
    steps=[];n=16;m=3*cutoff
    for i in range(n):
        steps.append(dict(transition=np.array([[.9,.02,0.],[0.,.85,.01],[.01,0.,.95]]),
            process_loading=np.array([[.05,0.,0.],[.01,.07,0.],[0.,-.01,.04]]),
            observation=np.eye(3),white_loading=np.eye(3)*.2))
    op=LinearInnovations(steps,epoch_count=n,state_dimension=3,observation_dimension=3,
        initial_loading=np.eye(3)*.1,maximum_bytes=100000,design_is_fixed=True,error_distribution='gaussian')
    rows=np.arange(3*n)[:,None];columns=np.arange(p)[None,:]
    design=((rows%p)==columns).astype(float)+.03*np.sin((rows+1)*(columns+1)/7)
    truth=np.cos(np.arange(p)/7)*.2
    earlier=design[:m]@truth+.1*np.sin(np.arange(m)/5)
    return op,design,earlier


def call(op,design,earlier,cutoff,scales=None):
    import numpy as np
    from lll.calibrated_linear_prediction import predict
    return predict(op,design,earlier,training_epochs=cutoff,
        parameter_scales=np.ones(design.shape[1]) if scales is None else scales,
        prediction_scales=np.ones(3*(op.epoch_count-cutoff)),rank_rtol=1e-12,
        estimability_rtol=1e-10,estimability_atol=1e-12,maximum_parameters=27)


def independent_prediction(op,design,earlier,cutoff):
    import numpy as np
    u=op.unwhiten(np.eye(3*op.epoch_count));cov=u@u.T;m=3*cutoff
    train=design[:m];later=design[m:]
    information=train.T@np.linalg.solve(cov[:m,:m],train)
    coefficient=np.linalg.solve(information,np.linalg.solve(cov[:m,:m],train).T)
    carry=np.linalg.solve(cov[:m,:m],cov[:m,m:]).T
    weights=later@coefficient+carry@(np.eye(m)-train@coefficient)
    predicted=weights@earlier
    error_cov=cov[m:,m:]-weights@cov[:m,m:]-cov[m:,:m]@weights.T+weights@cov[:m,:m]@weights.T
    return predicted,error_cov,coefficient@earlier


@pytest.mark.parametrize('p',[1,3,27])
@pytest.mark.parametrize('cutoff',[10,12])
def test_fitted_mean_and_uncertainty_match_independent_prediction_weights(p,cutoff):
    import numpy as np
    op,design,earlier=example(p,cutoff);result=call(op,design,earlier,cutoff)
    mean,cov,parameters=independent_prediction(op,design,earlier,cutoff)
    assert result['status']=='estimable' and result['training_rank']==p
    np.testing.assert_allclose(result['mean'].ravel(),mean,rtol=2e-11,atol=2e-12)
    np.testing.assert_allclose(result['minimum_norm_parameter_estimate'],parameters,rtol=2e-11,atol=2e-12)
    for i,block in enumerate(result['covariance']):
        np.testing.assert_allclose(block,cov[3*i:3*i+3,3*i:3*i+3],rtol=2e-11,atol=2e-12)
    assert result['parameter_uncertainty_included'] is True
    assert result['later_observations_used'] is False
    assert result['calibration_bounds_used'] is False and result['nonlinear_coverage_established'] is False


@pytest.mark.parametrize('later_changes',[False,True])
def test_unknown_calibration_directions_are_retained_in_prediction_gate(later_changes):
    import numpy as np
    op,design,earlier=example(3,10);design[:,1]=design[:,0]
    if later_changes:design[30:,1]+=.3
    result=call(op,design,earlier,10)
    assert result['training_rank']==2 and result['parameter_count']==3
    if later_changes:
        assert result['status']=='unidentifiable' and 'covariance' not in result and 'mean' not in result
    else:
        assert result['status']=='estimable' and result['calibration_fully_identified'] is False
        reduced=np.column_stack((design[:,0],design[:,2]))
        expected=call(op,reduced,earlier,10)
        np.testing.assert_allclose(result['mean'],expected['mean'],rtol=2e-11,atol=2e-12)
        np.testing.assert_allclose(result['covariance'],expected['covariance'],rtol=2e-11,atol=2e-12)


def test_zero_mean_design_preserves_process_prediction_without_fake_parameter_precision():
    import numpy as np
    op,design,earlier=example(3,10);design[:]=0.
    result=call(op,design,earlier,10)
    _,checkpoint=op.apply_block(earlier,first_epoch=0)
    expected=op.conditional_marginals(state=checkpoint)
    assert result['training_rank']==0 and result['calibration_fully_identified'] is False
    np.testing.assert_array_equal(result['mean'],expected['mean'])
    np.testing.assert_array_equal(result['covariance'],expected['covariance'])
    assert not result['calibration_loading'].any()


def test_full_rank_prediction_is_invariant_to_declared_parameter_units():
    import numpy as np
    op,design,earlier=example(3,10);saved=design.copy();raw=earlier.copy()
    a=call(op,design,earlier,10);b=call(op,design,earlier,10,np.array([.03,3.,30.]))
    for key in ('mean','covariance','minimum_norm_parameter_estimate'):
        np.testing.assert_allclose(a[key],b[key],rtol=2e-10,atol=2e-11)
    np.testing.assert_array_equal(design,saved);np.testing.assert_array_equal(earlier,raw)


@pytest.mark.parametrize('bad',['later_rows','shape','scales','cutoff','nonfinite'])
def test_invalid_prediction_design_or_withheld_residuals_are_rejected(bad):
    import numpy as np
    op,design,earlier=example(3,10);cutoff=10;scales=None
    if bad=='later_rows':earlier=np.r_[earlier,np.ones(18)]
    elif bad=='shape':design=design[:-1]
    elif bad=='scales':scales=np.array([1.,0.,1.])
    elif bad=='cutoff':cutoff=16
    else:design[0,0]=np.nan
    with pytest.raises(ValueError):call(op,design,earlier,cutoff,scales)
