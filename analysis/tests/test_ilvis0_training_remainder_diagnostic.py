# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
from lll.ilvis0_training_remainder_diagnostic import compare


def fixture():
    return dict(old_lower=[-2.,-3.,-4.],old_upper=[2.,3.,4.],scale=[2.,3.,1.],
        old_center=[1.,2.,3.],new_center=[1.,2.,3.],old_design=[[1.,0.],[0.,1.],[1.,1.]],
        new_design=[[1.,0.],[0.,1.],[1.,1.]],remainder=[.5,.25,1.],noise=.001,arithmetic=.00001)


def test_compare_keeps_all_axes_and_reports_wider_allowance():
    args=fixture();args['remainder'][2]=5.
    result=compare(**args)
    assert result['passed']
    assert result['new_half_width_m']==[1.00101,.75101,5.00101]
    assert result['width_ratio'][2]>1


@pytest.mark.parametrize('change',['center','coefficient','negative','missing'])
def test_disagreement_is_not_silently_promoted(change):
    args=fixture()
    if change=='center':args['new_center'][0]+=.001
    if change=='coefficient':args['new_design'][0][0]+=.001
    if change=='negative':args['remainder'][0]=-.1
    if change=='missing':args['new_design']=args['new_design'][:2]
    if change in ('negative','missing'):
        with pytest.raises(ValueError):compare(**args)
    else:assert not compare(**args)['passed']
