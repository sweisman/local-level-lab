# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independently recompute sealed ray feasibility; no native calls or fits."""
import argparse
from fractions import Fraction as F
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
PUBLIC=Path(__file__).resolve().parent
DATA=ROOT/'data/ilvis0-ray-probes-20261021'


def recompute(prediction,baseline,point,scale):
    if (len(prediction)<2 or len(prediction)!=len(baseline) or len(point)!=27 or len(scale)!=3
            or any(len(row)!=3 for row in (*prediction,*baseline))
            or any(not math.isfinite(float(v)) for v in (*point,*scale,
                *(v for row in (*prediction,*baseline) for v in row)))
            or any(abs(F(float(p)))>1 for p in point) or any(F(float(s))<=0 for s in scale)):
        raise ValueError('complete finite positions, in-box physical point and positive scales required')
    values=[[(F(float(v))-F(float(b)))*F(float(s)) for v,b,s in zip(row,base,scale,strict=True)]
        for row,base in zip(prediction,baseline,strict=True)]
    maxima=[max(abs(row[i]) for row in values[:-1]) for i in range(3)]
    return dict(training_max_axis_exact=list(map(str,maxima)),future_change_exact=list(map(str,values[-1])),
        feasible=all(v<=1 for v in maxima),training_margin_exact=str(1-max(maxima)))


