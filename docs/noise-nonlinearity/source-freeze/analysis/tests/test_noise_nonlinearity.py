# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


@pytest.fixture
def material():
    from lll.generated_noise_benchmark import material
    return material(duration_s=2.,queries=9,query_start_s=.1,query_step_s=.2,reserve=lambda **w:None)


@pytest.mark.parametrize('law',['increment','point'])
def test_nonlinear_draw_preserves_raw_inputs_seed_and_earlier_receiver_boundary(material,law):
    import numpy as np
    from lll.noise_nonlinearity import draw
    before=material['raw_theta'].copy();charges=[]
    a=draw(material,law=law,seed=26102500,reserve=lambda **w:charges.append(w))
    b=draw(material,law=law,seed=26102500,reserve=lambda **w:None)
    c=draw(material,law=law,seed=26102501,reserve=lambda **w:None)
    for name in ('theta_error','dv_error','receiver_error'):
        np.testing.assert_array_equal(a[name],b[name])
        assert not np.array_equal(a[name],c[name])
    np.testing.assert_array_equal(before,material['raw_theta'])
    assert a['receiver_error'].shape==(6,3)
    assert sum(v['noise_normal_variates'] for v in charges)==(18*600+6 if law=='increment' else 12*601)+42
    assert a['future_receiver_errors_generated'] is False


@pytest.mark.parametrize('patch',[{'law':'other'},{'seed':-1},{'seed':True}])
def test_nonlinear_draw_rejects_invalid_identity_before_charge(material,patch):
    from lll.noise_nonlinearity import draw
    args=dict(law='increment',seed=26102500);args.update(patch)
    with pytest.raises(ValueError):draw(material,**args,reserve=lambda **w:pytest.fail('charged invalid draw'))


def test_nonlinear_draw_reserves_before_any_random_generation(material,monkeypatch):
    from lll.noise_nonlinearity import draw
    from lll import measurement_noise
    monkeypatch.setattr(measurement_noise,'stream',lambda *a:pytest.fail('unpaid RNG'))
    def stop(**w):raise RuntimeError('no allowance')
    with pytest.raises(RuntimeError,match='no allowance'):draw(material,law='increment',seed=1,reserve=stop)


def operator(n=4):
    import numpy as np
    from lll.state_space_covariance import LinearInnovations
    steps=[dict(transition=np.eye(1),process_loading=np.ones((1,1))*.2,
        observation=np.array([[1.],[.5],[.2]]),white_loading=np.eye(3)*.1) for _ in range(n)]
    return LinearInnovations(iter(steps),epoch_count=n,state_dimension=1,observation_dimension=3,
        initial_loading=np.ones((1,1))*.3,maximum_bytes=100000,design_is_fixed=True,error_distribution='gaussian')


def test_nonlinear_conditional_errors_match_dense_sign_and_ignore_future_receiver():
    import numpy as np
    from lll.noise_nonlinearity import conditional_error
    op=operator();base=np.arange(12).reshape(4,3)*.01;change=np.ones((4,3))*.02
    receiver=np.ones((2,3))*.03;metric=np.repeat([[2.,3.,1.]],2,axis=0)
    actual=conditional_error(op,base,base+change,receiver,training_epochs=2,metric=metric)
    l=op.unwhiten(np.eye(12));cov=l@l.T
    k=np.linalg.solve(cov[:6,:6],cov[:6,6:]).T
    expected=(-change[2:].ravel()-k@(receiver-change[:2]).ravel()).reshape(2,3)*metric
    np.testing.assert_allclose(actual,expected,atol=1e-15)
    with pytest.raises(ValueError):conditional_error(op,base,base+change,np.ones((4,3)),training_epochs=2,metric=metric)


def test_antithetic_summary_separates_even_remainder_and_half_amplitude_response():
    import numpy as np
    from lll.noise_nonlinearity import summarize_pair
    odd=np.array([[.2,.4,.6],[.3,.5,.7]]);even=np.full((2,3),.0001)
    r=summarize_pair(odd+even,-odd+even,.5*odd+.25*even,-.5*odd+.25*even,
        standard_deviation=np.ones((2,3)),absolute_limit_m=.001,relative_limit=.01)
    assert r['passed'] and r['maximum_even_remainder_m']==pytest.approx(.0001)
    assert r['maximum_half_response_change_m']<1e-14
    assert r['independent_realizations']==1 and r['confidence_calibrated'] is False
    bad=summarize_pair(odd+.02,-odd+.02,.5*odd+.005,-.5*odd+.005,
        standard_deviation=np.ones((2,3)),absolute_limit_m=.001,relative_limit=.01)
    assert bad['passed'] is False


def test_antithetic_summary_keeps_fixed_numeric_floor_and_rejects_incomplete_curves():
    import numpy as np
    from lll.noise_nonlinearity import summarize_pair
    z=np.zeros((2,3))
    r=summarize_pair(z,z,z,z,standard_deviation=z,absolute_limit_m=.001,relative_limit=.01)
    assert r['passed'] and r['maximum_even_remainder_fraction_of_limit']==0
    with pytest.raises(ValueError):summarize_pair(z,z[:1],z,z,standard_deviation=z,absolute_limit_m=.001,relative_limit=.01)


def test_known_calibration_propagation_charges_before_native_call(material,monkeypatch):
    from lll.noise_nonlinearity import propagate
    from lll import ilvis0_precision_value
    monkeypatch.setattr(ilvis0_precision_value,'calculate',lambda *a,**kw:pytest.fail('unpaid native call'))
    def stop(**w):raise RuntimeError('no native allowance')
    with pytest.raises(RuntimeError,match='no native allowance'):
        propagate(material,theta=material['raw_theta'],dv=material['raw_dv'],operator=operator(9),kernel=lambda *a:None,reserve=stop)


def test_known_calibration_propagation_preserves_scalar_api_and_known_parameters(material,monkeypatch):
    import numpy as np
    from lll.noise_nonlinearity import propagate
    from lll import ilvis0_precision_value
    charges=[]
    def scalar(problem,point,model,**kwargs):
        assert problem.bounds.fit_earth_removal is False and model=='sphere_rotating'
        decoded=problem.bounds.decode(point)
        for k,v in material['sensor_correction'].items():assert decoded[k]==pytest.approx(v)
        return dict(coordinates=material['nominal_receiver'])
    monkeypatch.setattr(ilvis0_precision_value,'calculate',scalar)
    value=propagate(material,theta=material['raw_theta'],dv=material['raw_dv'],operator=operator(9),
        kernel=lambda *a:None,reserve=lambda **w:charges.append(w))
    np.testing.assert_array_equal(value,material['nominal_receiver'])
    assert charges==[dict(native_calls=1,packet_steps=600,packet_query_visits=5400)]
