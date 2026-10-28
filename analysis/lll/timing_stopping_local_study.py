# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local-anchor qualification definition; execution remains in shared components."""
IDENTITY='timing-local-qualification-20261027'
PLAN='docs/TIMING_ANCHOR_PLAN.md'
ADAPTER='analysis/lll/timing_stopping_local_study.py'
SCOPE='36 local-anchor analytical fits and eight direct controls; zero native, original or protected observations'


def configuration():
    from lll.timing_stopping_study import configuration as original
    return dict(original(),id=IDENTITY,scope=SCOPE,maximum_analytical_evaluations=7488,
        maximum_linear_solves=22500,maximum_fits=36)


def case_table():
    from lll.ilvis0_timing_controls import FIT_CASES,EXTRA_CASES
    from lll.timing_stopping_study import case_table as original
    return original(FIT_CASES+EXTRA_CASES)


def tasks():
    from lll.timing_stopping_study import tasks as original
    return original(case_table())


def sources(root):
    from lll.studies.dependencies import source_closure
    from lll.timing_stopping_study import sources as original
    return source_closure(root,original(root)+[ADAPTER,PLAN,'analysis/tests/test_timing_local_study.py',
        'analysis/tests/test_timing_anchor_controls.py'])


def prepare(root,*,qualification):
    import sys
    from lll.timing_stopping_study import prepare as shared
    return shared(root,qualification=qualification,definition=sys.modules[__name__])


def evaluate(work,context):
    from lll.timing_stopping_study import run_task
    return run_task(work,context,scope=SCOPE,configuration=configuration(),cases=case_table(),tasks=tasks())
