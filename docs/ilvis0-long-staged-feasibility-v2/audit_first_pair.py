# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read two immutable sealed cases; never merge active shards or run numerics."""
import argparse
from fractions import Fraction as F
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
DATA=ROOT/'data/ilvis0-long-staged-feasibility-v2-20261021';PUBLIC=Path(__file__).resolve().parent


def metrics(row,remainder,scale,arithmetic):
    widths=row['future_width_m'];targets=row['width_target_m']
    if (not all(row.get(k) is True for k in ('numerical_checks_passed','known_truth_retained','future_truth_contained'))
            or any(len(v)!=3 for v in (widths,targets,remainder,scale))
            or any(not math.isfinite(v) or v<=0 for v in [*widths,*targets,*scale])
            or any(not math.isfinite(v) or v<0 for v in [*remainder,arithmetic])):
        raise ValueError('complete valid numerical cases and aligned finite coordinate units required')
    useful=all(v<=t for v,t in zip(widths,targets,strict=True))
    if row.get('passed')!=useful or row.get('useful')!=useful:
        raise ValueError('saved outcome differs from fixed usefulness test')
    half=[F(v)*F(s)+F(arithmetic) for v,s in zip(remainder,scale,strict=True)]
    fractions=[2*v/F(w) for v,w in zip(half,widths,strict=True)]
    if any(v>1 for v in fractions):raise ValueError('additive error exceeds the saved total range')
    return dict(outcome='Pass' if useful else 'Too wide',numerical_checks_passed=True,
        width_m=widths,unshared_half_width_m=list(map(float,half)),unshared_width_fraction=list(map(float,fractions)))


def build():
    manifest=runner.verify(DATA);tasks=manifest['tasks'][:2]
    if [(t['payload']['model'],t['payload']['profile']) for t in tasks]!=[(0,False),(0,True)]:
        raise ValueError('only the first predeclared pair is eligible for this saved audit')
    # This validates immutable cases individually while workers own their shards.
    # runner.merge is deliberately not used: active shards cannot be merged.
    for shard in sorted({t['shard'] for t in tasks}):runner._validate_own_results(DATA,manifest,shard)
    rows=[];inputs={}
    for task in tasks:
        identity=task['identity'];path=DATA/'shards'/f"{task['shard']:03d}"/'results'/(identity+'.json')
        seal=path.with_suffix('.seal.json')
        if not seal.exists():raise ValueError('first-pair result is not sealed')
        envelope=runner._load(path);row=envelope['result'];inputs[str(path.relative_to(DATA))]=runner._sha(path)
        inputs[str(seal.relative_to(DATA))]=runner._sha(seal)
        def record(name):
            target=DATA/'artifacts'/identity/name;relative=str(target.relative_to(DATA))
            sha=runner._sha(target)
            if sha!=envelope['artifacts'][relative]:raise ValueError('sealed input changed')
            inputs[relative]=sha;return runner._load(target)
        bound=record('future-bound.json');region=record('stage-02-region.json')
        result=metrics(row,bound['unshared_remainder'],task['payload']['coordinate_scale'],region['arithmetic_allowance'])
        result.update(identity=identity,profile=task['payload']['profile'],
            acceleration_radii=[record(name)['norm_change'] for name in
                ('physical-proof.json','stage-01-proof.json','stage-02-proof.json')],
            bound_times_s=[record(f'raw-bound-{i:02d}.json')['elapsed_s'] for i in range(1,7)],
            sealed_artifacts_verified=len(envelope['artifacts']),artifact_sha256=runner._sha(path))
        rows.append(result)
    data=dict(manifest_sha256=runner._sha(DATA/'manifest.json'),scope='first two predeclared sealed generated cases only',
        cases=rows,inputs=inputs,optimizer_starts=0,native_evaluations=0,merged_active_shards=False,
        full_study_assessed=False,observational_coverage_qualified=False,scientific_decision='abstain')
    text=['# First pair: completed checks, unusably wide ranges','',
        'Both specified-field cases completed their numerical checks and retained the known answer. '
        'Neither meets the frozen prediction-width target. This fixed audit covers only those first two '
        'cases; see the [study page](README.md) for the full study status.','',
        '| Processing | North width | East width | Height width | Target N / E / height |',
        '|---|---:|---:|---:|---:|']
    for row in rows:
        text.append('| '+('Profiled removal' if row['profile'] else 'Zero removal')+' | '+
            ' | '.join(f'{v/1000:,.1f} km' for v in row['width_m'])+' | 20 / 20 / 50 m |')
    fractions=[v for row in rows for v in row['unshared_width_fraction']]
    text+=['',f"The additive, unshared approximation allowance accounts for {min(fractions):.1%}–{max(fractions):.1%} "
        'of these reported widths. Training reduces the initial-acceleration change bound from about '
        '24.4 m/s² to 1.7 m/s², but the later training stage hardly improves it. The remaining '
        'long-history approximation is still much too loose.','',
        '**These are generated-data bounds, not measured aircraft errors.** They do not change the '
        '53-stretch model comparisons or measure instrument drift. Containing the known answer '
        'does not qualify an interval thousands of kilometres wide.','',
        'The next method must sharpen the long-history enclosure and its use of training information. '
        'The five-epoch training subset also does not establish what all 292 earlier training epochs '
        'could achieve. More optimizer evaluations, a larger error allowance or a wider success '
        'threshold would not resolve this test.','',
        'All 158 side artifacts of these two cases were checked against their seals. This read-only '
        'audit performs no integration, fitting or active-shard merge. It is a first-pair diagnosis, '
        'not the final six-case study summary.','',
        '[Frozen scope](PLAN.md) · [Remaining gates](V01_GATES.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    return data,'\n'.join(text)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    data,text=build();data_path=PUBLIC/'first-pair-audit.json';report=PUBLIC/'FIRST_PAIR.md'
    receipt_path=PUBLIC/'first-pair-receipt.json'
    if args.check:
        receipt=runner._load(receipt_path)
        for name,sha in receipt['artifacts'].items():
            if runner._sha(PUBLIC/name)!=sha:raise ValueError('saved first-pair publication changed')
        if runner._load(data_path)!=data or report.read_text()!=text:raise ValueError('saved diagnosis changed')
        print('Verified two sealed cases and first-pair audit; no numerical work.');return
    runner._write(data_path,data);report.write_text(text)
    runner._write(receipt_path,dict(artifacts={name:runner._sha(PUBLIC/name) for name in
        ('audit_first_pair.py','first-pair-audit.json','FIRST_PAIR.md')},manifest_sha256=data['manifest_sha256']))
    print('Published fixed first-pair audit; no numerical work or merge.')


if __name__=='__main__':main()
