# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh cohorts and timing-method policy; campaign/scoring remain shared."""
import json
from lll import compensated_prediction_release as previous,prediction_calibration_study as original
from lll.timing_optimizer_native_study import NUMERICAL

SCOPE='fresh local-timing generated prediction calibration and independent validation; no original or protected inputs'
PLAN='docs/TIMING_CALIBRATION_RELEASE_PLAN.md'
ADAPTER='analysis/lll/timing_prediction_release.py'
PARENT='docs/timing-local-matrix'
GATE_MANIFEST='c0d20eb55199c1a797b5a7adc5d5f5527c1d99577049884709dd44fc1684e415'
GATE_SUMMARY='82008e4be330a9fa465236a9d3edde6ef874f4d1af20e30b78d46e18c2957565'
EXCLUDED_SEEDS=tuple(sorted(set(previous.EXCLUDED_SEEDS)|set(previous.recipe('calibration')['seeds'])|
    set(previous.recipe('validation')['seeds'])|{281474976810725,281474976810726,281474977010692,281474977010693}))
REQUIRED_SOURCES=previous.REQUIRED_SOURCES|frozenset(NUMERICAL)|{ADAPTER,
    'analysis/lll/timing_optimizer_native_study.py','analysis/lll/prediction_calibration_report.py'}
allowed_parent_updates=frozenset(('analysis/lll/prediction_calibration_study.py',
    'analysis/lll/prediction_calibration_report.py','analysis/lll/compensated_prediction_release.py',
    'analysis/lll/timing_optimizer_native_study.py','docs/TIMING_LOCAL_MATRIX_PLAN.md',
    'docs/COMPENSATED_CALIBRATION_PLAN.md'))
required_tests=['test_timing_release_population_binds_method_without_changing_inputs',
    'test_timing_release_requires_complete_hash_bound_optimizer_gate[source]',
    'test_timing_release_handoff_cannot_use_either_earlier_cohort',
    'test_timing_release_validation_requires_handoff_before_preparation',
    'test_timing_release_delegates_shared_campaign_and_counted_scope',
    'test_campaign_case_context_validates_before_scoring_and_preserves_failure[True]',
    'test_original_calibration_defaults_match_frozen_reference_exactly',
    'test_calibration_worker_preserves_exception_without_retry',
    'test_handoff_rejects_unexecuted_calibration_draws',
    'test_validation_futility_stops_at_fifth_distinct_family_not_four',
    'test_timing_release_audit_checks_real_journal_and_full_profile_columns[26]',
    'test_timing_release_audit_checks_real_journal_and_full_profile_columns[27]',
    'test_timing_release_disk_preflight_precedes_any_worker_or_charge[calibration-55]',
    'test_timing_release_disk_preflight_precedes_any_worker_or_charge[validation-35]']
required_report_tests=['test_closed_report_audits_explicit_method_without_relabeling[False]',
    'test_closed_report_audits_explicit_method_without_relabeling[True]',
    'test_timing_release_audit_checks_real_journal_and_full_profile_columns[26]',
    'test_timing_release_audit_checks_real_journal_and_full_profile_columns[27]']


def identity(role):
    recipe(role)
    return 'prediction-'+role+'-timing-20261027'


def recipe(role):
    r=previous.recipe(role);first=281474977210656 if role=='calibration' else 281474977310656
    return dict(r,version='timing-prediction-release-v1',seeds=list(range(first,first+len(r['seeds']))),
        excluded_seeds=list(EXCLUDED_SEEDS),maximum_wall_s=(240 if role=='calibration' else 144)*3600,
        minimum_free_bytes=(55 if role=='calibration' else 35)*2**30)


def case_recipe(seed):
    if type(seed) is not int or not any(seed in recipe(role)['seeds'] for role in ('calibration','validation')):
        raise ValueError('one fresh preassigned timing-release seed required')
    return dict(original._configured(seed),workers=4)


def tasks(role,population_sha256):
    return original.family_tasks(role,population_sha256,policy=recipe(role),case_provider=case_recipe)


def population(sources,environment):
    from lll.studies.artifacts import digest,encoded
    if not REQUIRED_SOURCES<=set(sources):raise ValueError('complete timing scientific sources required')
    p=previous.population(sources,environment)
    p['descriptor'].update(version='timing-prediction-population-v1',timing_method='native-clock-local-cells-v3',
        stopping_method='ilvis0-timing-cell-verification-v1',linear_solves_per_fit=620)
    return dict(sha256=digest(encoded(p['descriptor'])),descriptor=p['descriptor'])


