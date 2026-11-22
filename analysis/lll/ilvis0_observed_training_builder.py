# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rebuild a sealed recorded training problem without a later-position input."""

import gzip
import json


def build(context, spec):
    import numpy as np
    from .ilvis0_exploratory import MODELS, load_kernel
    from .ilvis0_shape import instrument_limits, load_tangent
    from .ilvis0_prediction import training_inputs
    from .ilvis0_training_forecast import training_problem
    from .ilvis0_gps_sensitivity import assumptions, coordinate_covariance

    policy = json.loads(context.input_path('recipe').read_bytes())
    if (policy['model'] != 'sphere_rotating' or
            policy['maximum_evaluations'] != 200 or
            policy['stopping'] != 'near_zero' or
            policy['maximum_interval_s'] != .0075 or
            spec['model'] != policy['model'] or
            spec['clock'] != 'header_elapsed' or
            spec['origin'] not in ('inner', 'outer')):
        raise ValueError('unchanged recorded training recipe required')
    common = json.loads(gzip.decompress(context.input_path().read_bytes()))
    prefix = json.loads(context.input_path(
        spec['segment_id']+'-'+spec['origin']+'-training').read_bytes())
    times = np.asarray(common['times'], float)
    values = np.asarray(common['values'], float)
    gps = np.asarray(prefix['training_gps'], float)
    layout = common['layout']
    count, outer = layout['receiver_epochs'], layout['training_epochs']
    cut = count//3 if spec['origin'] == 'inner' else outer
    horizon = min(outer-count//3, count-outer)
    if (common['segment_id'] != spec['segment_id'] or
            prefix['segment_id'] != spec['segment_id'] or
            count != len(times) or outer != 2*count//3 or
            layout['native_packets'] != len(values) or
            prefix['cut_epoch'] != cut or
            prefix['horizon_epochs'] != horizon or
            gps.shape != (cut, 3) or values.shape != (len(values), 15)):
        raise ValueError('unchanged sealed receiver cut and packets required')
    limits = instrument_limits(policy['gyro_offset_dph'])
    placeholder = np.zeros((count, 3))
    placeholder[:cut] = gps
    t, train_gps, v = training_inputs(times, placeholder, values,
                                     limits['time_offset'], cut=cut)
    assumption = next(item for item in assumptions()
                      if item.name == policy['training_weight'])
    blocks = np.tile(np.diag(np.square(policy['independent_neu_m'])),
                     (len(t), 1, 1))
    covariance = coordinate_covariance(t, train_gps[:, 0], train_gps[:, 2],
                                       blocks, assumption)
    directory = context.root/'shards'/f'{context.shard:03d}'/'kernels'
    kernel, kernel_meta = load_kernel(directory)
    tangent, tangent_meta = load_tangent(directory)
    for name, meta in (('ilvis0_native.c', kernel_meta),
                       ('ilvis0_tangent.cpp', tangent_meta)):
        if context.manifest['sources']['analysis/lll/'+name] != meta['source_sha256']:
            raise ValueError('compiled native source differs from freeze')
    context.save('compilation.json', dict(value=kernel_meta, tangent=tangent_meta))
    model = MODELS[0]
    if model != policy['model']:
        raise ValueError('original conditional model required')
    problem = training_problem(t, train_gps, theta=v[:, 9:12],
        dv=v[:, 12:15], dt=v[:, 2], covariance=covariance, model=model,
        limits=limits, profile=False, clock='header_elapsed',
        maximum_interval_s=policy['maximum_interval_s'], kernel=kernel,
        tangent_kernel=tangent)
    if len(problem.bounds.active) != 26:
        raise ValueError('all 26 calibration directions required')
    return problem, model, layout['native_packets'], cut
