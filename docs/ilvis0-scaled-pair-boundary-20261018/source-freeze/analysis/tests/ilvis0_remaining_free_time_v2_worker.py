# SPDX-License-Identifier: AGPL-3.0-or-later
"""Use unique source locks; preserve the zero-start first preparation."""
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ilvis0_remaining_free_time_worker as parent

TEMPLATE=Path(parent.__file__)
OUTPUT=ROOT/'data/ilvis0-remaining-free-time-v2-20261018'
GUIDE=ROOT/'docs/ilvis0-remaining-free-time-v2-20261018'
VERSION='ilvis0-remaining-two-case-free-time-v2'


def lock_directories(*directories):
    """Retain lock order while acquiring a shared source only once."""
    return list(dict.fromkeys(Path(p).resolve() for p in directories))


def executor_source(source):
    source=parent.executor_source(source)
    old='for directory in (OUTPUT,PARENT,ENDPOINTS,CONTROLS):'
    if source.count(old)!=1:raise ValueError('unrecognized source lock loop')
    source=source.replace(old,'for directory in lock_directories(OUTPUT,PARENT,ENDPOINTS,CONTROLS):')
    old="'test_ilvis0_remaining_free_time_worker.py'"
    if source.count(old)!=1:raise ValueError('unrecognized qualification list')
    return source.replace(old,old+",'test_ilvis0_remaining_free_time_v2_worker.py'")


def build_executor():
    module=types.ModuleType('_ilvis0_remaining_free_time_v2_source')
    module.__file__=str(Path(__file__).resolve())
    source=TEMPLATE.read_text()
    old='plan=source_plan();values=sources()'
    if source.count(old)!=1:raise ValueError('unrecognized preparation source check')
    source=source.replace(old,'plan=source_plan();values=executor.sources()')
    exec(compile(source,str(TEMPLATE),'exec'),module.__dict__)
    module.OUTPUT=OUTPUT;module.GUIDE=GUIDE;module.VERSION=VERSION
    module.executor_source=executor_source
    executor=module.build_executor()
    executor.lock_directories=lock_directories;executor.TESTS=38
    executor.QUALIFICATION=OUTPUT/'software-controls-revised'
    previous_sources=executor.sources

    def sources():
        values=previous_sources()
        for name in ('analysis/tests/ilvis0_remaining_free_time_v2_worker.py',
                     'analysis/tests/test_ilvis0_remaining_free_time_v2_worker.py'):
            values[str(ROOT/name)]=parent.parent.sha(ROOT/name)
        executor.prior.check_hashes(values);return values

    executor.sources=sources
    return executor


if __name__=='__main__':build_executor().main()
