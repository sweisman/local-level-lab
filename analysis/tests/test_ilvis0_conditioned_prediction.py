# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
import pytest
from lll import ilvis0_conditioned_prediction as candidate
from lll.ilvis0_acceleration_projection import Allowance
from lll.ilvis0_transform_audit import audit_case
from test_ilvis0_transform_audit import fixture


def evidence():
    result,training,future=deepcopy(fixture())
    future['bound']['center']=[0.]*3
    changed=deepcopy(future['bound'])
    changed.update(unshared_remainder=[.0625,.25,.125],
        position_unshared_remainder=[.03125,.21875,.09375],
        lever_unshared_remainder=[.03125]*3,
        conditioning=dict(applies_only_to_training_region=True,reference_binding='combined',region_binding='combined'))
    return result,training,future,changed


def test_componentwise_min_keeps_every_valid_allowance_and_exact_future_supports():
    result,training,future,changed=evidence();charges=[]
    updated=candidate.refine(training,future,changed,reserve=lambda i:charges.append(i))
    assert charges==list(range(1,7))
    assert updated['bound']['unshared_remainder']==[.0625,.125,.125]
    assert updated['bound']['position_unshared_remainder']==[.03125,.09375,.09375]
    assert updated['bound']['lever_unshared_remainder']==[.03125]*3
    assert updated['envelope']['upper']==[.09375,.15625,.15625]
    result.update(future_lower_m=updated['envelope']['lower'],future_upper_m=updated['envelope']['upper'])
    assert audit_case(result,training,updated)['exact_supports_checked']==6


@pytest.mark.parametrize('field',['center','previous_coefficients','acceleration_coefficients','transform_coefficients','reference_binding'])
def test_changed_native_expansion_is_rejected_before_support_work(field):
    _,training,future,changed=evidence();charges=[]
    if field=='reference_binding':changed[field]='other'
    elif field=='center':changed[field][0]=1.
    else:changed[field][0][0]=1.
    with pytest.raises(ValueError):candidate.refine(training,future,changed,reserve=lambda i:charges.append(i))
    assert not charges


def test_all_48_exact_supports_per_complete_case_are_reserved_and_executed(monkeypatch):
    from test_ilvis0_acceleration_projection import fixture as acceleration_fixture
    from lll.ilvis0_acceleration_projection import project
    from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
    from lll import ilvis0_affine_support as affine,ilvis0_saved_prediction_audit as independent,ilvis0_transform_audit as audit
    counts=dict(proposer=0,independent=0);saved=[]
    original_upper=affine.upper;original_support=independent.support
    def upper(*args):counts['proposer']+=1;return original_upper(*args)
    def support(*args):counts['independent']+=1;return original_support(*args)
    monkeypatch.setattr(affine,'upper',upper);monkeypatch.setattr(independent,'support',support);monkeypatch.setattr(audit,'support',support)
    allowance=Allowance(12,48,lambda record:saved.append(record))
    bundle=acceleration_fixture();certificate=project(**bundle,reserve=allowance.reserve)
    ConditionedAcceleration(bundle,certificate,reserve=lambda n:allowance.reserve(0,n))
    result,training,future,changed=evidence()
    updated=candidate.refine(training,future,changed,reserve=lambda _:allowance.reserve(1,3))
    result.update(future_lower_m=updated['envelope']['lower'],future_upper_m=updated['envelope']['upper'])
    allowance.reserve(0,6);audit.audit_case(result,training,updated)
    assert allowance.proposals==12 and allowance.supports==48
    assert counts==dict(proposer=30,independent=18)
    assert saved[-1]==dict(lp_proposals=12,exact_supports=48)
    with pytest.raises(ValueError,match='allowance'):allowance.reserve(0,1)
