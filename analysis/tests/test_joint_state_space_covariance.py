# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def problem(kind):
    import numpy as np
    if kind=='general':
        from test_state_space_covariance import fixture
        initial,steps=fixture()
        for i,s in enumerate(steps):
            s['observation_process_loading']=np.array([[.2,-.1],[-.15,.25],[.1,.12]])*(1+.1*i)
        return initial,steps,3
    initial=np.diag([.1,.02]);steps=[]
    for dt,fraction in zip((.005,1/300,.005,.005),(.2,.8,.4,.6)):
        sigma=.3*dt**.5
        steps.append(dict(transition=np.array([[1.,dt],[0.,1.]]),
            process_loading=np.array([[dt/2],[1.]])*sigma,
            observation=np.array([[1.,fraction*dt]]),
            observation_process_loading=np.array([[fraction*fraction*dt/2]])*sigma,
            white_loading=np.array([[.002]])))
    return initial,steps,1


def dense_joint(initial,steps):
    import numpy as np
    p=initial.shape[1];white=p+sum(s['process_loading'].shape[1] for s in steps)
    columns=white+sum(s['white_loading'].shape[1] for s in steps)
    state=np.zeros((initial.shape[0],columns));state[:,:p]=initial;observations=[]
    for s in steps:
        b=s['process_loading'];r=s['white_loading']
        observed=s['observation']@state
        observed[:,p:p+b.shape[1]]+=s['observation_process_loading']
        observed[:,white:white+r.shape[1]]+=r;white+=r.shape[1]
        state=s['transition']@state;state[:,p:p+b.shape[1]]+=b;p+=b.shape[1]
        observations.append(observed)
    loading=np.vstack(observations)
    return loading@loading.T


def operator(initial,steps,d,mode='before_transition_shared_noise'):
    from lll.state_space_covariance import LinearInnovations
    return LinearInnovations(steps,epoch_count=len(steps),state_dimension=len(initial),observation_dimension=d,
        initial_loading=initial,maximum_bytes=1024*1024,design_is_fixed=True,error_distribution='gaussian',
        observation_form=mode)


@pytest.mark.parametrize('kind',['general','packet'])
def test_shared_process_observation_whitening_matches_dense_all_columns(kind):
    import numpy as np
    from scipy.linalg import solve_triangular
    initial,steps,d=problem(kind);op=operator(initial,steps,d);c=dense_joint(initial,steps);lower=np.linalg.cholesky(c)
    values=np.sin(np.arange(len(c)*27).reshape(len(c),27));values[:,2]=0;values[:,5]=values[:,6]
    expected=solve_triangular(lower,values,lower=True)
    np.testing.assert_allclose(op.whiten(values),expected,rtol=2e-11,atol=2e-11)
    np.testing.assert_allclose(op.unwhiten(expected),values,rtol=2e-11,atol=2e-11)
    assert op.log_determinant==pytest.approx(2*np.log(np.diag(lower)).sum(),abs=2e-11)


@pytest.mark.parametrize('kind',['general','packet'])
def test_shared_process_observation_conditional_forecast_matches_dense(kind):
    import numpy as np
    initial,steps,d=problem(kind);op=operator(initial,steps,d);c=dense_joint(initial,steps);n=2*d
    earlier=np.sin(np.arange(n));_,checkpoint=op.apply_block(earlier,first_epoch=0)
    answer=op.conditional_marginals(state=checkpoint)
    mean=c[n:,:n]@np.linalg.solve(c[:n,:n],earlier)
    cov=c[n:,n:]-c[n:,:n]@np.linalg.solve(c[:n,:n],c[:n,n:])
    np.testing.assert_allclose(answer['mean'].ravel(),mean,rtol=2e-11,atol=2e-11)
    for i,block in enumerate(answer['covariance']):
        np.testing.assert_allclose(block,cov[d*i:d*i+d,d*i:d*i+d],rtol=2e-11,atol=2e-11)


def test_joint_loading_requires_matching_process_driver_columns():
    import numpy as np
    initial,steps,d=problem('general');steps[0]['observation_process_loading']=np.ones((d,3))
    with pytest.raises(ValueError):operator(initial,steps,d)


def test_observation_mode_is_bound_to_checkpoint_configuration():
    import numpy as np
    initial,steps,d=problem('general');a=operator(initial,steps,d);_,state=a.apply_block(np.zeros(2*d),first_epoch=0)
    for s in steps:del s['observation_process_loading']
    b=operator(initial,steps,d,mode='after_transition')
    with pytest.raises(ValueError):b.apply_block(np.zeros((len(steps)-2)*d),first_epoch=2,state=state)


def test_shared_packet_noise_is_not_equivalent_to_independent_query_noise():
    import numpy as np
    initial,steps,d=problem('packet');c=dense_joint(initial,steps)
    for s in steps:
        shared=s['observation_process_loading'];r=s['white_loading']
        s['white_loading']=np.hstack([r,shared]);s['observation_process_loading']=np.zeros_like(shared)
    independent=dense_joint(initial,steps)
    np.testing.assert_allclose(np.diag(c),np.diag(independent),rtol=2e-15,atol=2e-17)
    assert np.max(abs(c-independent))>1e-9


def test_joint_and_legacy_modes_require_explicit_exact_step_schema():
    initial,steps,d=problem('general')
    with pytest.raises(ValueError):operator(initial,steps,d,mode='after_transition')
    for s in steps:del s['observation_process_loading']
    with pytest.raises(ValueError):operator(initial,steps,d)
