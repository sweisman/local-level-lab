"""A forecast range must be useful as well as cover known truth."""

import pytest

from lll.forecast_envelope_contrast import diagnose


def bounds(lower, upper, target='receiver_measurement'):
    return dict(lower=lower, upper=upper, prediction_target=target,
                coordinate_chart='local_unwrapped_geodetic',
                nominal_joint_coverage_lower_bound=.95,
                assumptions_qualified_for_aircraft=False,
                later_observations_used=False)


def test_correct_narrow_envelope_is_unique_on_known_answer():
    result = diagnose({'sphere_rotating': bounds([-1., -1., -1.], [1., 1., 1.]),
                       'flat_still': bounds([2., -1., -1.], [4., 1., 1.])},
                      [[0., 0., 0.]], target='receiver_measurement')
    assert result['covered'] == {'sphere_rotating': True, 'flat_still': False}
    assert result['descriptive_unique_candidate'] == 'sphere_rotating'
    assert result['scientific_decision'] == 'abstain'


def test_wide_competing_envelope_forces_abstention():
    result = diagnose({'sphere_rotating': bounds([-1., -1., -1.], [1., 1., 1.]),
                       'flat_still': bounds([-100., -100., -100.],
                                            [100., 100., 100.])},
                      [[0., 0., 0.]], target='receiver_measurement')
    assert result['descriptive_unique_candidate'] is None
    assert result['scientific_decision'] == 'abstain'


def test_three_candidate_case_needs_one_containing_forecast():
    result = diagnose({
        'sphere_rotating': bounds([-1., -1., -1.], [1., 1., 1.],
                                  target='physical_position'),
        'sphere_still': bounds([2., -1., -1.], [4., 1., 1.],
                               target='physical_position'),
        'flat_still': bounds([5., -1., -1.], [7., 1., 1.],
                             target='physical_position')},
        [[0., 0., 0.]], target='physical_position')
    assert result['descriptive_unique_candidate'] == 'sphere_rotating'
    assert result['candidate_count'] == 3


@pytest.mark.parametrize('bad', ['wrong_target', 'marginal_only', 'not_future'])
def test_rejects_incompatible_or_unproven_forecast_range(bad):
    left = bounds([-1., -1., -1.], [1., 1., 1.])
    if bad == 'wrong_target':
        left['prediction_target'] = 'physical_position'
    elif bad == 'marginal_only':
        del left['nominal_joint_coverage_lower_bound']
    else:
        left['later_observations_used'] = True
    with pytest.raises(ValueError):
        diagnose({'sphere_rotating': left,
                  'flat_still': bounds([2., 2., 2.], [4., 4., 4.])},
                 [[0., 0., 0.]], target='receiver_measurement')
