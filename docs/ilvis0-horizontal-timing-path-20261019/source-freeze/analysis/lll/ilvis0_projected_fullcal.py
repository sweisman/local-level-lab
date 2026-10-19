# SPDX-License-Identifier: AGPL-3.0-or-later
"""Full 26/27-column generated controls; no archival data or decisions."""
from . import ilvis0_projected_trust_qualification as preceding


def tasks():
    rows=[]
    for old in preceding.tasks():
        profile=old['clock']=='variable';case='bias1_profiled_removal' if profile else 'bias1_unsubtracted'
        label='horizontal' if len(old['axes'])==2 else 'height'
        rows.append(dict(old,clock='nominal',profile=profile,case_id=case,
            identity=f"{old['model']}-{case}-{label}-{old['start']}"))
    return rows


def problem(task,f,kernel,tangent):
    import numpy as np
    from . import ilvis0_shape as shape,ilvis0_estimator as estimator
    sigma=np.tile(.01/f['metric'],len(f['gps_times']))
    return shape.TangentProblem(f['theta'],f['dv'],f['dt'],f['gps_times'],f['gps'],np.diag(sigma*sigma),
        f['initial'],estimator.Bounds(shape.instrument_limits(1.)),fit_earth_removal=task['profile'],
        kernel=kernel,tangent_kernel=tangent,clock_hypothesis='nominal_200Hz',
        processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.0075,
        gravity_mps2=9.81,disc_radius_m=6371000.)


def truth_point(task,f,p):
    import numpy as np
    return np.array([-1. if name=='earth_removal' else f['truth'].get(name,0.)/p.bounds.limits[name]
                     for name in p.bounds.active])


def start(task,p):
    import numpy as np
    point=np.zeros(len(p.bounds.active)) if task['start']=='zero' else np.array([.02 if i%2==0 else -.02 for i in range(len(p.bounds.active))])
    if task['profile']:point[-1]=-1. if task['start']=='zero' else -.8
    return point


def assess_fit(row):return preceding.assess_fit(row)


def compare_pair(a,b):
    if a.get('case_id')!=b.get('case_id'):return dict(passed=False,reason='different_processing_cases')
    return preceding.compare_pair(a,b)
