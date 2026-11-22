# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-data comparison of the noisy cohort's forecast scale and path gate."""

import hashlib
import json
import math
from pathlib import Path

from .generated_esa_bounded_cohort import ID, SCOPE, recipe, tasks


PLAN = 'docs/prediction-observed-development/GENERATED_NOISE_FLOOR_AUDIT_PLAN.md'


def expected_horizontal_rms(covariance, truth):
    """Fixed-calibration conditional second-moment scale in local metres."""
    import numpy as np
    from .airquantumgrav_truth import A, E2

    c = np.asarray(covariance, dtype=float)
    position = np.asarray(truth, dtype=float)
    if (position.ndim != 2 or position.shape[1:] != (3,) or not len(position)
            or c.shape != (len(position), 3, 3)
            or not np.all(np.isfinite(c)) or not np.all(np.isfinite(position))
            or np.any(np.abs(position[:, 0]) >= math.pi / 2)
            or np.any(np.diagonal(c, axis1=1, axis2=2) <= 0)
            or not np.allclose(c, c.swapaxes(1, 2), rtol=1e-10, atol=1e-15)):
        raise ValueError('complete positive finite conditional covariance required')
    phi, height = position[:, 0], position[:, 2]
    q = 1 - E2 * np.sin(phi)**2
    north = A * (1-E2) / q**1.5 + height
    east = (A / np.sqrt(q) + height) * np.cos(phi)
    if np.any(north <= 0) or np.any(east <= 0):
        raise ValueError('positive local metric required')
    variances = c[:, 0, 0] * north**2 + c[:, 1, 1] * east**2
    return float(np.sqrt(np.mean(variances)))


def build(root):
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    study = ClosedStudy(root, 'data/' + ID)
    try:
        frozen = {item['identity']: item for item in tasks()}
        actual = {name: {key: value for key, value in task.items()
                         if key not in ('index', 'shard')}
                  for name, task in study.tasks.items()}
        r = recipe()
        if (study.completion['state'] != 'complete'
                or study.manifest.get('scope') != SCOPE
                or study.input('recipe') != r
                or actual != frozen or set(study.rows) != set(frozen)
                or r['base']['accuracy']['horizontal_rms_m'] != .1):
            raise ValueError('unchanged closed eight-case cohort required')
        rows = {}
        for name in frozen:
            status = study.rows[name]
            if status['status'] != 'complete' or status['passed'] is not True:
                raise ValueError('complete technical cohort task required')
            result = study.envelope(name)['result']
            fit = study.artifact(name, 'fit.json')
            score = study.artifact(name, 'scores.json')
            conditional = study.artifact(name, 'conditional-scores.json')
            diagnostic = study.artifact(name, 'forecast-error-diagnostic.json')
            answer = study.artifact(name, 'scoring-observations.json')
            fixed = diagnostic['fixed_parameters']
            if (result.get('bounded_technical_passed') is not True
                    or result.get('original_prediction_passed') is not False
                    or fit.get('converged') is not True
                    or diagnostic.get('prediction_target') != 'physical_position'
                    or diagnostic.get('later_observations_used') is not False
                    or fixed.get('parameter_uncertainty_included') is not False
                    or fixed.get('conditioning_epochs') != 600
                    or fixed.get('forecast_epochs') != 300
                    or conditional.get('primary_raw_forecast_unchanged') is not True
                    or score.get('score_reference') !=
                       'generated noiseless physical truth'
                    or conditional.get('score_reference') !=
                       'generated noiseless physical truth'
                    or len(answer.get('coordinates', [])) != 900):
                raise ValueError('incomplete earlier-only saved score or covariance')
            future = answer['coordinates'][600:]
            scale = expected_horizontal_rms(fixed['covariance'], future)
            raw = score['prediction']['horizontal_rms_m']
            center = conditional['prediction']['horizontal_rms_m']
            if (not all(isinstance(v, (int, float)) and math.isfinite(v)
                        and v >= 0 for v in (raw, center))
                    or raw != result['prediction']['horizontal_rms_m']):
                raise ValueError('saved prediction scores differ')
            rows[name] = dict(law=frozen[name]['payload']['law'],
                              noise_floor_horizontal_rms_m=scale,
                              raw_horizontal_rms_m=raw,
                              conditional_horizontal_rms_m=center,
                              coded_horizontal_limit_m=.1)
        return dict(version='generated-esa-noise-floor-audit-v1',
                    verified=True, study='data/' + ID,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root / PLAN).read_bytes()).hexdigest(),
                    tasks_total=8, checked_tasks=len(rows),
                    noise_floor_above_coded_screen=sum(
                        row['noise_floor_horizontal_rms_m'] > .1
                        for row in rows.values()),
                    rows=rows, new_fits=0, original_reads=0,
                    protected_reads=0, aircraft_error_law_qualified=False,
                    scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    path = Path(args.output)
    if path.exists():
        raise ValueError('fresh audit output required')
    result = build(args.root)
    atomic(path, encoded(result))
    print(json.dumps({key: result[key] for key in
                      ('tasks_total', 'checked_tasks',
                       'noise_floor_above_coded_screen')}, sort_keys=True))


if __name__ == '__main__':
    main()
