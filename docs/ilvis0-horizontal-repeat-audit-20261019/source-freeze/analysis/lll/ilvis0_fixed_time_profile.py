# SPDX-License-Identifier: AGPL-3.0-or-later
"""Restricted nuisance profiles, never full free-time convergence decisions."""
import numpy as np

VERSION='ilvis0-fixed-time-profile-v1'


class FixedTimeProblem:
    profile_diagnostic_only=True

    def __init__(self,problem,anchor_normalized):
        anchor=float(anchor_normalized)
        if not np.isfinite(anchor) or abs(anchor)>1:
            raise ValueError('finite feasible fixed time required')
        self.problem=problem
        self.anchor=anchor
        self.full_active_parameters=tuple(problem.bounds.active)
        if self.full_active_parameters.count('time_offset')!=1 or len(self.full_active_parameters)<2:
            raise ValueError('one active time coordinate and at least one other parameter required')
        self.index=self.full_active_parameters.index('time_offset')
        self.keep=[i for i in range(len(self.full_active_parameters)) if i!=self.index]
        view=self
        class ReducedBounds:
            active=tuple(view.full_active_parameters[i] for i in view.keep)
            limits={k:v for k,v in problem.bounds.limits.items() if k!='time_offset'}
            def decode(self,point):return problem.bounds.decode(view.lift(point))
        self.bounds=ReducedBounds()
        self.bounds.decode(np.zeros(len(self.keep)))

    def lift(self,point):
        point=np.asarray(point,float)
        if point.shape!=(len(self.keep),) or not np.all(np.isfinite(point)) or np.any(abs(point)>1):
            raise ValueError('finite feasible nuisance point required')
        full=np.empty(len(self.full_active_parameters))
        full[self.keep]=point;full[self.index]=self.anchor
        return full

    def reduce(self,point):
        point=np.asarray(point,float)
        if (point.shape!=(len(self.full_active_parameters),) or not np.all(np.isfinite(point))
                or np.any(abs(point)>1) or point[self.index]!=self.anchor):
            raise ValueError('full point must retain the exact fixed time')
        return point[self.keep].copy()

    def residual_tangent(self,point,model):
        r,j,edges=self.problem.residual_tangent(self.lift(point),model)
        j=np.asarray(j,float)
        if j.shape!=(len(r),len(self.full_active_parameters)):
            raise ValueError('full native tangent shape changed')
        return r,j[:,self.keep],edges
