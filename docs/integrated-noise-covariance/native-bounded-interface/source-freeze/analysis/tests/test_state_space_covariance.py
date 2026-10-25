# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest


def fixture():
    import numpy as np
    steps=[]
    for i,dt in enumerate((.3,.7,.2,1.1,.4)):
        steps.append(dict(transition=np.array([[1.,dt],[0.,.95]]),
            process_loading=np.array([[.03,0.],[.01,.02]]),
            observation=np.array([[1.,.1*i],[.2,1.],[.5,-.3]]),
            white_loading=np.array([[.3,0.,0.],[.02,.4,0.],[-.01,.03,.5]])))
    return np.eye(2)*.05,steps


def dense_reference(initial,steps):
    """Independent mapping from independent drivers to all observations."""
    import numpy as np
    process=initial.shape[1]+sum(s['process_loading'].shape[1] for s in steps)
    columns=process+sum(s['white_loading'].shape[1] for s in steps)
    state=np.zeros((initial.shape[0],columns));state[:,:initial.shape[1]]=initial
    rows=[];p=initial.shape[1];w=process
    for step in steps:
        state=step['transition']@state;b=step['process_loading'];state[:,p:p+b.shape[1]]+=b;p+=b.shape[1]
        observation=step['observation']@state;d=step['white_loading']
        observation[:,w:w+d.shape[1]]+=d;w+=d.shape[1];rows.append(observation)
    loading=np.vstack(rows)
    return loading@loading.T


def operator(initial,steps,**options):
    from lll.state_space_covariance import LinearInnovations
    return LinearInnovations(steps,epoch_count=len(steps),state_dimension=2,observation_dimension=3,
        initial_loading=initial,maximum_bytes=1024*1024,design_is_fixed=True,error_distribution='gaussian',**options)


def test_general_innovations_match_dense_whitening_on_all_27_columns():
    import numpy as np
    from scipy.linalg import solve_triangular
    initial,steps=fixture();saved=copy.deepcopy(steps);op=operator(initial,steps)
    cov=dense_reference(initial,steps);lower=np.linalg.cholesky(cov)
    values=np.sin(np.arange(len(cov)*27).reshape(len(cov),27));values[:,2]=0.;values[:,5]=values[:,6]
    np.testing.assert_allclose(op.whiten(values),solve_triangular(lower,values,lower=True),rtol=2e-12,atol=2e-12)
    np.testing.assert_allclose(op.whiten(values[:,0]),solve_triangular(lower,values[:,0],lower=True),rtol=2e-12,atol=2e-12)
    assert op.log_determinant==pytest.approx(2*np.log(np.diag(lower)).sum(),rel=2e-12)
    assert op.whiten(values).shape==values.shape
    for before,after in zip(saved,steps):
        for key in before:assert np.array_equal(before[key],after[key])


def test_general_innovations_roundtrip_and_serializable_block_continuity():
    import json
    import numpy as np
    initial,steps=fixture();op=operator(initial,steps);values=np.cos(np.arange(15*27).reshape(15,27))
    white=op.whiten(values);np.testing.assert_allclose(op.unwhiten(white),values,rtol=2e-12,atol=2e-12)
    first,state=op.apply_block(values[:6],first_epoch=0)
    state=json.loads(json.dumps(state));second,end=op.apply_block(values[6:],first_epoch=2,state=state)
    np.testing.assert_allclose(np.vstack([first,second]),white,rtol=2e-12,atol=2e-12)
    assert end['next_epoch']==5
    with pytest.raises(ValueError):op.apply_block(values[6:],first_epoch=2)
    with pytest.raises(ValueError):op.apply_block(values[6:],first_epoch=1,state=state)
    with pytest.raises(ValueError):op.apply_block(values[6:,:26],first_epoch=2,state=state)
    with pytest.raises(ValueError):op.apply_block(white[6:],first_epoch=2,state=state,inverse=True)


def test_general_innovations_reject_changed_configuration_for_saved_state():
    import numpy as np
    initial,steps=fixture();a=operator(initial,steps);_,state=a.apply_block(np.zeros(6),first_epoch=0)
    steps[3]['observation'][0,0]+=.01;b=operator(initial,steps)
    with pytest.raises(ValueError):b.apply_block(np.zeros(9),first_epoch=2,state=state)


