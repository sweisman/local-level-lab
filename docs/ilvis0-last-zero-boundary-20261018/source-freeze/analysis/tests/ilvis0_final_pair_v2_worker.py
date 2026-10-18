# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separately frozen metadata correction; completed trial sources stay immutable."""
import gzip
import json
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ilvis0_final_pair_worker as parent

OUTPUT=ROOT/'data/ilvis0-final-pair-boundary-v2-20261018'
GUIDE=ROOT/'docs/ilvis0-final-pair-boundary-v2-20261018'
VERSION='ilvis0-final-profiled-pair-correct-context-v2'


def make_plan(*args):
    plan=parent.make_plan(*args);plan['version']=VERSION
    for task in plan['tasks']:
        old='::final_pair_representable_check'
        if not task['identity'].endswith(old):raise ValueError('unrecognized completed task identity')
        task['identity']=task['identity'][:-len(old)]+'::final_pair_context_v2_check'
    return plan


def source_context(task):
    from lll.ilvis0_saved_context import context_bytes
    arrays=[]
    for artifact in (task['original_linearization'],task['context_epoch']):
        if parent.sha(Path(artifact['path']))!=artifact['sha256']:raise ValueError('original saved context changed')
        with gzip.open(artifact['path'],'rt') as stream:arrays.append(json.load(stream))
    payload=context_bytes(*arrays,task['task']['selected']['segment']['receiver_fixes'],
        initial_time_s=task['task']['provenance']['first_interval_start_utc_s'])
    context=json.loads(gzip.decompress(payload))
    if (context['active_parameters']!=task['fit']['active_parameters']
            or context['normalized_parameters']!=task['fit']['normalized_parameters']):
        raise ValueError('saved endpoint parameters changed')
    return payload


def sources():
    values=parent.sources()
    for name in ('analysis/lll/ilvis0_saved_context.py','analysis/tests/test_ilvis0_saved_context.py',
        'analysis/tests/ilvis0_final_pair_v2_worker.py','analysis/tests/test_ilvis0_final_pair_v2_worker.py'):
        values[str(ROOT/name)]=parent.sha(ROOT/name)
    return values


def executor_source(source):
    source=parent.executor_source(source)
    old="str(ROOT/'analysis/tests/test_ilvis0_final_pair_worker.py')"
    new="str(ROOT/'analysis/tests/test_ilvis0_final_pair_v2_worker.py'),str(ROOT/'analysis/tests/test_ilvis0_saved_context.py')"
    if source.count(old)!=1:raise ValueError('unrecognized frozen qualification command')
    return source.replace(old,new).replace('# Final profiled-pair boundary results','# Corrected-context pair results')


def build_executor():
    module=types.ModuleType('_final_pair_context_v2');module.__file__=str(Path(__file__).resolve())
    exec(compile(Path(parent.__file__).read_text(),str(Path(parent.__file__)),'exec'),module.__dict__)
    for key,value in dict(OUTPUT=OUTPUT,GUIDE=GUIDE,VERSION=VERSION,make_plan=make_plan,
            source_context=source_context,sources=sources,executor_source=executor_source).items():
        setattr(module,key,value)
    executor=module.build_executor();executor.source_context=source_context
    return executor


if __name__=='__main__':build_executor().main()
