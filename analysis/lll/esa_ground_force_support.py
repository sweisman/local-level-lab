# SPDX-License-Identifier: AGPL-3.0-or-later
"""Assess force-magnitude calibration leverage from two sealed ESA ground stops."""

import argparse
from contextlib import closing
import hashlib
import itertools
import json
import os
from pathlib import Path


BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_GROUND_FORCE_SUPPORT_PLAN.md'
FREEZE = BASE+'esa-ground-force-support-freeze.json'
RESULT = BASE+'esa-ground-force-support-result.json'
MAX_ROWS = 1365154
RATE = 300
AXES = ('x', 'y', 'z')


def force_gradient(force, bias, gain, bias_scale, gain_scale):
    """Derivative in normalized calibration coordinates, bias then gain."""
    import numpy as np

    denom = 1.+gain
    corrected = (force-bias)/denom
    unit = corrected/np.linalg.norm(corrected)
    return np.r_[-unit*bias_scale/denom, -unit*corrected*gain_scale/denom]


def anchor_comparison(design, roots, anchor, *, rank_rtol):
    import numpy as np
    from .esa_fitted_scale_support import REFERENCE_SD, support

    _, singular, vh = np.linalg.svd(anchor, full_matrices=True)
    rank = int(np.count_nonzero(singular > rank_rtol*singular[0]))
    remaining = vh[rank:].T
    return dict(ground_rank=rank, ground_singular_values=singular.tolist(),
        free=support(design, roots, rank_rtol=rank_rtol, reference_sd=REFERENCE_SD),
        anchored=support(design@remaining, roots, rank_rtol=rank_rtol, reference_sd=REFERENCE_SD))


def stop_summary(stream, header, raw):
    import numpy as np
    from .airquantumgrav import records
    from .esa_component_preflight import WIDTH

    count = raw['samples']
    first_line, last_line = raw['first_line_number'], raw['last_line_number']
    if (type(count) is not int or not 0 < count <= MAX_ROWS or first_line < 2
            or last_line-first_line+1 != count):
        raise ValueError('sealed ground record boundaries required')
    stream.seek(WIDTH*(first_line-1))

    def lines():
        for _ in range(count):
            row = stream.read(WIDTH)
            if len(row) != WIDTH or not row.endswith(b'\n') or b'\n' in row[:-1]:
                raise ValueError('unexpected ground source record boundary')
            yield row

    parsed = records(itertools.chain((header,), lines()))
    samples = np.fromiter(((r['gps_time_s'], *r['acceleration_mps2'], r['temperature_c']) for r in parsed),
                          dtype=np.dtype((np.float64, 5)), count=count)
    time_range = samples[[0,-1], 0].tolist()
    if (time_range != [raw['first_sample_time_s'], raw['last_sample_time_s']]
            or np.any(np.diff(samples[:, 0]) > 1.5/RATE)):
        raise ValueError('saved ground times or timing continuity differ')
    bins = np.floor((samples[:, 0]-samples[0, 0])/60).astype(int)
    bin_count = np.bincount(bins)
    complete = np.flatnonzero(bin_count >= .95*RATE*60)
    means = np.column_stack([np.bincount(bins, weights=column)[complete]/bin_count[complete]
                             for column in samples[:, 1:4].T])
    mean = samples[:, 1:4].mean(axis=0)
    return dict(source_lines=[first_line, last_line], time_range_s=time_range, samples=count,
        mean_force_body_m_s2=mean.tolist(), mean_vector_magnitude_m_s2=float(np.linalg.norm(mean)),
        mean_temperature_c=float(samples[:, 4].mean()), minute_indices=complete.tolist(),
        minute_means_body_m_s2=means.tolist(), minute_vector_magnitudes_m_s2=np.linalg.norm(means, axis=1).tolist())


def ground_observations(root, records):
    import numpy as np
    from .esa_component_preflight import RECORDS, WIDTH
    from .esa_ground_rate_scale import SOURCE
    from .studies.artifacts import digest

    inventory, first, second = (json.loads(records[key]) for key in ('inventory', 'first', 'second'))
    source = root/SOURCE
    source_sha = inventory['source_sha256']
    raw = (first['raw_imu'], second['second_raw_imu'])
    if (inventory['source_file'] != source.name or inventory['records'] != RECORDS
            or second['first_raw_sha256'] != digest(records['first'])
            or any(r['source_sha256'] != source_sha or r['uses_model_fits'] is not False for r in (first, second))
            or sum(r['samples'] for r in raw) != MAX_ROWS):
        raise ValueError('exact receiver-selected ground reports required')
    with source.open('rb') as stream:
        before = os.fstat(stream.fileno())
        if before.st_size != (RECORDS+1)*WIDTH or hashlib.file_digest(stream, 'sha256').hexdigest() != source_sha:
            raise ValueError('original opened iMAR source differs')
        stream.seek(0)
        header = stream.read(WIDTH)
        summaries = [stop_summary(stream, header, rows) for rows in raw]
        after = os.fstat(stream.fileno())
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('iMAR original changed during checked reads')
    a, b = (np.asarray(s['mean_force_body_m_s2']) for s in summaries)
    angle = float(np.rad2deg(np.arctan2(np.linalg.norm(np.cross(a, b)), a@b)))
    return dict(source_sha256=source_sha, stops=summaries, mean_force_direction_separation_deg=angle,
                unconstrained_site_force_rank=0)


