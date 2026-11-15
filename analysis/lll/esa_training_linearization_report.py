# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only local adequacy audit of the completed ESA training fit."""

import argparse
import hashlib
import json
import math
from pathlib import Path


RANK_RTOL = 1e-8


def analyze_fit(fit, *, training_epochs):
    """Compare a sealed whitened fit with its local linear Gaussian reference.

    The reference describes a fixed, correctly specified covariance and a
    linear fitted mean. It is not a calibrated nonlinear goodness-of-fit test.
    """
    import numpy as np

    local = fit.get('local_linearization', {})
    if (type(training_epochs) is not int or training_epochs < 2 or
            fit.get('converged') is not True or
            fit.get('stopping_rule_verified') is not True or
            fit.get('active_bounds') != [] or
            local.get('convention') !=
                'whitened residual derivative by normalized parameter'):
        raise ValueError('complete interior whitened fit required')
    residual = np.asarray(local.get('residual'), dtype=float)
    jacobian = np.asarray(local.get('jacobian'), dtype=float)
    count = training_epochs * 3
    if (residual.shape != (count,) or jacobian.ndim != 2 or
            jacobian.shape[0] != count or not 1 <= jacobian.shape[1] < count or
            len(fit.get('active_parameters', [])) != jacobian.shape[1] or
            not np.all(np.isfinite(residual)) or
            not np.all(np.isfinite(jacobian))):
        raise ValueError('complete finite fitted residual and tangent required')
    quadratic = float(residual @ residual)
    cost = fit.get('residual_sum_squares')
    if (not isinstance(cost, (int, float)) or not math.isfinite(cost) or
            abs(quadratic - cost) > max(1e-8, 1e-10 * abs(cost))):
        raise ValueError('saved whitened cost does not replay')
    u, singular, _ = np.linalg.svd(jacobian, full_matrices=False)
    if not np.all(np.isfinite(singular)) or singular[0] <= 0:
        raise ValueError('nonzero local mean-design rank required')
    rank = int(np.count_nonzero(singular > RANK_RTOL * singular[0]))
    if rank < 1 or rank >= count:
        raise ValueError('positive residual rank and degrees of freedom required')
    fitted = float(np.linalg.norm(u[:, :rank].T @ residual))
    residual_norm = math.sqrt(quadratic)
    degrees = count - rank
    return dict(training_epochs=training_epochs, observation_count=count,
        fitted_parameter_count=jacobian.shape[1], local_rank=rank,
        rank_relative_tolerance=RANK_RTOL,
        smallest_to_largest_singular_ratio=float(singular[-1] / singular[0]),
        quadratic=quadratic,
        observed_whitened_rms=math.sqrt(quadratic / count),
        linear_reference_degrees_of_freedom=degrees,
        linear_reference_expected_quadratic=degrees,
        linear_reference_expected_rms=math.sqrt(degrees / count),
        quadratic_to_linear_reference_ratio=quadratic / degrees,
        local_tangent_residual_fraction=(fitted / residual_norm
                                         if residual_norm else 0.),
        nonlinear_reference_calibrated=False,
        scientific_decision='abstain')


def build(root):
    from .esa_training_split_study import ID as FIT_ID, LAWS
    from .esa_training_innovation_study import ID as DIAGNOSTIC_ID
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    fit_study = ClosedStudy(root, 'data/' + FIT_ID)
    diagnostic_study = ClosedStudy(root, 'data/' + DIAGNOSTIC_ID)
    try:
        if (fit_study.completion['state'] != 'complete' or
                diagnostic_study.completion['state'] != 'complete' or
                set(fit_study.tasks) != set(LAWS) or
                set(diagnostic_study.tasks) != set(LAWS) or
                diagnostic_study.input('source-binding')[
                    'fit_manifest_sha256'] !=
                    fit_study.completion['manifest_sha256']):
            raise ValueError('matching sealed fit and innovation records required')
        rows = {}
        for law in LAWS:
            fit = fit_study.artifact(law, 'fit.json')
            innovation = diagnostic_study.artifact(
                law, 'innovation-summary.json')
            if (fit_study.envelope(law)['result']['passed'] is not True or
                    diagnostic_study.envelope(law)['result']['passed'] is not True or
                    innovation['law'] != law or
                    innovation['fit_manifest_sha256'] !=
                        fit_study.completion['manifest_sha256'] or
                    innovation['training_replay']['replay_passed'] is not True or
                    innovation['later_receiver_values_used'] is not False or
                    innovation['protected_reads'] != 0):
                raise ValueError('sealed training-only evidence differs')
            result = analyze_fit(fit, training_epochs=innovation['training_epochs'])
            if abs(result['quadratic'] - innovation['quadratic']) > 1e-8:
                raise ValueError('saved innovation cost differs from fitted tangent')
            rows[law] = result
        return dict(version='esa-training-linear-reference-v1',
            fit_study='data/' + FIT_ID,
            fit_manifest_sha256=fit_study.completion['manifest_sha256'],
            innovation_study='data/' + DIAGNOSTIC_ID,
            innovation_manifest_sha256=diagnostic_study.completion['manifest_sha256'],
            source_sha256=hashlib.sha256((root /
                'analysis/lll/esa_training_linearization_report.py').read_bytes()
            ).hexdigest(),
            laws=rows, later_receiver_values_used=False,
            protected_confirmation_groups_opened=0,
            nonlinear_reference_calibrated=False,
            scientific_decision='abstain')
    finally:
        diagnostic_study.close()
        fit_study.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    result = build(args.root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({law:dict(rank=row['local_rank'],
        quadratic=row['quadratic'], ratio=row['quadratic_to_linear_reference_ratio'])
        for law, row in result['laws'].items()}, sort_keys=True))


if __name__ == '__main__':
    main()
