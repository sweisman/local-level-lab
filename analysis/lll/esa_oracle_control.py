# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-calibration prediction control for generated ESA-like IMU streams."""

import math


def load_case(root, law):
    """Read one sealed noisy input stream, without fitting or future receiver data."""
    import hashlib
    import io
    from pathlib import Path
    import numpy as np
    from .airquantumgrav_truth import truth
    from .airquantumgrav_observation_truth import start
    from .esa_fit_adjusted_control_study import LAWS, SCOPE
    from .esa_fit_adjusted_control_report import _study, _artifact
    from .studies.artifacts import digest, encoded

    if law not in LAWS:
        raise ValueError('declared generated law required')
    root = Path(root).resolve()
    study, lineage = _study(root)
    try:
        sources = ('analysis/lll/airquantumgrav_truth.py',
                   'analysis/lll/airquantumgrav_observation_truth.py',
                   'analysis/lll/ilvis0_tangent.cpp',
                   'analysis/lll/ilvis0_wide_tangent.py',
                   'analysis/lll/ilvis0_forecast.py')
        if study.manifest['scope'] != SCOPE or any(
                study.manifest['sources'].get(name) !=
                hashlib.sha256((root/name).read_bytes()).hexdigest()
                for name in sources):
            raise ValueError('sealed oracle source differs')
        task = study.tasks[law]['payload']
        if (task.get('truth_law') != law or task.get('model') != 'sphere_rotating'
                or task.get('latitude_deg') != 55. or task.get('start') != 0
                or task.get('profile') is not False):
            raise ValueError('sealed generated task differs')
        raw = _artifact(study, law, 'measured-inputs.npz', raw=True)
        with np.load(io.BytesIO(raw), allow_pickle=False) as measured:
            if set(measured.files) != {'theta', 'dv', 'dt', 'times'}:
                raise ValueError('complete measured IMU input required')
            arrays = {name:np.array(measured[name], dtype=float, copy=True)
                      for name in measured.files}
        binding = _artifact(study, law, 'input-binding.json')
        rows = _artifact(study, law, 'training-receiver.json')
        if (len(rows) != 600 or binding.get('training_epochs') != 600 or
                binding.get('truth_law') != law or
                binding.get('training_receiver_sha256') != digest(encoded(rows))
                or arrays['theta'].shape != (270000, 3) or
                arrays['dv'].shape != (270000, 3) or
                arrays['dt'].shape != (270000,) or
                arrays['times'].shape != (900,) or
                not np.array_equal(arrays['times'], .5+np.arange(900.)) or
                any(digest(np.asarray(arrays[name], dtype='<f8').tobytes()) !=
                    binding['measured_raw_array_sha256'][name]
                    for name in ('theta', 'dv', 'dt'))):
            raise ValueError('sealed measured input or receiver binding differs')
        earlier = np.array([[math.radians(row['latitude_deg']),
                             math.radians(row['longitude_deg']),row['height_m']]
                            for row in rows[:2]], dtype=float)
        known = start(truth('sphere_rotating', np.array([0.]),
            latitude_deg=55., pattern='fast', removal=0.,
            height_profile='climb', gravity_model='inverse_square_height'),
            model='sphere_rotating', sign=1)
        return dict(**arrays, earlier_coordinates=earlier,
                    known_state=known, limits=study.input('recipe')['limits'],
                    training_epochs=600,
                    parent_manifest_sha256=study.completion['manifest_sha256'],
                    parent_input_sha256=digest(raw),
                    lineage_sha256=lineage)
    finally:
        study.close()


def oracle_problem(theta, dv, dt, times, earlier_coordinates, known_state,
                   limits, tangent_kernel, *, rate_hz):
    """Build a forecast-only tangent problem; no calibration is estimated."""
    import numpy as np
    from .ilvis0_estimator import Bounds
    from .ilvis0_shape import TangentProblem

    theta, dv, dt, times = (np.asarray(value, dtype=float)
                            for value in (theta, dv, dt, times))
    gps = np.asarray(earlier_coordinates, dtype=float)
    if (rate_hz not in (200, 300) or dt.ndim != 1 or
            theta.shape != (len(dt), 3) or dv.shape != theta.shape or
            times.ndim != 1 or len(times) < 3 or
            gps.shape != (2, 3) or
            not all(np.all(np.isfinite(value))
                    for value in (theta, dv, dt, times, gps)) or
            np.any(dt <= 0) or np.any(dt > 1.5/rate_hz) or
            np.any(np.diff(times) <= 0) or
            not isinstance(known_state, dict) or
            known_state.get('corrections_supplied_not_fitted') is not True):
        raise ValueError('complete generated forecast and known state required')
    bounds = Bounds(limits)
    parameters = known_state['parameters']
    if any(name not in parameters or not math.isfinite(parameters[name])
           for name in bounds.active):
        raise ValueError('complete finite known correction vector required')
    point = np.array([parameters[name]/limits[name]
                      for name in bounds.active], dtype=float)
    count = int(np.searchsorted(np.cumsum(dt),
        times[1]+limits['time_offset'], side='left'))+1
    if not 1 <= count <= len(dt):
        raise ValueError('forecast prefix lacks timing support')
    problem = TangentProblem(theta[:count], dv[:count], dt[:count],
        times[:2], gps, np.eye(6), known_state['initial'], bounds,
        tangent_kernel=tangent_kernel, kernel=None, fit_earth_removal=False,
        clock_hypothesis='header_elapsed',
        processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=1.5/rate_hz,
        gravity_mps2=known_state['gravity_mps2'],
        disc_radius_m=6371000.)
    problem.bounds.decode(point)
    return problem, point
