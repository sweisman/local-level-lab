# SPDX-License-Identifier: AGPL-3.0-or-later
"""Use a complete, verified local timing grid to seed an unchanged free fit."""
import copy
import math

VERSION='ilvis0-profile-seeded-free-time-v1'


def select_seed(profiles,anchors,active_parameters):
    names=list(active_parameters);anchors=list(anchors)
    if (names.count('time_offset')!=1 or len(anchors)<2 or len(set(anchors))!=len(anchors)
            or any(not math.isfinite(t) or abs(t)>1 for t in anchors)
            or len(profiles)!=len(anchors)):
        raise ValueError('complete finite distinct timing grid and full parameter order required')
    index=names.index('time_offset');found=[]
    for row in profiles:
        point=row['normalized_parameters'];anchor=row['anchor_normalized'];cost=row['cost']
        if (row['conditional_passed'] is not True or row['active_parameters']!=names
                or len(point)!=len(names) or any(not math.isfinite(x) or abs(x)>1 for x in point)
                or point[index]!=anchor or anchor not in anchors or anchor in found
                or not math.isfinite(cost) or cost<0):
            raise ValueError('all profile points must be verified, compatible and feasible')
        found.append(anchor)
    if set(found)!=set(anchors):raise ValueError('incomplete profile coverage')
    return copy.deepcopy(min(profiles,key=lambda row:(row['cost'],row['anchor_normalized'])))


def fit_candidate(problem,model,*,profiles,anchors,maximum_evaluations=80,physical_step=None):
    from . import ilvis0_solver_trust_v2 as solver
    selected=select_seed(profiles,anchors,problem.bounds.active)
    result=solver.fit_candidate(problem,model,start=selected['normalized_parameters'],
        maximum_evaluations=maximum_evaluations,physical_step=physical_step)
    result.update(profile_seed_version=VERSION,selected_profile=selected,
        searched_timing_anchors=list(anchors),free_time_converged=bool(result['converged']),
        global_optimum_proven=False,search_scope='supplied verified local grid; full original timing bound restored')
    return result
