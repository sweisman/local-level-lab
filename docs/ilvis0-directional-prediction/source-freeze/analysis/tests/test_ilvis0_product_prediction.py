# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
from fractions import Fraction as F
import pytest
from lll import ilvis0_product_prediction as prediction
from lll import ilvis0_rotation_products as products
from lll.ilvis0_acceleration_projection import Allowance
from test_ilvis0_transform_audit import fixture as original_fixture
from test_ilvis0_rotation_products import fixture as matrix_fixture


def fixture():
    _,training,saved=deepcopy(original_fixture());spec=matrix_fixture()
    spec.update(reference_binding='parent',source_id='source')
    spec['transform']['reference_binding']='parent'
    cuts=products.build(**spec);region=prediction.extend(training,saved,cuts)
    saved['bound']['transform_coefficients']=[[0.]*9 for _ in range(3)]
    saved['bound']['transform_coefficients'][0][0]=.25
    saved['envelope']['certificates'][0]=dict(upper='1/4',negated_lower='1/4',
        upper_multipliers=[0.]*2,lower_multipliers=[0.]*2)
    saved['envelope']['lower'][0]=-.40625;saved['envelope']['upper'][0]=.40625
    return training,saved,cuts,region


def test_augmented_objectives_keep_all_original_coefficients_and_exact_endpoints():
    training,saved,cuts,region=fixture();charges=[]
    future=prediction.rebuild(region,saved,region['lower'],region['upper'],reserve=charges.append)
    assert charges==list(range(1,7)) and len(future['lower'])==78
    assert future['envelope']['upper'][0]<saved['envelope']['upper'][0]
    assert future['envelope']['lower'][0]>=saved['envelope']['lower'][0]
    check=prediction.audit(training,saved,region,future,cuts)
    assert check['exact_supports_checked']==6 and check['original_parameter_count']==51
    assert future['bound']==saved['bound'] and future['jacobian']==saved['jacobian']
    assert region['center'][:51]==training['region']['center']
    assert all(row[51:]==[0.]*27 for row in region['inequality_design'][:2])


@pytest.mark.parametrize('change',['source','row','columns','remainder','endpoint','scale','origin','arithmetic'])
def test_independent_audit_rejects_changed_source_or_lost_terms(change):
    training,saved,cuts,region=fixture()
    future=prediction.rebuild(region,saved,region['lower'],region['upper'],reserve=lambda *_:None)
    if change=='source':future['reference']['binding']='other'
    elif change=='row':region['inequality_design'][0][0]=1.
    elif change=='columns':future['jacobian'][0].pop()
    elif change=='remainder':future['bound']['unshared_remainder'][0]=0.
    elif change=='scale':region['coordinate_scale'][0]=2.
    elif change=='origin':region['origin'][0]=1.
    elif change=='arithmetic':region['arithmetic_allowance']=0.
    else:future['envelope']['upper'][0]=0.
    with pytest.raises(ValueError):prediction.audit(training,saved,region,future,cuts)


def test_all_support_operations_have_precharged_allowance(monkeypatch):
    from lll import ilvis0_affine_support as affine,ilvis0_saved_prediction_audit as exact
    training,saved,cuts,region=fixture();calls=[];charges=[];upper=affine.upper;support=exact.support
    def counted_upper(*args):calls.append('proposal');return upper(*args)
    def counted_support(*args):calls.append('verify');return support(*args)
    monkeypatch.setattr(affine,'upper',counted_upper);monkeypatch.setattr(exact,'support',counted_support)
    allowance=Allowance(6,24,lambda event:charges.append(event))
    future=prediction.rebuild(region,saved,region['lower'],region['upper'],reserve=lambda _:allowance.reserve(1,3))
    allowance.reserve(0,6);prediction.audit(training,saved,region,future,cuts)
    assert len(calls)==24 and calls.count('verify')==6
    assert charges[-1]==dict(lp_proposals=6,exact_supports=24)
    with pytest.raises(ValueError):allowance.reserve(0,1)


def test_complete_adapter_is_portable_and_performs_no_native_work(tmp_path,monkeypatch):
    from pathlib import Path
    from saved_prediction_fixtures import generated_context
    root=Path(__file__).resolve().parents[2]
    task,context,saved=generated_context(root/'docs/ilvis0-column-orientation-prediction',tmp_path,monkeypatch)
    task['payload']['maximum_exact_supports']=24
    from lll import ilvis0_transform_native
    monkeypatch.setattr(ilvis0_transform_native,'enclose',lambda *_a,**_k:pytest.fail('no native bound'))
    result=prediction.evaluate(task,context)
    assert result['passed'] and result['parameter_count']==78 and result['original_parameter_count']==51
    assert result['native_evaluations']==result['bound_evaluations']==0
    assert result['lp_proposals_reserved']==6 and result['exact_supports_reserved']==24
    assert 'independent-audit.json' in saved
