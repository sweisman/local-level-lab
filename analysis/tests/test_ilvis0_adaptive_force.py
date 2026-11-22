"""Known-answer receiver-only controls with fixed and uncertain windows."""

import math

import numpy as np
import pytest

from lll import ilvis0_adaptive_force
from lll.ilvis0_error_model import Spec, covariance
from lll.ilvis0_receiver_support import SupportPolicy, motion_from_gga_fixes, select_support


TIMES = np.arange(13.)
PHI, LON_RATE, HEIGHT = -.6, 4e-5, 4000.
GRAVITY, DISC_RADIUS, RATE = 9.8, 6371000., 7.292115e-5
POLICY = SupportPolicy((2., 4.), 1.5, 5, 100., 300., 5., 5., .5)


def fixes(acceleration):
    return tuple(dict(utc_week_s=t, latitude_deg=math.degrees(PHI),
                      longitude_deg=math.degrees(LON_RATE*t),
                      orthometric_height_m=HEIGHT + acceleration*(t-6.)**2,
                      geoid_separation_m=0., fix_quality=1) for t in TIMES)


def declared_inputs():
    white = np.diag([1e-16, 1e-16, .01])
    return dict(spec=Spec(white=white, components=((3., .5*white),),
                          offset=.3*white, drift_origin_s=0., drift_span_s=12.),
                targets_s=(6.,), policy=POLICY, degree=2,
                derivative_envelopes=np.array([[1., .001, 5000.], [0., LON_RATE, 1.],
                                               [0., 0., .07], [0., 0., 0.]]),
                background_rate_rads=RATE, gravity_bounds_mps2=(GRAVITY, GRAVITY),
                disc_radius_m=DISC_RADIUS)


def exact_magnitudes(height_acceleration):
    """Constant-latitude eastbound force from cylindrical motion geometry."""
    sin_phi, cos_phi = math.sin(PHI), math.cos(PHI)
    prime = 6378137. / math.sqrt(1. - 0.0066943799901413165*sin_phi**2)
    sphere = (prime+HEIGHT)*cos_phi*LON_RATE
    disc = DISC_RADIUS*(math.pi/2-PHI)*LON_RATE
    return {
        'sphere_rotating': math.hypot(sin_phi * (LON_RATE+2*RATE)*sphere,
                                      cos_phi * (LON_RATE+2*RATE)*sphere
                                      - GRAVITY - height_acceleration),
        'sphere_still': math.hypot(sin_phi*LON_RATE*sphere,
                                   cos_phi*LON_RATE*sphere-GRAVITY-height_acceleration),
        'flat_still': math.hypot(LON_RATE*disc, GRAVITY+height_acceleration),
        'flat_geographic_field': math.hypot((LON_RATE+2*RATE*sin_phi)*disc,
                                            2*RATE*cos_phi*disc-GRAVITY-height_acceleration),
    }


def test_stable_selection_recovers_four_independent_exact_force_magnitudes():
    result = ilvis0_adaptive_force.assess(
        fixes(0.), coordinate_error_bounds=np.zeros((13, 3)), **declared_inputs())
    assert result['targets'][0]['possible_choices_s'] == [4.]
    assert result['branches'] == [(0, 4.)]
    assert result['joint_covariance_mps4'].shape == (4, 4)
    for model, exact in exact_magnitudes(0.).items():
        measured = result['required_force_magnitude_mps2'][model][0]
        low, high = result['magnitude_ranges_mps2'][model][0]
        np.testing.assert_allclose(measured, exact, atol=1e-10, rtol=0.)
        assert low-1e-10 <= exact <= high+1e-10


