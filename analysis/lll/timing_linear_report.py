# SPDX-License-Identifier: AGPL-3.0-or-later
"""Report sealed linear calculations independently of task-envelope acceptance."""
import json
from pathlib import Path


def sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root,['analysis/lll/timing_linear_report.py',
        'analysis/tests/test_timing_linear_report.py','analysis/tests/test_timing_linear_diagnosis.py',
        'analysis/tests/test_timing_cells.py','analysis/tests/test_timing_cells_known_optimum.py',
        'docs/TIMING_LINEAR_DIAGNOSIS_PLAN.md','docs/TIMING_LINEAR_ANCHOR_PLAN.md'])


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy,load_python_reference
    from lll.studies.artifacts import encoded
    from lll.airquantumgrav_geographic_report import construction_counts
    from lll.airquantumgrav_inventory import environment
    s=ClosedStudy(root,prefix)
    try:
        name='analysis/lll/timing_linear_diagnosis.py';sha=s.manifest['sources'][name]
        helper=load_python_reference(s.read('source-freeze/'+name,sha,raw=True),
            name='lll._closed_linear_diagnosis_helper',sha256=sha)
        selected=s.input('selection');cfg=s.input('configuration');expected=helper.tasks(selected)
        if (cfg!=helper.configuration() or s.manifest['scope']!=cfg['scope']
                or s.input('environment')!=environment()
                or [{k:v for k,v in t.items() if k not in ('index','shard')} for t in s.tasks.values()]!=expected
                or any(s.summary['charged'].values())):raise ValueError('exact zero-native diagnosis required')
        for name,sha in s.manifest['sources'].items():s.read('source-freeze/'+name,sha,raw=True)
        rows=[];failures=[];charges=0;accepted=0
        for matrix in selected['rows']:
            identity=matrix['identity']
            if identity not in s.rows:
                failures.append(dict(identity=identity,reason='unexecuted'));continue
            envelope=s.envelope(identity);outcome=envelope['result'];accepted+=outcome['passed']
            base='artifacts/'+identity+'/'
            for name,sha in envelope['artifacts'].items():s.read(name,sha,raw=True)
            if base+'linear-solves.sqlite' in envelope['artifacts']:
                charges+=construction_counts(s.artifact(identity,'linear-solves.sqlite',raw=True),
                    s.completion['manifest_sha256'],identity,dict(linear_solves=1),complete=False)['linear_solves']
            if base+'diagnosis.json' in envelope['artifacts']:
                saved=s.artifact(identity,'diagnosis.json');audit=helper.audit_proposal(matrix,saved['proposal'])
                if encoded(audit)!=encoded(saved['audit']):raise ValueError('independent scalar audit differs')
                rows.append(audit)
            if not outcome['passed']:
                failures.append(dict(identity=identity,error_type=outcome.get('error_type'),reason=outcome.get('reason')))
        if charges<len(rows) or charges>4:raise ValueError('linear charges differ from saved calculations')
        return dict(version='saved-linear-baseline-report-v1',verified=True,completed_diagnoses=len(rows),
            accepted_task_envelopes=accepted,charged_linear_solves=charges,rows=rows,failures=failures,
            nonworsening=sum(r['nonworsening'] for r in rows),elapsed_s=s.summary['elapsed_s'],
            manifest_sha256=s.completion['manifest_sha256'],summary_sha256=s.completion['summary_sha256'],
            parent_completion=selected['parent_completion'],native_calls=0,nonlinear_fit_starts=0,
            exact_saved_cell_anchor_replay=False,labels_changed=False,scientific_decision='abstain')
    finally:s.close()


