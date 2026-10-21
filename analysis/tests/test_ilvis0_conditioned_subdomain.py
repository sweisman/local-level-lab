# SPDX-License-Identifier: AGPL-3.0-or-later
"""A smaller domain inherits a proved bound only with all parent constraints."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
import importlib.util
import numpy as np
import pytest


def test_subdomain_proof_exists():
    assert importlib.util.find_spec('lll.ilvis0_conditioned_subdomain') is not None


@pytest.fixture(scope='module')
def setup():
    from test_ilvis0_conditioned_transform_native import case
    config,theta,dv,dt,center,lo,hi,reference,parent=case(0,False)
    lower=lo.tolist()+[0.]*24;upper=hi.tolist()+[0.]*24;row=[0.]*51;row[12]=row[13]=1.
    region=dict(parameter_count=51,center=center.tolist()+[0.]*24,lower=lower,upper=upper,
        inequality_design=[row,[-v for v in row]],inequality_upper=[.205,-.195],
        binding=reference.binding,source_id=reference.parent.source_id,future_truth_used=False)
    bundle=dict(training=dict(region=region),reference=reference.report(),lower=lower,upper=upper)
    child=deepcopy(region);child.update(parameter_count=78,center=region['center']+[0.]*27,
        lower=lower+[0.]*27,upper=upper+[0.]*27,
        inequality_design=[r+[0.]*27 for r in region['inequality_design']])
    child['lower'][12]=.025;child['upper'][12]=.175
    extra=[0.]*78;extra[13]=1.
    child['inequality_design'].append(extra);child['inequality_upper'].append(.175)
    return parent,bundle,dict(region=child,reference=reference.report()),reference


def test_subdomain_retains_parent_bounds_and_binds_immutable_inputs(setup):
    from lll.ilvis0_conditioned_subdomain import SubdomainAcceleration
    parent,bundle,training,reference=setup;child=deepcopy(training);region=child['region']
    proof=SubdomainAcceleration(parent,bundle,child,region['lower'][:27],region['upper'][:27])
    assert proof.norm_change==parent.norm_change and proof.component_changes==parent.component_changes
    assert proof.original_remainder==parent.original_remainder
    assert proof.binding!=parent.binding
    assert proof.match(reference.report(),region['lower'][:27],region['upper'][:27])==(
        parent.norm_change,parent.component_changes)
    proof.match_training(child)
    assert proof.report()['parent_exact_supports_verified']==6
    assert proof.report()['additional_exact_supports']==0
    assert proof.report()['inherited_constraint_count']==2
    with pytest.raises(FrozenInstanceError):proof.norm_change=0.
    child['region']['inequality_upper'][0]+=.01
    with pytest.raises(ValueError):proof.match_training(child)
    assert proof.norm_change==parent.norm_change


@pytest.mark.parametrize('change',['expanded_box','missing_row','loosened_row','permuted_column',
    'changed_source','changed_center','changed_frame','missing_column','parent_input','wrong_domain','future_used'])
def test_changed_or_unproved_subdomains_are_rejected(setup,change):
    from lll.ilvis0_conditioned_subdomain import SubdomainAcceleration
    parent,original,training,reference=setup;bundle=deepcopy(original);child=deepcopy(training);r=child['region']
    lo=r['lower'][:27];hi=r['upper'][:27]
    if change=='expanded_box':r['lower'][12]=lo[12]=-.01
    if change=='missing_row':r['inequality_design'].pop(0);r['inequality_upper'].pop(0)
    if change=='loosened_row':r['inequality_upper'][0]+=.001
    if change=='permuted_column':r['inequality_design'][0][11]=r['inequality_design'][0][12];r['inequality_design'][0][12]=0.
    if change=='changed_source':r['source_id']='other'
    if change=='changed_center':r['center'][0]+=.01
    if change=='changed_frame':r['coordinate_scale']=[1.,1.,1.]
    if change=='missing_column':r['lower'].pop()
    if change=='parent_input':bundle['upper'][12]+=.001
    if change=='wrong_domain':lo[12]+=.001
    if change=='future_used':r['future_truth_used']=True
    with pytest.raises(ValueError):SubdomainAcceleration(parent,bundle,child,lo,hi)
