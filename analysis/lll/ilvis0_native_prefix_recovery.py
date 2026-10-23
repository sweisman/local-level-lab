# SPDX-License-Identifier: AGPL-3.0-or-later
"""Recover unretained cached reports using verified original and oracle records.

No cold-calculation or point-oracle callable is accepted. This adapter reuses
the common native batch implementation; it does not implement new physics.
"""


def recover(value,*,original_reports,native_records,prefix_kernels,reserve,charge,save,
            maximum_seconds,maximum_packet_steps,maximum_rss_bytes,checkpoint=lambda:None):
    import math
    import resource
    import time
    import numpy as np
    from .ilvis0_native_prefix import enclose_many
    from .ilvis0_native_prefix_long import batch_limits
    from .ilvis0_native_prefix_audit import check_saved_pair
    from .studies.artifacts import save_phase
    times=value['times'];n=len(value['dt'])
    if (len(times)!=2 or not times[0]<times[1] or len(original_reports)!=2 or len(native_records)!=2
            or type(maximum_packet_steps) is not int or maximum_packet_steps<=0
            or type(maximum_rss_bytes) is not int or maximum_rss_bytes<=0
            or not math.isfinite(maximum_seconds) or maximum_seconds<=0):
        raise ValueError('two fixed queries, finite resources and complete saved records required')
    for original,native,t in zip(original_reports,native_records,times,strict=True):
        check_saved_pair(original,original,native,expected_time=t)
    prepaid=dict(batch_limits(n),packet_steps=maximum_packet_steps);used={k:0 for k in prepaid}
    def check_resources():
        checkpoint()
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>maximum_rss_bytes:
            raise ValueError('frozen cached-recovery peak-memory allowance exceeded')
    def spend(**counts):
        for key,nvalue in counts.items():
            if (key not in used or type(nvalue) is not int or nvalue<=0
                    or used[key]+nvalue>prepaid[key]):raise ValueError('prepaid cached-recovery work exceeded')
        for key,nvalue in counts.items():used[key]+=nvalue
        if 'packet_steps' not in counts or used['packet_steps']%256==0:check_resources()
    check_resources();reserve(**prepaid);charge(bound_calls=1,bound_steps=9*maximum_packet_steps)
    save_phase(save,0,'cached recovery',times_s=list(times));started=time.monotonic()
    try:
        result=enclose_many(value['configuration'],value['theta'],value['dv'],value['dt'],times=times,
            lower=value['lower'],upper=value['upper'],reference=value['reference'],conditioning=value['conditioning'],
            prefix_kernels=prefix_kernels,maximum_packet_steps=maximum_packet_steps,reserve=spend,
            maximum_seconds=maximum_seconds)
    finally:
        elapsed=time.monotonic()-started
        save('batch-progress.json',dict(elapsed_s=elapsed,actual_prepaid_work=used,reservations=prepaid,
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
    reports=[bound.report() for bound in result['bounds']]
    for i,report in enumerate(reports):save(f'batched-{i:02d}.json',report)
    save('batch-work.json',dict(work=result['work'],actual_prepaid_work=used,reservations=prepaid,binding=result['binding']))
    if elapsed>maximum_seconds:raise ValueError('frozen cached-recovery time allowance exceeded')
    check_resources();checks=[]
    for i,(original,report,native,t,bound) in enumerate(zip(original_reports,reports,native_records,times,result['bounds'],strict=True)):
        checked=check_saved_pair(original,report,native,expected_time=t)
        actual=bound.design(np.asarray(native['jacobian'],float),value['reference'])
        if actual.shape!=(3,51) or not np.array_equal(actual,checked['matrix']):
            raise ValueError('cached native design differs from the 51 saved coefficient columns')
        save(f'design-{i:02d}.json',checked);checks.append(checked)
    return dict(passed=True,report_comparisons=len(checks),design_columns_checked=51,
        maximum_native_center_error_m=max(max(c['native_center_error_m']) for c in checks),
        native_calls=0,original_cold_calls=0,bound_calls=1,elapsed_s=elapsed,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        work=result['work'],original_reads=0,optimizer_starts=0,long_history_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
