# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.ilvis0_rf04_velocity_resolution import grid_match, rounding_allowance, velocity_ne


def test_rf04_course_vectors_follow_north_east_and_wrap():
    np.testing.assert_allclose(velocity_ne([2, 3, 4], [360, 90, 180]),
                               [[2., 0.], [0., 3.], [-4., 0.]], atol=1e-14)


def test_rf04_rounding_allowance_covers_component_changes_at_a_southward_heading():
    speed = np.array([220.])
    course = np.array([183.])
    allowance = rounding_allowance(speed, course, speed_step=.000514444444, course_step=.1)
    actual = velocity_ne(speed-.000257, course+.05)-velocity_ne(speed, course)
    assert np.all(abs(actual) <= allowance)
    assert allowance[0, 1] > 10*allowance[0, 0]


def test_rf04_grid_check_distinguishes_report_steps_from_five_sample_average_steps():
    samples = [179.90, 179.92, 180.10]
    assert grid_match(samples, .1, 2.5e-5)['matched'] == 2
    assert grid_match(samples, .02, 2.5e-5)['matched'] == 3
