# SPDX-License-Identifier: AGPL-3.0-or-later
"""One frozen full-length, noise-free check of the generated IMU oracle."""

import math
from pathlib import Path


def test_full_length_noiseless_known_correction_forecast(tmp_path):
    import numpy as np
    from lll.airquantumgrav_geographic_controls import construct, position_errors
    from lll.airquantumgrav_noisy_study import recipe
    from lll.airquantumgrav_observation_truth import observe, receiver_samples, start
    from lll.airquantumgrav_truth import truth
    from lll.ilvis0_exploratory import load_kernel
    from lll.noisy_realization_attribution import oracle_value_forecast
    from lll.studies.artifacts import atomic, encoded

    parent = recipe()
    model = 'sphere_rotating'
    arguments = dict(model=model, latitude_deg=55., pattern=parent['pattern'],
                     removal=0., height_profile=parent['height_profile'],
                     gravity_model=parent['gravity_model'])
    rate_times = np.arange(360001, dtype=float) / parent['rate_hz']
    queries = (parent['query_start_s']
               + np.arange(parent['queries']) * parent['query_step_s'])
    raw = observe(truth(times=rate_times, **arguments), sign=1)
    raw['times'] = rate_times
    increments = construct(raw, method='linear_points',
                           rate_hz=parent['rate_hz'],
                           reserve=lambda **work: None)
    known = start(truth(times=np.array([0.]), **arguments),
                  model=model, sign=1)
    kernel, compilation = load_kernel(tmp_path, gravity_anchor_height_m=1500.)
    charges = []
    prediction = oracle_value_forecast(
        dict(**increments, times=queries), known, model=model, profile=False,
        limits=parent['limits'], kernel=kernel,
        reserve=lambda **work: charges.append(work))
    answer = receiver_samples(times=queries, sign=1, **arguments)
    errors = np.asarray(position_errors(prediction, answer, model=model))
    later = errors[800:]
    horizontal_rms = math.sqrt(float(np.mean(np.sum(later[:, :2]**2, axis=1))))
    height_rms = math.sqrt(float(np.mean(later[:, 2]**2)))
    report = dict(model=model, profile=False, noise=False,
                  intervals=len(increments['dt']), queries=len(queries),
                  native_charges=charges,
                  horizontal_rms_m=horizontal_rms, height_rms_m=height_rms,
                  first_horizontal_m=float(np.linalg.norm(errors[0, :2])),
                  boundary_horizontal_m=float(np.linalg.norm(errors[799, :2])),
                  last_horizontal_m=float(np.linalg.norm(errors[-1, :2])),
                  compilation=compilation)
    path = Path(__file__).resolve().parents[2] / (
        'docs/noisy-realization-attribution/long-noiseless-control/result.json')
    atomic(path, encoded(report))
    assert charges == [dict(native_calls=1, packet_visits=360000 * 1200)]
    assert horizontal_rms <= 10.
    assert height_rms <= 30.
