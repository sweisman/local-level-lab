# SPDX-License-Identifier: AGPL-3.0-or-later
"""Disjoint proposed cohorts and combined gate; campaign machinery stays shared."""
import json
from lll import timing_prediction_release as previous,prediction_calibration_study as original

SCOPE='fresh feasible-anchor generated prediction calibration and validation; no original or protected observations'
PLAN='docs/FEASIBLE_CALIBRATION_RELEASE_PLAN.md'
ADAPTER='analysis/lll/feasible_prediction_release.py'
PARENT='docs/timing-matrix-completion'
GATE_REPORT_SHA256='e885e0cf411d24d8ac7b241f15332d89bc319b327423b65d06718be4a8bf6e5c'
GATE_SOURCE_SHA256='c5c18fa6689dd178d4989f2f86849530b2a3f85044bb24eddd916020085fafa4'
EXCLUDED_SEEDS=tuple(sorted(set(previous.EXCLUDED_SEEDS)|set(previous.recipe('calibration')['seeds'])|
    set(previous.recipe('validation')['seeds'])))
REQUIRED_SOURCES=previous.REQUIRED_SOURCES|{ADAPTER,'analysis/lll/timing_matrix_assembly.py'}
allowed_parent_updates=frozenset()
TESTS=['analysis/tests/'+name for name in ('test_feasible_prediction_release.py',
    'test_timing_prediction_release.py','test_prediction_timing_hooks.py',
    'test_compensated_prediction_release.py','test_prediction_calibration_study.py',
    'test_prediction_calibration_report.py','test_prediction_family_state.py')]
required_tests=previous.required_tests+[
    'test_feasible_release_binds_corrected_method_without_changing_physics_or_noise',
    'test_feasible_release_requires_exact_combined_gate_and_complete_source_binding[source]',
    'test_feasible_release_requires_exact_combined_gate_and_complete_source_binding[report_hash]',
    'test_feasible_release_validation_requires_its_own_complete_handoff',
    'test_feasible_release_delegates_same_preparer_executor_and_counted_scope',
    'test_feasible_release_disk_check_precedes_launch_and_charges[calibration-55]',
    'test_feasible_release_disk_check_precedes_launch_and_charges[validation-35]']
required_report_tests=previous.required_report_tests
audit_fit=previous.audit_fit


def identity(role):
    recipe(role)
    return 'prediction-'+role+'-feasible-20261028'


def recipe(role):
    r=previous.recipe(role);first=281474977410656 if role=='calibration' else 281474977510656
    return dict(r,version='feasible-prediction-release-v1',seeds=list(range(first,first+len(r['seeds']))),
        excluded_seeds=list(EXCLUDED_SEEDS))


def case_recipe(seed):
    if type(seed) is not int or not any(seed in recipe(role)['seeds'] for role in ('calibration','validation')):
        raise ValueError('one fresh preassigned feasible-release seed required')
    return dict(original._configured(seed),workers=4)


def tasks(role,population_sha256):
    return original.family_tasks(role,population_sha256,policy=recipe(role),case_provider=case_recipe)


def population(sources,environment):
    from lll.studies.artifacts import digest,encoded
    if not REQUIRED_SOURCES<=set(sources):raise ValueError('complete feasible-release scientific sources required')
    p=previous.population(sources,environment)
    p['descriptor'].update(version='feasible-prediction-population-v1',linear_initialization='feasible_anchor',
        linear_nonworsening_required=True)
    return dict(sha256=digest(encoded(p['descriptor'])),descriptor=p['descriptor'])


def policy():
    p=previous.policy()
    for name in ('recipe','tasks','case_recipe','population','EXCLUDED_SEEDS','SCOPE','qualification_sources'):
        setattr(p,name,globals()[name])
    p.plan=PLAN
    return p


def verify_optimizer_gate(report,binding,current,environment):
    from lll.studies.artifacts import digest,encoded
    if (digest(encoded(report))!=GATE_REPORT_SHA256 or report.get('qualified') is not True
            or report.get('cases')!=48 or report.get('start_pairs')!=24 or report.get('original_input_replays')!=4
            or report.get('shared_source_files')!=241 or report.get('all_shared_sources_identical') is not True
            or report.get('environment_identical') is not True or report.get('original_labels_changed') is not False
            or binding.get('completion')!=report.get('evidence',{}).get(PARENT)
            or digest(encoded(binding.get('sources',{})))!=GATE_SOURCE_SHA256
            or binding.get('environment')!=environment
            or any(current.get(k)!=v for k,v in binding['sources'].items())):
        raise ValueError('complete unchanged combined optimizer qualification required')


def optimizer_report(root):
    from lll.timing_matrix_assembly import inspect
    from lll.studies.artifacts import digest,encoded
    report=inspect(root)
    if digest(encoded(report))!=GATE_REPORT_SHA256:
        raise ValueError('exact qualified combined optimizer report required')
    return report


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
    return sorted(parents|set(source_closure(root,[ADAPTER,PLAN]+TESTS)))


def prepare(root,*,role,qualification,calibration=None):
    if role=='validation' and calibration is None:raise ValueError('closed fresh calibration handoff required')
    import sys
    from lll.compensated_prediction_release import prepare as shared
    return shared(root,role=role,qualification=qualification,calibration=calibration,definition=sys.modules[__name__])


def launch(root,*,role,reserved_threads):
    import shutil
    from pathlib import Path
    from lll.ilvis0_control_shards import launch as shared
    root=Path(root).resolve();minimum=recipe(role)['minimum_free_bytes']
    if shutil.disk_usage(root).free<minimum:
        raise ValueError(f'phase requires at least {minimum//2**30} GiB free disk before launch')
    return shared(root/'data'/identity(role),reserved_threads=reserved_threads)