@pytest.mark.parametrize('fault',['transition','loading','observation','singular','nonfinite','short','long'])
def test_general_innovations_reject_invalid_or_unmatched_steps(fault):
    import numpy as np
    initial,steps=fixture();count=len(steps)
    if fault=='transition':steps[0]['transition']=np.eye(3)
    elif fault=='loading':steps[0]['process_loading']=np.zeros((3,1))
    elif fault=='observation':steps[0]['observation']=np.ones((2,2))
    elif fault=='singular':steps[0]['white_loading']=np.zeros((3,3))
    elif fault=='nonfinite':steps[0]['transition'][0,0]=np.nan
    from lll.state_space_covariance import LinearInnovations
    if fault=='short':steps=steps[:-1]
    elif fault=='long':steps=steps+[steps[-1]]
    with pytest.raises(ValueError):LinearInnovations(steps,epoch_count=count,state_dimension=2,observation_dimension=3,
        initial_loading=initial,maximum_bytes=1024*1024,design_is_fixed=True,error_distribution='gaussian')


def test_general_innovations_checks_memory_before_consuming_steps():
    from lll.state_space_covariance import LinearInnovations
    def forbidden():
        raise AssertionError('storage allowance must be checked before reading steps')
        yield
    with pytest.raises(ValueError,match='storage'):
        LinearInnovations(forbidden(),epoch_count=64080,state_dimension=8,observation_dimension=3,
            initial_loading=None,maximum_bytes=1,design_is_fixed=True,error_distribution='gaussian')


@pytest.mark.parametrize('cut',[0,1,3,5])
def test_conditional_future_marginals_match_independent_dense_conditioning(cut):
    import numpy as np
    initial,steps=fixture();op=operator(initial,steps);cov=dense_reference(initial,steps)
    training=np.sin(np.arange(3*cut));state=None
    if cut:_,state=op.apply_block(training,first_epoch=0)
    result=op.conditional_marginals(state=state)
    if cut:
        cross=cov[3*cut:,:3*cut]
        expected_mean=cross@np.linalg.solve(cov[:3*cut,:3*cut],training)
        expected_cov=cov[3*cut:,3*cut:]-cross@np.linalg.solve(cov[:3*cut,:3*cut],cross.T)
    else:expected_mean=np.zeros(len(cov));expected_cov=cov
    np.testing.assert_allclose(result['mean'].ravel(),expected_mean,rtol=2e-12,atol=2e-12)
    for i,block in enumerate(result['covariance']):
        np.testing.assert_allclose(block,expected_cov[3*i:3*i+3,3*i:3*i+3],rtol=2e-12,atol=2e-12)
    assert result['conditioning_epochs']==cut and result['forecast_epochs']==len(steps)-cut
    assert result['later_observations_used'] is False
    assert result['parameter_uncertainty_included'] is False


def test_conditional_forecast_rejects_incomplete_or_multicolumn_state():
    import numpy as np
    initial,steps=fixture();op=operator(initial,steps)
    _,matrix_state=op.apply_block(np.zeros((6,27)),first_epoch=0)
    with pytest.raises(ValueError):op.conditional_marginals(state=matrix_state)
    _,state=op.apply_block(np.zeros(6),first_epoch=0)
    for key,value in (('configuration','changed'),('mean',[[0.]]),('inverse',True),('next_epoch',10)):
        bad=copy.deepcopy(state);bad[key]=value
        with pytest.raises(ValueError):op.conditional_marginals(state=bad)


def test_conditional_forecast_does_not_consume_unused_future_residuals():
    import numpy as np
    initial,steps=fixture();op=operator(initial,steps);values=np.arange(15.)
    _,state=op.apply_block(values[:6],first_epoch=0)
    result=op.conditional_marginals(state=state);values[6:]=1e30
    again=op.conditional_marginals(state=state)
    assert np.array_equal(result['mean'],again['mean'])
    assert np.array_equal(result['covariance'],again['covariance'])
