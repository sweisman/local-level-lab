# SPDX-License-Identifier: AGPL-3.0-or-later
"""Retain every earlier necessary constraint during staged bound refinement.

This checks schema and set arithmetic, not the scientific validity or provenance
of supplied inequalities. There is no statistical coverage or fitting operation.
"""
from copy import deepcopy
from collections import Counter
import math


def _finite(values,size):
    return (isinstance(values,(list,tuple)) and len(values)==size
            and all(type(v) in (int,float) and math.isfinite(v) for v in values))


def _validate(region):
    required=('parameter_count','physical_parameter_count','shared_error_count','binding',
        'source_id','force_source_id','coordinate_scale','origin','center','arithmetic_allowance',
        'future_truth_used','lower','upper','inequality_design','inequality_upper')
    if not isinstance(region,dict) or any(key not in region for key in required):
        raise ValueError('complete source-bound necessary-constraint region required')
    n=region['parameter_count']; rows=region['inequality_design']
    if (type(n) is not int or n not in (51,78) or region['physical_parameter_count']!=27
            or region['shared_error_count']!=24 or region['future_truth_used'] is not False
            or any(not isinstance(region[k],str) or not region[k] for k in ('binding','source_id','force_source_id'))
            or any(not _finite(region[k],n) for k in ('center','lower','upper'))
            or any(a>b for a,b in zip(region['lower'],region['upper']))
            or not _finite(region['coordinate_scale'],3) or any(v<=0. for v in region['coordinate_scale'])
            or not _finite(region['origin'],3) or not _finite([region['arithmetic_allowance']],1)
            or region['arithmetic_allowance']<0. or not isinstance(rows,(list,tuple)) or not rows
            or any(not _finite(row,n) for row in rows) or not _finite(region['inequality_upper'],len(rows))):
        raise ValueError('finite full-dimensional necessary constraints without future truth required')


def merge(previous,fresh):
    """Intersect boxes and append rows, preserving shared reference coordinates.

    Earlier constraints remain necessary prerequisites for a bound conditioned
    on their region. No old inequality is weakened or replaced by a new one.
    """
    _validate(previous); _validate(fresh)
    invariant=('parameter_count','physical_parameter_count','shared_error_count','binding','source_id',
               'force_source_id','coordinate_scale','origin','center','arithmetic_allowance')
    if any(previous[k]!=fresh[k] for k in invariant):
        raise ValueError('staged reference, coordinate system, arithmetic or parameter directions changed')
    lower=[max(a,b) for a,b in zip(previous['lower'],fresh['lower'])]
    upper=[min(a,b) for a,b in zip(previous['upper'],fresh['upper'])]
    if any(a>b for a,b in zip(lower,upper)):
        raise ValueError('contradictory declared boxes; no feasible staged region')
    result=deepcopy(fresh)
    result.update(lower=lower,upper=upper,
        inequality_design=deepcopy(list(previous['inequality_design'])+list(fresh['inequality_design'])),
        inequality_upper=list(previous['inequality_upper'])+list(fresh['inequality_upper']),
        staged_constraints=dict(version='ilvis0-monotone-training-region-v1',
            previous_rows=len(previous['inequality_design']),added_rows=len(fresh['inequality_design']),
            all_prior_rows_preserved=True,all_physical_directions_preserved=True),
        observational_coverage_qualified=False,scientific_decision='abstain')
    return result


def merge_epochs(previous,fresh):
    """Append nonoverlapping native epochs while retaining their original rows.

    This keeps the 51-coordinate TrainingRegion shape. A later product extension
    can add its separate coordinates without discarding these constraints.
    """
    for region in (previous,fresh):
        _validate(region); times=region.get('times_s',[]); n=len(times)
        if (region['parameter_count']!=51 or not 1<=n<=256 or not _finite(times,n)
                or times[0]<0. or any(b<=a for a,b in zip(times,times[1:]))
                or not isinstance(region.get('design'),(list,tuple)) or len(region['design'])!=3*n
                or any(not _finite(row,51) for row in region['design'])
                or not _finite(region.get('target_lower'),3*n) or not _finite(region.get('target_upper'),3*n)
                or any(a>b for a,b in zip(region['target_lower'],region['target_upper']))
                or len(region['inequality_design'])!=6*n):
            raise ValueError('complete native epoch rows and 51 coordinates required')
        expected=Counter((tuple(row),limit) for row,limit in zip(region['design'],region['target_upper']))
        expected.update((tuple(-v for v in row),-limit) for row,limit in zip(region['design'],region['target_lower']))
        actual=Counter((tuple(row),limit) for row,limit in zip(region['inequality_design'],region['inequality_upper']))
        if actual!=expected:
            raise ValueError('native inequalities do not preserve the complete design and target bounds')
    if fresh['times_s'][0]<=previous['times_s'][-1] or len(previous['times_s'])+len(fresh['times_s'])>256:
        raise ValueError('later nonoverlapping training epochs within the declared finite support required')
    result=merge(previous,fresh)
    for key in ('times_s','design','target_lower','target_upper'):
        result[key]=deepcopy(list(previous[key])+list(fresh[key]))
    return result
