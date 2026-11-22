# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only local calibration SVD for two generated complete fits."""

import hashlib
import json
import math
from pathlib import Path

from .generated_esa_bounded_pilot_v2 import ID, PLAN, recipe
from .generated_esa_bounded_pilot_v2_report import build as verified_pilot


AUDIT_PLAN = ('docs/prediction-observed-development/'
              'GENERATED_WEAK_DIRECTION_PLAN.md')


def diagnose(jacobian, names, residual, *, rank_rtol=1e-10):
    """Return the weakest normalized local direction and its loading names."""
    import numpy as np

    a = np.asarray(jacobian, dtype=float)
    r = np.asarray(residual, dtype=float)
    if (a.ndim != 2 or not 1 <= a.shape[1] <= 27
            or a.shape[0] < a.shape[1] or r.shape != (a.shape[0],)
            or len(names) != a.shape[1]
            or len(set(names)) != len(names)
            or not all(isinstance(name, str) and name for name in names)
            or not np.all(np.isfinite(a)) or not np.all(np.isfinite(r))
            or not 0 < rank_rtol < 1):
        raise ValueError('complete finite whitened residual Jacobian required')
    _, singular, vectors = np.linalg.svd(a, full_matrices=False)
    if not len(singular) or singular[0] <= 0 or singular[-1] <= 0:
        raise ValueError('nonzero local calibration spectrum required')
    weak = vectors[-1].copy()
    pivot = int(np.argmax(np.abs(weak)))
    if weak[pivot] < 0:
        weak = -weak
    order = np.argsort(-np.abs(weak))[:5]
    return dict(rank=int(np.count_nonzero(singular > singular[0]*rank_rtol)),
                parameter_count=len(names),
                largest_singular_value=float(singular[0]),
                weakest_singular_value=float(singular[-1]),
                weakest_to_largest_ratio=float(singular[-1]/singular[0]),
                weakest_local_inverse_scale=float(1/singular[-1]),
                weakest_vector=weak.tolist(),
                top_loadings=[dict(parameter=names[int(index)],
                                   normalized_loading=float(weak[index]))
                              for index in order],
                recomputed_cost=float(r@r),
                rank_rtol=rank_rtol)


def build(root):
    """Read and verify the sealed generated pilot without fitting or scoring."""
    import numpy as np
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    original = verified_pilot(root)
    if (original['tasks_total'] != 2
            or original['technical_passing'] != 2
            or original['original_physical_passing'] != 0
            or original['scientific_decision'] != 'abstain'):
        raise ValueError('exact closed two-law generated pilot required')
    study = ClosedStudy(root, 'data/' + ID)
    try:
        if study.input('recipe') != recipe():
            raise ValueError('generated recipe changed')
        rows = {}
        for law in ('increment', 'point'):
            raw = study.artifact(law, 'fit.json', raw=True)
            fit = json.loads(raw)
            linear = fit.get('local_linearization', {})
            if (fit.get('converged') is not True
                    or fit.get('stopping_rule_verified') is not True
                    or fit.get('scientific_decision') != 'abstain'
                    or linear.get('convention') !=
                       'whitened residual derivative by normalized parameter'
                    or linear.get('active_parameters') != fit.get('active_parameters')
                    or len(linear.get('residual', [])) != 1800
                    or len(linear.get('jacobian', [])) != 1800
                    or len(fit.get('active_parameters', [])) != 26):
                raise ValueError('sealed full training Jacobian required')
            summary = diagnose(np.asarray(linear['jacobian'], dtype=float),
                               fit['active_parameters'], linear['residual'])
            if not math.isclose(summary['recomputed_cost'],
                                fit['residual_sum_squares'],
                                rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError('local residual and saved cost differ')
            rows[law] = dict(**summary,
                             active_bounds=fit['active_bounds'],
                             original_physical_passed=False,
                             fit_artifact_sha256=hashlib.sha256(raw).hexdigest())
        left = np.asarray(rows['increment']['weakest_vector'])
        right = np.asarray(rows['point']['weakest_vector'])
        if (left.shape != (26,) or right.shape != (26,)
                or study.artifact('increment', 'fit.json')['active_parameters'] !=
                   study.artifact('point', 'fit.json')['active_parameters']):
            raise ValueError('matched calibration axes required')
        return dict(version='generated-esa-weak-direction-report-v1',
                    verified=True, study='data/' + ID,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    original_plan_sha256=hashlib.sha256((root / PLAN).read_bytes()).hexdigest(),
                    audit_plan_sha256=hashlib.sha256((root / AUDIT_PLAN).read_bytes()).hexdigest(),
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    tasks_total=2, original_physical_passing=0,
                    weak_direction_abs_similarity=float(abs(left @ right)),
                    laws=rows, new_fits=0, original_reads=0,
                    protected_reads=0, scientific_decision='abstain')
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
        raise ValueError('fresh saved-fit audit required')
    result = build(args.root)
    atomic(output, encoded(result))
    print(json.dumps(dict(tasks_total=result['tasks_total'],
                          weak_direction_abs_similarity=result[
                              'weak_direction_abs_similarity'],
                          original_physical_passing=result[
                              'original_physical_passing']), sort_keys=True))


if __name__ == '__main__':
    main()