def test_correlated_height_error_can_change_to_a_nominally_rejected_window():
    noisy, true = fixes(.032), fixes(.029)
    inputs = declared_inputs()
    result = ilvis0_adaptive_force.assess(
        noisy, coordinate_error_bounds=np.tile([0., 0., .109], (13, 1)),
        return_receiver_weights=True, **inputs)
    motion = motion_from_gga_fixes(true, maximum_gap_s=POLICY.maximum_gap_s)
    true_choice = select_support(TIMES, motion['speed_mps'], motion['course_deg'],
                                 motion['vertical_rate_mps'], target_s=6., policy=POLICY)
    assert true_choice['selected_half_window_s'] == 4.
    assert result['targets'][0]['nominal_choice_s'] == 2.
    assert result['targets'][0]['possible_choices_s'] == [2., 4., None]
    assert result['branches'] == [(0, 2.), (0, 4.)]
    for model, exact in exact_magnitudes(.058).items():
        assert all(low <= exact <= high for low, high in result['magnitude_ranges_mps2'][model])
    dense = covariance(TIMES, inputs['spec'])
    weights = result['magnitude_receiver_weights']
    np.testing.assert_allclose(result['joint_covariance_mps4'], weights@dense@weights.T,
                               rtol=1e-10, atol=1e-12)
    assert abs(result['joint_covariance_mps4'][0, 1]) > 1e-6
    assert result['scientific_decision'] == 'abstain'


def test_incomplete_windows_remain_abstentions_despite_coordinate_error():
    inputs = declared_inputs()
    inputs['targets_s'] = (0., 6.)
    result = ilvis0_adaptive_force.assess(
        fixes(0.), coordinate_error_bounds=np.zeros((13, 3)), **inputs)
    assert result['targets'][0]['possible_choices_s'] == [None]
    assert result['targets'][1]['possible_choices_s'] == [4.]
    assert result['branches'] == [(1, 4.)]
    inputs['targets_s'] = (0.,)
    result = ilvis0_adaptive_force.assess(
        fixes(0.), coordinate_error_bounds=np.zeros((13, 3)), **inputs)
    assert result['branches'] == []
    assert result['joint_covariance_mps4'] is None
    assert result['magnitude_ranges_mps2'] is None


def test_screening_coordinate_error_contains_joint_nonlocal_rate_changes():
    initial = np.column_stack((PHI+2e-6*TIMES, np.pi+LON_RATE*(TIMES-6.), HEIGHT+.05*TIMES))
    modes = np.column_stack((3e-7*np.sin(TIMES/2.), 4e-7*np.cos(TIMES/3.),
                            .1*np.sin(TIMES/4.)))

    def screen(coordinates):
        return motion_from_gga_fixes([
            dict(utc_week_s=t, latitude_deg=math.degrees(phi),
                 longitude_deg=(math.degrees(lon)+180.)%360.-180.,
                 orthometric_height_m=h, geoid_separation_m=0., fix_quality=1)
            for t, (phi, lon, h) in zip(TIMES, coordinates, strict=True)], maximum_gap_s=1.5)

    original = screen(initial)
    radii = np.tile([3e-7, 4e-7, .1], (len(TIMES), 1))
    bound = ilvis0_adaptive_force.screening_errors(TIMES, initial, radii,
                                                  np.asarray(original['speed_mps']))
    for scale in (-1., -.4, 0., .3, 1.):
        observed = screen(initial+scale*modes)
        for key, allowance in [('speed_mps', 'speed_error_mps'),
                               ('course_deg', 'course_error_deg'),
                               ('vertical_rate_mps', 'vertical_error_mps')]:
            change = np.asarray(observed[key])-original[key]
            if key == 'course_deg':
                change = (change+180.)%360.-180.
            assert max(abs(change)) <= bound[allowance]
    radii[6, 0] = np.pi/2
    with pytest.raises(ValueError, match='chart boundary'):
        ilvis0_adaptive_force.screening_errors(TIMES, initial, radii,
                                               np.asarray(original['speed_mps']))


