# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rebuild a sealed generated turning training problem for numerical controls."""

import json
import math
from pathlib import Path


def project_root(study_directory, study_id):
    directory = Path(study_directory).resolve()
    if (directory.name != study_id or directory.parent.name != 'data'
            or not study_id.startswith('generated-turning-')):
        raise ValueError('declared study directory required')
    return directory.parents[1]


def reconstruct(context, *, study_id, identity, reserve_construction,
                reserve_native, save):
    """Return the exact noisy parent problem and its saved feasible fit point.

    Native work, generated draws, and archive reads remain caller-charged.
    No later receiver observation or model-dependent outcome is consulted.
    """
    import numpy as np
    from .airquantumgrav_error_policy import build
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_noisy_inputs import construct, error_law
    from .geometry_calibration_study import ID as parent_id, recipe as parent_recipe, tasks as parent_tasks
    from .ilvis0_native_error_training import ErrorTrainingFactory
    from .structured_noisy_study import _kernels
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy
    from .turning_fixed_point_study import parent_binding

    if identity not in ('turning-level', 'turning-climb'):
        raise ValueError('declared generated turning parent required')
    project = project_root(context.root, study_id)
    if json.loads(context.input_path('parent_binding').read_bytes()) != parent_binding(project):
        raise ValueError('sealed parent completion or fit hashes changed')
    parent = ClosedStudy(project, 'data/'+parent_id)
    try:
        fit = parent.artifact(identity, 'fit.json')
        binding = parent.artifact(identity, 'input-binding.json')
        training = parent.artifact(identity, 'training-observations.json')
        operator = parent.artifact(identity, 'training-error-operator.json')
    finally:
        parent.close()
    declared = {task['identity']:task['payload'] for task in parent_tasks()}
    payload = declared[identity]
    if fit['converged'] is not False or fit['model'] != payload['model']:
        raise ValueError('unchanged nonconverged parent fit required')
    recipe = parent_recipe()
    case = dict(recipe, route=payload['route'], height_profile=payload['height_profile'])
    configured = dict(case, noise=case['noise_by_law']['increment'])
    spec = {key:value for key,value in payload.items()
            if key not in ('route', 'height_profile', 'law')}
    material = construct(spec, configured, reserve=reserve_construction,
                         height_profile=payload['height_profile'])
    cut = material['training_epochs']
    prefix = binding['training_prefix_packets']
    rows = material['training_rows']
    times = material['times'][:cut]
    gps = np.asarray([[math.radians(row['latitude_deg']),
                       math.radians(row['longitude_deg']), row['height_m']]
                      for row in rows], float)
    if (material['binding'] != binding['noise'] or len(rows) != cut
            or cut != binding['training_epochs']
            or prefix != training['native_prefix_packets']
            or training['coordinates'] != gps.tolist()
            or training['times_s'] != times.tolist()
            or binding['training_receiver_sha256'] != digest(encoded(rows))
            or any(binding['training_prefix_sha256'][key] != digest(
                np.asarray(material[key][:prefix], dtype='<f8').tobytes())
                for key in ('theta', 'dv', 'dt'))):
        raise ValueError('generated training input differs from sealed parent')
    weight = build(rows, policy_id=payload['policy_id'])
    anchor = rows[0]['height_m']
    if (weight.configuration != training['weight_configuration']
            or not np.array_equal(weight.times, times)
            or anchor != binding['gravity_anchor_height_m']):
        raise ValueError('training weight or gravity anchor changed')
    noise_kernel, native_factory = _kernels(context, environment())
    kernel, tangent, compilation = native_factory(anchor)
    save('compilation.json', compilation)
    factory = ErrorTrainingFactory(noise=error_law(configured['noise']),
        noise_kernel=noise_kernel, gravity_anchor_height_m=anchor,
        maximum_packets=len(material['dt']), maximum_queries=len(material['times']),
        maximum_bytes=64*1024**2, anchor_policy=recipe['covariance_anchor_policy'])
    problem = factory(times, gps, theta=material['theta'][:prefix],
        dv=material['dv'][:prefix], dt=material['dt'][:prefix],
        model=payload['model'], limits=recipe['limits'], profile=payload['profile'],
        clock='header_elapsed', maximum_interval_s=1.5/recipe['rate_hz'],
        kernel=kernel, tangent_kernel=tangent, training_weight=weight,
        time_origin_s=0., reserve=reserve_native)
    if (problem.error_descriptor != operator
            or list(problem.bounds.active) != fit['active_parameters']):
        raise ValueError('native training operator or nuisance columns changed')
    save('replay-binding.json', dict(parent_fit_sha256=digest(encoded(fit)),
        regenerated_noise_sha256=digest(encoded(material['binding'])),
        training_prefix_packets=prefix, training_epochs=cut,
        training_error_configuration=problem.error_descriptor['configuration'],
        original_reads=0, protected_reads=0, later_receiver_reads=0))
    return problem, fit, prefix, cut
