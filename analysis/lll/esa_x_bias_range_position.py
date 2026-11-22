# SPDX-License-Identifier: AGPL-3.0-or-later
"""Earlier affine fit constraints on the whole unresolved X-bias range."""
import argparse
from contextlib import closing
from fractions import Fraction as F
import json
import math
import os
from pathlib import Path
import platform

from .calibration_loss_support import support
from .compute_budget import environment
from .esa_x_bias_affine_bound import WEIGHTS, WEIGHTS_SHA, rounded_sqrt
from .esa_x_bias_direction_profile import REPORT as DIRECTION
from .esa_x_bias_position_replay import EXACT_ALLOWANCE, ID, MODELS
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

FOLDER = 'docs/prediction-observed-development/'
PLAN = FOLDER+'ESA_X_BIAS_RANGE_POSITION_PLAN.md'
REPORT = FOLDER+'esa-x-bias-range-position-result.json'
DIRECTION_SHA = '3f5900438199a4f47854e55294e2fd1576b1d808c62180d860eb8a22d9f33105'


def certify_box(residual,center,jacobian,point,lower,upper):
    """Minimize one exact supporting plane on an arbitrary closed box."""
    r,base,x,lo,hi = (tuple(map(F,row)) for row in (residual,center,point,lower,upper))
    step = [value-reference for value,reference in zip(x,base,strict=True)]
    if (len(r)!=len(jacobian) or any(not a<=b<=c for a,b,c in zip(lo,x,hi,strict=True))):
        raise ValueError('complete affine point in its restricted box required')
    design = [tuple(map(F,row)) for row in jacobian]
    path = [v+sum(a*b for a,b in zip(row,step,strict=True)) for v,row in zip(r,design,strict=True)]
    gradient = [2*sum(a*b for a,b in zip(col,path,strict=True)) for col in zip(*design,strict=True)]
    floor = sum(v*v for v in path)
    floor += sum(g*((a if g>=0 else c)-b) for g,a,b,c in zip(gradient,lo,x,hi,strict=True))
    return max(F(0),floor),sum(v*v for v in r)


def compare(study,boundary):
    import numpy as np
    from scipy.optimize import lsq_linear

    limit = study.input('recipe')['limits']['accel_bias_x']
    if not 0<boundary<limit or limit!=.1:
        raise ValueError('positive directional boundary must be inside the sealed X allowance')
    results = []
    for model in MODELS:
        fit = study.input(model+'-fit')
        local = fit['local_linearization']
        axis = fit['active_parameters'].index('accel_bias_x')
        center = np.asarray(fit['normalized_parameters'],float)
        j = np.asarray(local['jacobian'],float)
        residual = np.asarray(local['residual'],float)
        if (len(center)!=27 or residual.shape!=(1200,) or j.shape!=(len(residual),len(center))
                or np.any(abs(center)>1.) or not all(np.isfinite(a).all() for a in (center,residual,j))):
            raise ValueError('exact earlier weighted calibration design required')
        goal = np.zeros(len(center))
        goal[axis] = 1.
        support_bound = support(j,residual,goal,-1.-center,1.-center,budget=EXACT_ALLOWANCE)
        lo,hi = -np.ones(len(center)),np.ones(len(center))
        lo[axis] = math.nextafter(boundary/limit,-math.inf)
        proposed = lsq_linear(j,-residual,bounds=(lo-center,hi-center),
                              method='bvls',tol=1e-12,max_iter=100)
        point = np.clip(center+proposed.x,lo,hi)
        floor,nominal = certify_box(residual,center,j,point,lo,hi)
        required = rounded_sqrt(floor,upper=False)-rounded_sqrt(
            nominal+F(EXACT_ALLOWANCE),upper=True)
        maximum = F(limit)*(F(float(center[axis]))+F(support_bound['upper_bound']))
        max_bias = min(limit,math.nextafter(float(maximum),math.inf))
        results.append(dict(model=model,nominal_x_bias_mps2=float(limit*center[axis]),
            maximum_affine_bias_upper_mps2=max_bias,
            affine_bias_witness_mps2=float(limit*(center[axis]+support_bound['achieved'])),
            affine_support=support_bound,restricted_squared_loss_lower_exact=str(floor),
            previous_squared_loss_exact=str(nominal),
            restricted_loss_increase_lower=math.nextafter(float(floor-nominal),-math.inf),
            needed_nonlinear_residual_norm_lower=max(0.,math.nextafter(required,-math.inf)),
            affine_proposal_settled=bool(proposed.success),affine_proposal_iterations=int(proposed.nit),
            restricted_proposal=point.tolist(),parameter_names=fit['active_parameters']))
    return dict(results=results,minimum_restricted_x_bias_mps2=boundary,
        affine_proposals=3,support_calculations=3,new_fits=0,new_native_calls=0,reserved_reads=0,
        nonlinear_remainder_certified=False,scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('freeze','run'))
    args = parser.parse_args()
    threads = environment(threads=1)
    if any(os.environ.get(k)!=v for k,v in threads.items()):
        raise ValueError('one numerical thread required')
    import numpy as np
    import scipy

    root = Path.cwd()
    direction = json.loads((root/DIRECTION).read_bytes())['result']
    if digest(encoded(direction))!=DIRECTION_SHA:
        raise ValueError('same sealed directional boundary required')
    sources = [Path(__file__),root/PLAN,root/'analysis/tests/test_esa_x_bias_range_position.py']
    sources.extend(root/'analysis/lll'/name for name in (
        'calibration_loss_support.py','esa_x_bias_affine_bound.py','esa_x_bias_direction_profile.py',
        'compute_budget.py','studies/artifacts.py','studies/closed.py'))
    manifest = encoded(dict(inputs=dict(weights=WEIGHTS_SHA,direction=DIRECTION_SHA),
        sources={str(p.relative_to(root)):digest(p.read_bytes()) for p in sources},
        environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
            os=platform.system(),arch=platform.machine(),threads=threads),
        max_proposals=3,max_proposal_iterations=100,max_support_searches=3,max_support_iterations=200,
        max_native_calls=0,max_fits=0))
    binding = root/'data'/ID/'range-position-freeze.json'
    if args.action=='freeze' and not binding.exists():
        atomic(binding,manifest)
    if binding.read_bytes()!=manifest:
        raise ValueError('earlier affine range freeze differs')
    if args.action=='freeze':
        print(digest(manifest))
        return
    path = root/REPORT
    charge = binding.with_name('range-position-charge.json')
    allowance = encoded(dict(manifest_sha256=digest(manifest),affine_proposals=3,support_searches=3))
    if not path.exists():
        with closing(ClosedStudy(root,WEIGHTS)) as study:
            if study.completion['manifest_sha256']!=WEIGHTS_SHA or study.completion['state']!='complete':
                raise ValueError('original closed weighted fit archives required')
            if charge.exists():
                raise ValueError('earlier affine ranges already charged')
            atomic(charge,allowance)
            result = compare(study,direction['common_globe_interval_through_zero_mps2'][1])
            atomic(path,encoded(dict(freeze=json.loads(manifest),freeze_sha256=digest(manifest),
                result=result,result_sha256=digest(encoded(result)))))
    saved = json.loads(path.read_bytes())
    if (charge.read_bytes()!=allowance or saved['freeze_sha256']!=digest(manifest)
            or digest(encoded(saved['freeze']))!=digest(manifest)
            or digest(encoded(saved['result']))!=saved['result_sha256']):
        raise ValueError('sealed earlier affine range result differs')
    print('Three earlier affine ranges, SHA-256 '+saved['result_sha256'])


if __name__=='__main__':
    main()
