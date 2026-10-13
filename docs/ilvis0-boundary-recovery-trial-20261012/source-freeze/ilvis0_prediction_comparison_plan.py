# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite retrospective comparison specification; no data access or launcher."""
import math

VERSION='ilvis0-prediction-covariance-preparation-v1'
MODELS=('sphere_rotating','sphere_still','flat_still')
CASES=('bias1_unsubtracted','bias1_profiled_removal')


def make(split,median_seconds_per_sweep,slowest_seconds_per_sweep):
    n=split['training_epochs'];future=split['prediction_epochs']
    if (type(n) is not int or type(future) is not int or n<2 or future<1
            or n!=2*(n+future)//3 or not isinstance(split['segment_id'],str)
            or not split['segment_id']):
        raise ValueError('valid fixed chronological split required')
    times=[split[k] for k in ('first_training_time_s','last_training_time_s',
        'first_prediction_time_s','last_prediction_time_s')]
    if not all(math.isfinite(t) for t in times) or not all(a<b for a,b in zip(times,times[1:])):
        raise ValueError('finite ordered training/prediction intervals required')
    if (not math.isfinite(median_seconds_per_sweep) or not math.isfinite(slowest_seconds_per_sweep)
            or not 0<median_seconds_per_sweep<=slowest_seconds_per_sweep):
        raise ValueError('finite positive ordered runtime estimates required')
    covariances=[dict(name=f'h1_v3_tau{tau}',correlation_s=tau,
        white_sigma_neu_m=[.3,.3,.7],correlated_sigma_neu_m=[1.,1.,3.],
        offset_sigma_neu_m=[1.,1.,3.],drift_sigma_neu_m=[1.,1.,3.],calibrated=False)
        for tau in (10,300)]
    tasks=[dict(identity='::'.join((split['segment_id'],cov['name'],case,model)),
        covariance=cov['name'],processing_case=case,model=model,
        parameters=27 if case==CASES[1] else 26,
        maximum_starts=1,maximum_fit_sweeps=200,maximum_diagnostic_sweeps=55)
        for cov in covariances for case in CASES for model in MODELS]
    # Full-record diagnostic tangents cost more than training-prefix sweeps.
    # Value probes are charged at the same conservative tangent cost here.
    length_ratio=(times[-1]-times[0])/(times[1]-times[0])
    fit_ceiling=200*len(tasks);diagnostic_ceiling=55*len(tasks)
    runtime=dict(method='saved per-evaluation wall time; diagnostics scaled by duration ratio',
        training_seconds_per_sweep_median=median_seconds_per_sweep,
        training_seconds_per_sweep_slowest=slowest_seconds_per_sweep,
        full_to_training_duration_ratio=length_ratio,
        ceiling_minutes_at_median=(fit_ceiling+diagnostic_ceiling*length_ratio)*median_seconds_per_sweep/60,
        ceiling_minutes_at_slowest=(fit_ceiling+diagnostic_ceiling*length_ratio)*slowest_seconds_per_sweep/60,
        benchmark_of_new_objective=False,guaranteed_wall_time=False)
    return dict(version=VERSION,state='prepared_not_launchable',observed_allowance_authorized=False,
        split=dict(split),tasks=tasks,identities=[r['identity'] for r in tasks],
        covariances=covariances,maximum_starts=len(tasks),maximum_per_identity=1,retry_reserve=0,
        maximum_fit_sweeps=fit_ceiling,maximum_diagnostic_sweeps=diagnostic_ceiling,
        maximum_native_sweeps=fit_ceiling+diagnostic_ceiling,
        numerical_threads=2,workers=1,clock='header_elapsed',
        optimizer='frozen_original_fit_shape_candidate',integration='ordinary_increment',
        gyro_offset_limit_dph=1.,gyro_gain_limit_fraction=.02,
        estimate_covariance_from_candidate_residuals=False,
        covariance_policy='shared full-record covariance; training marginal; full-record drift anchor',
        receiver_covariance_calibrated=False,confidence_calibrated=False,
        prospective_validation=False,scientific_decision='abstain',
        diagnostics=dict(normalized_step=.01,remove_bound_columns=False,reoptimized_profiles=False,
            maximum_tangent_sweeps_per_fit=1,maximum_value_sweeps_per_fit=54,
            center_reused_from_tangent=True,
            feasible_probe_policy='center plus each permitted +/-.01 axis step; skip infeasible direction',
            failed_fit_policy='retain failed convergence label; diagnostics only for saved finite feasible center',
            uncertainty='descriptive local geometry and axis sensitivity; no calibrated intervals'),
        runtime_estimate=runtime)
