# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite deterministic starts and selection, not a global-optimum certificate."""
import math

VERSION='ilvis0-fixed-timing-multistart-v1'


def starts(seed,names,timing_grid):
    seed=list(seed);names=list(names);grid=list(timing_grid)
    if (len(seed)!=len(names) or len(set(names))!=len(names) or names.count('time_offset')!=1
            or not grid or len(set(grid))!=len(grid)
            or any(not math.isfinite(x) or abs(x)>1 for x in [*seed,*grid])):
        raise ValueError('finite feasible full vector and unique timing grid required')
    index=names.index('time_offset');result=[]
    for time in grid:
        u=seed.copy();u[index]=time;result.append(u)
    return result


def select(rows,*,expected_ids):
    expected=list(expected_ids);identities=[r['identity'] for r in rows]
    if (not expected or len(expected)!=len(set(expected)) or len(identities)!=len(set(identities))
            or set(identities)!=set(expected)):
        raise ValueError('every unique predeclared start must be retained')
    for row in rows:
        fit=row.get('fit',{});cost=fit.get('residual_sum_squares')
        point=fit.get('normalized_parameters')
        if (type(cost) not in (int,float) or not math.isfinite(cost) or cost<0
                or not point or any(not math.isfinite(x) or abs(x)>1 for x in point)
                or type(fit.get('converged')) is not bool):
            raise ValueError('complete finite feasible outcome required for every start')
    selected=min(rows,key=lambda r:(r['fit']['residual_sum_squares'],r['identity']))
    return dict(version=VERSION,selected_identity=selected['identity'],passed=selected['fit']['converged'],
        selected_cost=selected['fit']['residual_sum_squares'],attempted_identities=identities,
        all_starts_converged=all(r['fit']['converged'] for r in rows),
        global_optimum_established=False,scientific_decision='abstain')
