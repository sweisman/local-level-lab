# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only finite continuation plan; no observations or fits are evaluated."""
import math

VERSION = 'ilvis0-recovery-subset-plan-v1'
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
CASES = ('bias1_unsubtracted', 'bias1_profiled_removal')


def build(records, selected):
    if len(selected) != 4 or len(set(selected)) != 4:
        raise ValueError('three distinct failures and one completed control required')
    indexed = {r['segment_id']: r for r in records}
    tasks = []
    rates = []
    for index, sid in enumerate(selected):
        if sid not in indexed:
            raise ValueError('selected interval missing from preserved results')
        record = indexed[sid]
        fits = {(c['case_id'], f['model']): f for c in record['cases'] for f in c['fits']}
        if set(fits) != {(c, m) for c in CASES for m in MODELS}:
            raise ValueError('exact original six-fit matrix required')
        control = index == 3
        if control and any(not f['converged'] for f in fits.values()):
            raise ValueError('control must have six completed reference fits')
        current = []
        for case in CASES:
            for model in MODELS:
                old = fits[case, model]
                if old['converged'] and not control:
                    continue
                point = old['normalized_parameters']
                if (not point or len(point) != len(old['active_parameters'])
                        or any(not math.isfinite(u) or abs(u) > 1 for u in point)):
                    raise ValueError('saved feasible point and parameter order required')
                if old['evaluations'] < 1 or not math.isfinite(old['elapsed_s']) or old['elapsed_s'] <= 0:
                    raise ValueError('positive recorded runtime/evaluation count required')
                task = dict(segment_id=sid, case_id=case, model=model,
                            role='control' if control else 'recovery',
                            identity='::'.join((sid, case, model, 'primary')),
                            start='saved_feasible_solution')
                tasks.append(task)
                current.append(task)
                rates.append(old['elapsed_s'] / old['evaluations'])
        if not control:
            if not current:
                raise ValueError('failure example has no unfinished fit')
            candidates = [t for t in current if t['model'] == MODELS[index]] or current
            repeat = dict(candidates[0], role='repeatability',
                          identity=candidates[0]['identity'].removesuffix('primary') + 'repeat',
                          start='saved_feasible_solution_plus_fixed_0.01_perturbation')
            tasks.append(repeat)
            source = fits[repeat['case_id'], repeat['model']]
            rates.append(source['elapsed_s'] / source['evaluations'])
    ceiling = len(tasks) * 602
    estimate = sum(r * 602 for r in rates)
    return dict(version=VERSION, state='prepared_only', selected_segment_ids=selected,
                tasks=tasks, identities=[t['identity'] for t in tasks],
                maximum_starts=len(tasks), retries=0, maximum_fit_sweeps=600,
                maximum_diagnostic_sweeps=2, maximum_native_sweeps=ceiling,
                numerical_threads=2, x_scale='jac', perturbation=0.01,
                repeat_cost_relative_tolerance=1e-6, repeat_track_rms_tolerance_m=0.01,
                control_cost_relative_tolerance=1e-6,
                estimate_at_ceiling_hours=estimate / 3600,
                estimate_range_hours=[0.8 * estimate / 3600, 1.2 * estimate / 3600],
                runtime_estimate_basis='same-recording first-pass elapsed seconds/evaluation; not a guarantee',
                reuse_converged_reference_fits=True, physical_bounds_unchanged=True,
                clock='nominal_200Hz', covariance='h1_v3_tau60',
                scientific_decision='abstain', observed_allowance_authorized=False)
