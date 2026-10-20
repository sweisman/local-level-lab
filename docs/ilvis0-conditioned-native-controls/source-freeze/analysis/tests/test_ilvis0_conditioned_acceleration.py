# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
from dataclasses import FrozenInstanceError
from fractions import Fraction as F
import pytest
from lll.ilvis0_acceleration_projection import project
from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
from test_ilvis0_acceleration_projection import fixture


def evidence():
    bundle=fixture();certificate=project(**bundle,reserve=lambda *_:None)
    return bundle,certificate


def test_verifier_is_immutable_source_bound_and_lp_free(monkeypatch):
    bundle,certificate=evidence();charges=[]
    from lll import ilvis0_affine_support
    monkeypatch.setattr(ilvis0_affine_support,'propose',lambda *_:pytest.fail('consumer must not propose'))
    condition=ConditionedAcceleration(bundle,certificate,reserve=lambda n:charges.append(n))
    assert charges==[6] and condition.supports_verified==6
    norm,components=condition.match(bundle['reference'],bundle['lower'][:27],bundle['upper'][:27])
    assert F(norm)**2>=sum((F(v)**2 for v in components),F(0))
    assert norm==certificate['norm_change']
    assert condition.report()['region_binding']=='combined'
    with pytest.raises(FrozenInstanceError):condition.norm_change=100.


@pytest.mark.parametrize('changed',['digest','reference','source','objective','shift','negative_dual',
    'support','endpoint','radius','component','sign','missing_axis'])
def test_corrupted_certificates_are_rejected(changed):
    bundle,certificate=evidence();certificate=deepcopy(certificate)
    if changed=='digest':certificate['input_binding']='other'
    elif changed=='reference':certificate['acceleration_binding']='other'
    elif changed=='source':certificate['source_id']='other'
    elif changed=='objective':certificate['axes'][0]['objective'][42]=1.
    elif changed=='shift':certificate['axes'][0]['shift']='1'
    elif changed=='negative_dual':certificate['axes'][0]['certificates'][0]['multipliers'][0]=-1.
    elif changed=='support':certificate['axes'][0]['certificates'][0]['exact_upper']='0'
    elif changed=='endpoint':certificate['axes'][0]['upper']=10.
    elif changed=='radius':certificate['norm_change']=0.
    elif changed=='component':certificate['axes'][0]['change']=0.
    elif changed=='sign':certificate['axes'][0]['certificates'][0]['sign']=-1
    else:certificate['axes'].pop()
    with pytest.raises(ValueError):ConditionedAcceleration(bundle,certificate,reserve=lambda *_:None)


def test_changed_reference_and_expanded_domain_cannot_consume_bound():
    bundle,certificate=evidence();condition=ConditionedAcceleration(bundle,certificate,reserve=lambda *_:None)
    other=deepcopy(bundle['reference']);other['acceleration']['center'][0]+=1.
    with pytest.raises(ValueError,match='reference'):condition.match(other,bundle['lower'][:27],bundle['upper'][:27])
    low=bundle['lower'][:27];low[0]-=.01
    with pytest.raises(ValueError,match='domain'):condition.match(bundle['reference'],low,bundle['upper'][:27])
    # Even a subset must be explicitly re-bound: this API forbids silent region reuse.
    low[0]=0.
    with pytest.raises(ValueError,match='domain'):condition.match(bundle['reference'],low,bundle['upper'][:27])


def test_reservation_failure_precedes_any_verification(monkeypatch):
    bundle,certificate=evidence()
    from lll import ilvis0_saved_prediction_audit
    monkeypatch.setattr(ilvis0_saved_prediction_audit,'support',lambda *_:pytest.fail('support before charge'))
    def reject(_):raise ValueError('exhausted')
    with pytest.raises(ValueError,match='exhausted'):ConditionedAcceleration(bundle,certificate,reserve=reject)
