# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
from copy import deepcopy
import pytest
from lll.ilvis0_width_components import components


def fixture():
    region=dict(coordinate_scale=[2.,1.,1.],arithmetic_allowance=.03125)
    future=dict(bound=dict(unshared_remainder=[.125]*3),envelope=dict(
        certificates=[dict(upper='1/4',negated_lower='1/8')]*3,
        lower=[-.5]*3,upper=[.4375,.1875,.1875]))
    return future,region


def test_decomposition_uses_saved_certificate_terms_without_support_evaluations():
    future,region=fixture();result=components(future,region,0)
    assert result['affine_width']=='3/8' and result['unshared_width']=='1/2'
    assert result['arithmetic_width']=='1/16' and result['rounding_padding']=='0'
    assert result['total_width']=='15/16'
    assert result['saved_remainder_floor']=='9/16'
    assert result['new_support_evaluations']==0


@pytest.mark.parametrize('change',['negative','inconsistent','scale'])
def test_negative_or_inconsistent_saved_metadata_is_not_reinterpreted(change):
    future,region=fixture()
    if change=='negative':future['bound']['unshared_remainder'][0]=-.1
    elif change=='scale':region['coordinate_scale'][0]=0.
    else:future['envelope']['upper'][0]=.4
    with pytest.raises(ValueError):components(future,region,0)
