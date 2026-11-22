# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only comparison of saved 400- and 600-report ESA training tangents."""

import gzip
import hashlib
import json
import math
import statistics
from pathlib import Path

EARLY = 'data/esa-rolling-origin-400-development-v1-20261115'
LATE = 'data/esa-training-split-recheck-development-v1-20261115'
PLAN = 'docs/prediction-observed-development/ESA_TRAINING_DURATION_WEAKNESS_PLAN.md'
PARAMETERS = ('gyro_bias_z', 'accel_bias_z')


def _motion(rows):
    speeds = [math.hypot(row['north_mps'], row['east_mps']) for row in rows]
    courses = [(math.degrees(math.atan2(row['east_mps'], row['north_mps']))
                + 360.) % 360. for row in rows]
    if (len(rows) < 2 or any(not math.isfinite(value) or value <= 0
                             for value in speeds)
            or any(not math.isfinite(value) for value in courses)
            or max(courses) - min(courses) >= 180.):
        raise ValueError('finite nonwrapping saved receiver course required')
    return dict(reports=len(rows),duration_s=rows[-1]['time_s']-rows[0]['time_s'],
                course_first_deg=courses[0],course_last_deg=courses[-1],
                course_min_deg=min(courses),course_max_deg=max(courses),
                median_ground_speed_mps=float(statistics.median(speeds)),
                north_speed_first_mps=rows[0]['north_mps'],
                north_speed_last_mps=rows[-1]['north_mps'],
                east_speed_first_mps=rows[0]['east_mps'],
                east_speed_last_mps=rows[-1]['east_mps'],
                height_change_m=rows[-1]['height_m']-rows[0]['height_m'])


def _analyze(fit, epochs):
    import numpy as np
    from .local_tangent import conditional_column_norm

    local = fit.get('local_linearization', {})
    names = local.get('active_parameters')
    matrix = np.asarray(local.get('jacobian'), dtype=float)
    saved = np.asarray(fit.get('singular_values'), dtype=float)
    if (fit.get('converged') is not True or fit.get('active_bounds') != []
            or local.get('convention') !=
                'whitened residual derivative by normalized parameter'
            or names != fit.get('active_parameters')
            or len(names) != 26 or matrix.shape != (3 * epochs, 26)
            or saved.shape != (26,) or not np.all(np.isfinite(matrix))
            or any(name not in names for name in PARAMETERS)):
        raise ValueError('complete interior saved training tangent required')
    _, singular, vh = np.linalg.svd(matrix, full_matrices=False)
    if not np.allclose(singular, saved, rtol=1e-8, atol=1e-9):
        raise ValueError('saved singular values do not reproduce')
    weak = np.abs(vh[-1])
    fitted = dict(zip(names, fit['normalized_parameters'], strict=True))
    conditional = {name: conditional_column_norm(matrix, names.index(name))
                   for name in PARAMETERS}
    prefix = ({name: conditional_column_norm(matrix[:1200], names.index(name))
               for name in PARAMETERS} if epochs == 600 else None)
    return dict(epochs=epochs, parameters=names,
                weakest_singular=float(singular[-1]),
                strongest_singular=float(singular[0]),
                weakest_to_strongest=float(singular[-1] / singular[0]),
                top_three_weak_loadings=[names[i] for i in np.argsort(-weak)[:3]],
                weak_loading={name: float(weak[names.index(name)])
                              for name in PARAMETERS},
                conditional_column_norm=conditional,
                first_400_rows_at_same_fit_conditional_column_norm=prefix,
                normalized_fit={name: float(fitted[name]) for name in PARAMETERS},
                near_bound={name: abs(fitted[name]) >= .99 for name in PARAMETERS})


