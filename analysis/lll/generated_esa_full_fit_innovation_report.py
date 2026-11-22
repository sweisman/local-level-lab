# SPDX-License-Identifier: AGPL-3.0-or-later
"""Summarize sealed generated 600-report fits without refitting."""

import hashlib
import json
import math
from pathlib import Path

from .prediction_fitted_innovation_audit import correlation


ID = 'generated-esa-600-innovation-null-v1-20261117'
PLAN = 'docs/prediction-observed-development/FULL_FIT_INNOVATION_NULL_PLAN.md'
ESA_REPORT = 'docs/prediction-observed-development/training-innovation-result.json'


def fit_innovations(fit, *, training_epochs):
    import numpy as np

    if (type(training_epochs) is not int or training_epochs <= 20
            or not isinstance(fit, dict)):
        raise ValueError('saved fit and sufficient training epochs required')
    passing = (fit.get('converged') is True and
               fit.get('stopping_rule_verified') is True)
    result = dict(numerical_passing=passing,
                  converged=fit.get('converged'),
                  stopping_rule_verified=fit.get('stopping_rule_verified'),
                  evaluations=fit.get('evaluations'),
                  training_cost=fit.get('residual_sum_squares'))
    if not passing:
        return result
    linear = fit.get('local_linearization', {})
    residual = linear.get('residual')
    jacobian = np.asarray(linear.get('jacobian'), dtype=float)
    if (linear.get('convention') !=
            'whitened residual derivative by normalized parameter'
            or not isinstance(residual, list)
            or len(residual) != 3 * training_epochs
            or len(linear.get('active_parameters', [])) != 26
            or jacobian.shape != (3 * training_epochs, 26)
            or not np.all(np.isfinite(jacobian))
            or any(type(x) not in (int, float) or not math.isfinite(x)
                   for x in residual)
            or not math.isclose(sum(x*x for x in residual),
                                fit['residual_sum_squares'],
                                rel_tol=1e-10, abs_tol=1e-10)):
        raise ValueError('saved full-fit residual inconsistent with cost')
    singular = np.linalg.svd(jacobian, compute_uv=False)
    result['tangent_rank'] = int(np.count_nonzero(
        singular > singular[0] * 1e-10))
    result['smallest_to_largest_singular_ratio'] = float(
        singular[-1] / singular[0]) if singular[0] else 0.
    result['axes'] = {}
    for axis, name in enumerate(('north', 'east', 'height')):
        values = residual[axis::3]
        result['axes'][name] = dict(
            whitened_rms=math.sqrt(sum(x*x for x in values)/training_epochs),
            correlations={str(lag): correlation(values, lag)
                          for lag in (1, 5, 20)})
    return result


def build(root):
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    public_bytes = (root / ESA_REPORT).read_bytes()
    public = json.loads(public_bytes)
    study = ClosedStudy(root, 'data/' + ID)
    try:
        recipe = study.input('recipe')
        if (study.completion['state'] not in ('complete', 'terminal')
                or len(study.tasks) != 2
                or set(study.tasks) != {'increment', 'point'}
                or recipe.get('duration_s') != 900.
                or recipe.get('rate_hz') != 300
                or recipe.get('queries') != 900
                or recipe.get('maximum_evaluations') != 200
                or study.manifest.get('scope') !=
                    'two independent known-answer 600-report complete fits; '
                    'no original or protected aircraft input'
                or public.get('training_epochs') != 600
                or public.get('scientific_decision') != 'abstain'):
            raise ValueError('sealed full generated pilot and ESA reference required')
        rows = {}
        for law in ('increment', 'point'):
            row = study.rows[law]
            if row['status'] != 'complete':
                rows[law] = dict(status=row['status'], numerical_passing=False,
                                 outcome='interrupted_or_error')
                continue
            envelope = study.envelope(law)
            outcome = envelope['result']
            if not any(path.endswith('/fit.json')
                       for path in envelope['artifacts']):
                rows[law] = dict(status=row['status'], result_passed=False,
                    numerical_passing=False, outcome='technical_error_before_fit',
                    error_type=outcome.get('error_type'),
                    reason=outcome.get('reason'))
                continue
            if outcome.get('scientific_decision') != 'abstain':
                raise ValueError('generated task made a scientific decision')
            if outcome.get('error_type') is not None:
                rows[law] = dict(status=row['status'], result_passed=False,
                    numerical_passing=False, outcome='technical_error_after_fit',
                    error_type=outcome['error_type'],
                    reason=outcome.get('reason'),
                    fit_artifact_sha256=hashlib.sha256(study.artifact(
                        law, 'fit.json', raw=True)).hexdigest())
                continue
            if (outcome.get('training_epochs') != 600
                    or outcome.get('prediction_epochs') != 300
                    or outcome.get('original_reads') != 0
                    or outcome.get('protected_reads') != 0
                    ):
                raise ValueError('generated task scope or input boundary changed')
            fit = study.artifact(law, 'fit.json')
            summary = fit_innovations(fit, training_epochs=600)
            if summary['converged'] != outcome['converged']:
                raise ValueError('saved result and fit convergence differ')
            rows[law] = dict(status=row['status'], result_passed=outcome['passed'],
                **summary, fit_artifact_sha256=hashlib.sha256(study.artifact(
                    law, 'fit.json', raw=True)).hexdigest())
        return dict(version='generated-esa-full-fit-innovation-report-v1',
                    verified=True, study='data/' + ID,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    report_source_sha256=hashlib.sha256(
                        Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root / PLAN).read_bytes()).hexdigest(),
                    esa_reference_sha256=hashlib.sha256(public_bytes).hexdigest(),
                    tasks_total=2, tasks_complete=sum(
                        row['status'] == 'complete' for row in rows.values()),
                    numerical_passing_fits=sum(
                        row['numerical_passing'] for row in rows.values()),
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
    output = Path(args.output)
    if output.exists():
        raise ValueError('fresh pilot report required')
    result = build(args.root)
    atomic(output, encoded(result))
    print(json.dumps(dict(tasks_complete=result['tasks_complete'],
                          numerical_passing_fits=result['numerical_passing_fits']),
                     sort_keys=True))


if __name__ == '__main__':
    main()
