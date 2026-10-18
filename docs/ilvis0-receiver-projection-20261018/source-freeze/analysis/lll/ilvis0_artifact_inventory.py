# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inspect declared primary artifacts without original reads or native integration."""
import gzip
import hashlib
import json
import math
from pathlib import Path

VERSION='ilvis0-primary-artifact-inventory-v1'
CASES=('bias1_unsubtracted','bias1_profiled_removal')
MODELS=('sphere_rotating','sphere_still','flat_still')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    data=Path(path).read_bytes()
    return json.loads(gzip.decompress(data) if str(path).endswith('.gz') else data)


def public_path(root,name):
    root=Path(root).resolve();path=Path(name)
    if path.is_absolute():
        if not path.is_relative_to(root):raise ValueError('artifact outside the declared checkout')
        path=path.relative_to(root)
    if '..' in path.parts:raise ValueError('unsafe artifact path')
    if path.parts[:1]==('data',):path=Path('docs',*path.parts[1:])
    result=root/path
    if not result.resolve().is_relative_to(root):raise ValueError('artifact escapes checkout')
    return result


def primary_fit(comparison,case_id,model):
    cases=comparison['cases']
    if len(cases)!=2 or {c['case_id'] for c in cases}!=set(CASES):raise ValueError('both unique processing cases required')
    for case in cases:
        fits=case['fits']
        if len(fits)!=3 or {f['model'] for f in fits}!=set(MODELS):raise ValueError('three unique declared primary models required')
    selected=next(f for c in cases if c['case_id']==case_id for f in c['fits'] if f['model']==model)
    if selected.get('converged') is not True:raise ValueError('current declared primary must have passed')
    return selected


def find_artifact(root,directory,fit,manifest,kind):
    name=fit.get(kind+'_file');digest=fit.get(kind+'_sha256')
    if name is None and digest is None:return None
    if not isinstance(name,str) or Path(name).name!=name or not isinstance(digest,str) or len(digest)!=64:
        raise ValueError('complete hashed artifact reference required')
    candidates=[Path(directory)/name]
    candidates.extend(public_path(root,p) for p,h in manifest.get('inputs',{}).items() if h==digest)
    for path in dict.fromkeys(candidates):
        if path.is_file():
            if sha(path)!=digest:raise ValueError('declared artifact hash mismatch: '+str(path))
            return path
    return None


def validate_payload(fit,saved,epochs,fixes):
    names=fit['active_parameters'];point=fit['normalized_parameters']
    if (fit.get('converged') is not True or saved['active_parameters']!=names or saved['normalized_parameters']!=point
            or not names or len(set(names))!=len(names) or len(point)!=len(names)
            or any(not math.isfinite(x) or abs(x)>1 for x in point)):
        raise ValueError('passing primary and exact finite parameter layout required')
    residual=saved['residual'];jac=saved['jacobian'];n=len(fixes)
    if (not n or len(residual)!=3*n or len(jac)!=3*n or any(len(row)!=len(names) for row in jac)
            or any(not math.isfinite(x) for x in residual) or any(not math.isfinite(x) for row in jac for x in row)):
        raise ValueError('finite complete residual and all Jacobian columns required')
    cost=math.fsum(x*x for x in residual);expected=fit['residual_sum_squares']
    if not math.isfinite(expected) or abs(cost-expected)>1e-10*max(cost,expected,1.):
        raise ValueError('saved objective disagrees with current primary')
    gps=[[f['latitude_rad'],f['longitude_rad'],f['height_m']] for f in fixes]
    if any(not math.isfinite(v) for row in gps for v in row):raise ValueError('finite receiver coordinates required')
    if 'gps' in saved and saved['gps']!=gps:raise ValueError('saved receiver positions disagree with selection')
    times=saved.get('times_s',None if epochs is None else epochs.get('times_s'))
    if (not isinstance(times,list) or len(times)!=n or any(not math.isfinite(x) for x in times)
            or any(b<=a for a,b in zip(times,times[1:]))):raise ValueError('complete ordered saved epoch times required')
    if epochs is not None and epochs['times_s']!=times:raise ValueError('saved epoch artifacts disagree')
    absolute=[f['time_s'] for f in fixes]
    if any(not math.isfinite(x) for x in absolute) or any(b<=a for a,b in zip(absolute,absolute[1:])):
        raise ValueError('complete ordered selected receiver times required')
    origin=absolute[0]-times[0];tolerance=8*math.ulp(max(abs(x) for x in absolute+times+[origin]))
    discrepancy=max(abs((a-t)-origin) for a,t in zip(absolute,times))
    if discrepancy>tolerance:raise ValueError('saved/selected epoch intervals do not share a constant origin')
    return dict(parameter_match=True,receiver_epochs=n,parameters=len(names),residual_count=len(residual),
        saved_cost=cost,embedded_receiver_context='gps' in saved and 'times_s' in saved,
        time_origin_s=origin,time_origin_maximum_difference_s=discrepancy,time_origin_roundoff_limit_s=tolerance,
        time_origin_is_independently_verified=False)