def build():
    publication.check(DATA,PUBLIC);manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    if summary['completed']!=12 or not summary['passed']:raise ValueError('complete twelve-ray evidence required')
    inputs={};cache={}
    def read_path(path,expected=None):
        path=Path(path);relative=str(path.relative_to(ROOT));digest=runner._sha(path)
        if expected is not None and digest!=expected:raise ValueError('sealed audit input changed')
        inputs[relative]=digest
        if relative not in cache:cache[relative]=runner._load(path)
        return cache[relative]
    def reference(ref):return read_path(runner.path_within(ROOT,ref['path']),ref['sha256'])
    maximum=dict(proposals=1,training_column_products=23652,saved_training_checks=876,search_steps=48,
        point_checks=27,future_column_products=81,queried_epochs=293,position_checks=879)
    groups={False:[],True:[]};bindings={};rows=[]
    for task in manifest['tasks']:
        identity=task['identity'];spec=task['payload'];profile=spec['profile']
        result_path=DATA/'shards'/format(task['shard'],'03d')/'results'/(identity+'.json')
        envelope=read_path(result_path);row=envelope['result']
        if not row['passed'] or envelope['charged']!=dict(native_calls=1,packet_visits=28128000,bound_calls=0,bound_steps=0):
            raise ValueError('complete charged native result required')
        def artifact(name):
            relative='artifacts/'+identity+'/'+name
            return read_path(DATA/relative,envelope['artifacts'][relative])
        native=artifact('native-raw.json');point=artifact('point-before-native.json')
        record=manifest['inputs'][spec['bundle_key']];bundle=read_path(DATA/record['path'],record['sha256'])
        baseline=reference(bundle['baseline'])
        binding=(bundle['baseline']['sha256'],tuple(spec['coordinate_scale']))
        if profile in bindings and binding!=bindings[profile]:raise ValueError('mixed zero-reference fixtures')
        bindings[profile]=binding
        if native['status']!=0 or baseline['status']!=0 or native['point']!=point['point']:
            raise ValueError('native success at the predeclared represented point required')
        if len(native['prediction'])!=293 or len(baseline['prediction'])!=293:
            raise ValueError('complete original 293 epochs required')
        check=recompute(native['prediction'],baseline['prediction'],point['point'],spec['coordinate_scale'])
        if (check['training_max_axis_exact']!=row['training_max_axis_exact']
                or check['future_change_exact']!=row['future_change_exact']
                or check['feasible']!=row['nonlinear_training_feasible']
                or row['future_used_for_training_gate'] is not False):
            raise ValueError('independent exact numerical check disagrees')
        counts=dict.fromkeys(maximum,0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=read_path(DATA/name,envelope['artifacts'][name])
            if any(k not in counts or type(v) is not int or v<1 for k,v in event['increase'].items()):
                raise ValueError('invalid auxiliary reservation')
            counts={k:v+event['increase'].get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(counts[k]>maximum[k] for k in counts):
                raise ValueError('auxiliary accounting mismatch')
        if counts!=maximum or row['work']!=maximum:raise ValueError('incomplete fixed diagnostic work')
        checked=dict(identity=identity,profile=profile,**check);rows.append(checked)
        if check['feasible']:groups[profile].append(checked)
    spans={}
    for profile,selected in groups.items():
        candidates=[dict(identity='zero-reference',future_change_exact=['0']*3)]+selected;axes=[]
        for axis,target in enumerate((20,20,50)):
            values=[(F(r['future_change_exact'][axis]),r['identity']) for r in candidates]
            low,low_id=min(values);high,high_id=max(values);width=high-low
            axes.append(dict(width_exact=str(width),width_m=float(width),target_m=target,target_exceeded=width>target,
                minimum_witness=low_id,maximum_witness=high_id))
        spans['profiled_removal' if profile else 'zero_removal']=axes
    audit=dict(checked_points=len(rows),all_feasible=all(r['feasible'] for r in rows),
        minimum_training_margin_m=float(min(F(r['training_margin_exact']) for r in rows)),rows=rows,spans=spans,
        original_reads=0,native_queries=0,optimizer_starts=0,outer_uncertainty_bound=False,
        native_execution_error_qualified=False,observational_coverage_qualified=False)
    lines=['# What the nonlinear ray test establishes','',
        'An independent saved-data audit confirms that all twelve scaled calibrations '
        'stay within the original parameter box and satisfy the ±1-metre constraint '
        'at every one of the 292 earlier epochs. It recomputes the differences from '
        'the sealed positions using exact rational arithmetic; it does not reuse '
        'the study’s feasibility calculation. No trajectories are rerun.','',
        '| Processing | North spread | East spread | Height spread |',
        '|---|---:|---:|---:|']
    for name,label in (('zero_removal','Zero removal'),('profiled_removal','Profiled removal')):
        values=spans[name];lines.append('| '+label+' | '+' | '.join(f"{v['width_m']:.6f} m" for v in values)+' |')
    lines+=['','The zero-removal north spread exceeds the frozen 20-metre width target. '
        'An interval containing all of these training-compatible numerical trajectories '
        'cannot be 20 metres wide. Thus conservative bounding is not the only obstacle '
        'in this generated coordinate-box fixture. A more accurate interval algorithm '
        'cannot erase the demonstrated separation.','',
        'This is not a result for the separate running study’s perturbed observations, '
        'nor a universal failure of withheld prediction. An observation model with '
        'additional justified joint constraints is a different problem and must be '
        'tested as such. The smaller sampled spreads in the other coordinates are '
        'not upper bounds and do not establish unique prediction.','',
        'The accepted points have at least '
        f"{audit['minimum_training_margin_m']:.6f} m of margin inside the training limit. "
        'The recorded native integrator produced the trajectories; exact auditing of '
        'its outputs does not itself prove its floating-point execution error. '
        'There is no aircraft fit, detection significance or change to the 53-stretch findings.','',
        'The original limits remain unchanged. Further work should distinguish what '
        'the training data can constrain from the overestimation introduced by an '
        'enclosure, and justify the observation-error model before new aircraft '
        'prediction fits.','',
        '[All numerical outcomes](README.md) · [Frozen scope](PLAN.md) · '
        '[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md).']
    outputs={'independent-audit.json':json.dumps(audit,indent=2,sort_keys=True)+'\n',
        'INTERPRETATION.md':'\n'.join(lines)+'\n'}
    for name,text in outputs.items():(PUBLIC/name).write_text(text)
    inputs[str(Path(__file__).relative_to(ROOT))]=runner._sha(Path(__file__))
    test=ROOT/'analysis/tests/test_ilvis0_ray_audit.py';inputs[str(test.relative_to(ROOT))]=runner._sha(test)
    receipt=dict(inputs=inputs,outputs={n:runner._sha(PUBLIC/n) for n in outputs},native_queries=0,optimizer_starts=0)
    runner._replace(PUBLIC/'independent-audit-receipt.json',receipt)
    print('Independently verified all12 points and fixed charges; zero native evaluations.')


def check():
    receipt=runner._load(PUBLIC/'independent-audit-receipt.json')
    for name,digest in receipt['inputs'].items():
        if runner._sha(runner.path_within(ROOT,name))!=digest:raise ValueError('audit input changed')
    for name,digest in receipt['outputs'].items():
        if runner._sha(PUBLIC/name)!=digest:raise ValueError('audit output changed')
    print('Verified independent audit hashes; no trajectory evaluations.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    args=parser.parse_args();check() if args.check else build()
