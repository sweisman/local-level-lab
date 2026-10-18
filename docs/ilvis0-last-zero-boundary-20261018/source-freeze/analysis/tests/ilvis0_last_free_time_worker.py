# SPDX-License-Identifier: AGPL-3.0-or-later
"""Release final-stretch timing from verified matched profile endpoints."""
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ilvis0_remaining_free_time_v2_worker as parent

TEMPLATE=Path(parent.parent.__file__)
PARENT=ROOT/'data/ilvis0-last-time-profile-20261018'
PARENT_GUIDE=ROOT/'docs/ilvis0-last-time-profile-20261018'
OUTPUT=ROOT/'data/ilvis0-last-free-time-20261018'
GUIDE=ROOT/'docs/ilvis0-last-free-time-20261018'
VERSION='ilvis0-last-two-case-free-time-v1'
SID='b4e44ddc0f130ecd45674c78'
CASES=parent.parent.CASES


def executor_source(source):
    source=parent.executor_source(source)
    edits=[("'test_ilvis0_remaining_free_time_v2_worker.py'",
            "'test_ilvis0_remaining_free_time_v2_worker.py','test_ilvis0_last_free_time_worker.py'"),
           ('../ilvis0-remaining-time-profile-20261018/RESULTS.md',
            '../ilvis0-last-time-profile-20261018/RESULTS.md')]
    for old,new in edits:
        if source.count(old)!=1:raise ValueError('unrecognized final free-time executor: '+old)
        source=source.replace(old,new)
    return source


def build_executor():
    module=types.ModuleType('_ilvis0_last_free_time_source')
    module.__file__=str(Path(__file__).resolve())
    source=TEMPLATE.read_text()
    old='plan=source_plan();values=sources()'
    if source.count(old)!=1:raise ValueError('unrecognized preparation source check')
    source=source.replace(old,'plan=source_plan();values=executor.sources()')
    exec(compile(source,str(TEMPLATE),'exec'),module.__dict__)
    module.PARENT=PARENT;module.PARENT_GUIDE=PARENT_GUIDE;module.SID=SID
    module.OUTPUT=OUTPUT;module.GUIDE=GUIDE;module.VERSION=VERSION
    module.executor_source=executor_source
    executor=module.build_executor()
    executor.lock_directories=parent.lock_directories;executor.case_groups=module.case_groups
    executor.TESTS=50
    previous_sources=executor.sources

    def sources():
        values=previous_sources()
        for name in ('analysis/tests/ilvis0_remaining_free_time_v2_worker.py',
                     'analysis/tests/test_ilvis0_remaining_free_time_v2_worker.py',
                     'analysis/tests/ilvis0_last_free_time_worker.py',
                     'analysis/tests/test_ilvis0_last_free_time_worker.py'):
            values[str(ROOT/name)]=parent.parent.parent.sha(ROOT/name)
        executor.prior.check_hashes(values);return values

    executor.sources=sources
    return executor


if __name__=='__main__':build_executor().main()
