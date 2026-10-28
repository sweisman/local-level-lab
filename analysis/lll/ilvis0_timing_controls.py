# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent analytical objectives and declared answers; no archive inputs."""
import math
import numpy as np
from .ilvis0_solver_controls import ControlBounds

FIT_CASES=('interior','boundary','nonlinear','curved_redundant','kink_zero','kink_shifted',
           'timed_quadratic','timed_redundant27')
EXTRA_CASES=('timed_nonlinear',)
PROBES=('kink_minimum','shifted_minimum','ramp_zero','ramp_shifted','sharp_minimum',
        'physical_failure','repeat_failure','budget_failure')


def fit_reference(name):
    if name not in FIT_CASES+EXTRA_CASES:raise ValueError('declared analytical fit case required')
    if name in ('interior','nonlinear'):u=[.2,-.4];r=[0.,0.,1.];unique=True
    elif name=='boundary':u=[1.,-.4];r=[-.5,0.,1.];unique=True
    elif name=='curved_redundant':u=[.3,.3];r=[0.,0.,1.];unique=False
    elif name.startswith('kink_'):u=[.25 if name=='kink_shifted' else 0.];r=[15.];unique=False
    elif name=='timed_quadratic':u=[.2];r=[0.,1.];unique=True
    elif name=='timed_nonlinear':u=[0.];r=[1.,0.];unique=False
    else:u=[.3/math.sqrt(27)]*27;r=[0.,1.];unique=False
    return dict(optimum=u,residual=r,cost=1.25 if name=='boundary' else 225. if name.startswith('kink_') else 1.,
        unique=unique,objective_tolerance=3e-6 if name.startswith('kink_') else 1e-7,
        prediction_tolerance=1e-7 if name.startswith('kink_') else 1e-4,parameter_tolerance=1e-5)


def starts(n):
    signs=np.where(np.arange(n)%2,-1.,1.)
    return [np.zeros(n).tolist(),(-.8*signs).tolist(),(.6*signs).tolist(),(.9*signs).tolist()]


class TimedControl:
    def __init__(self,name,center,columns=1):
        self.name=name;self.center=center;self.calls=0;self.bounds=ControlBounds(columns)
        names=list(self.bounds.active);names[25 if columns==27 else 0]='time_offset'
        self.bounds.active=tuple(names);self.bounds.limits={'time_offset':.01}
        self.dt=np.array([.5+.01*center,.5,.5]);self.gps_times=np.array([.5])

    def residual_tangent(self,u,model):
        self.calls+=1;u=np.asarray(u,float);self.bounds.decode(u);column=self.bounds.active.index('time_offset')
        x=u[column];b=.01 if self.name=='sharp_minimum' else 1e-10 if self.name=='physical_failure' else 5e-5
        if self.name=='timed_quadratic':
            r=np.array([x-.2,1.]);j=np.zeros((2,len(u)));j[0,column]=1.
        elif self.name=='timed_redundant27':
            r=np.array([sum(u)/math.sqrt(27)-.3,1.]);j=np.zeros((2,27));j[0,:]=1/math.sqrt(27)
        elif self.name=='timed_nonlinear':
            r=np.array([1.,.001*(x+x**3)]);j=np.zeros((2,len(u)));j[1,column]=.001*(1+3*x*x)
        else:
            ramp=self.name in ('ramp_zero','ramp_shifted','physical_failure')
            r=np.array([15.+b*(x if ramp else abs(x-self.center))]);j=np.zeros((1,len(u)))
            j[0,column]=b*(1 if ramp or x>=self.center else -1)
            if self.name=='repeat_failure' and self.calls>1:r[0]+=1.
        return r,j,0


def problem_for(name):
    if name in FIT_CASES[:4]:
        from .ilvis0_boundary_controls import problem_for as legacy
        return legacy(name)[0]
    if name not in FIT_CASES+EXTRA_CASES+PROBES:raise ValueError('declared independent analytical control required')
    center=.25 if name in ('kink_shifted','shifted_minimum','ramp_shifted') else .2 if name=='timed_quadratic' else 0.
    if name=='timed_redundant27':center=.3/math.sqrt(27)
    return TimedControl(name,center,27 if name=='timed_redundant27' else 1)


def probe_reference(name):
    if name not in PROBES:raise ValueError('declared direct control required')
    reason=('all_timing_cells_stable' if name in ('kink_minimum','shifted_minimum') else
        'not_stationary' if name=='sharp_minimum' else 'baseline_not_repeatable' if name=='repeat_failure' else
        'budget_exhausted_before_solve' if name=='budget_failure' else 'timing_cell_not_stable')
    return dict(point=[.25 if name in ('shifted_minimum','ramp_shifted') else 0.],
        expected_acceptance=name in ('kink_minimum','shifted_minimum'),
        physical_scale=1e9 if name=='physical_failure' else 1.,expected_budget_rejection=name=='budget_failure',
        expected_reason=reason)
