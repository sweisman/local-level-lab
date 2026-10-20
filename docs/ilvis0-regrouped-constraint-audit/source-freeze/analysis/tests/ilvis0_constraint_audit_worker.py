# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite saved-constraint projection audit; never predict or fit native data."""
import argparse
import csv
from fractions import Fraction as F
import io
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment
if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with one worker and four threads')
import ilvis0_streaming_worker as base
from lll import ilvis0_constraint_projection as audit
from lll.ilvis0_shape import PARAMETERS

NAME='ilvis0-regrouped-constraint-audit-20261020';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-regrouped-constraint-audit'
UPSTREAM=ROOT/'docs/ilvis0-regrouped-cover'
TASKS=[dict(identity=f'constraint-{m}-{int(p)}-{s}',kind='saved-constraint',
    source_identity=f'regrouped-sector-{m}-{int(p)}-{s}') for m in range(3) for p in (False,True) for s in range(8)]
LIMITS=dict(base.LIMITS,maximum_identities=48,maximum_native_evaluations=0,maximum_packet_visits=0,
    maximum_lp_proposals=2592,maximum_exact_certificates=5184,maximum_wall_s=120)
SOURCE_NAMES=base.SOURCE_NAMES+['analysis/lll/ilvis0_constraint_projection.py','analysis/lll/ilvis0_affine_support.py',
    'analysis/tests/test_ilvis0_constraint_projection.py','analysis/tests/ilvis0_constraint_audit_worker.py',
    'analysis/tests/test_ilvis0_constraint_audit_worker.py','docs/ilvis0-regrouped-constraint-audit/PLAN.md']


def configure():
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=SimpleNamespace(evaluate=evaluate);base.publish=publish


def prepare():
    if DATA.exists():raise ValueError('audit freeze exists; never overwrite')
    receipt=base.load(UPSTREAM/'evidence-receipt.json')['artifacts']
    for name,digest in receipt.items():
        if base.sha(UPSTREAM/name)!=digest:raise ValueError('saved source artifact changed')
    manifest=base.load(UPSTREAM/'manifest.json');summary=base.load(UPSTREAM/'summary.json');complete=base.load(UPSTREAM/'completion.json')
    if (not summary['passed'] or complete['manifest_sha256']!=base.sha(UPSTREAM/'manifest.json')
            or complete['summary_sha256']!=base.sha(UPSTREAM/'summary.json')):raise ValueError('saved source study is not sealed/passing')
    support=ROOT/'data/ilvis0-affine-support-qualification-20261019';q=base.load(support/'manifest.json')
    qc=base.load(support/'completion.json');qs=base.load(support/'summary.json')
    if (not qs['passed'] or qc['manifest_sha256']!=base.sha(support/'manifest.json') or qc['summary_sha256']!=base.sha(support/'summary.json')
            or base.sha(ROOT/'analysis/lll/ilvis0_affine_support.py')!=q['sources']['analysis/lll/ilvis0_affine_support.py']):
        raise ValueError('qualified exact support prerequisite changed')
    baselines=base.load(UPSTREAM/manifest['inputs']['baselines']['path']);inputs={}
    for task in TASKS:
        source=next(r for r in summary['results'] if r['identity']==task['source_identity'])
        row=base.load(UPSTREAM/source['artifact'])
        if not row['passed'] or row.get('excluded'):raise ValueError('audit expects all retained passing sectors')
        training=base.load(UPSTREAM/('evidence/'+row['identity']+'-training.json.gz'))
        future=base.load(UPSTREAM/('evidence/'+row['identity']+'-future.json.gz'))
        case=base.load(UPSTREAM/manifest['inputs'][row['case_key']]['path'])
        payload=dict(source_result=row,training=training,future=future,truth=case['truth'],
            parameter_names=PARAMETERS,baseline_width_m=baselines[row['case_key']]['width_after_m'],source_sha256=source['artifact_sha256'])
        path='inputs/'+task['identity']+'.json.gz';base.write(DATA/path,payload);inputs[task['identity']]=dict(path=path,sha256=base.sha(DATA/path))
    paths=set(SOURCE_NAMES)
    paths.update(str(Path(m.__file__).resolve().relative_to(ROOT)) for name,m in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(ROOT))
    for name in paths:
        target=DATA/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    base.write(DATA/'manifest.json',dict(version=NAME,tasks=TASKS,limits=LIMITS,inputs=inputs,
        source_manifest_sha256=base.sha(UPSTREAM/'manifest.json'),source_receipt_sha256=base.sha(UPSTREAM/'evidence-receipt.json'),
        environment=base.environment(),numerical_environment=environment(threads=4),sources={n:base.sha(ROOT/n) for n in sorted(paths)},
        compilers={c:subprocess.check_output([c,'--version'],text=True).splitlines()[0] for c in ('cc','c++')}))
    base.write(DATA/'authorization.json',dict(scope='standing V01 saved generated-constraint diagnosis; zero native work',
        limits=LIMITS,manifest_sha256=base.sha(DATA/'manifest.json')))


def verify(current=False):
    manifest=base.verify(current=current)
    for record in manifest['inputs'].values():
        if base.sha(DATA/record['path'])!=record['sha256']:raise ValueError('frozen audit input changed')
    return manifest


