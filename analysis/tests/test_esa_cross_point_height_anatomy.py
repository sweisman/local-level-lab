"""Height-error anatomy uses saved forecasts without new fitting."""

from pathlib import Path


def test_height_anatomy_counts_contiguous_misses():
    from lll.esa_cross_point_height_anatomy import describe

    result = describe([0, 3, 4, -5, 0, 3], [1] * 6)
    assert result['first_nominal_95_miss_index'] == 1
    assert result['longest_nominal_95_miss_run'] == 3
    assert result['nominal_95_inside'] == 2
    assert result['last_signed_error_m'] == 3


def test_sealed_height_anatomy_keeps_failed_coverage():
    from lll.esa_cross_point_height_anatomy import build

    root = Path(__file__).resolve().parents[2]
    result = build(root)
    assert result['verified'] is True
    assert result['new_fits'] == 0
    assert result['reserved_groups_opened'] == 0
    assert result['height']['weighted_point']['nominal_95_inside'] == 25
    assert result['height']['receiver_only_point']['nominal_95_inside'] == 23
    assert result['height']['weighted_point']['empirical_95_scale_factor'] > 1
    assert result['scientific_decision'] == 'abstain'
