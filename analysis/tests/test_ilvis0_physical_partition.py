# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
from fractions import Fraction as F
import itertools
import math
import pytest
from lll import ilvis0_physical_partition as partition


def test_closed_children_cover_every_parent_coordinate_without_dropping_parameters():
    lower=[-1.]*27;upper=[1.]*27;lower[0]=.1;upper[0]=.3
    result=partition.split(lower,upper,axes=(0,1));audit=partition.audit(result,lower,upper,axes=(0,1))
    assert audit['passed'] and audit['children']==4 and audit['physical_parameter_count']==27
    assert all(len(child['lower'])==len(child['upper'])==27 for child in result['children'])
    for x,y in itertools.product((lower[0],result['midpoints']['0'],upper[0]),(-1.,0.,1.)):
        point=[0.]*27;point[0]=x;point[1]=y
        assert any(all(F(a)<=F(v)<=F(b) for a,v,b in zip(c['lower'],point,c['upper'])) for c in result['children'])
    # A shared boundary belongs to both closed children, not a missing sliver.
    mid=[0.]*27;mid[0]=result['midpoints']['0']
    assert sum(all(a<=v<=b for a,v,b in zip(c['lower'],mid,c['upper'])) for c in result['children'])==4


def test_fixed_and_adjacent_binary_coordinates_do_not_create_fake_refinement():
    lo=[0.]*27;hi=[0.]*27;lo[1]=-1.;hi[1]=1.
    result=partition.split(lo,hi,axes=(0,1));assert len(result['children'])==2
    assert partition.audit(result,lo,hi,axes=(0,1))['passed']
    hi[1]=lo[1]=0.;lo[0]=.5;hi[0]=math.nextafter(.5,1.)
    result=partition.split(lo,hi,axes=(0,1));assert len(result['children'])==1
    assert result['children'][0]['lower']==lo and result['children'][0]['upper']==hi


@pytest.mark.parametrize('change',['missing','duplicate','gap','other-coordinate'])
def test_independent_cover_audit_rejects_missing_or_changed_cells(change):
    lo=[-1.]*27;hi=[1.]*27;result=partition.split(lo,hi,axes=(0,1))
    if change=='missing':result['children'].pop()
    elif change=='duplicate':result['children'][1]=deepcopy(result['children'][0])
    elif change=='gap':result['children'][0]['upper'][0]=-.1
    else:result['children'][0]['lower'][26]=0.
    with pytest.raises(ValueError):partition.audit(result,lo,hi,axes=(0,1))


@pytest.mark.parametrize('axes',[(0,0),(27,),(0,1,2),(-1,)])
def test_unregistered_or_duplicate_partition_axes_are_rejected(axes):
    with pytest.raises(ValueError):partition.split([-1.]*27,[1.]*27,axes=axes)


def test_exact_nonbinary_endpoints_cannot_be_silently_rounded_into_a_different_domain():
    lo=[-1.]*27;hi=[1.]*27;lo[0]=F(1,3)
    with pytest.raises(ValueError):partition.split(lo,hi,axes=(0,1))
