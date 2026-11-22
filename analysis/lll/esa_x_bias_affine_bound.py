# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact support-plane lower bound for the archived X-bias affine endpoint."""
import argparse
from contextlib import closing
from fractions import Fraction as F
import json
import math
import os
from pathlib import Path
import platform

from .compute_budget import environment
from .esa_calibration_contrast import WEIGHTS, WEIGHTS_SHA
from .esa_x_bias_position_replay import ID, MODELS
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_X_BIAS_AFFINE_BOUND_PLAN.md'
REPLAY = BASE+'esa-x-bias-position-replay-result.json'
OUT = BASE+'esa-x-bias-affine-bound-result.json'
REPLAY_SHA = '01560f7e7e6f7e5c880b87149fbb51a53b5f58964d701b60f5c92d5c29a12e23'


def affine_floor(residual, center, design, point, index):
    """Minimize the supporting plane over [-1,1] with the endpoint fixed."""
    r,c,x = (tuple(map(F,row)) for row in (residual,center,point))
    if len(c)!=len(x) or x[index]!=1 or any(abs(v)>1 for v in (*c,*x)) or len(r)!=len(design):
        raise ValueError('aligned feasible affine point with fixed endpoint required')
    step = tuple(a-b for a,b in zip(x,c,strict=True))
    columns = tuple(zip(*(tuple(map(F,row)) for row in design),strict=True))
    if len(columns)!=len(c):
        raise ValueError('unaligned affine design')
    values = [v+sum(a*b for a,b in zip(row,step,strict=True))
              for v,row in zip(r,zip(*columns,strict=True),strict=True)]
    gradient = [2*sum(a*b for a,b in zip(col,values,strict=True)) for col in columns]
    floor = sum(v*v for v in values)
    floor += sum(g*((-1 if g>=0 else 1)-v) for i,(g,v) in enumerate(zip(gradient,x)) if i!=index)
    return max(F(0),floor),sum(v*v for v in r)


def rounded_sqrt(value, *, upper):
    result = math.sqrt(float(value))
    while (F(result)**2 < value if upper else F(result)**2 > value):
        result = math.nextafter(result,math.inf if upper else 0.)
    return result


def build(study, replay):
    result = []
    for case, model in zip(replay['results'],MODELS,strict=True):
        fit = study.input(model+'-fit')
        names = fit['active_parameters']
        point = case['checks']['compensated']['normalized_point']
        if case['model']!=model or names!=case['original_parameter_names'] or len(point)!=27:
            raise ValueError('same compensated point and archived derivative required')
        local = fit['local_linearization']
        floor, nominal = affine_floor(
            local['residual'],fit['normalized_parameters'],local['jacobian'],point,names.index('accel_bias_x'))
        allow = nominal+F(case['earlier_loss_allowance'])
        gap = rounded_sqrt(floor,upper=False)-rounded_sqrt(allow,upper=True)
        result.append(dict(model=model, affine_squared_loss_lower=str(floor),
            nominal_squared_loss_exact=str(nominal),
            affine_loss_increase_lower=float(floor-nominal),
            necessary_nonlinear_residual_norm_lower=max(0.,math.nextafter(gap,-math.inf))))
    return dict(certificates=result,new_fits=0,new_native_calls=0,reserved_reads=0,
                nonlinear_bound_certified=False,scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('freeze','run'))
    args = parser.parse_args()
    threads = environment(threads=1)
    if any(os.environ.get(key)!=value for key,value in threads.items()):
        raise ValueError('one numerical thread required')
    root = Path.cwd()
    path = root/OUT
    binding = root/'data'/ID/'affine-bound-freeze.json'
    raw = (root/REPLAY).read_bytes()
    if digest(raw)!=REPLAY_SHA:
        raise ValueError('archived endpoint replay receipt differs')
    sources = [Path(__file__),root/PLAN,root/'analysis/tests/test_esa_x_bias_affine_bound.py',
               root/'analysis/lll/studies/closed.py',root/'analysis/lll/studies/artifacts.py']
    freeze = encoded(dict(replay=REPLAY_SHA,parent=WEIGHTS_SHA,sources={
            str(p.relative_to(root)):digest(p.read_bytes()) for p in sources},
        environment=dict(python=platform.python_version(),threads=threads),
        max_certificates=3,max_native_calls=0,max_fits=0))
    if args.action=='freeze' and not binding.exists():
        atomic(binding,freeze)
    if binding.read_bytes()!=freeze:
        raise ValueError('affine bound freeze differs')
    if args.action=='freeze':
        print(digest(freeze))
        return
    if not path.exists():
        with closing(ClosedStudy(root,WEIGHTS)) as study:
            if study.completion['manifest_sha256']!=WEIGHTS_SHA:
                raise ValueError('same archived earlier fits required')
            result = build(study,json.loads(raw))
            atomic(path,encoded(dict(freeze=json.loads(freeze),freeze_sha256=digest(freeze),
                                      result=result,result_sha256=digest(encoded(result)))))
    sealed = json.loads(path.read_bytes())
    if (sealed['freeze_sha256']!=digest(freeze) or digest(encoded(sealed['freeze']))!=digest(freeze)
            or digest(encoded(sealed['result']))!=sealed['result_sha256']):
        raise ValueError('sealed affine bound differs')
    print(sealed['result']['certificates'][0]['necessary_nonlinear_residual_norm_lower'])


if __name__=='__main__':
    main()
