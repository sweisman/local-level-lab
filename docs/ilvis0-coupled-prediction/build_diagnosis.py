# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only decomposition of sealed prediction widths; no refits/supports."""
import csv
from fractions import Fraction as F
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll.ilvis0_width_components import components

PUBLIC=Path(__file__).resolve().parent


def main():
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for name,digest in receipt['artifacts'].items():
        if runner._sha(runner.path_within(PUBLIC,name))!=digest:raise ValueError('sealed prediction evidence changed')
    manifest=runner._load(PUBLIC/'manifest.json');summary=runner._load(PUBLIC/'summary.json')
    baseline=runner._load(PUBLIC/manifest['inputs']['baseline']['path'])['cases']
    rows=[];known=[];names=('north','east','height');groups=set()
    for item in summary['results']:
        result=runner._load(PUBLIC/item['artifact'])['result']
        if not result['passed'] or result['excluded']:continue
        identity=result['identity'];directory=PUBLIC/'artifacts'/identity
        future=runner._load(directory/'future.json');region=runner._load(directory/'training.json')['region']
        group=(result['task']['model'],result['task']['profile'])
        original=next(r for r in baseline if (r['model'],r['profile'])==group)
        if result['truth_in_sector']:
            if group in groups:raise ValueError('unique known generated sector required')
            groups.add(group)
        for axis in range(3):
            value=components(future,region,axis);target=F(original['union_width_m'][axis])/2
            row=dict(identity=identity,model=group[0],profile=group[1],sector=result['task']['sector'],
                known_truth_sector=result['truth_in_sector'],axis=names[axis],
                **{k:float(F(v)) for k,v in value.items() if k.endswith('width') or k in ('rounding_padding','saved_remainder_floor')},
                target_width=float(target),remainder_alone_exceeds_target=F(value['saved_remainder_floor'])>target)
            rows.append(row)
            if result['truth_in_sector']:
                if not value['affine_width_nonnegative']:raise ValueError('negative affine width in verified feasible sector')
                known.append(row)
    if groups!={(m,p) for m in range(3) for p in (False,True)}:raise ValueError('all six known feasible sectors required')
    csv_path=PUBLIC/'width-components.csv'
    with csv_path.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    labels=('Globe with specified field','Globe with zero field','Flat disc')
    text=['# What keeps the prediction ranges wide?','',
        'This report displays the terms of already-verified certificates. It performs '
        'no new support calculation, propagation bound or native prediction.','',
        'The table uses the predeclared known-feasible generated sector in each group. '
        'It separates the affine calibration range from the saved unshared/arithmetic '
        'allowances. Outward endpoint rounding is retained in the CSV.','',
        '| Candidate / removal | Axis | Total width (m) | Affine part (m) | Saved remainder floor (m) | Fixed target (m) | Floor exceeds target |',
        '|---|---|---:|---:|---:|---:|---|']
    for row in known:
        label=labels[row['model']]+(' / profiled' if row['profile'] else ' / zero')
        text.append(f"| {label} | {row['axis']} | {row['total_width']:.4f} | {row['affine_width']:.4f} | "
            f"{row['saved_remainder_floor']:.4f} | {row['target_width']:.4f} | {'Yes' if row['remainder_alone_exceeds_target'] else 'No'} |")
    above=sum(r['remainder_alone_exceeds_target'] for r in known)
    text+=['',f"Saved remainder floors exceed the target on {above}/18 known-feasible axes.",'']
    if above:
        text+=['The present formula cannot meet every target by tightening its affine '
            'supports alone. The affected native remainder bounds must also be '
            'recomputed on a justified smaller domain or retain more dependence.']
    else:
        text+=['These saved floors do not themselves prevent the target. A bounded '
            'subdivision of the physical calibration domain is therefore a justified '
            'next test before more expensive native-bound recalculation.']
    text+=['','These floors belong to the current error-range formula; they are not '
        'measurements of sensor noise or irreducible physical uncertainty. A floor '
        'argument requires a nonempty region, established here by each sealed '
        'known generated calibration. It does not establish that every other '
        'orientation sector is physically feasible.','',
        '[Every sector/axis](width-components.csv) · [Completed comparison](README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    report=PUBLIC/'DECOMPOSITION.md';report.write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'decomposition-receipt.json',dict(
        source_evidence_sha256=runner._sha(PUBLIC/'evidence-receipt.json'),
        builder_sha256=runner._sha(Path(__file__)),helper_sha256=runner._sha(ROOT/'analysis/lll/ilvis0_width_components.py'),
        artifacts={p.name:runner._sha(p) for p in (report,csv_path)},new_support_evaluations=0,new_native_evaluations=0))
    print(f'Published saved-only decomposition: {len(rows)} sector/axis rows; {above}/18 known floors above target.')

if __name__=='__main__':main()
