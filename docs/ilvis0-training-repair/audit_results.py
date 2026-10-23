# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact saved-position audit. No native calls, SVD solves or optimization."""
import argparse
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
PUBLIC=Path(__file__).resolve().parent;DATA=ROOT/'data/ilvis0-training-repair-20261021'


def build():
    publication.check(DATA,PUBLIC);manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    if summary['completed']!=4 or not summary['passed']:raise ValueError('complete diagnostic required')
    sources={};inputs={};cache={}
    helper=ROOT/'docs/ilvis0-ray-probes/audit_results.py';sources[str(helper.relative_to(ROOT))]=runner._sha(helper)
    loader=importlib.util.spec_from_file_location('_repair_independent_positions',helper)
    module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module)
    def read(path,digest=None):
        path=Path(path);key=str(path.relative_to(ROOT));actual=runner._sha(path)
        if digest is not None and actual!=digest:raise ValueError('sealed audit input changed')
        inputs[key]=actual
        if key not in cache:cache[key]=runner._load(path)
        return cache[key]
    def ref(value):return read(runner.path_within(ROOT,value['path']),value['sha256'])
    rows=[]
    for task in manifest['tasks']:
        identity=task['identity'];spec=task['payload'];item=manifest['inputs'][spec['bundle_key']]
        pointer=read(DATA/item['path'],item['sha256']);bundle=ref(pointer['original_bundle']);seed=ref(pointer['seed'])
        observations=ref(bundle['observations']);truth=[ref(r) for r in bundle['truth_records']]
        envelope=read(DATA/'shards'/f'{task["shard"]:03d}'/'results'/(identity+'.json'));row=envelope['result']
        def artifact(name):
            relative='artifacts/'+identity+'/'+name
            return read(DATA/relative,envelope['artifacts'][relative])
        proposal=artifact('proposal-before-native.json')
        count=int(proposal['proposal_valid'])
        if envelope['charged']!=dict(native_calls=count,packet_visits=576000*count,bound_calls=0,bound_steps=0):
            raise ValueError('charged native count mismatch')
        if any(row.get(k)!=v for k,v in dict(physical_parameter_count=27,linear_solves=1,
                original_observations_used=True,future_observations_used=False).items()):
            raise ValueError('complete evidence semantics required')
        if not count:
            rows.append(dict(identity=identity,proposal_valid=False));continue
        point=proposal['point'];delta=proposal['correction']
        if (len(point)!=27 or len(delta)!=27 or any(abs(F(v))>1 for v in point)
                or max(map(lambda x:abs(F(x)),delta))>F(1,4)
                or any(float(F(a)+F(b))!=p for a,b,p in zip(seed['point'],delta,point,strict=True))):
            raise ValueError('original-box represented point construction mismatch')
        residual=[]
        for k in range(6):
            for axis in range(3 if k<5 else 1):
                j=seed['jacobian'][k][axis];unit=F(float(spec['coordinate_scale'][axis]))
                r=sum((F(float(v))*F(d) for v,d in zip(j,delta,strict=True)),F(0))
                if k<5:r+=F(seed['prediction'][k][axis])-F(truth[k]['prediction'][axis])
                residual.append(r*unit)
        if max(map(abs,residual))>F(1,1000):raise ValueError('exact linear proposal check failed')
        native=artifact('native.json')
        if native['status']!=0 or native['point']!=point:raise ValueError('successful nonlinear query at proposed point required')
        check=module.recompute(native['prediction'],observations['observations']+[truth[-1]['prediction']],
            point,spec['coordinate_scale']);candidate=row['candidate']
        if (check['feasible']!=candidate['nonlinear_training_feasible']
                or check['training_max_axis_exact']!=candidate['training_max_axis_exact']
                or check['future_change_exact']!=candidate['future_change_exact']):
            raise ValueError('independent exact feasibility disagreement')
        rows.append(dict(identity=identity,proposal_valid=True,**check))
    sources[str(Path(__file__).relative_to(ROOT))]=runner._sha(Path(__file__))
    return dict(rows=rows,feasible_points=sum(r.get('feasible',False) for r in rows),
        checked_points=sum(r['proposal_valid'] for r in rows),native_calls=0,linear_solves=0,
        inputs=inputs,sources=sources,observational_coverage_qualified=False,scientific_decision='abstain')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    target=PUBLIC/'independent-audit.json';result=build()
    if args.check:
        if runner._load(target)!=result:raise ValueError('saved exact audit changed')
        print('Verified independent saved-position audit.')
    else:runner._write(target,result);print('Saved independent audit; no native calls or linear solves.')
