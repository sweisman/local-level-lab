# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compiled midpoint controls; no observed data or prediction-coverage claim."""
from fractions import Fraction as F
import pytest


@pytest.fixture(scope='module')
def backend(tmp_path_factory):
    from lll.ilvis0_path_step import load_backend
    return load_backend(tmp_path_factory.mktemp('path-step'))[0]


def fixture():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_motion import State,exponential
    c=J.constant
    # Nonzero derivatives in position, speed, attitude, sensor calibration,
    # gravity, radius and clock. These are actual derivatives, not coefficients.
    s=J.affine(0,[1,1],[0,0])
    attitude=exponential([c(F(1,100))+s/1000,c(F(-1,200))+s.square()/2000,s**3/3000])
    state=State((c(F(-2,3))+s/10**6,c(F(1,4))-s/10**7,c(1500)+s/2),
        (c(185)+s/3,c(65)-s.square()/5,c(-1)+s**3/7),attitude)
    dt=c(F(1,200))+s/10**5
    theta=tuple((c(v)-s/10**7)/(1+s/10000) for v in (F(1,50000),F(-1,40000),F(1,30000)))
    dv=tuple((c(v)-s.square()/10**6)/(1+s/2000) for v in (F(1,1000),F(-1,2000),F(-49,1000)))
    return state,theta,dv,dt,c(F(49,5))+s/100,c(6378137)+s/100,c(0)


def flattened(state):
    return (*state.coordinates,*state.velocity,*(v for row in state.attitude for v in row))


@pytest.mark.parametrize('model',[0,1,2])
@pytest.mark.parametrize('removal',[F(0),F(1,2)])
def test_every_step_derivative_encloses_high_precision_rational_reference(backend,monkeypatch,model,removal):
    from lll.ilvis0_path_jets import Jet3 as J
    from lll import ilvis0_path_motion as reference
    args=list(fixture());args[-1]=J.constant(removal)
    # Tighten reference rounding only in memory; frozen source files stay intact.
    monkeypatch.setattr(reference,'_q',lambda v:v.rounded(binary_bits=192))
    expected=reference.step(model,*args);actual=backend.step(model,*args)
    for compiled,rational in zip(flattened(actual),flattened(expected)):
        for (lo,hi),(left,right) in zip(compiled.exact,rational.exact):
            assert lo<=left<=right<=hi


def test_independent_gain_control_has_known_third_derivative(backend):
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_motion import State
    c=J.constant;s=J.affine(0,[1,1],[0,0]);dt=c(F(1,200));g=c(F(49,5))
    identity=tuple(tuple(c(int(i==j)) for j in range(3)) for i in range(3))
    state=State((c(0),c(0),c(1000)),(c(0),)*3,identity)
    answer=backend.step(2,state,[c(0)]*3,[c(0),c(0),-g*dt/(1+s/2)],dt,g,c(6000000),c(0))
    for n,accel in enumerate((F(0),F(49,10),F(-49,10),F(147,20))):
        for value,target in ((answer.velocity[2],accel/200),
                (answer.coordinates[2],(1000 if n==0 else 0)-accel/80000)):
            lo,hi=value.exact[n]
            assert lo<=target<=hi and hi-lo<F(1,10**8)


def test_stable_rotation_branches_and_switch_rejection(backend):
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_motion import exponential
    for angle in (F(1,1000),F(1,4)):
        vector=[J.constant(0),J.constant(0),J.constant(angle)]
        actual=backend.rotation(vector);expected=exponential(vector)
        for row,ref in zip(actual,expected):
            for a,b in zip(row,ref):
                # The reference's 96-bit absolute rounding is wider near zero.
                assert a.exact[0][0]<=b.exact[0][1] and b.exact[0][0]<=a.exact[0][1]
    with pytest.raises(ValueError,match='unsupported'):
        backend.rotation([J.constant(0),J.constant(0),J.constant(['0.009','0.011'])])


def test_invalid_domains_fail_before_a_result_is_returned(backend):
    from lll.ilvis0_path_jets import Jet3 as J
    args=list(fixture())
    for model in (-1,3,True):
        with pytest.raises(ValueError):backend.step(model,*args)
    for index,value in ((3,J.constant(-1)),(4,J.constant(0)),(5,J.constant(-1)),(6,J.constant(2))):
        bad=args.copy();bad[index]=value
        with pytest.raises(ValueError):backend.step(0,*bad)
    with pytest.raises(ValueError):backend.step(0,args[0],args[1][:2],*args[2:])
    with pytest.raises(ValueError):backend.rotation([J.constant(0)]*2)


def test_closure_metadata_includes_every_compiled_source(tmp_path):
    from lll.ilvis0_path_step import load_backend
    _,metadata=load_backend(tmp_path)
    assert set(metadata['sources'])=={'ilvis0_path_step.cpp','ilvis0_path_arithmetic.cpp','ilvis0_compiled_bounds.cpp'}
    assert metadata['derivative_order']==3 and metadata['stable_rotation_branches_only']
    assert not metadata['floating_point_native_execution_covered']
    assert not metadata['full_history_qualified']
