# SPDX-License-Identifier: AGPL-3.0-or-later
"""Profile an unchanged complete-domain bound; preserve partial failures."""
from pathlib import Path


def evaluate(task,context):
    import cProfile,pstats,time
    from lll.ilvis0_direct_range_preflight import evaluate as original
    profiler=cProfile.Profile();result=None;error=None
    wall=time.monotonic();cpu=time.process_time();profiler.enable()
    try:result=original(task,context)
    except Exception as caught:error=dict(error_type=type(caught).__name__,reason=str(caught))
    finally:profiler.disable()
    wall=time.monotonic()-wall;cpu=time.process_time()-cpu
    statistics=pstats.Stats(profiler)
    functions=[dict(file=Path(k[0]).name,line=k[1],function=k[2],calls=v[1],self_time_s=v[2],cumulative_s=v[3])
        for k,v in statistics.stats.items()]
    native=[r for r in functions if r['file']=='ilvis0_direct_native.py' and r['function']=='enclose']
    source_calls=[r for r in functions if r['file']=='ilvis0_direct_source_taylor.py' and r['function']=='append']
    if len(native)>1 or len(source_calls)>1 or any(r['calls']>1600 for r in source_calls):
        raise ValueError('unexpected whole-profile invocation or source count')
    report=dict(identity=task['identity'],passed=result is not None and result['passed'],bound_completed=result is not None,
        error=error,wall_s=wall,process_cpu_s=cpu,cpu_to_wall_ratio=cpu/wall if wall>0 else None,
        bound_profile=native,source_prefix_profile=source_calls,
        functions=sorted(functions,key=lambda r:r['cumulative_s'],reverse=True)[:60],
        bound_evaluations=1 if native else 0,native_evaluations=0,original_reads=0,optimizer_starts=0,
        numerical_qualification=False,observational_coverage_qualified=False,scientific_decision='abstain')
    context.save('whole-profile.json',report)
    if result is not None:context.save('completed-preflight.json',result)
    return report
