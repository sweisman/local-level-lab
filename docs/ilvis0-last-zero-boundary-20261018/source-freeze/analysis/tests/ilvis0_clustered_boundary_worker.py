# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate clustered-boundary freeze, reusing the verified diagnostic executor."""
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ilvis0_profile_boundary_worker as parent

TEMPLATE=Path(parent.__file__)
OUTPUT=ROOT/'data/ilvis0-clustered-boundary-20261017'
GUIDE=ROOT/'docs/ilvis0-clustered-boundary-20261017'
LEFT_AUDIT=ROOT/'data/ilvis0-left-boundary-audit-20261017'
VERSION='ilvis0-full-cluster-boundary-diagnostic-v1'


def executor_source(source):
    """Checked plumbing changes only; preserve the frozen worker and gates."""
    edits=[
        ('from lll.ilvis0_exact_boundary import check_endpoint',
         'from lll.ilvis0_clustered_boundary import check_endpoint',1),
        ("time_index=list(full.bounds.active).index('time_offset'),geometry_at=geometry_at)",
         "time_index=list(full.bounds.active).index('time_offset'),geometry_at=geometry_at,times=times,packet_count=len(values),scale=full.bounds.limits['time_offset'])",1),
        ("'target',30)","'target',26)",2),
        ('maximum_native_evaluations=66','maximum_native_evaluations=58',3),
        ('maximum_geometry_queries=6144,maximum_affine_solves=14',
         'maximum_geometry_queries=402048,maximum_affine_solves=6',1),
        ('diagnostic_limit=30','diagnostic_limit=26',1),
        ('len(calls)>66','len(calls)>58',1),
        ("inputs=prior.scientific_inputs(parent['inputs'])",
         "inputs=prior.scientific_inputs(parent['inputs']);inputs.update(extra_inputs())",1),
        ('for directory in (OUTPUT,STOPPED,VERIFIED,AUDIT):',
         'for directory in (OUTPUT,STOPPED,VERIFIED,AUDIT,CLUSTER_PARENT,LEFT_AUDIT):',1),
        ("str(ROOT/'analysis/tests/test_ilvis0_exact_boundary.py')",
         "str(ROOT/'analysis/tests/test_ilvis0_clustered_boundary.py')",1),
        ("str(ROOT/'analysis/tests/test_ilvis0_profile_boundary_worker.py')",
         "str(ROOT/'analysis/tests/test_ilvis0_clustered_boundary_worker.py')",1),
        ('checked.update(geometry_queries=geometry_queries,geometry_checks=geometry_calls)',
         "checked.update(geometry_queries=checked['cluster_geometry_queries'],geometry_checks=int(bool(checked.get('clock_search')))+int(bool(checked.get('geometry'))))",1),
    ]
    for old,new,count in edits:
        if source.count(old)!=count:raise ValueError('unrecognized frozen executor layout: '+old)
        source=source.replace(old,new)
    return source


def build_executor():
    executor=types.ModuleType('_ilvis0_cluster_executor')
    # Detach must relaunch this wrapper, not the completed template study.
    executor.__file__=str(Path(__file__).resolve())
    exec(compile(executor_source(TEMPLATE.read_text()),str(TEMPLATE),'exec'),executor.__dict__)
    executor.OUTPUT=OUTPUT;executor.GUIDE=GUIDE
    executor.QUALIFICATION=OUTPUT/'software-controls';executor.VERSION=VERSION;executor.TESTS=12
    executor.CLUSTER_PARENT=parent.OUTPUT;executor.LEFT_AUDIT=LEFT_AUDIT
    original_sources=executor.sources;original_plan=executor.make_plan

    def sources():
        values=original_sources()
        for name in ('analysis/lll/ilvis0_clustered_boundary.py','analysis/tests/ilvis0_clustered_boundary_worker.py',
                     'analysis/tests/test_ilvis0_clustered_boundary.py','analysis/tests/test_ilvis0_clustered_boundary_worker.py'):
            values[str(ROOT/name)]=executor.sha(ROOT/name)
        executor.prior.check_hashes(values)
        return values

    def make_plan(*args):
        result=original_plan(*args)
        for task in result['tasks']:task['identity']+='::cluster_search_v1'
        result.update(search='existing complete-cluster negative-to-positive bracket search',
            maximum_clock_window_s=1e-6,final_stopping_rule_changed=False)
        return result

    def extra_inputs():
        values={}
        for runtime,public in ((parent.OUTPUT,parent.GUIDE),(LEFT_AUDIT,ROOT/'docs'/LEFT_AUDIT.name)):
            executor.prior.sealed(runtime,published=public)
            for name in ('manifest.json','summary.json','completion.json'):
                values[str(runtime/name)]=executor.sha(runtime/name)
            values[str(public/'evidence-receipt.json')]=executor.sha(public/'evidence-receipt.json')
        return values

    executor.sources=sources;executor.make_plan=make_plan;executor.extra_inputs=extra_inputs
    return executor


if __name__=='__main__':build_executor().main()
