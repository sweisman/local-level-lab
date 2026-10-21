# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check serial execution of unchanged preflight calculations and full reports."""


def evaluate(task,context):
    import time
    from lll.ilvis0_sharded_native import read
    from lll.ilvis0_direct_range_preflight import evaluate as original
    allocation=context.manifest['allocation']
    if allocation['workers']!=1 or allocation['threads']!=1:
        raise ValueError('one serial worker and one numerical thread required')
    wall=time.monotonic();cpu=time.process_time()
    try:result=original(task,context)
    except Exception as caught:
        context.save('serial-failure-timing.json',dict(evaluator_wall_s=time.monotonic()-wall,
            evaluator_cpu_s=time.process_time()-cpu,error_type=type(caught).__name__,reason=str(caught)))
        raise
    wall=time.monotonic()-wall;cpu=time.process_time()-cpu
    actual=read(context.directory/'bound.json');expected=read(context.input_path(task['payload']['exact_report_key']))
    differences=sorted(k for k in set(actual)|set(expected) if actual.get(k)!=expected.get(k))
    return dict(result,passed=result['passed'] and not differences,exact_report_match=not differences,
        differing_fields=differences,evaluator_wall_s=wall,evaluator_cpu_s=cpu,
        evaluator_cpu_to_wall_ratio=cpu/wall if wall>0 else None,
        execution_recipe_qualification=True,observational_coverage_qualified=False,scientific_decision='abstain')
