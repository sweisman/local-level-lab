"""A generated saved-point forecast must survive the no-fit propagation path."""
import gzip
import io
import json
import math
from pathlib import Path

import numpy as np


def test_generated_smoke_reproduces_sealed_baseline_without_refit(tmp_path):
    from lll.esa_fixed_rate_propagation import propagate
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_training_forecast import initialize_training
    from lll.studies.closed import ClosedStudy

    root = Path(__file__).resolve().parents[2]
    study = ClosedStudy(
        root, 'data/prediction-observed-development-continuation-v1-20261113-smoke-v3')
    try:
        assert study.completion['state'] == 'complete'
        binding = study.input('saved-input-binding')
        recipe = study.input('recipe')
        fit = study.input('saved-increment-fit')
        saved = study.input('saved-increment-forecast')
        training = json.loads(gzip.decompress(study.input('training', raw=True)))
        with np.load(io.BytesIO(study.input('interval', raw=True))) as raw:
            theta, dv, dt = (raw[key] for key in ('theta', 'dv', 'dt'))
        times = np.asarray(saved['times_s'], dtype=float)
        gps = np.asarray([[math.radians(row['latitude_deg']),
                           math.radians(row['longitude_deg']), row['height_m']]
                          for row in training], dtype=float)
        prefix = binding['training_prefix_packets']
        initial, gravity = initialize_training(
            times[:len(training)], gps, theta=theta[:prefix],
            dv=dv[:prefix], dt=dt[:prefix], model='sphere_rotating',
            maximum_interval_s=recipe['maximum_interval_s'],
            clock=recipe['clock'])
        kernel, metadata = load_tangent(
            tmp_path, gravity_anchor_height_m=training[0]['height_m'])
        assert metadata['gravity_anchor_height_m'] == training[0]['height_m']
        charges = []
        result = propagate(
            theta=theta, dv=dv, dt=dt, training_prefix=prefix,
            training_times=times[:len(training)], training_gps=gps,
            forecast_times=times, initial=initial, gravity=gravity,
            point=fit['normalized_parameters'],
            active_parameters=fit['active_parameters'],
            limits=recipe['limits'], model='sphere_rotating', profile=False,
            clock=recipe['clock'], maximum_interval_s=recipe['maximum_interval_s'],
            tangent_kernel=kernel, reserve=lambda **charge: charges.append(charge))
        assert charges == [dict(native_calls=1, packet_visits=len(dt)*len(times))]
        assert result['refits'] == 0
        assert result['scientific_decision'] == 'abstain'
        np.testing.assert_allclose(result['coordinates'], saved['coordinates'],
                                   rtol=0, atol=1e-12)
    finally:
        study.close()
