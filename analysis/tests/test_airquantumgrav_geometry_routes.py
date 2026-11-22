"""Independent geometry checks for controlled synthetic route variants."""

import numpy as np
import pytest

from lll.airquantumgrav_truth import truth


@pytest.mark.parametrize('model', ['sphere_rotating', 'sphere_still', 'flat_still'])
def test_turning_route_has_course_swing_and_consistent_derivatives(model):
    times = np.linspace(0., 120., 241)
    result = truth(model, times, latitude_deg=55., pattern='fast',
                   removal=.35, route='turning', height_profile='level',
                   gravity_model='inverse_square_height')
    ground = result['velocity_local_mps']
    course = np.degrees(np.arctan2(ground[:, 1], ground[:, 0]))
    assert course[-1] - course[0] < -40.
    assert np.all(result['coordinates'][:, 2] == 2500.)
    np.testing.assert_allclose(np.gradient(result['position_world_m'], times, axis=0)[2:-2],
                               result['velocity_world_mps'][2:-2], atol=.05)
    np.testing.assert_allclose(np.gradient(result['velocity_world_mps'], times, axis=0)[2:-2],
                               result['acceleration_world_mps2'][2:-2], atol=.003)


def test_straight_route_has_no_northward_motion_and_default_is_unchanged():
    times = np.linspace(0., 120., 241)
    default = truth('sphere_rotating', times, latitude_deg=-55.,
                    pattern='fast', removal=.35)
    explicit = truth('sphere_rotating', times, latitude_deg=-55.,
                     pattern='fast', removal=.35, route='eastbound')
    for key in default:
        np.testing.assert_array_equal(default[key], explicit[key])
    straight = truth('sphere_rotating', times, latitude_deg=-55.,
                     pattern='fast', removal=.35, route='straight',
                     height_profile='level')
    np.testing.assert_allclose(straight['velocity_local_mps'][:, 0], 0., atol=1e-10)
    np.testing.assert_allclose(straight['coordinates'][:, 2], 2500., atol=0.)