def build(root):
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    early = ClosedStudy(root, EARLY)
    late = ClosedStudy(root, LATE)
    try:
        if (early.completion['state'] != 'complete'
                or late.completion['state'] != 'complete'
                or set(early.tasks) != {'increment', 'point'}
                or set(late.tasks) != {'increment', 'point'}
                or early.input('saved-input-binding', raw=True) !=
                   late.input('saved-input-binding', raw=True)
                or early.input('parent_identity', raw=True) !=
                   late.input('parent_identity', raw=True)
                or early.input('recipe', raw=True) !=
                   late.input('recipe', raw=True)):
            raise ValueError('same sealed ESA development source and recipe required')
        early_rows = json.loads(gzip.decompress(early.input('training', raw=True)))
        late_rows = json.loads(gzip.decompress(late.input('training', raw=True)))
        if (len(early_rows) != 400 or len(late_rows) != 600
                or early_rows != late_rows[:400]):
            raise ValueError('exact nested 400/600 receiver training rows required')
        motion=dict(first_400=_motion(early_rows),
                    added_200=_motion(late_rows[400:]))
        laws = {}
        for law in ('increment', 'point'):
            for study in (early, late):
                if (study.tasks[law]['payload'] !=
                        dict(law=law, model='sphere_rotating', start=0)
                        or study.rows[law]['status'] != 'complete'
                        or study.envelope(law)['result']['passed'] is not True):
                    raise ValueError('same completed candidate and start required')
            early_operator = early.artifact(law, 'training-error-operator.json')
            late_operator = late.artifact(law, 'training-error-operator.json')
            shared_operator_fields = (
                'active_parameters', 'bounds', 'gravity_mps2',
                'gravity_anchor_height_m', 'noise_roots',
                'noise_correlation_times_s', 'receiver_white',
                'receiver_offset', 'receiver_drift',
                'receiver_drift_origin_s', 'receiver_drift_span_s',
                'receiver_components', 'receiver_policy')
            if any(early_operator[key] != late_operator[key]
                   for key in shared_operator_fields):
                raise ValueError('unchanged declared error-law parameters required')
            first = _analyze(early.artifact(law, 'fit.json'), 400)
            second = _analyze(late.artifact(law, 'fit.json'), 600)
            if first['parameters'] != second['parameters']:
                raise ValueError('same normalized parameter coordinates required')
            laws[law] = dict(first_400=first, first_600=second,
                weakest_singular_factor=second['weakest_singular']/first['weakest_singular'],
                conditional_column_norm_factor={name:
                    second['conditional_column_norm'][name]/
                    first['conditional_column_norm'][name]
                    for name in PARAMETERS},
                within_600_fit_added_rows_factor={name:
                    second['conditional_column_norm'][name]/
                    second['first_400_rows_at_same_fit_conditional_column_norm'][name]
                    for name in PARAMETERS},
                early_fit_sha256=hashlib.sha256(
                    early.artifact(law, 'fit.json', raw=True)).hexdigest(),
                late_fit_sha256=hashlib.sha256(
                    late.artifact(law, 'fit.json', raw=True)).hexdigest())
        return dict(version='esa-training-duration-weakness-v1',
                    studies=[EARLY, LATE],
                    manifest_sha256=[early.completion['manifest_sha256'],
                                     late.completion['manifest_sha256']],
                    summary_sha256=[early.completion['summary_sha256'],
                                    late.completion['summary_sha256']],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root/PLAN).read_bytes()).hexdigest(),
                    exact_training_prefix=True,
                    same_declared_error_law_parameters=True,
                    receiver_motion=motion,laws=laws, new_fits=0,
                    original_reads=0, reserved_esa_group_reads=0,
                    scientific_decision='abstain')
    finally:
        early.close()
        late.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.exists():
        raise ValueError('fresh saved-data report required')
    result = build(args.root)
    atomic(output, encoded(result))
    print(json.dumps({law: dict(
        weakest_singular_factor=row['weakest_singular_factor'],
        conditional_column_norm_factor=row['conditional_column_norm_factor'])
        for law, row in result['laws'].items()}))


if __name__ == '__main__':
    main()
