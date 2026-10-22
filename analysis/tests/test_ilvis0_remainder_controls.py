# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
from fractions import Fraction as F

import pytest


def test_recipe_keeps_broad_domain_and_fixed_probe_matrix():
    from lll.ilvis0_remainder_controls import recipe,validate_recipe,limits
    value=recipe();validate_recipe(value)
    assert value['packets']==800 and value['time_s']==2.5 and value['clock_limit_s']==1.
    assert value['lower']==[-1.]*27 and value['upper']==[1.]*27
    assert set(value['probes'])=={'physical','conditioned'}
    for family in value['probes'].values():
        assert len(family)==4 and all(len(p)==27 for p in family)
        assert family[0]==[0.]*27
    assert limits('conditioned')['lp_proposals']==6
    assert limits('conditioned')['exact_supports']==24
    assert limits('physical')['physical_proofs']==1


@pytest.mark.parametrize('key',('packets','time_s','lower','maximum_bound_seconds','probes'))
def test_recipe_cannot_silently_change_scope(key):
    from lll.ilvis0_remainder_controls import recipe,validate_recipe
    value=deepcopy(recipe());value[key]=None
    with pytest.raises(ValueError):validate_recipe(value)


def test_force_region_retains_all_columns_and_rejects_outside_probe():
    from test_ilvis0_remainder_interface import fixture
    from lll.ilvis0_remainder_controls import force_region,check_witness
    _,reference,_=fixture();bundle=force_region(reference,[-1.]*27,[1.]*27,.2)
    region=bundle['training']['region'];center=[0.]*51
    assert region['parameter_count']==51 and len(region['inequality_design'])==6
    assert all(len(row)==51 for row in region['inequality_design'])
    assert check_witness(region,center)['feasible']
    assert region['binding']==reference.binding
    point=center.copy();point[41]=1.
    assert region['inequality_design'][2][41]==reference.acceleration.caps[8]
    # Tighten only this helper's artificial test region to expose its row check.
    region=deepcopy(region);region['inequality_upper']=[0.]*6
    with pytest.raises(ValueError,match='outside'):
        check_witness(region,point)
