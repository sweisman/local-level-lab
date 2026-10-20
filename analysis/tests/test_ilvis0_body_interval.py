# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import numpy as np
import pytest
from test_ilvis0_conditioned_transform_native import case as training_case
from lll.ilvis0_source_norm_preflight import body_bound,point_oracle
from lll.ilvis0_source_stream import SourceStream,load_stream


def test_prefix_body_interval_exists():
    assert importlib.util.find_spec('lll.ilvis0_body_interval') is not None


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):return load_stream(tmp_path_factory.mktemp('body-interval'))[0]


@pytest.mark.parametrize('model,profile',[(m,p) for m in range(3) for p in (False,True)])
def test_training_range_and_arbitrary_reference_rows_bound_source_errors(model,profile,kernel):
    from lll.ilvis0_body_interval import BodyInterval
    config,theta,dv,dt,center,lo,hi,reference,conditioning=training_case(model,profile)
    source=dict(configuration=config,theta=theta,dv=dv,dt=dt)
    interval=BodyInterval(reference,conditioning,lo,hi)
    baseline,_=body_bound(source,reference,lo,hi,.04)
    with SourceStream(kernel,source,center,.04,maximum_packets=len(dt)) as stream:
        for _ in dt:frame=stream.append()
    values=frame['values'][1];jac=frame['jacobian'][1].copy()
    # Deliberately alter a chosen row: the interval-to-affine conversion must
    # remain safe rather than assuming every supplied row is a derivative.
    jac[1,2,12]+=.01
    report=interval.bound(baseline,values,jac)
    assert report.details['uses_training_conditioning']
    assert report.jacobian.shape==(2,3,27)
    for sign in (-1,0,1):
        point=center.copy();point[12]+=.08*sign;point[13]-=.08*sign
        a,b,_=point_oracle(source,point,.04)
        for actual,bounded,row in zip((a,b),(report.a,report.b),jac,strict=True):
            assert np.all(abs(actual-bounded.center)<=bounded.component_change+1e-10)
            assert np.all(abs(actual-bounded.center-row@(point-center))<=bounded.component_remainder+1e-10)


def test_mismatched_domain_or_source_anchor_is_rejected(kernel):
    from lll.ilvis0_body_interval import BodyInterval
    config,theta,dv,dt,center,lo,hi,reference,conditioning=training_case(0,False)
    with pytest.raises(ValueError,match='domain'):BodyInterval(reference,conditioning,lo-.001,hi)
    interval=BodyInterval(reference,conditioning,lo,hi)
    source=dict(configuration=config,theta=theta,dv=dv,dt=dt)
    baseline,_=body_bound(source,reference,lo,hi,.04)
    with SourceStream(kernel,source,center,.04,maximum_packets=len(dt)) as stream:
        for _ in dt:frame=stream.append()
    values=frame['values'][1].copy();values[1,0]+=1
    with pytest.raises(ValueError,match='anchor'):interval.bound(baseline,values,frame['jacobian'][1])


def test_source_certificate_is_immutable_and_contradictions_are_not_branch_fallbacks(kernel):
    from dataclasses import FrozenInstanceError
    from lll.ilvis0_body_interval import BodyInterval,UnsupportedBodyBranch
    from lll.ilvis0_cached_transport import Value
    config,theta,dv,dt,center,lo,hi,reference,conditioning=training_case(0,False)
    interval=BodyInterval(reference,conditioning,lo,hi)
    with pytest.raises(FrozenInstanceError):interval.norm_error=0
    assert isinstance(interval.alo,tuple) and not interval.baseline_jac.flags.writeable
    source=dict(configuration=config,theta=theta,dv=dv,dt=dt)
    with SourceStream(kernel,source,center,.04,maximum_packets=len(dt)) as stream:
        for _ in dt:frame=stream.append()
    values=frame['values'][1].copy();values[1]=[0.,0.,.2]
    contradictory=Value([0.,0.,.2])
    with pytest.raises(ValueError,match='contradicts') as caught:
        interval.bound(contradictory,values,frame['jacobian'][1])
    assert not isinstance(caught.value,UnsupportedBodyBranch)


def test_verified_parent_conditioning_remains_valid_on_a_contained_domain():
    from lll.ilvis0_body_interval import BodyInterval
    *_,lo,hi,reference,conditioning=training_case(0,False)
    mid=(lo+hi)/2;lower=(lo+mid)/2;upper=(mid+hi)/2
    interval=BodyInterval(reference,conditioning,lower,upper)
    assert interval.lower==tuple(lower) and interval.upper==tuple(upper)
    assert interval.uses_training
