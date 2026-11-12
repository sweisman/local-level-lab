# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare fixed candidate error laws on one matched training prefix.

This is a training-score diagnostic. It never selects a law for scientific use
or claims bounded/nonlinear calibration or future coverage.
"""
import math


def compare(candidates):
    import numpy as np

    if (not isinstance(candidates, dict) or len(candidates) < 2 or
            any(not isinstance(name, str) or not name for name in candidates)):
        raise ValueError('at least two named candidate error laws required')
    records = []
    for law_id, item in candidates.items():
        if not isinstance(item, dict) or set(item) != {'fit', 'binding', 'diagnostic'}:
            raise ValueError('earlier-only candidate records required')
        fit, binding, diagnostic = (item[key] for key in
                                    ('fit', 'binding', 'diagnostic'))
        if not all(isinstance(value, dict) for value in (fit, binding, diagnostic)):
            raise ValueError('complete earlier-only candidate records required')
        try:
            epochs = binding['training_epochs']
            withheld = binding['prediction_epochs']
            prefix = (binding['training_receiver_sha256'],
                      tuple((name, binding['training_prefix_sha256'][name])
                            for name in ('theta', 'dv', 'dt')),
                      epochs, withheld)
            score = fit['gaussian_training_score']
            nll = float(score['negative_log_likelihood'])
            names = fit['active_parameters']
            bounds = fit['active_bounds']
            fixed = diagnostic['fixed_parameters']
            mean = np.asarray(fixed['mean'], dtype=float)
            covariance = np.asarray(fixed['covariance'], dtype=float)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError('complete earlier-only fit, binding and forecast required') from error
        if (type(epochs) is not int or epochs < 2 or
                type(withheld) is not int or withheld < 1 or
                score.get('row_count') != 3*epochs or
                score.get('covariance_parameters_estimated') is not False or
                fit.get('prediction_receiver_positions_used_in_training') is not False or
                binding.get('original_reads') != 0 or binding.get('protected_reads') != 0 or
                diagnostic.get('later_observations_used') is not False or
                diagnostic.get('prediction_target') != 'receiver_measurement' or
                diagnostic.get('training_epochs') != epochs or
                diagnostic.get('prediction_epochs') != withheld or
                fixed.get('parameter_uncertainty_included') is not False or
                not isinstance(names, list) or not names or
                not isinstance(bounds, list) or not set(bounds) <= set(names) or
                mean.shape != (withheld, 3) or
                covariance.shape != (withheld, 3, 3) or
                not math.isfinite(nll) or
                not np.all(np.isfinite(mean)) or
                not np.all(np.isfinite(covariance)) or
                np.any(np.diagonal(covariance, axis1=1, axis2=2) <= 0)):
            raise ValueError('finite matched earlier-only candidate evidence required')
        records.append(dict(law_id=law_id, prefix=prefix, model=fit.get('model'),
                            active_parameters=names, nll=nll,
                            converged=fit.get('converged') is True and
                                      fit.get('stopping_rule_verified') is True,
                            bounds=bounds, mean=mean,
                            sigma=np.sqrt(np.diagonal(covariance,
                                                      axis1=1, axis2=2))))
    first = records[0]
    if any(row['prefix'] != first['prefix'] for row in records[1:]):
        raise ValueError('same measured training prefix required for every law')
    if (not first['model'] or any(row['model'] != first['model'] or
            row['active_parameters'] != first['active_parameters']
            for row in records[1:])):
        raise ValueError('same physical candidate and nuisance columns required')
    common = dict(candidate_laws=sorted(candidates),
                  training_epochs=first['prefix'][2],
                  prediction_epochs=first['prefix'][3],
                  active_bounds_by_law={row['law_id']:row['bounds'] for row in records},
                  selected_law=None, later_observations_used=False,
                  coverage_calibrated=False, scientific_decision='abstain')
    if any(not row['converged'] for row in records):
        return dict(common, status='numerically_unqualified',
                    training_ranking=None, numerical_unique_minimum=False,
                    maximum_future_sigma_ratio=None)
    ranking = sorted(records, key=lambda row: (row['nll'], row['law_id']))
    best = ranking[0]['nll']
    rows = [dict(law_id=row['law_id'], negative_log_likelihood=row['nll'],
                 delta_nll=row['nll']-best) for row in ranking]
    sigma = np.stack([row['sigma'] for row in records])
    ratio = float(np.max(np.max(sigma, axis=0)/np.min(sigma, axis=0)))
    unique = rows[1]['delta_nll'] > 16*np.finfo(float).eps*max(
        1., abs(best), abs(rows[1]['negative_log_likelihood']))
    return dict(common,
                status=('active_bounds_unsupported' if any(row['bounds'] for row in records)
                        else 'training_only_unqualified'),
                training_ranking=rows, numerical_unique_minimum=bool(unique),
                maximum_future_sigma_ratio=ratio)
