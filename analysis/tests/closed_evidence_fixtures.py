# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact local evidence dependencies of historical integration tests."""

from collections import defaultdict

# Node names are deliberately exact. Software controls and public evidence
# tests stay mandatory in both modes.
LOCAL_EVIDENCE = {
    'data/esa-error-law-cross-score-development-v1-20261114/completion.json': (
        ('test_esa_conditional_cross_point_study.py',
         'test_cross_point_requires_complete_bound_parents'),
    ),
    'data/esa-weighting-control-development-v1-20261114/completion.json': (
        ('test_esa_conditional_cross_point_study.py',
         'test_cross_point_requires_complete_bound_parents'),
    ),
    'data/esa-conditional-forecast-development-v3-20261114/completion.json': (
        ('test_esa_conditional_cross_point_study.py',
         'test_cross_point_requires_complete_bound_parents'),
        ('test_esa_cross_point_height_anatomy.py',
         'test_sealed_height_anatomy_keeps_failed_coverage'),
    ),
    'data/esa-conditional-cross-point-development-v1/completion.json': (
        ('test_esa_conditional_cross_point_v2_study.py',
         'test_cross_point_v2_preserves_failed_task_and_limits'),
        ('test_esa_conditional_cross_point_v3_study.py',
         'test_cross_point_v3_preserves_both_failed_attempts'),
    ),
    'data/esa-conditional-cross-point-development-v3/completion.json': (
        ('test_esa_cross_point_height_anatomy.py',
         'test_sealed_height_anatomy_keeps_failed_coverage'),
    ),
    'data/esa-conditional-cross-point-development-v2/completion.json': (
        ('test_esa_conditional_cross_point_v3_study.py',
         'test_cross_point_v3_preserves_both_failed_attempts'),
    ),
    'data/esa-observed-model-dispatch-globe-pairs-v2/completion.json': (
        ('test_esa_dispatch_start_equivalence_v2.py',
         'test_saved_esa_start_audit_replays_sealed_pairs'),
    ),
    'data/prediction-observed-development-continuation-v1-20261113-smoke-v3/completion.json': (
        ('test_esa_fixed_rate_propagation.py',
         'test_generated_smoke_reproduces_sealed_baseline_without_refit'),
        ('test_esa_fixed_rate_wide.py',
         'test_wide_kernel_reproduces_sealed_generated_baseline'),
    ),
    'data/esa-training-split-recheck-development-v1-20261115/completion.json': (
        ('test_esa_innovation_morphology.py',
         'test_saved_esa_morphology_retains_all_three_channels'),
        ('test_esa_training_quality_audit.py',
         'test_saved_quality_audit_uses_only_training_rows'),
    ),
    'data/esa-training-innovation-development-v1-20261115/completion.json': (
        ('test_esa_local_projection_null.py',
         'test_saved_esa_projection_control_uses_no_new_fit'),
    ),
    'data/esa-fit-adjusted-control-v1-20261115/completion.json': (
        ('test_esa_local_projection_null.py',
         'test_saved_esa_projection_control_uses_no_new_fit'),
        ('test_esa_oracle_control.py',
         'test_sealed_oracle_case_uses_original_measured_stream_and_only_early_receiver'),
    ),
    'data/generated-esa-bounded-full-fit-v2-20261117/completion.json': (
        ('test_generated_esa_bound_components_report.py',
         'test_saved_full_rank_pilot_is_calibration_width_dominated'),
        ('test_generated_esa_bounded_cohort_report.py',
         'test_sealed_pilot_artifacts_match_reporter_physical_schema'),
        ('test_generated_esa_bounded_cohort_report.py',
         'test_closed_cohort_keeps_all_eight_and_separate_outcomes'),
        ('test_generated_esa_calibration_recovery_report.py',
         'test_closed_generated_cases_remain_inaccurate_and_fit_calibration_differs'),
        ('test_generated_esa_calibration_substitution_report.py',
         'test_closed_native_substitution_preserves_both_original_paths'),
        ('test_generated_esa_calibration_substitution_study.py',
         'test_original_case_receipt_has_two_bound_aware_fits'),
        ('test_generated_esa_simultaneous_bound_report.py',
         'test_sealed_two_law_audit_preserves_physical_failures'),
        ('test_generated_esa_weak_direction_report.py',
         'test_closed_pilot_has_same_weak_axis_but_no_physical_pass'),
        ('test_generated_esa_weak_perturbation_report.py',
         'test_closed_weak_perturbation_is_small_beside_existing_path_miss'),
    ),
    'data/generated-esa-bounded-cohort-v1-20261117/completion.json': (
        ('test_generated_esa_bounded_cohort_report.py',
         'test_closed_cohort_keeps_all_eight_and_separate_outcomes'),
        ('test_generated_esa_noise_floor_audit.py',
         'test_closed_cohort_noise_floor_exceeds_inherited_screen'),
    ),
    'data/generated-esa-600-innovation-null-v1-20261117/completion.json': (
        ('test_generated_esa_path_error_audit.py',
         'test_closed_generated_pilot_audit_preserves_failed_outcomes'),
    ),
    'data/generated-matched-one-sided-v2-20261117/completion.json': (
        ('test_generated_joint_profile_replay.py',
         'test_replay_does_not_charge_reading_sealed_future'),
        ('test_generated_joint_replay_source.py',
         'test_sealed_straight_case_has_three_bound_candidates'),
        ('test_generated_joint_replay_source.py',
         'test_changed_numerical_environment_is_rejected'),
        ('test_generated_joint_saved_audit.py',
         'test_terminal_task_contains_three_complete_profiles_and_exact_receipts'),
    ),
    'data/generated-geometry-calibration-v1-20261117/completion.json': (
        ('test_generated_joint_saved_audit.py',
         'test_terminal_task_contains_three_complete_profiles_and_exact_receipts'),
        ('test_geometry_calibration_report.py',
         'test_nonconverged_turns_keep_failure_labels_and_saved_tangent_diagnostics'),
    ),
    'data/ilvis0-rolling-origin-development-v1/completion.json': (
        ('test_ilvis0_remaining_prediction_study.py',
         'test_historical_science_lock_accepts_only_audited_changes'),
    ),
    'data/ilvis0-remaining-prediction-transfer-20261118/completion.json': (
        ('test_ilvis0_remaining_prediction_study.py',
         'test_historical_science_lock_accepts_only_audited_changes'),
    ),
    'data/model-declared-paired-fit-20261115-v2/completion.json': (
        ('test_ilvis0_start_equivalence_study.py',
         'test_old_one_start_study_cannot_be_reinterpreted_as_two_start_release'),
    ),
    'data/model-declared-start-equivalence-v1/completion.json': (
        ('test_ilvis0_start_equivalence_v2_study.py',
         'test_v2_study_preserves_failed_parent_and_qualification'),
    ),
    'data/prediction-simultaneous-law-family-v3-runtime-20261112-continuation/freeze.json': (
        ('test_prediction_fitted_innovation_audit.py',
         'test_saved_generated_innovations_account_for_all_fits'),
    ),
    'data/prediction-simultaneous-law-family-v3-runtime-20261112/completion.json': (
        ('test_prediction_fitted_innovation_audit.py',
         'test_saved_generated_innovations_account_for_all_fits'),
    ),
    'data/prediction-simultaneous-law-family-v3-runtime-20261112-continuation/stage-000/completion.json': (
        ('test_prediction_fitted_innovation_audit.py',
         'test_saved_generated_innovations_account_for_all_fits'),
    ),
}


def missing_by_node(root, archived):
    """List only declared dependencies absent from both disk and the archive."""
    missing = defaultdict(list)
    for path, nodes in LOCAL_EVIDENCE.items():
        # A direct legacy lineage reader needs its expanded freeze JSON.
        if (root / path).is_file() or (path.endswith('/completion.json') and path in archived):
            continue
        for node in nodes:
            missing[node].append(path)
    return missing
