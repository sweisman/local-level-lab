# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only linear-step diagnosis for the sealed ESA 400/120 matrix."""

import math
from pathlib import Path


STUDY = 'data/esa-rolling-origin-400-model-matrix-20261118'
OUTPUT = 'docs/prediction-observed-development/ESA_400_120_STOPPING_GEOMETRY.json'


def summarize_fit(fit):
    """Compare the saved local quadratic prediction with the rejected full step.

    This solves only a 26-variable *saved linear* problem. It does not evaluate
    the physical model, change a fit or use a receiver observation.
    """
    import numpy as np
    from scipy.optimize import lsq_linear

    if type(fit.get('converged')) is not bool:
        raise ValueError('saved convergence label required')
    linear = fit['local_linearization']
    residual = np.asarray(linear['residual'], dtype=float)
    jacobian = np.asarray(linear['jacobian'], dtype=float)
    point = np.asarray(linear['normalized_parameters'], dtype=float)
    if (residual.ndim != 1 or point.ndim != 1 or not len(point) or
            jacobian.shape != (len(residual), len(point)) or
            not np.all(np.isfinite(residual)) or
            not np.all(np.isfinite(jacobian)) or
            not np.all(np.isfinite(point)) or np.any(abs(point) > 1)):
        raise ValueError('finite saved local linearization required')
    rejected = [step for step in fit['step_history']
                if step.get('method') == 'full_bounded' and
                step.get('accepted') is False]
    if not rejected:
        raise ValueError('rejected full step required')
    last = rejected[-1]
    correction = lsq_linear(jacobian, -residual,
                            bounds=(-1-point, 1-point), method='bvls',
                            tol=1e-10, max_iter=100)
    if not correction.success or not np.all(np.isfinite(correction.x)):
        raise ValueError('saved linear correction unfinished')
    delta = jacobian @ correction.x
    cost = float(residual @ residual)
    direct = cost-float((residual+delta) @ (residual+delta))
    stable = float(-2*(residual @ delta)-(delta @ delta))
    probe = fit['stability_probe']
    limit = float(probe['position_rms_tolerance_m'])
    rms = np.asarray(probe['position_rms_neu_m'], dtype=float)
    if (limit <= 0 or rms.shape != (3,) or
            not np.all(np.isfinite(rms)) or np.any(rms < 0) or
            not all(math.isfinite(float(last[key])) for key in
                    ('predicted_reduction', 'actual_reduction'))):
        raise ValueError('finite saved rejected-step and physical probe required')
    return dict(saved_converged=fit['converged'],
                scientific_decision='abstain',
                linear_predicted_reduction_direct=direct,
                linear_predicted_reduction_stable=stable,
                linear_reduction_relative_difference=(
                    abs(direct-stable)/max(abs(stable), 1e-30)),
                last_rejected_predicted_reduction=float(last['predicted_reduction']),
                last_rejected_actual_reduction=float(last['actual_reduction']),
                position_rms_ratio=float(max(rms)/limit),
                position_rms_neu_m=rms.tolist(),
                linear_correction_norm=float(np.linalg.norm(correction.x)),
                saved_residual_cost=cost)


def build(root):
    """Open only hash-verified archived fit artifacts; never rerun a fit."""
    from .esa_rolling_origin_400_model_matrix import tasks
    from .studies.artifacts import digest
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    study = ClosedStudy(root, STUDY)
    try:
        if (study.summary['completed'] != 24 or
                study.summary['state'] != 'terminal' or
                set(study.tasks) != {task['identity'] for task in tasks()}):
            raise ValueError('sealed terminal 24-fit matrix required')
        rows = []
        for law in ('increment', 'point'):
            for start in (0, 1):
                identity = f'flat_still-0-{law}-{start}'
                fit = study.artifact(identity, 'fit.json')
                row = summarize_fit(fit)
                if row['saved_converged']:
                    raise ValueError('original failed fit required')
                row.update(identity=identity,
                           fit_sha256=study.envelope(identity)['artifacts'][
                               f'artifacts/{identity}/fit.json'])
                rows.append(row)
        return dict(version='esa-400-120-stopping-geometry-v1',
                    study=STUDY, rows=rows,
                    fit_manifest_sha256=study.completion['manifest_sha256'],
                    fit_summary_sha256=study.completion['summary_sha256'],
                    source_sha256=digest(Path(__file__).read_bytes()),
                    original_reads=0, protected_reads=0, optimizer_starts=0,
                    numerical_outcomes_changed=False,
                    scientific_decision='abstain')
    finally:
        study.close()


def main():
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    arguments = parser.parse_args()
    root = Path(arguments.root).resolve()
    report = build(root)
    atomic(root/OUTPUT, encoded(report))
    print(f"{OUTPUT}: {len(report['rows'])} saved failures; 0 new fits")


if __name__ == '__main__':
    main()