def render(report):
    complete=(len(report['rows'])==4
        and sum(not r['original_fit_converged'] and not r['nonworsening'] for r in report['rows'])==2
        and sum(r['original_fit_converged'] and r['nonworsening'] for r in report['rows'])==2)
    conclusion=('The two failed calibration cases return higher predicted costs than a feasible zero step. '
        'The matched earlier controls do not. This isolates a problem in the bounded linear calculation; '
        'it does not establish the cause of every earlier numerical failure.' if complete else
        'The expected four-case comparison is incomplete or differs from the anticipated pattern. '
        'Preserve the returned outcomes without claiming the complete matched comparison.')
    if len(report['rows'])==4 and all(r['nonworsening'] and r['linear_success'] for r in report['rows']):
        conclusion=('All four proposals retain or reduce the feasible anchor objective and report solver success. '
            'This checks the revised bounded linear calculation on the matched saved matrices; '
            'it does not qualify the complete nonlinear optimizer or establish calibration coverage.')
    lines=['# Saved bounded linear calculation checks','',
        f"**{report['completed_diagnoses']} saved linear calculations were independently checked.**",'',
        conclusion,'',
        '| Saved fit | Starting cost | Returned linear cost | Worse than zero step? |',
        '|---|---:|---:|---|']
    for i,row in enumerate(report['rows']):
        label=('Earlier control' if row['original_fit_converged'] else 'Failed case')+f', start {i%2}'
        lines.append(f"| {label} | {row['anchor_cost']:.9f} | {row['predicted_cost']:.9f} | "
                     f"{'No' if row['nonworsening'] else 'Yes'} |")
    schema_error=(report['accepted_task_envelopes']==0 and len(report.get('failures',[]))==4
        and all(f.get('reason')=='one explicit software result and continued scientific abstention required'
                for f in report['failures']))
    outcome=f"The runner accepted {report['accepted_task_envelopes']}/4 task envelopes. "
    if schema_error:
        outcome+=('A schema error omitted the required top-level abstention field after the calculations '
            'were saved. Their hashes, scalar arithmetic and four charged solves were checked separately. '
            'No calculation was rerun, and the rejected envelope labels remain unchanged.')
    else:outcome+='Every returned outcome and charged solve is retained; no closed study was restarted.'
    lines+=['',outcome,'',
        'Every calculation retains all 26 nuisance directions and the original physical bounds. '
        'It uses the exact saved final linearization; it is not a native replay at a different anchor. '
        'No original fit is relabeled, no calibration threshold is established and validation stays blocked.','',
        'Next: reproduce the linear-solver failure with an independent known-answer problem, '
        'then qualify a correction before any new campaign.','',
        '[Results CSV](results.csv) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).']
    return '\n'.join(lines)+'\n'


def publish(root,prefix,*,qualification,output='docs/timing-linear-baseline-diagnosis'):
    from lll.studies.qualification import checked
    from lll.studies.artifacts import atomic,encoded,digest
    from lll.airquantumgrav_inventory import environment
    from lll.ilvis0_control_publication import publish as package,check
    from lll.timing_arithmetic_report import csv_bytes
    from lll.timing_linear_diagnosis import PLAN
    root=Path(root).resolve();public=root/output;data=root/prefix
    request,tests=checked(root,qualification,sources=sources(root),environment=environment(),minimum_tests=56,
        required_tests=['test_linear_report_distinguishes_saved_calculations_from_rejected_envelopes',
            'test_linear_report_does_not_relabel_failed_fits_or_claim_native_replay',
            'test_corrected_linear_report_describes_four_accepted_nonworsening_results'])
    if (public/'evidence-receipt.json').exists():raise ValueError('fresh publication required')
    report=inspect(root,prefix);package(data,public,render(report),plan=PLAN)
    extras={'results.csv':csv_bytes(report['rows']),'artifacts/publication/verified-report.json':encoded(report),
        'artifacts/publication/reporter.py':Path(__file__).read_bytes(),
        'artifacts/publication/reporter-qualification-request.json':request,
        'artifacts/publication/reporter-qualification-report.xml':tests}
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in extras.items():atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt));check(data,public)
    if encoded(inspect(root,output))!=encoded(report):raise ValueError('public replay differs')
    return dict(publication=output,artifacts=len(receipt['artifacts']),report=report,
                numerical_work=0,compaction_pending=True)
