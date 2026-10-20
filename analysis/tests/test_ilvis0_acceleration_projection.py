# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
from fractions import Fraction as F
import json
from types import SimpleNamespace
import pytest
from lll import ilvis0_acceleration_projection as projection


def fixture():
    rows=[]
    for sign in (1.,-1.):
        row=[0.]*51;row[0]=row[1]=sign;rows.append(row)
    region=dict(parameter_count=51,center=[0.]*51,lower=[-1.]*51,upper=[1.]*51,
        inequality_design=rows,inequality_upper=[.1,.1],binding='combined',source_id='source',
        future_truth_used=False)
    jac=[]
    for scale in (1.,-2.,3.):
        row=[0.]*27;row[0]=row[1]=scale;jac.append(row)
    reference=dict(binding='combined',parent=dict(binding='parent',source_id='source'),
        acceleration=dict(version='ilvis0-common-reference-acceleration-component-v1',
            binding='acceleration',reference_binding='parent',center=[10.,-2.,3.],
            jacobian=jac,caps=[0.]*9,change=10.,remainder=0.))
    return dict(training=dict(region=region),reference=reference,
        lower=region['lower'],upper=region['upper'])


def test_joint_projection_is_narrow_despite_wide_coordinates():
    bundle=fixture();charges=[]
    result=projection.project(**bundle,reserve=lambda p,s:charges.append((p,s)))
    assert charges==[(1,3)]*6 and result['parameter_count']==51
    assert result['radius_ratio']<.038 and result['twofold_radius_reduction']
    for axis,scale in zip(result['axes'],(1,2,3)):
        assert F(axis['exact_upper'])-F(axis['exact_lower'])>=2*F(.1)*scale
        assert axis['change']<.1000001*scale
        assert len(axis['objective'])==51
    assert result['scientific_decision']=='abstain'


def test_shift_signed_rows_and_remainder_use_columns_39_to_41():
    bundle=fixture();region=bundle['training']['region']
    region['center'][0]=.25
    acc=bundle['reference']['acceleration'];acc['caps'][6:9]=[.125,.25,.5]
    acc['caps'][:6]=[100.]*6  # velocity/clock caps cannot replace acceleration caps
    result=projection.project(**bundle,reserve=lambda *_:None)
    for i,axis in enumerate(result['axes']):
        assert axis['objective'][39+i]==acc['caps'][6+i]
        assert sum(v!=0 for v in axis['objective'][27:])==1
        expected=F(acc['center'][i])-F(acc['jacobian'][i][0])*F(.25)
        assert F(axis['shift'])==expected
        assert axis['lower']<=float(expected)<=axis['upper']


@pytest.mark.parametrize('failure',['binding','parent','source','future','columns','caps','box'])
def test_source_mismatch_and_incomplete_domains_fail_before_charging(failure):
    bundle=fixture();region=bundle['training']['region'];ref=bundle['reference'];charges=[]
    if failure=='binding':ref['binding']='other'
    elif failure=='parent':ref['acceleration']['reference_binding']='other'
    elif failure=='source':ref['parent']['source_id']='other'
    elif failure=='future':region['future_truth_used']=True
    elif failure=='columns':region['parameter_count']=50
    elif failure=='caps':ref['acceleration']['caps'][6]=-1.
    else:bundle['lower']=[-2.]*51
    with pytest.raises(ValueError):projection.project(**bundle,reserve=lambda *v:charges.append(v))
    assert not charges


def test_counter_reserves_before_execution_and_rejects_overrun():
    saved=[];budget=projection.Allowance(2,6,lambda record:saved.append(deepcopy(record)))
    budget.reserve(1,3);budget.reserve(1,3)
    with pytest.raises(ValueError,match='allowance'):budget.reserve(1,3)
    assert budget.proposals==2 and budget.supports==6
    assert saved==[dict(lp_proposals=1,exact_supports=3),dict(lp_proposals=2,exact_supports=6)]


def test_independent_verifier_rejects_wrong_support(monkeypatch):
    from lll import ilvis0_affine_support
    original=ilvis0_affine_support.propose
    def changed(*args):
        result=original(*args);result['exact_upper']+=1;return result
    monkeypatch.setattr(ilvis0_affine_support,'propose',changed)
    with pytest.raises(ValueError,match='independent'):projection.project(**fixture(),reserve=lambda *_:None)


def test_worker_saves_training_only_bound_before_opening_anchor(tmp_path,monkeypatch):
    from lll import ilvis0_control_shards
    monkeypatch.setattr(ilvis0_control_shards,'_check_continue',lambda *_:None)
    path=tmp_path/'training.json';path.write_text(json.dumps(fixture()))
    anchor=tmp_path/'anchor.json';anchor.write_text(json.dumps(dict(point=[0.]*51)))
    saved={}
    def input_path(key=None):
        if key:
            assert key=='anchor' and 'projection.json' in saved
            return anchor
        return path
    context=SimpleNamespace(root=tmp_path,manifest={},input_path=input_path,
        save=lambda name,value:saved.update({name:value}))
    task=dict(identity='case',payload=dict(anchor_key='anchor',model=0,profile=False,
        maximum_proposals=6,maximum_exact_supports=18))
    result=projection.evaluate(task,context)
    assert result['passed'] and result['anchor_contained']
    assert result['lp_proposals_reserved']==6 and result['exact_supports_reserved']==18
    assert len(saved['projection.json']['axes'])==3
    assert saved['anchor-check.json']['feasible']
