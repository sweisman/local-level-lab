# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer calibration ambiguity of a gyro-free scalar force comparison.

One constant isotropic gain is used for the complete constructed leg, not a
fresh calibration at each epoch. This is a limitation control, not a fit to data.
"""
import numpy as np
import pytest

from ilvis0_channel_reference import reference,PROFILES,MODELS,BACKGROUND,GRAVITY,RADIUS
from lll import ilvis0_exploratory,ilvis0_receiver_force


@pytest.mark.parametrize('truth_model',MODELS)
@pytest.mark.parametrize('candidate',MODELS)
def test_one_permitted_constant_gain_absorbs_straight_leg_scalar_separation(truth_model,candidate,record_property):
    gain=None;maximum=0.;uncorrected=0.
    allowed=min(ilvis0_exploratory.LIMITS['accel_gain_'+axis] for axis in 'xyz')
    for t in range(21):
        truth=reference(truth_model,PROFILES['eastbound'],float(t))
        required=ilvis0_receiver_force.evaluate(truth['coordinates'],truth['rate'],truth['second'],
            model=candidate,background_rate_rads=BACKGROUND if candidate=='sphere_rotating' else 0.,
            gravity_mps2=GRAVITY,disc_radius_m=RADIUS)['specific_force_ned_mps2']
        target=float(np.linalg.norm(required))
        if gain is None:gain=float(np.linalg.norm(truth['body_forces'][0])/target-1.)
        for raw in truth['body_forces']:
            uncorrected=max(uncorrected,abs(float(np.linalg.norm(raw))-target))
            maximum=max(maximum,abs(float(np.linalg.norm(raw/(1.+gain)))-target))
    assert abs(gain)<=allowed
    assert maximum<1e-10
    if truth_model!=candidate:assert uncorrected>1e-6
    record_property('truth_model',truth_model)
    record_property('candidate',candidate)
    record_property('constant_gain_fraction',gain)
    record_property('allowed_gain_fraction',allowed)
    record_property('uncorrected_maximum_magnitude_difference_mps2',uncorrected)
    record_property('corrected_maximum_magnitude_difference_mps2',maximum)