def policy():
    from types import SimpleNamespace
    return SimpleNamespace(recipe=recipe,tasks=tasks,case_recipe=case_recipe,population=population,
        EXCLUDED_SEEDS=EXCLUDED_SEEDS,SCOPE=SCOPE,native_bindings=previous.native_bindings,
        qualification_sources=qualification_sources,plan=PLAN,audit_fit=audit_fit,
        required_report_tests=required_report_tests)


def verify_optimizer_gate(report,binding,current,environment):
    completion=binding.get('completion',{})
    if (report.get('verified') is not True or report.get('native_qualified') is not True
            or report.get('complete')!=48 or report.get('selected')!=48 or report.get('failures')
            or len(report.get('rows',[]))!=48 or len(report.get('pairs',[]))!=24
            or not all(r['passed'] for r in report['rows']+report['pairs'])
            or report.get('original_binding_replays_exact') is not True
            or report.get('manifest_sha256')!=GATE_MANIFEST or report.get('summary_sha256')!=GATE_SUMMARY
            or completion.get('manifest_sha256')!=GATE_MANIFEST or completion.get('summary_sha256')!=GATE_SUMMARY
            or binding.get('environment')!=environment or not set(NUMERICAL)<=set(binding.get('sources',{}))
            or any(current.get(k)!=v for k,v in binding['sources'].items())):
        raise ValueError('complete unchanged timing optimizer qualification required')


def optimizer_report(root):
    from lll import timing_optimizer_matrix_study as definition
    from lll.timing_optimizer_native_report import inspect
    return inspect(root,PARENT,definition=definition)


def audit_fit(study,identity,spec):
    from lll.timing_optimizer_native_report import audit_verification
    from lll.airquantumgrav_geographic_report import construction_counts
    fit=study.artifact(identity,'fit.json')
    counts=construction_counts(study.artifact(identity,'timing-linear.sqlite',raw=True),
        study.completion['manifest_sha256'],identity,dict(linear_solves=620),complete=False)
    if fit['linear_solves']!=counts['linear_solves']:raise ValueError('timing linear accounting differs')
    return dict(audit_verification(fit,expected_columns=27 if spec['profile'] else 26),linear_solves=counts['linear_solves'])


def evaluate(task,context):
    from lll.airquantumgrav_inventory import environment
    from lll.coordinate_optimizer_study import kernels
    from lll.timing_optimizer_native_study import timing_case_context
    verify_optimizer_gate(json.loads(context.input_path('optimizer-gate').read_bytes()),
        json.loads(context.input_path('optimizer-binding').read_bytes()),context.manifest['sources'],environment())
    return original.evaluate(task,context,protocol=policy(),kernel_provider=kernels,case_context=timing_case_context)


def qualification_sources(root):
    from lll.studies.closed import ClosedStudy
    from lll.studies.dependencies import source_closure
    s=ClosedStudy(root,PARENT)
    try:parents=set(s.manifest['sources'])
    finally:s.close()
    own=[ADAPTER,PLAN,'analysis/tests/test_timing_prediction_release.py','analysis/tests/test_prediction_timing_hooks.py',
        'analysis/tests/test_compensated_prediction_release.py','analysis/tests/test_prediction_calibration_study.py',
        'analysis/tests/test_prediction_calibration_report.py','analysis/tests/test_prediction_family_state.py']
    return sorted(parents|set(source_closure(root,own)))


def prepare(root,*,role,qualification,calibration=None):
    if role=='validation' and calibration is None:raise ValueError('closed fresh calibration handoff required')
    import sys
    return previous.prepare(root,role=role,qualification=qualification,calibration=calibration,definition=sys.modules[__name__])


def launch(root,*,role,reserved_threads):
    """Launch an authorized prepared phase only after its disk-space preflight."""
    import shutil
    from pathlib import Path
    from lll.ilvis0_control_shards import launch as shared
    root=Path(root).resolve();minimum=recipe(role)['minimum_free_bytes']
    if shutil.disk_usage(root).free<minimum:
        raise ValueError(f'phase requires at least {minimum//2**30} GiB free disk before launch')
    return shared(root/'data'/identity(role),reserved_threads=reserved_threads)
