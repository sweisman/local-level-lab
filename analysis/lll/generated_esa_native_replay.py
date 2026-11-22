# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rebuild a sealed generated IMU case for fixed-parameter native forecasts."""


def rebuild(task, context, recipe, reference, *, preflight,
            reserve_construction):
    """Return the original IMU/path problem after exact input verification."""
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import construct
    from .generated_esa_weak_perturbation_study import route_spec
    from .ilvis0_training_forecast import training_problem
    from .structured_noisy_study import _kernels
    from .structured_noisy_training import case_recipe
    from .studies.artifacts import digest, encoded

    law = task['payload']['law']
    material = construct(route_spec(task['payload']),
                         case_recipe(recipe, law),
                         reserve=reserve_construction)
    times = np.asarray(material['times'], dtype=float)
    theta = np.asarray(material['theta'], dtype=float)
    dv = np.asarray(material['dv'], dtype=float)
    dt = np.asarray(material['dt'], dtype=float)
    cut = material['training_epochs']
    if (len(dt) != round(recipe['duration_s']*recipe['rate_hz'])
            or len(times) != recipe['queries']
            or cut != (6 if preflight else 600)
            or reference['law'] != law
            or len(reference['point']) != 26
            or len(reference['names']) != 26):
        raise ValueError('generated reconstruction or parameter axes changed')
    if not preflight:
        binding = reference['binding']
        hashes = {key: digest(np.asarray(value, dtype='<f8').tobytes())
                  for key, value in (('theta', theta), ('dv', dv),
                                     ('dt', dt), ('times', times))}
        if (hashes != binding['full_array_sha256']
                or digest(encoded(material['training_rows'])) !=
                   binding['training_receiver_sha256']
                or binding['native_packets'] != len(dt)
                or binding['training_epochs'] != cut):
            raise ValueError('regenerated IMU or receiver input differs')
        context.save('reconstructed-binding.json', dict(
            full_array_sha256=hashes,
            training_receiver_sha256=binding['training_receiver_sha256'],
            original_manifest_sha256=reference['original_manifest_sha256']))
    noise, factory = _kernels(context, environment())
    del noise
    anchor = material['training_rows'][0]['height_m']
    _, tangent, compilation = factory(anchor)
    context.save('compilation.json', compilation)
    gps = np.array([[np.deg2rad(row['latitude_deg']),
                     np.deg2rad(row['longitude_deg']), row['height_m']]
                    for row in material['training_rows']])
    prefix = int(np.searchsorted(np.cumsum(dt),
                 times[cut-1] + recipe['limits']['time_offset'],
                 side='left')) + 1
    problem = training_problem(
        times[:cut], gps, theta=theta[:prefix], dv=dv[:prefix],
        dt=dt[:prefix], covariance=np.eye(3*cut),
        model='sphere_rotating', limits=recipe['limits'], profile=False,
        clock='header_elapsed', maximum_interval_s=1.5/recipe['rate_hz'],
        kernel=None, tangent_kernel=tangent)
    if list(problem.bounds.active) != reference['names']:
        raise ValueError('saved calibration parameter order changed')
    return dict(problem=problem, theta=theta, dv=dv, dt=dt, times=times,
                training_epochs=cut)
