# SPDX-License-Identifier: AGPL-3.0-or-later
"""Boundary tests: omitting the kink remainder would fail these controls."""
import math
import numpy as np
import pytest

from lll.ilvis0_geographic_bounds import Coordinates,Scalar,State
from lll.ilvis0_local_step_bounds import Value,Matrix


def module():
    from lll import ilvis0_history_bounds
    return ilvis0_history_bounds


@pytest.mark.parametrize('center',[0.,.75,1.,1.25,2.])
def test_fraction_encloses_both_kinks_with_native_one_sided_slope(center):
    bound,slope=module().packet_fraction(Scalar.interval(center,0.,2.),start=.5,duration=1.)
    expected=1. if .5<center<=1.5 else 0.
    assert slope==expected
    for t in np.linspace(0.,2.,121):
        f=float(np.clip(t-.5,0.,1.));f0=float(np.clip(center-.5,0.,1.))
        assert bound.lower<=f<=bound.upper
        assert abs(f-f0-slope*(t-center))<=bound.value.remainder+1e-15


def test_exact_internal_boundary_uses_preceding_packet_derivative():
    time=Scalar.interval(1.,.8,1.2)
    before,ds_before=module().packet_fraction(time,start=0.,duration=1.)
    after,ds_after=module().packet_fraction(time,start=1.,duration=1.)
    assert (ds_before,ds_after)==(1.,0.)
    assert before.value.remainder>=.2-1e-15
    assert after.value.remainder>=.2-1e-15
    first,slope=module().packet_fraction(Scalar.interval(0.,0.,.1),start=0.,duration=1.)
    assert first.center==0. and slope==1.


def test_packet_fraction_preserves_nonlinear_time_remainder():
    time=Scalar(Value(.5,.1,.02),.4,.6)
    fraction,slope=module().packet_fraction(time,start=0.,duration=1.)
    assert slope==1. and fraction.value.remainder>=.02


def initial():
    return State(Coordinates(Scalar.fixed(math.radians(-65.)),Scalar.fixed(3.2),Scalar.fixed(9000.)),
        Value([180.,30.,0.]),Matrix(np.eye(3),0.,0.,'rotation'))


def inputs(n=3):
    durations=np.full(n,.005);starts=np.r_[0.,np.cumsum(durations)[:-1]]
    theta=[Value([1e-5,-2e-5,1e-5]) for _ in range(n)]
    dv=[Value([.001,.001,-.04905]) for _ in range(n)]
    return dict(initial=initial(),theta=theta,dv=dv,durations=durations,starts=starts,
        removal=Scalar.interval(0.,0.,1.),gravity=Scalar.fixed(9.81),
        lever=Value([1.,2.,.5]),model='sphere_rotating',disc_radius_m=6371000.)


def test_history_contains_exact_boundary_and_both_neighbors_without_dropping_packets():
    data=inputs();output=module().history(time=Scalar.interval(.005,.003,.012),**data)
    assert output.packet_indices==(0,1,2)
    assert output.boundary_crossings==2
    assert output.report()['packet_boundary_crossing_covered'] is True
    assert output.report()['floating_point_enclosure_verified'] is False
    assert output.report()['scientific_decision']=='abstain'
    for t in (.003,.005,.007,.01,.012):
        actual=module().history(time=Scalar.fixed(t),**data)
        np.testing.assert_array_less(np.abs(actual.observation.center-output.observation.center),
            np.array([s.value.change for s in (output.observation.latitude,output.observation.longitude,output.observation.height)])+1e-10)


def test_zero_time_is_identity_and_future_packets_do_not_expand_state():
    data=inputs();result=module().history(time=Scalar.fixed(0.),**data)
    assert result.packet_indices==()
    np.testing.assert_array_equal(result.state.position.center,data['initial'].position.center)
    np.testing.assert_array_equal(result.state.velocity.center,data['initial'].velocity.center)
    assert result.state.attitude.change==0.


@pytest.mark.parametrize('bad',['negative_time','end_exceeded','gap','reversal','zero_dt','length'])
def test_support_defects_are_rejected_instead_of_repaired(bad):
    data=inputs();time=Scalar.fixed(.005)
    if bad=='negative_time':time=Scalar.interval(.005,-.001,.01)
    elif bad=='end_exceeded':time=Scalar.interval(.005,0.,.02)
    elif bad=='gap':data['starts'][1]+=.001
    elif bad=='reversal':data['starts'][1]=-.001
    elif bad=='zero_dt':data['durations'][1]=0.
    else:data['theta']=data['theta'][:-1]
    with pytest.raises(ValueError):module().history(time=time,**data)
