# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
from types import SimpleNamespace
import numpy as np
import pytest
from lll import ilvis0_shared_norms as norms
from lll.ilvis0_shared_reference_terms import ReferenceErrors
from lll.ilvis0_reference_acceleration import AccelerationTerms
from lll.ilvis0_common_force_transform import ForceTransform
from test_ilvis0_shared_reference_terms import config


def components(fixed=False):
    center=np.full(27,.1);lo=center if fixed else -np.ones(27);hi=center if fixed else np.ones(27)
    r=ReferenceErrors(config(),lo,hi,center)
    return AccelerationTerms(r,[.001,-.002,-.04905],.005,9.81),ForceTransform(r)


def test_known_norm_blocks_keep_all_columns_and_skip_velocity_clock():
    a,m=components();cut=norms.build(a,m)
    assert cut.design.shape==(182,51) and cut.upper.shape==(182,)
    assert np.count_nonzero(cut.design[:,:30])==0
    assert [b['indices'] for b in cut.blocks][-3:]==[[42,45,48],[43,46,49],[44,47,50]]
    with pytest.raises(ValueError):cut.design[0,0]=1


def test_outward_integer_direction_support_contains_unit_ball_and_excludes_cube():
    a,m=components();cut=norms.build(a,m,block_names=['force-column-x'])
    for vector in ([1.,0.,0.],[-1.,0.,0.],[.6,.8,0.],[0.,-.6,.8]):
        x=np.zeros(51);x[[42,45,48]]=vector
        assert max(norms.exact_slacks(cut,x))<=0
    x=np.zeros(51);x[[42,45,48]]=1.
    assert max(norms.exact_slacks(cut,x))>0
    for row,b in zip(cut.design,cut.upper):
        assert F(float(b))**2>=sum((F(float(v))**2 for v in row),F(0))


def test_zero_caps_use_the_existing_zero_error_convention():
    a,m=components(fixed=True);cut=norms.build(a,m)
    assert np.count_nonzero(cut.upper)==0
    assert max(norms.exact_slacks(cut,np.r_[m.reference.center,np.zeros(24)]))==0
    x=np.zeros(51);x[42]=.1
    assert max(norms.exact_slacks(cut,x))>0


def test_equal_caps_alone_are_not_accepted_as_norm_provenance():
    fake=SimpleNamespace(caps=np.ones(9),binding='fake')
    a,m=components()
    with pytest.raises(ValueError):norms.build(fake,m)
    with pytest.raises(ValueError):norms.build(a,fake)
    with pytest.raises(ValueError):norms.build(a,m,block_names=['velocity-clock'])
    with pytest.raises(ValueError):norms.build(a,m,block_names=[])


def test_another_source_reference_is_rejected():
    a,m=components();r=m.reference
    other=ReferenceErrors(dict(config(),source_id='other'),r.lower,r.upper,r.center)
    with pytest.raises(ValueError):norms.build(a,ForceTransform(other))