def test_generated_gps_and_rotated_body_history_share_one_sensor_calibration():
    from lll.ilvis0_adaptive_calibration import compare

    inputs = declared_inputs()
    inputs['targets_s'] = (5., 6., 7.)
    assessment = ilvis0_adaptive_force.assess(
        fixes(0.), coordinate_error_bounds=np.zeros((13, 3)), **inputs)
    magnitude = exact_magnitudes(0.)['sphere_rotating']
    body = magnitude*np.array([[0., 1., 0.], [0., 0., -1.], [1., 0., 0.]])
    gain = np.array([.012, -.008, .004])
    bias = np.array([.07, -.03, .02])
    point = np.r_[gain, bias]
    bounds = np.column_stack((point-.00001, point+.00001))
    result = compare(assessment, measured_specific_force=body*(1.+gain)+bias,
                     measurement_error_mps2=np.full((3, 3), .00001),
                     calibration_bounds=bounds, maximum_boxes=8)
    assert result['required_target_indices'] == [0, 1, 2]
    assert result['candidates']['sphere_rotating']['status'] == 'scalar_compatible'
    for model in ('sphere_still', 'flat_still', 'flat_geographic_field'):
        assert result['candidates'][model]['status'] == 'scalar_excluded'
        assert result['candidates'][model]['boxes_excluded'] == 1
    assert result['scientific_decision'] == 'abstain'


def test_gps_error_that_allows_abstention_cannot_drive_calibration_exclusion():
    from lll.ilvis0_adaptive_calibration import compare

    assessment = ilvis0_adaptive_force.assess(
        fixes(.032), coordinate_error_bounds=np.tile([0., 0., .109], (13, 1)),
        **declared_inputs())
    result = compare(assessment, measured_specific_force=[[0., 0., -12.]],
                     measurement_error_mps2=np.zeros((1, 3)),
                     calibration_bounds=np.zeros((6, 2)), maximum_boxes=8)
    assert result['required_target_indices'] == []
    assert {row['status'] for row in result['candidates'].values()} == {'no_required_targets'}
    assert sum(row['boxes_evaluated'] for row in result['candidates'].values()) == 0


@pytest.mark.parametrize('model,latitude,route', [
    ('sphere_rotating', -62., 'turning'), ('sphere_still', 47., 'straight'),
    ('flat_still', 43., 'turning'), ('flat_geographic_field', -49., 'straight'),
])
@pytest.mark.parametrize('height_error_m', [0., .08])
def test_moving_known_truth_survives_shared_calibration_with_bounded_receiver_error(
        model, latitude, route, height_error_m):
    from lll.ilvis0_adaptive_calibration import compare
    from lll.ilvis0_matched_truth import matched_truth

    times = np.arange(1., 15.)
    targets = (5., 7., 9., 10.)
    arguments = dict(latitude_deg=latitude, route=route, removal=.35)
    nav = matched_truth(model, times, **arguments)['coordinates']
    measured_height = nav[:, 2] + height_error_m*np.sin(times/2.5)
    reports = [dict(utc_week_s=t, latitude_deg=math.degrees(phi),
                    longitude_deg=math.degrees(lon), orthometric_height_m=h,
                    geoid_separation_m=0., fix_quality=1)
               for t, (phi, lon, _), h in zip(times, nav, measured_height, strict=True)]
    body = matched_truth(model, targets, **arguments)['specific_force_mps2']
    gain = np.array([.012, -.008, .004])
    bias = np.array([.07, -.03, .02])
    center = np.r_[gain, bias]
    spec = declared_inputs()['spec']
    policy = SupportPolicy((2., 4.), 1.5, 5, 25., 130., 5., 5., .5)
    predicted = ilvis0_adaptive_force.assess(
        reports, spec=spec, targets_s=targets, policy=policy, degree=2,
        derivative_envelopes=[[1.3, 1., 2600.], [1e-5, 4e-5, 0.],
                              [2e-7, 1e-7, 0.], [5e-9, 5e-9, 0.]],
        coordinate_error_bounds=np.tile([0., 0., height_error_m], (len(times), 1)),
        background_rate_rads=RATE, gravity_bounds_mps2=(9.81, 9.81),
        disc_radius_m=DISC_RADIUS)
    result = compare(predicted, measured_specific_force=body*(1.+gain)+bias,
                     measurement_error_mps2=np.zeros(body.shape),
                     calibration_bounds=np.column_stack((center-.00001, center+.00001)),
                     maximum_boxes=8)
    assert result['required_target_indices'] == list(range(len(targets)))
    assert result['candidates'][model]['status'] == 'scalar_compatible'
    for target, index in enumerate(result['required_target_indices']):
        matching = result['candidates'][model]['matching_windows_s'][target]
        assert matching and all((index, width) in predicted['branches'] for width in matching)
