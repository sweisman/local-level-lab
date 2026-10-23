# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independently audit original-fixture probes from sealed outputs only."""
import argparse
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
PUBLIC=Path(__file__).resolve().parent;DATA=ROOT/'data/ilvis0-truth-probes-20261021'
MATH_SOURCE=ROOT/'docs/ilvis0-ray-probes/audit_results.py'
spec=importlib.util.spec_from_file_location('_independent_position_arithmetic',MATH_SOURCE)
mathematics=importlib.util.module_from_spec(spec);spec.loader.exec_module(mathematics)


def recompute_native(native,point,observations,future_truth,scale):
    if native['status']!=0 or native['point']!=point['point']:
        raise ValueError('successful native calculation at the predeclared point required')
    return mathematics.recompute(native['prediction'],list(observations)+[future_truth],native['point'],scale)


def build():
    publication.check(DATA,PUBLIC);manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    if summary['completed']!=4 or not summary['passed']:raise ValueError('complete fixed four-task evidence required')
    inputs={};cache={}
    def read_path(path,expected=None):
        path=Path(path);digest=runner._sha(path)
        if expected is not None and digest!=expected:raise ValueError('sealed input changed')
        relative=str(path.relative_to(ROOT));inputs[relative]=digest
        if relative not in cache:cache[relative]=runner._load(path)
        return cache[relative]
    def reference(ref):return read_path(runner.path_within(ROOT,ref['path']),ref['sha256'])
    maximum=dict(truth_checks=6,lp_proposals=1,exact_primal_checks=1,point_constructions=3,
        physical_point_checks=81,future_column_products=243,queried_epochs=18,nonlinear_position_checks=54)
    groups={False:[],True:[]};bindings={};checked=[]
    for task in manifest['tasks']:
        identity=task['identity'];payload=task['payload'];profile=payload['profile']
        path=DATA/'shards'/format(task['shard'],'03d')/'results'/(identity+'.json')
        envelope=read_path(path);row=envelope['result']
        if not row['passed'] or envelope['charged']!=dict(native_calls=3,packet_visits=1728000,bound_calls=0,bound_steps=0):
            raise ValueError('complete fixed charges required')
        def artifact(name):
            relative='artifacts/'+identity+'/'+name
            return read_path(DATA/relative,envelope['artifacts'][relative])
        entry=manifest['inputs'][payload['bundle_key']];bundle=read_path(DATA/entry['path'],entry['sha256'])
        observations=reference(bundle['observations']);truth_records=[reference(r) for r in bundle['truth_records']]
        truth=truth_records[0]['point'];scale=payload['coordinate_scale']
        binding=(bundle['observations']['sha256'],tuple(r['sha256'] for r in bundle['truth_records']),tuple(scale))
        if profile in bindings and binding!=bindings[profile]:raise ValueError('mixed original observation fixtures')
        bindings[profile]=binding
        if (observations['times_s']!=[2.,10.,30.,180.,290.] or observations['allowance_m']!=1.
                or observations['future_observations_used'] is not False
                or any(r['status']!=0 or r['point']!=truth for r in truth_records)):
            raise ValueError('original noisy observations and common truth required')
        truth_check=mathematics.recompute([r['prediction'] for r in truth_records],
            observations['observations']+[truth_records[-1]['prediction']],truth,scale)
        if not truth_check['feasible']:raise ValueError('known truth violates actual training constraints')
        proposal=artifact('affine-proposal.json');z=list(map(F,proposal['point']))
        if len(z)!=27 or any(abs(v)>1 for v in z):raise ValueError('full in-box LP direction required')
        for record in truth_records[:-1]:
            for jac,unit in zip(record['jacobian'],scale,strict=True):
                change=sum((F(float(float(c)*float(unit)*.5))*v for c,v in zip(jac,z,strict=True)),F(0))
                if abs(change)>1:raise ValueError('exact saved affine direction violates proposal constraint')
        points=artifact('all-points-before-native.json')
        if not points['all_saved_before_outcomes'] or len(points['points'])!=3:raise ValueError('all predeclared points required')
        for ordinal,(point,ratio) in enumerate(zip(points['points'],('1/50','1/20','1/10'),strict=True)):
            expected=[float(F(float(t))+F(1,2)*F(ratio)*v) for t,v in zip(truth,z,strict=True)]
            if point['scale_exact']!=ratio or point['point']!=expected or point['original_truth']!=truth:
                raise ValueError('changed scale or displaced expansion')
            native=artifact(f'native-{ordinal:02d}.json')
            if len(native['prediction'])!=6:raise ValueError('all original query epochs required')
            result=recompute_native(native,point,observations['observations'],truth_records[-1]['prediction'],scale)
            saved=row['candidates'][ordinal]
            if (result['feasible']!=saved['nonlinear_training_feasible']
                    or result['training_max_axis_exact']!=saved['training_max_axis_exact']
                    or result['future_change_exact']!=saved['future_change_exact']
                    or saved['future_used_for_training_gate'] is not False):
                raise ValueError('independent actual-observation audit disagrees')
            item=dict(identity=identity,scale=ratio,profile=profile,**result);checked.append(item)
            if result['feasible']:groups[profile].append(item)
        counts=dict.fromkeys(maximum,0)
        for name in sorted(n for n in envelope['artifacts'] if Path(n).name.startswith('reservation-')):
            event=read_path(DATA/name,envelope['artifacts'][name])
            if any(k not in counts or type(v) is not int or v<1 for k,v in event['increase'].items()):
                raise ValueError('invalid reservation')
            counts={k:v+event['increase'].get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(counts[k]>maximum[k] for k in counts):raise ValueError('reservation mismatch')
        if counts!=maximum or row['work']!=maximum:raise ValueError('missing fixed diagnostic work')
    spans={}
    for profile,selected in groups.items():
        values=[[F(0)]*3]+[list(map(F,r['future_change_exact'])) for r in selected]
        widths=[max(v[i] for v in values)-min(v[i] for v in values) for i in range(3)]
        spans['profiled_removal' if profile else 'zero_removal']=dict(feasible_points=len(selected),
            width_exact=list(map(str,widths)),width_m=list(map(float,widths)),
            target_exceeded=[w>t for w,t in zip(widths,(20,20,50))])
    audit=dict(checked_points=12,feasible_points=sum(r['feasible'] for r in checked),rows=checked,spans=spans,
        original_observations_independently_checked=True,known_truth_retained=True,
        zero_reference_used=False,native_queries=0,optimizer_starts=0,outer_enclosure=False,
        observational_coverage_qualified=False,native_execution_error_qualified=False)
    lines=['# What the original-observation probes establish','',
        f"Independent exact arithmetic confirms {audit['feasible_points']}/12 candidate calibrations "
        'fit the original five perturbed training observations within ±1 metre. '
        'All twelve points, scales, forward outputs and charges are checked; '
        'failed training matches remain excluded from the spread. No trajectories are rerun.','',
        '| Processing | Accepted calibrations | Sampled N spread | Sampled E spread | Sampled height spread |',
        '|---|---:|---:|---:|---:|']
    for key,label in (('zero_removal','Zero removal'),('profiled_removal','Profiled removal')):
        values=spans[key];lines.append(f"| {label} | {values['feasible_points']}/6 | "+' | '.join(f'{v:.6f} m' for v in values['width_m'])+' |')
    if any(any(v['target_exceeded']) for v in spans.values()):
        lines+=['','At least one sampled spread exceeds its original width target. '
            'An interval containing those actual training-compatible numerical '
            'trajectories cannot meet that target for this generated fixture.']
    else:
        lines+=['','These sampled spreads do **not** exceed the original 20/20/50-metre '
            'targets. This test therefore does not establish that the targets are '
            'impossible for the original observations. It also does not prove them '
            'achievable: unexamined calibrations can produce a wider range. A useful '
            'outer enclosure remains necessary.']
    lines+=['','The earlier zero-reference fixture admitted 21.75 m north separation. '
        'Its observations and expansion were different. Neither its larger spread '
        'nor the smaller spreads here can be transferred between the problems.','',
        'The audit uses the actual stored observations, including their perturbations, '
        'rather than silently substituting the known truth or zero expansion. '
        'It independently recomputes nonlinear feasibility, verifies the LP primal '
        'directions and checks every fixed candidate construction. It does not assert '
        'exact optimization, native execution-error coverage, an aircraft error law '
        'or statistical significance.','',
        'The original long-record study continues unchanged. Its earlier wide-range '
        'failures remain failures; these sampled points do not replace its required '
        'whole-domain prediction bounds. The 53-stretch findings are unchanged.','',
        '[Every candidate](README.md) · [Frozen limits](PLAN.md) · '
        '[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md).']
    outputs={'independent-audit.json':json.dumps(audit,indent=2,sort_keys=True)+'\n',
        'INTERPRETATION.md':'\n'.join(lines)+'\n'}
    for name,text in outputs.items():(PUBLIC/name).write_text(text)
    for path in (Path(__file__),MATH_SOURCE,ROOT/'analysis/tests/test_ilvis0_truth_audit.py'):
        inputs[str(path.relative_to(ROOT))]=runner._sha(path)
    runner._replace(PUBLIC/'independent-audit-receipt.json',dict(inputs=inputs,
        outputs={n:runner._sha(PUBLIC/n) for n in outputs},native_queries=0,optimizer_starts=0))
    print('Independently checked all12 actual-fixture candidates, original observations and charges; zero native calls.')


def check():
    receipt=runner._load(PUBLIC/'independent-audit-receipt.json')
    for name,digest in receipt['inputs'].items():
        if runner._sha(runner.path_within(ROOT,name))!=digest:raise ValueError('audit input changed')
    for name,digest in receipt['outputs'].items():
        if runner._sha(PUBLIC/name)!=digest:raise ValueError('audit output changed')
    print('Verified actual-fixture audit hashes; no trajectory work.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    args=parser.parse_args();check() if args.check else build()
