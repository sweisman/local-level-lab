"""The original extended-precision path reproduces its sealed generated forecast."""
from pathlib import Path


def test_wide_kernel_reproduces_sealed_generated_baseline(tmp_path):
    from lll.esa_fixed_rate_protocol import material, run_one
    from lll.ilvis0_wide_tangent import load
    from lll.studies.closed import ClosedStudy

    root = Path(__file__).resolve().parents[2]
    study = ClosedStudy(
        root, 'data/prediction-observed-development-continuation-v1-20261113-smoke-v3')
    try:
        binding = study.input('saved-input-binding')
        rows = material(
            study.input('interval', raw=True), study.input('training', raw=True),
            binding=binding, fit=study.input('saved-increment-fit'),
            saved=study.input('saved-increment-forecast'),
            recipe=study.input('recipe'), smoke=True)
        anchor = rows['training_gps'][0, 2]
        kernel, metadata = load(tmp_path, gravity_anchor_height_m=anchor)
        assert metadata['internal_mantissa_bits'] >= 64
        charges = []
        result = run_one(rows, 'linear_points', tangent_kernel=kernel,
                         reserve=lambda **charge: charges.append(charge))
        assert result['baseline_reproduced'] is True
        assert charges == [dict(native_calls=1, packet_visits=400*9)]
        assert result['refits'] == 0
    finally:
        study.close()
