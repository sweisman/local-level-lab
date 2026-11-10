# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh host-service release declaration; all numerical execution stays shared."""
from lll import feasible_prediction_release as parent
from lll.studies.prediction_release import PredictionRelease

release=PredictionRelease(parent=parent,suffix='host-20261030',
    scope='fresh host-service generated prediction calibration and independent validation; no original or protected observations',
    plan='docs/HOST_CALIBRATION_RELEASE_PLAN.md',adapter='analysis/lll/host_prediction_release.py',
    optimizer_report_path='docs/timing-matrix-combined/artifacts/verified-report.json',
    first_seeds=(281474977610656,281474977710656),reporting_updates=((
        'analysis/lll/prediction_calibration_report.py',
        '8e6258c9799c1171d880999049b0e2f8da9ec6a38068dbbbe78ff2d3b7be3696',
        '05dba3d38a29e97dad1786c5b9f7b6766eac2a469c3da2fe807c37b625ab465a'),),
    tests=('analysis/tests/test_host_prediction_release.py','analysis/tests/test_study_recovery.py',
           'analysis/tests/test_execution_probe.py'),required_case_names=(
        'test_host_release_cohorts_and_caps_are_complete_and_disjoint[calibration-7176-281474977610656-281474977610954-240]',
        'test_host_release_cohorts_and_caps_are_complete_and_disjoint[validation-4344-281474977710656-281474977710836-144]',
        'test_host_release_preserves_the_qualified_physics_noise_and_stopping',
        'test_host_release_source_bridge_accepts_only_the_exact_reporting_update[None]',
        'test_host_release_reads_pinned_optimizer_evidence_and_checks_current_math',
        'test_host_release_cannot_exempt_a_numerical_file_from_qualification',
        'test_host_release_cannot_reuse_any_declared_cohort',
        'test_host_release_validation_requires_its_own_complete_handoff',
        'test_host_release_disk_and_recovery_guards_precede_launch[calibration-55]',
        'test_host_release_disk_and_recovery_guards_precede_launch[validation-35]',
        'test_host_release_uses_the_shared_preparer_and_qualified_executor',
        'test_handoff_rejects_interrupted_cohort_even_with_finite_draw_scores',
        'test_split_shard_lost_start_pair_prevents_futile_calibration_resume',
        'test_completion_during_lock_acquisition_takes_precedence',
        'test_probe_honors_existing_cooperative_stop_without_a_signal'))

evaluate=release.evaluate
