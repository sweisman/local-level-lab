# SPDX-License-Identifier: AGPL-3.0-or-later
from dataclasses import FrozenInstanceError
import numpy as np
import pytest
from lll.ilvis0_directional_acceleration import DirectionalAcceleration
from lll.ilvis0_transform_native import make_reference
from test_ilvis0_native_box_bounds import configuration


def fixture():
    config=configuration();n=5;dt=np.full(n,.005);theta=np.zeros((n,3))
    dv=np.tile([0.,0.,-.04905],(n,1));lo=-np.ones(27);hi=np.ones(27);center=np.zeros(27)
    config['limits'][:]=0.;config['limits'][:3]=[.01,.01,3.]
    reference=make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    return reference,lo,hi


def test_typed_bound_keeps_reference_remainder_and_tighter_vertical_radius():
    reference,lo,hi=fixture();proof=DirectionalAcceleration(reference,lo,hi)
    radius,parts=proof.match(reference.report(),lo,hi)
    assert radius>=max(parts)
    assert parts[2]<.0011 and parts[2]<reference.acceleration.change/100
    assert proof.original_remainder==reference.acceleration.remainder
    assert proof.report()['uses_training_data'] is False
    assert proof.report()['preserves_shared_remainders'] is True


def test_proof_and_source_are_immutable():
    reference,lo,hi=fixture();proof=DirectionalAcceleration(reference,lo,hi)
    with pytest.raises(FrozenInstanceError):proof.norm_change=0
    lo[0]=0
    with pytest.raises(ValueError,match='domain'):proof.match(reference.report(),lo,hi)
    report=reference.report();report['binding']='changed'
    with pytest.raises(ValueError,match='reference'):proof.match(report,proof.lower,proof.upper)


@pytest.mark.parametrize('change',['outside','reverse','nan','margin'])
def test_bad_domain_or_margin_rejected(change):
    reference,lo,hi=fixture();margin=1e-10
    if change=='outside':lo[0]=-2
    if change=='reverse':lo[0]=2
    if change=='nan':hi[0]=float('nan')
    if change=='margin':margin=-1
    with pytest.raises(ValueError):DirectionalAcceleration(reference,lo,hi,numerical_margin=margin)
