# SPDX-License-Identifier: AGPL-3.0-or-later
"""Source-preserving entry point to the existing complete-cluster timing search."""
import numpy as np
from . import ilvis0_boundary_adapter as adapter,ilvis0_boundary_followup as followup

VERSION='ilvis0-source-preserving-cluster-search-v1'


def check_endpoint(book,identity,native,model,point,saved_residual,physical_step,*,time_index,
                   geometry_at,times,packet_count,scale):
    point=np.asarray(point,float);saved_residual=np.asarray(saved_residual,float)
    if saved_residual.ndim!=1 or not len(saved_residual) or not np.all(np.isfinite(saved_residual)):
        raise ValueError('finite saved source residual required')
    cache={};original=None
    def fresh(u,*,fresh=True):
        nonlocal original
        if not fresh:raise ValueError('fresh cluster checks required')
        value=book.call(identity,'diagnostic','tangent',native,u,model)
        if original is None:
            original=adapter.displacement_metrics(saved_residual,value[0],physical_step)
            if not original['passed']:raise ValueError('saved source prediction changed')
        cache[tuple(u)]=value;return value
    result=adapter.diagnose(point,fresh,physical_step,time_index=time_index,times=times,
        packet_count=packet_count,scale=scale,maximum_evaluations=26)
    result.setdefault('normalized_parameters',point.tolist())
    selected=followup.selected_evaluation(point,result,cache)
    result.update(source_relocation=original,center_native=selected,optimizer_starts=0,
        source_preservation_version=VERSION,original_labels_changed=False,
        cluster_geometry_queries=result.get('clock_search',{}).get('clock_queries',0)+result.get('geometry',{}).get('queries',0))
    if selected is not None:
        cumulative=adapter.displacement_metrics(saved_residual,selected[0],physical_step)
        result['cumulative_from_source']=cumulative
        if not cumulative['passed']:result.update(passed=False,reason='cumulative_from_saved_source_not_stable')
    return result
