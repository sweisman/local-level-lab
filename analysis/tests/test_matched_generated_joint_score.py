# SPDX-License-Identifier: AGPL-3.0-or-later
from lll.matched_generated_joint_score import rank_models


def test_joint_order_profiles_globe_before_interpreting_the_field():
    assert rank_models({'sphere_rotating': 6., 'sphere_still': 4., 'flat_still': 5.}) == {
        'shape': 'globe', 'preferred_model': 'sphere_still'}
    assert rank_models({'sphere_rotating': 6., 'sphere_still': 5., 'flat_still': 5.}) == {
        'shape': 'tie', 'preferred_model': None}
    assert rank_models({'sphere_rotating': 6., 'sphere_still': 5., 'flat_still': 4.}) == {
        'shape': 'disc', 'preferred_model': 'flat_still'}