def evaluate(task,directory,charge):
    manifest=verify();case=base.load(DATA/manifest['inputs'][task['identity']]['path']);row=case['source_result']
    constraints=case['training']['constraints'];lo=row['contraction']['lower'];hi=row['contraction']['upper'];truth=case['truth']
    base.write(DATA/'reservations'/(task['identity']+'.json'),dict(identity=task['identity'],lp_proposals=54,exact_certificates=108))
    start=base.load(DATA/'start.json')['started_unix'];calls=0
    def before():
        nonlocal calls
        if calls>=54 or time.time()-start>=120:raise ValueError('finite audit proposal/time allowance exhausted')
        calls+=1
    parameters=audit.project(lo,hi,constraints['inequality_design'],constraints['inequality_upper'],before_proposal=before)
    retained=True
    for parameter,name in zip(parameters,case['parameter_names']):
        parameter['parameter_name']=name
        if row['truth_in_sector']:
            value=F(float(truth[parameter['parameter_index']]))
            retained=retained and F(parameter['lower'])<=value<=F(parameter['upper'])
    if len(parameters)!=27 or len(case['parameter_names'])!=27:raise ValueError('a nuisance column disappeared')
    breakdown=audit.width_breakdown(row['future_lower_m'],row['future_upper_m'],row['future_remainder_after_m'],row['certificates'])
    targets=[v/10. for v in case['baseline_width_m']]
    return dict(identity=task['identity'],kind=task['kind'],passed=bool(retained),source_identity=row['identity'],case_key=row['case_key'],
        sector=row['task']['sector'],parameters=parameters,known_truth_checked=row['truth_in_sector'],known_truth_retained=bool(retained),
        width_breakdown=breakdown,tenfold_target_m=targets,
        nonlinear_floor_exceeds_target=[width>target for width,target in zip(breakdown['nonlinear_width_m'],targets)],
        lp_proposals=calls,exact_certificates=2*calls,parameter_count=27,
        original_reads=0,native_evaluations=0,optimizer_starts=0,scientific_decision='abstain')


def publish():
    manifest=verify();summary=base.load(DATA/'summary.json');PUBLIC.mkdir(parents=True,exist_ok=True)
    rows=[base.load(DATA/r['artifact']) for r in summary['results']]
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json']
    names += [r['artifact'] for r in summary['results']]+['source-freeze/'+n for n in manifest['sources']]
    names += [r['path'] for r in manifest['inputs'].values()]
    charged=manifest['tasks'][:summary['charged']['identities']]
    names += ['starts/'+t['identity']+'.json' for t in charged]+['reservations/'+t['identity']+'.json' for t in charged]
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-regrouped-constraint-audit/PLAN.md',PUBLIC/'PLAN.md')
    parameters=[dict(identity=r['identity'],source_identity=r['source_identity'],case_key=r['case_key'],sector=r['sector'],
        **{k:v for k,v in p.items() if not k.endswith('multipliers')}) for r in rows for p in r.get('parameters',[])]
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=list(parameters[0]) if parameters else ['identity'])
    writer.writeheader();writer.writerows(parameters);(PUBLIC/'parameters.csv').write_text(stream.getvalue())
    lines=['# Saved calibration-constraint audit','',f"{sum(r['passed'] for r in rows)}/{len(manifest['tasks'])} saved-sector audits pass; state: {summary['state']}.",'',
        'Every row preserves all 27 nuisance coordinates. These are generated calibration ranges under necessary constraints, '
        'not measured device performance or independent aircraft observations.','',
        '| Parameter | Sectors examined | Further narrowed | Median ratio to row-contracted width |','|---|---:|---:|---:|']
    for name in PARAMETERS:
        group=[p for p in parameters if p['parameter_name']==name]
        if group:lines.append(f"| {name} | {len(group)} | {sum(p['narrowed'] for p in group)} | {statistics.median(p['width_ratio'] for p in group):.6f} |")
    lines+=['','| Case | Sectors | Existing nonlinear floor exceeds target N / E / height |','|---|---:|---|']
    for key in dict.fromkeys(r.get('case_key') for r in rows):
        group=[r for r in rows if r.get('case_key')==key]
        flags=[sum(r['nonlinear_floor_exceeds_target'][i] for r in group) for i in range(3)]
        lines.append(f"| {key} | {len(group)} | {' / '.join(str(v) for v in flags)} |")
    lines+=['','A floor applies to the retained computed remainder, not to true aircraft uncertainty. '
        'Recomputing a rigorously smaller remainder could change it; a better linear optimizer alone cannot erase it. '
        'LP failure uses the qualified full-box fallback. No rank threshold drops unidentified columns.','',
        f"Reserved/used identities: {summary['charged']['identities']}/{len(rows)}; completed LP proposals: {sum(r.get('lp_proposals',0) for r in rows)}. "
        'Zero native integration, Earth-model fits or original-file reads.','',
        '[All parameter intervals](parameters.csv) · [Frozen scope](PLAN.md) · [Source comparison](../ilvis0-regrouped-cover/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    base.write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:base.sha(PUBLIC/n) for n in names+['README.md','PLAN.md','parameters.csv']}),replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__);g=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','check','package-only'):g.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 48 saved-constraint audit identities.')
    elif args.run:verify(True);base.run();print('Saved-constraint audit finished.')
    elif args.package_only:publish();print('Published saved audit without new proposals.')
    else:verify();print('Verified saved-constraint audit freeze/results.')


if __name__=='__main__':main()
