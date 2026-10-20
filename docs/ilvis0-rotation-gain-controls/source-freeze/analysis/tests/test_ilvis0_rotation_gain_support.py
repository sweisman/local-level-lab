# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
from types import SimpleNamespace
import numpy as np
import pytest
from lll import ilvis0_rotation_gain_support as supports
from test_ilvis0_shared_norms import components


def test_reciprocal_chords_are_exact_upper_bounds_including_point_domains():
    for left, right in ((F(-9,10), F(9,10)), (F(-1,1000), F(1,1000)), (F(1,8), F(1,8))):
        alpha, beta = supports.reciprocal_chord(left, right)
        for k in range(33):
            g = left + (right-left)*F(k,32)
            assert alpha + beta*g >= 1/(1+g)
        assert alpha+beta*left == 1/(1+left)
        assert alpha+beta*right == 1/(1+right)
    for lo, hi in ((-1, 0), (0, -1), (-2, -1)):
        with pytest.raises(ValueError): supports.reciprocal_chord(F(lo), F(hi))


def test_supports_keep_all_columns_and_explicit_source_bindings():
    a, m = components()
    cut = supports.build(a, m)
    assert cut.design.shape == (78,51) and cut.upper.shape == (78,)
    assert np.count_nonzero(cut.design[:,27:42]) == 0
    assert cut.reference_binding == m.reference.binding
    assert cut.transform_binding == m.binding
    assert cut.report()['physical_parameter_count'] == 27
    assert cut.report()['floating_point_enclosure_verified'] is False
    with pytest.raises(ValueError): cut.design[0,0] = 1
    with pytest.raises(ValueError): supports.build(a, SimpleNamespace(binding=m.binding))


def test_actual_matrix_maps_are_retained_and_zero_caps_remain_valid():
    for fixed in (False, True):
        a, m = components(fixed=fixed)
        cut = supports.build(a, m)
        r = m.reference
        rng = np.random.default_rng(20261020)
        for x in (r.center, r.lower, r.upper, *[r.lower+(r.upper-r.lower)*v for v in rng.random((12,27))]):
            point = np.r_[x, np.zeros(15), m.normalized_values_at(x)]
            assert max(supports.exact_slacks(cut, point)) <= 0
    assert all(F(v) >= 0 for v in cut.metadata['center_relaxations'])


def test_outward_matrix_stretch_is_excluded_despite_unit_error_norm():
    from lll.ilvis0_shared_norms import build, exact_slacks
    a, m = components()
    cut = supports.build(a, m)
    point = np.r_[m.reference.center, np.zeros(24)]
    column = m.center[:,0]
    point[[42,45,48]] = column/(2*np.linalg.norm(column))
    assert max(exact_slacks(build(a,m),point)) <= 0
    assert max(supports.exact_slacks(cut,point)) > 0


def test_source_mismatch_and_nonfinite_points_are_rejected():
    from lll.ilvis0_shared_reference_terms import ReferenceErrors
    from lll.ilvis0_common_force_transform import ForceTransform
    from test_ilvis0_shared_reference_terms import config
    a, m = components()
    r = m.reference
    other = ReferenceErrors(dict(config(),source_id='different'),r.lower,r.upper,r.center)
    with pytest.raises(ValueError): supports.build(a,ForceTransform(other))
    with pytest.raises(ValueError): supports.exact_slacks(supports.build(a,m),np.full(51,np.nan))
