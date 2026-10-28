# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh feasible-start qualification; reuse the shared analytical worker."""
from lll.timing_stopping_local_study import case_table,tasks

IDENTITY='timing-feasible-optimizer-qualification-20261027'
PLAN='docs/TIMING_FEASIBLE_OPTIMIZER_PLAN.md'
ADAPTER='analysis/lll/timing_feasible_study.py'
SCOPE='36 feasible-start analytical optimizer fits and eight direct probes; zero native or original observations'
TESTS=['analysis/tests/'+name for name in (
    'test_timing_feasible_study.py','test_timing_linear_report.py','test_timing_linear_diagnosis.py',
    'test_timing_cells.py','test_timing_cells_known_optimum.py','test_ilvis0_timing_stop.py',
    'test_timing_stopping_study.py','test_timing_stopping_report.py','test_timing_anchor_controls.py',
    'test_timing_intervals.py','test_timing_local_study.py','test_timing_cell_report.py',
    'test_timing_cell_study.py','test_timing_optimizer_hooks.py','test_prediction_timing_hooks.py')]


def configuration():
    from lll.timing_stopping_local_study import configuration as original
    return dict(original(),id=IDENTITY,scope=SCOPE)


def sources(root):
    from lll.studies.dependencies import source_closure
    from lll.timing_stopping_local_study import sources as original
    return source_closure(root,original(root)+[ADAPTER,PLAN]+TESTS)


def prepare(root,*,qualification):
    import sys
    from lll.timing_stopping_study import prepare as shared
    return shared(root,qualification=qualification,definition=sys.modules[__name__])


def evaluate(work,context):
    from lll.timing_stopping_study import run_task
    return run_task(work,context,scope=SCOPE,configuration=configuration(),cases=case_table(),tasks=tasks())
