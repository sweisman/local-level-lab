"""Structured receiver errors through common GPS-selected force windows."""

import math

import numpy as np
import pytest

from lll.ilvis0_receiver_support import SupportPolicy


def _inputs(count):
    radius = 6378137. + 1000.
    fixes = [dict(utc_week_s=float(i), latitude_deg=0.,
                  longitude_deg=math.degrees(200.*i/radius),
                  orthometric_height_m=970., geoid_separation_m=30.,
                  fix_quality=1)
             for i in range(count)]
    policy = SupportPolicy(
        half_windows_s=(5., 10.), maximum_gap_s=1.5,
        minimum_samples=5, minimum_speed_mps=100.,
        maximum_speed_mps=300., maximum_course_span_deg=5.,
        maximum_speed_span_mps=5.,
        maximum_vertical_rate_span_mps=.5)
    return fixes, policy


def _spec():
    from lll.ilvis0_error_model import Spec
    white = np.diag([1e-16, 1e-16, .09])
    return Spec(white=white,
                components=((4., .1*white),),
                offset=.05*white,
                drift_origin_s=0., drift_span_s=200.)


@pytest.mark.parametrize('transformed', [False, True])
def test_structured_selected_force_matches_dense_bridge(transformed):
    from lll.ilvis0_error_model import covariance
    from lll.ilvis0_joint_receiver_force import (
        assess_candidates, assess_candidates_structured)
    fixes, policy = _inputs(21)
    times = np.asarray([row['utc_week_s'] for row in fixes])
    spec = _spec()
    transforms = (np.stack([np.diag([1.+i/1000., .9-i/2000., 1.])
                            for i in range(len(fixes))])
                  if transformed else None)
    kwargs = dict(targets_s=[10., 12.], policy=policy, degree=2,
                  background_rate_rads=7.292115e-5,
                  gravity_mps2=9.8, disc_radius_m=6371000.)
    dense = assess_candidates(fixes, covariance(times, spec, transforms), **kwargs)
    structured = assess_candidates_structured(fixes, spec,
                                              transforms=transforms, **kwargs)
    assert structured['selected_indices'] == dense['selected_indices']
    assert structured['supported_target_indices'] == [0, 1]
    for model in structured['model_order']:
        np.testing.assert_allclose(
            structured['required_force_magnitude_mps2'][model],
            dense['required_force_magnitude_mps2'][model], atol=1e-12)
    np.testing.assert_allclose(structured['joint_covariance_mps4'],
                               dense['joint_covariance_mps4'],
                               rtol=2e-10, atol=2e-12)
    assert structured['scientific_decision'] == 'abstain'


def test_structured_selected_force_exceeds_dense_full_record_cap():
    from lll.ilvis0_joint_receiver_force import assess_candidates_structured
    fixes, policy = _inputs(200)
    result = assess_candidates_structured(
        fixes, _spec(), targets_s=[100.], policy=policy, degree=2,
        background_rate_rads=7.292115e-5,
        gravity_mps2=9.8, disc_radius_m=6371000.)
    assert result['supported_target_indices'] == [0]
    assert result['joint_covariance_mps4'].shape == (3, 3)


def test_structured_selected_force_abstains_without_support():
    from lll.ilvis0_joint_receiver_force import assess_candidates_structured
    fixes, policy = _inputs(21)
    kwargs = dict(targets_s=[0.], degree=2,
                  background_rate_rads=7.292115e-5,
                  gravity_mps2=9.8, disc_radius_m=6371000.)
    result = assess_candidates_structured(fixes, _spec(), policy=policy,
                                          **kwargs)
    assert result['supported_target_indices'] == []
    assert result['joint_covariance_mps4'] is None
    assert result['scientific_decision'] == 'abstain'
    with pytest.raises(ValueError, match='policy'):
        assess_candidates_structured(fixes, _spec(), policy=None, **kwargs)


def test_matched_field_keeps_receiver_selected_support_and_required_vectors():
    from lll.ilvis0_joint_receiver_force import assess_candidates_structured
    fixes, policy = _inputs(21)
    kwargs = dict(targets_s=[0., 10., 12.], policy=policy, degree=2,
                  background_rate_rads=7.292115e-5, gravity_mps2=9.8,
                  disc_radius_m=6371000.)
    legacy = assess_candidates_structured(fixes, _spec(), **kwargs)
    result = assess_candidates_structured(fixes, _spec(), include_matched_disc=True, **kwargs)
    assert result['selected_indices'] == legacy['selected_indices']
    assert result['supported_target_indices'] == [1, 2]
    assert result['joint_covariance_mps4'].shape == (8, 8)
    np.testing.assert_allclose(result['joint_covariance_mps4'][:6, :6],
                               legacy['joint_covariance_mps4'])
    for candidate in result['model_order']:
        vector = result['required_force_ned_mps2'][candidate]
        np.testing.assert_allclose(np.linalg.norm(vector, axis=1),
                                   result['required_force_magnitude_mps2'][candidate])
