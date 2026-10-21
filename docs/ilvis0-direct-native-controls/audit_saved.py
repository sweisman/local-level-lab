# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify point-source work and bound changes from sealed metadata only."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import statistics
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
DATA=ROOT/'data/ilvis0-direct-native-controls-20261021';PUBLIC=Path(__file__).resolve().parent


def main():
    publication.check(DATA,PUBLIC);manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    if not summary['passed']:raise ValueError('passing complete native controls required')
    ratios={key:[[],[],[]] for key in ('unshared_remainder','position_unshared_remainder',
        'force_unshared_remainder','lever_unshared_remainder')}
    details=[];bound_count=point_steps=direct_steps=0
    for item in summary['results']:
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        record=runner._load(DATA/item['artifact']);case_steps=0
        baseline=runner._load(DATA/manifest['inputs'][task['payload']['baseline_key']]['path'])
        for name in sorted(record['artifacts']):
            if not Path(name).name.startswith('bound-'):continue
            row=runner._load(DATA/name);index=str(int(Path(name).stem.split('-')[-1]))
            steps=row['source_direct_steps']
            if (type(steps) is not int or not 0<=steps<=task['payload']['packets']
                    or steps!=row['source_derivative_steps'] or not row['source_direct_remainder_installed']):
                raise ValueError('missing or excessive direct source work')
            case_steps+=steps;bound_count+=1
            for key,axes in ratios.items():
                before=baseline['ceilings'][index][key];after=row[key]
                if len(before)!=3 or len(after)!=3:raise ValueError('three complete coordinates required')
                for axis,(a,b) in enumerate(zip(before,after,strict=True)):
                    a,b=F(a),F(b)
                    if not 0<=b<=a:raise ValueError('native remainder widened')
                    if a:axes[axis].append(float(b/a))
            details.append(dict(identity=item['identity'],bound=index,point_steps=steps))
        limits=task['payload']['source_limits']
        if case_steps>limits['source_point_steps'] or case_steps>limits['source_direct_steps']:
            raise ValueError('point or direct formula work exceeds reservation')
        point_steps+=case_steps;direct_steps+=case_steps
    if bound_count!=348:raise ValueError('complete 348-bound matrix required')
    result=dict(bound_count=bound_count,point_steps=point_steps,direct_formula_steps=direct_steps,
        relative_remainders={key:[dict(count=len(v),minimum=min(v),median=statistics.median(v),maximum=max(v))
            if v else dict(count=0) for v in axes] for key,axes in ratios.items()},
        details=details,observed_reads=0,native_evaluations=0,optimizer_starts=0,
        builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        observational_coverage_qualified=False,scientific_decision='abstain')
    runner._replace(PUBLIC/'source-work-audit.json',result)
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for name in ('source-work-audit.json','audit_saved.py'):receipt['artifacts'][name]=runner._sha(PUBLIC/name)
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)
    print(f'Verified {bound_count} bounds; {point_steps} point steps and {direct_steps} direct-formula steps.')


if __name__=='__main__':main()