def replay(study, ground):
    import numpy as np
    from . import esa_conditioned_tangent as parent
    from .esa_fitted_scale_support import RANK_LIMITS
    from .ilvis0_exploratory import ConditionalBounds
    from .ilvis0_solver_position import physical_metric
    from .innovations_snapshot import restore

    cut = parent.TRAIN
    times = np.asarray(study.input('forecast_times')[:cut])
    response = np.kron((.5*(times-times[0])**2)[:, None], np.eye(3))
    force = [np.asarray(s['mean_force_body_m_s2']) for s in ground['stops']]
    bounds = ConditionalBounds(study.input('recipe')['limits'], fit_earth_removal=True)
    keys = [f'{kind}_{axis}' for kind in ('accel_bias', 'accel_gain') for axis in AXES]
    scales = np.asarray([bounds.limits[k] for k in keys])
    results = {}
    for model in parent.MODELS:
        fit = study.input(parent.key(model, 'fit'))
        training = study.input(parent.key(model, 'training_observations'))
        report = study.artifact(model, 'conditioned-tangent.json')
        op = restore(study.artifact(model, 'full-factors.npz', raw=True),
                     expected_sha256=report['snapshot_sha256'],
                     expected_configuration=report['operator_configuration'], maximum_bytes=parent.STORAGE)
        prefix = op.prefix(cut)
        names = fit['active_parameters']
        if (prefix.configuration != report['prefix_configuration'] or training['times_s'] != times.tolist()
                or list(bounds.active) != names):
            raise ValueError('sealed training design or calibration recipe changed')
        actual_time = times+training['time_origin_gps_sow_s']
        if any(s['time_range_s'][0] <= actual_time[-1] and s['time_range_s'][1] >= actual_time[0]
               for s in ground['stops']):
            raise ValueError('ground stops must be outside the airborne training interval')
        point = np.asarray(fit['normalized_parameters'])
        calibrated = bounds.decode(np.clip(point, -1., 1.))
        values = np.asarray([calibrated[name] for name in keys])
        gradients = np.zeros((len(force), len(names)))
        gradients[:, [names.index(k) for k in keys]] = [
            force_gradient(f, values[:3], values[3:], scales[:3], scales[3:]) for f in force]
        conversion = np.tile(physical_metric(training['coordinates'][:1])[0], cut)
        pattern = prefix.whiten(response/conversion[:, None])
        design = np.asarray(fit['local_linearization']['jacobian'])
        results[model] = {str(rtol): anchor_comparison(design, dict(persistent=pattern), gradients, rank_rtol=rtol)
                          for rtol in RANK_LIMITS}
    return results


def run(root, action):
    from . import esa_conditioned_tangent as parent
    from .esa_fitted_scale_support import RANK_LIMITS, SOURCE_SHA
    from .esa_ground_rate_scale import FIRST, INVENTORY, SECOND
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure

    with closing(ClosedStudy(root, 'data/'+parent.ID)) as study:
        if (study.completion['manifest_sha256'] != SOURCE_SHA or study.completion['state'] != 'complete'
                or set(study.rows) != set(parent.MODELS) or any(not row['passed'] for row in study.rows.values())):
            raise ValueError('complete sealed training designs required')
        records = {name: (root/path).read_bytes() for name, path in
                   [('inventory', INVENTORY), ('first', FIRST), ('second', SECOND)]}
        sources = (Path(__file__).relative_to(root).as_posix(), PLAN, 'analysis/tests/test_esa_ground_force_support.py')
        freeze = encoded(dict(source=study.completion, environment=runtime_environment(),
            sources={name:digest((root/name).read_bytes()) for name in source_closure(root, sources)},
            ground_report_hashes={name: digest(raw) for name, raw in records.items()},
            models=parent.MODELS, rank_limits=RANK_LIMITS, source_hash_passes=1, maximum_rows=MAX_ROWS,
            design_projections=12, fit_starts=0, native_calls=0, later_receiver_positions=0, protected_reads=0))
        if action == 'freeze':
            _write_equal(root/FREEZE, freeze)
            return dict(freeze_sha256=digest(freeze))
        if (root/FREEZE).read_bytes() != freeze:
            raise ValueError('frozen ground projection definition differs')
        ground = ground_observations(root, records)
        result = encoded(dict(freeze_sha256=digest(freeze), ground=ground, models=replay(study, ground),
                              scientific_decision='abstain', fit_starts=0, native_calls=0,
                              later_receiver_positions=0, protected_reads=0))
    _write_equal(root/RESULT, result)
    return dict(sha256=digest(result), training_designs=len(parent.MODELS), ground_stops=len(ground['stops']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(json.dumps(run(Path.cwd(), parser.parse_args().action), sort_keys=True))
