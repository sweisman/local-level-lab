# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generated controls for a selective-precision derivative experiment."""
import hashlib
from pathlib import Path


def test_hybrid_tangent_keeps_values_and_derivatives_across_six_generated_cases(tmp_path):
    """Catch lost or misrouted parameter slopes, including near-zero slopes."""
    from lll.ilvis0_hybrid_tangent import load
    from lll import ilvis0_wide_tangent as wide
    from lll.ilvis0_mixed_benchmark import calculate, recipe

    r = dict(recipe(), duration_s=2., queries=9, query_start_s=.1, query_step_s=.2)
    source = hashlib.sha256(Path('analysis/lll/ilvis0_tangent.cpp').read_bytes()).hexdigest()
    loader = hashlib.sha256(Path(wide.__file__).read_bytes()).hexdigest()

    def kernels(anchor):
        reference, reference_meta = wide.load(tmp_path, gravity_anchor_height_m=anchor)
        candidate, candidate_meta = load(
            tmp_path, gravity_anchor_height_m=anchor,
            expected_source_sha256=source, expected_loader_sha256=loader,
        )
        return {'reference': reference, 'candidate': candidate}, {
            'reference': reference_meta, 'candidate': candidate_meta,
        }

    for model in ('sphere_rotating', 'sphere_still', 'flat_still'):
        for profile in (False, True):
            result = calculate(
                dict(model=model, latitude_deg=55., profile=profile, start=0), r,
                kernel_factory=kernels, reserve=lambda **_: None,
                reserve_construction=lambda **_: None,
                save=lambda *_: None, save_bytes=lambda *_: None,
                check_continue=lambda: None,
            )
            assert result['checks']['values_bitwise_identical']
            assert result['checks']['differences_bitwise_identical']
            assert result['checks']['boundary_counts_identical']
            assert result['checks']['jacobian_within_tolerance']
            assert result['active_columns'] == 26 + int(profile)
