# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import pytest
from lll.ilvis0_feasible_witness import Region


def test_strict_anchor_repairs_to_exact_halfspace_boundary():
    region=Region([-1,-1],[1,1],[[1,1]],[F(1,4)])
    witness=region.repair([1,1],[0,0])
    assert witness['mixing_fraction']==F(7,8)
    assert witness['point']==(F(1,8),F(1,8))
    assert max(region.slacks(witness['point']))==0
    assert region.objective([1,1],witness['point'])==F(1,4)


def test_box_violations_and_boundary_anchors_are_preserved():
    region=Region([-1,-1],[1,1],[],[])
    witness=region.repair([2,-3],[0,0])
    assert witness['mixing_fraction']==F(2,3)
    assert witness['point']==(F(2,3),F(-1))
    boundary=Region([-1],[1],[[1]],[0])
    witness=boundary.repair([1],[0])
    assert witness['mixing_fraction']==1 and witness['point']==(F(0),)


def test_point_box_and_already_feasible_point_need_no_hidden_adjustments():
    point=Region([F(1,8)]*51,[F(1,8)]*51,[],[])
    witness=point.repair([1]*51,[F(1,8)]*51)
    assert witness['mixing_fraction']==1 and len(witness['point'])==51
    assert point.objective([-1]*51,witness['point'])==F(-51,8)
    assert point.repair(witness['point'],witness['point'])['mixing_fraction']==0


def test_invalid_anchor_is_rejected_instead_of_repaired():
    with pytest.raises(ValueError,match='anchor'):
        Region([-1],[1],[[0]],[-1]).repair([0],[0])
    with pytest.raises(ValueError,match='anchor'):
        Region([-1],[1],[],[]).repair([0],[2])


@pytest.mark.parametrize('args',[
    ([],[],[],[]),([1],[0],[],[]),([-1],[1],[[1,2]],[0]),
    ([-1],[1],[[1]],[]),([float('nan')],[1],[],[]),
    ([-1],[float('inf')],[],[]),
])
def test_malformed_or_nonfinite_regions_are_rejected(args):
    with pytest.raises(ValueError):Region(*args)


def test_binary_input_values_and_rational_repairs_remain_exact():
    region=Region([-1],[1],[[1]],[.1])
    witness=region.repair([1],[0])
    assert witness['point']==(F(.1),)
    assert witness['point'][0]!=F(1,10)
    with pytest.raises(ValueError):region.repair([float('nan')],[0])
    with pytest.raises(ValueError):region.objective([1,2],[0])
