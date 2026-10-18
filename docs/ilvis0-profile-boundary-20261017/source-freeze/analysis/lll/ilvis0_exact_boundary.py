# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check an exact timing knot without discarding movement from the saved source."""
import numpy as np
from . import ilvis0_boundary_followup as candidate
from .ilvis0_boundary_adapter import displacement_metrics

VERSION='ilvis0-source-preserving-exact-boundary-v1'


def check_endpoint(book,identity,native,model,point,saved_residual,physical_step,*,time_index,geometry_at):
    point=np.asarray(point,float);saved_residual=np.asarray(saved_residual,float)
    if saved_residual.ndim!=1 or not len(saved_residual) or not np.all(np.isfinite(saved_residual)):
        raise ValueError('finite preserved source residual required')
    cache={};relocation=None
    def evaluate(u,*,fresh=False):
        nonlocal relocation
        if not fresh:raise ValueError('fresh native checks required')
        value=book.call(identity,'diagnostic','tangent',native,u,model)
        if relocation is None:
            relocation=displacement_metrics(saved_residual,value[0],physical_step)
            if not relocation['passed']:raise ValueError('source-to-knot relocation not stable')
        cache[tuple(u)]=value
        return value
    result=candidate.check(point,evaluate,physical_step,time_index=time_index,geometry_at=geometry_at)
    selected=candidate.selected_evaluation(point,result,cache)
    result.update(source_relocation=relocation,center_native=selected,optimizer_starts=0,
        source_preservation_version=VERSION,original_labels_changed=False)
    if selected is not None:
        cumulative=displacement_metrics(saved_residual,selected[0],physical_step)
        result['cumulative_from_source']=cumulative
        if not cumulative['passed']:
            result.update(passed=False,reason='cumulative_from_saved_source_not_stable')
    return result
