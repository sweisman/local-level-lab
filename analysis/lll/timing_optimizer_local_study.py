# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local timing native regression policy; original shared evaluator is reused."""
IDENTITY='timing-local-native-regression-20261027'
PLAN='docs/TIMING_LOCAL_NATIVE_PLAN.md'
ADAPTER='analysis/lll/timing_optimizer_local_study.py'
SCOPE='four exposed original-start local-anchor optimizer regressions; no calibration, original or protected data'
GATE='docs/timing-local-qualification'
GATE_MANIFEST='a12cc5870f3c6f9d13d17eedc2d64b4de8e1d99a039a7733588a6908658f72b5'
GATE_SUMMARY='4f47717597a2fc4226c2216e782e820dd9f2abe59005545ae610f070991b8648'


def configuration():
    from lll.timing_optimizer_native_study import configuration as original
    return dict(original(),id=IDENTITY,scope=SCOPE)


def tasks():
    from lll.timing_optimizer_native_study import tasks as original
    return original()


def verify_gate(report,binding,current,environment):
    from lll.timing_optimizer_native_study import verify_gate as shared
    return shared(report,binding,current,environment,expected=dict(complete=44,fit_passed=36,pairs=9,
        manifest_sha256=GATE_MANIFEST,summary_sha256=GATE_SUMMARY))


def gate_report(root):
    from lll import timing_stopping_local_study as definition
    from lll.timing_stopping_report import inspect
    return inspect(root,GATE,definition=definition)


def sources(root):
    from lll.timing_optimizer_native_study import sources as original
    from lll.studies.dependencies import source_closure
    return source_closure(root,original(root)+[ADAPTER,PLAN,'analysis/tests/test_timing_local_native_study.py'])


def prepare(root,*,qualification):
    import sys
    from lll.timing_optimizer_native_study import prepare as shared
    return shared(root,qualification=qualification,definition=sys.modules[__name__])


def evaluate(task,context):
    import sys
    from lll.timing_optimizer_native_study import run_task
    return run_task(task,context,definition=sys.modules[__name__])
