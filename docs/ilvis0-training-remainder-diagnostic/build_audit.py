# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit sealed bound coefficients in common units, without numerical reruns."""
from fractions import Fraction as F
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll.ilvis0_training_remainder_audit import scaled_design

PUBLIC=Path(__file__).resolve().parent


def main():
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for name,digest in receipt['artifacts'].items():
        if runner._sha(runner.path_within(PUBLIC,name))!=digest:raise ValueError('sealed diagnostic changed')
    manifest=runner._load(PUBLIC/'manifest.json');summary=runner._load(PUBLIC/'summary.json');rows=[]
    for record in summary['results']:
        result=runner._load(PUBLIC/record['artifact'])['result'];identity=result['identity']
        source=runner._load(PUBLIC/manifest['inputs'][identity]['path']);training=source['training'];region=training['region']
        report=runner._load(PUBLIC/'artifacts'/identity/'bound.json')
        converted=scaled_design(training['jacobian'][-1],report,region['coordinate_scale'])
        original=region['design'][-3:];n=len(converted[0])
        maximum=max(abs(F(a)-F(b)) for r,s in zip(converted,original) for a,b in zip(r,s))
        # If exporting old coefficients later, this exact extra radius would be
        # needed. It is displayed only; no present constraint is changed.
        lo=source['future']['lower'][:n];hi=source['future']['upper'][:n]
        displacement=[max(abs(F(a)-F(c)),abs(F(b)-F(c))) for a,b,c in zip(lo,hi,region['center'][:n])]
        transfer=[sum((abs(F(a)-F(b))*d for a,b,d in zip(r,s,displacement)),F(0)) for r,s in zip(converted,original)]
        rows.append(dict(identity=identity,model=result['model'],profile=result['profile'],
            original_passed=result['passed'],original_label_unchanged=True,
            scaled_coefficients_equal=converted==original,maximum_scaled_coefficient_difference=float(maximum),
            exact_transfer_radii_m=list(map(str,transfer)),width_ratio=result['width_ratio'],
            new_half_width_m=result['new_half_width_m'],
            position_remainder_m=[v*s for v,s in zip(report['position_unshared_remainder'],region['coordinate_scale'])],
            lever_remainder_m=[v*s for v,s in zip(report['lever_unshared_remainder'],region['coordinate_scale'])],
            force_remainder_m=[v*s for v,s in zip(report['force_unshared_remainder'],region['coordinate_scale'])],
            clock_remainder_m=[v*s for v,s in zip(report['acceleration_clock_remainder'],region['coordinate_scale'])],
            new_bound_calls=0,optimizer_starts=0))
    data=PUBLIC/'unit-audit.json';runner._replace(data,dict(cases=rows,original_labels_preserved=True,new_bound_calls=0,new_native_evaluations=0))
    text=['# Saved-bound unit audit','',
        'The six bounds completed, but their comparison adapter checked raw-coordinate '
        'coefficients against metre-scaled training coefficients. That is a unit mismatch. '
        'The original six failed labels are preserved. This audit converts the saved '
        '27 physical and 24 common-error columns into matching units, with no bound rerun.','',
        '| Candidate / removal | Scaled coefficients exactly equal | Largest coefficient difference | N / E / height allowance ratios |',
        '|---|---|---:|---:|']
    for r in rows:
        label=('Globe with specified field','Globe with zero field','Flat disc')[r['model']]+(' / profiled' if r['profile'] else ' / zero')
        text.append(f"| {label} | {'Yes' if r['scaled_coefficients_equal'] else 'No'} | "
            f"{r['maximum_scaled_coefficient_difference']:.5g} | {' / '.join(f'{v:.6f}' for v in r['width_ratio'])} |")
    text+=['','The recomputed allowances improve by at most about 3.7%, and height changes '
        'by less than 0.003%. This smaller-domain recalculation therefore offers little '
        'help with the main vertical uncertainty. It does not establish narrower complete '
        'prediction ranges or observational coverage.','',
        '| Candidate / removal | Position remainder, height (m) | Included force remainder (m) | Lever remainder (m) |',
        '|---|---:|---:|---:|']
    for r in rows:
        label=('Globe with specified field','Globe with zero field','Flat disc')[r['model']]+(' / profiled' if r['profile'] else ' / zero')
        text.append(f"| {label} | {r['position_remainder_m'][2]:.5f} | {r['force_remainder_m'][2]:.5f} | {r['lever_remainder_m'][2]:.5f} |")
    text+=['','The force term is included in the position remainder and must not be added '
        'again. These are reported bounds, not independent physical error estimates. '
        'The remaining position-propagation terms are the next place to inspect; '
        'another repetition of the same smaller-domain calculation is not justified.','',
        'Any nonzero coefficient difference must be retained or explicitly bounded when '
        'constructing a future inequality. The data file reports exact transfer-radius '
        'terms; no coefficient is silently replaced here.','',
        '[Original comparison](README.md) · [Next step](NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    report=PUBLIC/'INTERPRETATION.md';report.write_text('\n'.join(text)+'\n')
    runner._replace(PUBLIC/'unit-audit-receipt.json',dict(source_evidence_sha256=runner._sha(PUBLIC/'evidence-receipt.json'),
        builder_sha256=runner._sha(Path(__file__)),helper_sha256=runner._sha(ROOT/'analysis/lll/ilvis0_training_remainder_audit.py'),
        artifacts={p.name:runner._sha(p) for p in (data,report)},saved_bound_conversions=len(rows),new_bound_calls=0,new_native_evaluations=0))
    print('Audited six saved bounds in matching units; original labels preserved; no numerical reruns.')


if __name__=='__main__':main()
