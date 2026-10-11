# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare saved unit-scale fits with the original prediction trial; no fitting."""
import csv
import importlib.util
import json
from pathlib import Path

from lll import ilvis0_saved_audit as audit

HERE=Path(__file__).resolve().parent
BASELINE=HERE.parent/'ilvis0-prediction-trial-20261011'
VERSION='ilvis0-unit-scale-prediction-trial-v2'


def matched_fit(new,old,case_id):
    before,after=audit.fit_status(old),audit.fit_status(new)
    preserved=before!='converged' or after=='converged'
    qualified=(after=='converged' and new['residual_sum_squares']<=old['residual_sum_squares']*1.001+1e-9) if before=='converged' else None
    a=old.get('prediction_diagnostics',{}).get('prediction',{})
    b=new.get('prediction_diagnostics',{}).get('prediction',{})
    return dict(case_id=case_id,model=new['model'],baseline_status=before,new_status=after,
        completed_baseline_preserved=preserved,objective_qualified=qualified,
        baseline_training_cost=old.get('residual_sum_squares'),new_training_cost=new.get('residual_sum_squares'),
        baseline_prediction_horizontal_m=a.get('horizontal_rms_m'),new_prediction_horizontal_m=b.get('horizontal_rms_m'),
        baseline_prediction_vertical_m=a.get('vertical_rms_m'),new_prediction_vertical_m=b.get('vertical_rms_m'))


def build(directory=HERE,baseline=BASELINE):
    directory,baseline=map(Path,(directory,baseline))
    source=BASELINE/'build_report.py'
    spec=importlib.util.spec_from_file_location('isolated_prediction_renderer',source)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    audit.verify_artifacts(baseline,module.load(baseline/'evidence-receipt.json'))
    original=module.load(baseline/'summary.json'); before=module.load(baseline/'completion.json')
    if (before['summary_sha256']!=module.sha(baseline/'summary.json')
        or before['manifest_sha256']!=module.sha(baseline/'manifest.json')):
        raise ValueError('baseline completion differs')
    audit.verify_artifacts(directory,module.load(directory/'evidence-receipt.json'))
    summary=module.load(directory/'summary.json')
    if summary['split']!=original['split']: raise ValueError('matched split differs')
    current_manifest=module.load(directory/'manifest.json')
    original_manifest=module.load(baseline/'manifest.json')
    for key in ('cases','clock','initialization','split_policy','covariance_policy',
                'prospective_validation','parameter_uncertainty_included'):
        if current_manifest.get(key)!=original_manifest.get(key):
            raise ValueError('matched scientific scope differs: '+key)
    old={(c['case_id'],f['model']):f for c in original['cases'] for f in c['fits']}
    new={(c['case_id'],f['model']):f for c in summary['cases'] for f in c['fits']}
    if len(old)!=6 or len(new)!=6 or set(old)!=set(new): raise ValueError('matched population differs')
    rows=[matched_fit(new[key],old[key],key[0]) for key in new]
    qualification=all(r['new_status']=='converged' and r['completed_baseline_preserved']
        and r['objective_qualified'] is not False for r in rows)
    module.VERSION=VERSION
    module.build(directory)
    name='matched-baseline.csv'
    with (directory/name).open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    introduction=('# Fixed solver scaling: matched prediction comparison\n\n'
        f'**Comparison qualification: {"passed" if qualification else "not passed"}.** '
        'Passing requires all six new fits to converge, preserving the five previously '
        'completed fits without worsening their training objectives by more than 0.1%. '
        'This does not qualify a global optimum, factory calibration or statistical '
        'significance. The original unfinished result remains unchanged. '
        '[Matched original results](matched-baseline.csv) preserve every comparison.\n\n')
    text=(directory/'RESULTS.md').read_text()
    text=introduction+text.split('\n',1)[1]
    text=text.replace('docs/ilvis0-prediction-trial-20261011/build_report.py',
        'docs/ilvis0-unit-scale-trial-20261011/build_report.py')
    (directory/'RESULTS.md').write_text(text)
    receipt=module.load(directory/'report-receipt.json')
    receipt['comparison_qualification_passed']=qualification
    receipt['sources'][str(Path(__file__).resolve())]=module.sha(Path(__file__))
    for filename in ('evidence-receipt.json','completion.json','manifest.json','summary.json'):
        p=baseline/filename; receipt['inputs'][str(p.resolve())]=module.sha(p)
    receipt['artifacts'].update({n:module.sha(directory/n) for n in ('RESULTS.md',name)})
    (directory/'report-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    return rows


if __name__=='__main__': build()
