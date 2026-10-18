# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed-parameter receiver projections; never refit or relabel a model."""
import math
from .ilvis0_artifact_inventory import CASES,MODELS

VERSION='ilvis0-fixed-parameter-receiver-audit-v1'
VIEWS={'full':('latitude','longitude','height'),'horizontal':('latitude','longitude'),'height':('height',)}


def complete_groups(rows):
    groups={};identities=set();expected={(c,m) for c in CASES for m in MODELS}
    for row in rows:
        identity=(row['segment_id'],row['case_id'],row['model'])
        if identity in identities or identity[1:] not in expected:raise ValueError('unique declared case/model identities required')
        identities.add(identity);groups.setdefault(identity[0],[]).append(row)
    if not groups or any(len(values)!=6 for values in groups.values()):raise ValueError('all six inventory outcomes required per stretch')
    return {sid:sorted(values,key=lambda r:(r['case_id'],r['model'])) for sid,values in sorted(groups.items())
            if all(r['status']=='ready' for r in values)}


def assess(projection,residual,jacobian):
    import numpy as np
    r,j=projection.apply(residual,jacobian)
    singular=np.linalg.svd(j,compute_uv=False)
    cutoff=float(max(j.shape)*np.finfo(float).eps*singular[0]) if len(singular) else 0.
    return dict(cost=float(r@r),observations=len(r),columns=j.shape[1],
        numerical_rank=int(np.sum(singular>cutoff)),numerical_rank_cutoff=cutoff,
        singular_values=singular.tolist(),minimum_singular_value=float(singular[-1]) if len(singular) else None,
        normalized_residual_rms=float(np.sqrt(np.mean(r*r))),rank_is_diagnostic_only=True,
        reoptimized=False,scientific_decision='abstain')


def contrasts(rows):
    expected={(c,v,m) for c in CASES for v in VIEWS for m in MODELS}
    by_key={(r['case_id'],r['view'],r['model']):r for r in rows}
    if len(rows)!=len(expected) or set(by_key)!=expected:raise ValueError('all eighteen fixed-parameter projections required')
    if any(not math.isfinite(r['cost']) or r['cost']<0 for r in rows):raise ValueError('finite nonnegative objectives required')
    result=[]
    for case in CASES:
        for view in VIEWS:
            costs={m:by_key[(case,view,m)]['cost'] for m in MODELS}
            shape=costs['flat_still']-min(costs['sphere_rotating'],costs['sphere_still'])
            result.append(dict(case_id=case,view=view,flat_minus_globe_cost=shape,
                zero_minus_specified_field_cost=costs['sphere_still']-costs['sphere_rotating'],
                fixed_parameter_shape_preference='globe' if shape>0 else 'flat' if shape<0 else 'tie',
                not_reoptimized=True,scientific_decision='abstain'))
    return result
