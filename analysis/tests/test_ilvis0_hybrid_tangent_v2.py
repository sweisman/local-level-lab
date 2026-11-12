"""The revised prototype routes the observed weak attitude columns wide."""

import hashlib
from pathlib import Path

import pytest


def test_revised_precision_map_adds_attitude_x_y_without_changing_old_module():
    from lll import ilvis0_hybrid_tangent as original
    from lll import ilvis0_hybrid_tangent_v2 as revised
    from lll import ilvis0_wide_tangent as wide

    assert revised.WIDE_COLUMNS == tuple(sorted((*original.WIDE_COLUMNS, 0, 1)))
    assert original.WIDE_COLUMNS == (2, 3, 4, 9, 11, 14, 16, 18, 19, 20)
    assert len(revised.FAST_COLUMNS) == 15
    native = Path('analysis/lll/ilvis0_tangent.cpp').read_bytes()
    source = wide.derive(native, expected_sha256=hashlib.sha256(native).hexdigest())
    transformed = revised.derive(source, expected_sha256=hashlib.sha256(source).hexdigest())
    assert b'std::array<double,15>' in transformed
    assert b'std::array<long double,12>' in transformed
    assert b'static constexpr int FAST_MAP[27]={-1,-1' in transformed
    assert b'static constexpr int WIDE_MAP[27]={0,1' in transformed
    with pytest.raises(ValueError, match='hash'):
        revised.derive(source, expected_sha256='0' * 64)


def test_revised_tangent_matches_wide_on_six_generated_physical_cases(tmp_path):
    from lll import ilvis0_hybrid_tangent_v2 as revised
    from lll import ilvis0_wide_tangent as wide
    from lll.ilvis0_mixed_benchmark import calculate, recipe

    r = dict(recipe(), duration_s=2., queries=9,
             query_start_s=.1, query_step_s=.2)
    source = hashlib.sha256(Path('analysis/lll/ilvis0_tangent.cpp').read_bytes()).hexdigest()
    loader = hashlib.sha256(Path(wide.__file__).read_bytes()).hexdigest()

    def kernels(anchor):
        reference, reference_meta = wide.load(
            tmp_path, gravity_anchor_height_m=anchor)
        candidate, candidate_meta = revised.load(
            tmp_path, gravity_anchor_height_m=anchor,
            expected_source_sha256=source, expected_loader_sha256=loader)
        return {'reference': reference, 'candidate': candidate}, {
            'reference': reference_meta, 'candidate': candidate_meta}

    for model in ('sphere_rotating', 'sphere_still', 'flat_still'):
        for profile in (False, True):
            result = calculate(
                dict(model=model, latitude_deg=55., profile=profile, start=0),
                r, kernel_factory=kernels, reserve=lambda **_: None,
                reserve_construction=lambda **_: None,
                save=lambda *_: None, save_bytes=lambda *_: None,
                check_continue=lambda: None)
            assert result['checks']['values_bitwise_identical']
            assert result['checks']['differences_bitwise_identical']
            assert result['checks']['boundary_counts_identical']
            assert result['checks']['jacobian_within_tolerance']
