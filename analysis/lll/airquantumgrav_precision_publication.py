# SPDX-License-Identifier: AGPL-3.0-or-later
"""Presentation-only packaging of the frozen saved-array precision audit."""

MODES=('double-legacy','double-stable','long-double-stable')


def qualification_sources():
    return ['analysis/lll/airquantumgrav_precision_publication.py',
        'analysis/tests/test_airquantumgrav_precision_publication.py']


def required_tests():
    return ['test_precision_publication_separates_diagnostic_resolution_from_fit_acceptance',
        'test_precision_publication_refuses_to_overwrite_a_sealed_report']


def table(report):
    import csv
    import io
    stream=io.StringIO(newline='');writer=csv.writer(stream)
    writer.writerow(['identity','model','profile','policy_id','start','complete','original_numerical_pass',
        'mode','baseline_cost','corrected_cost','relative_cost_change','maximum_local_position_change_m'])
    for row in report['rows']:
        prefix=[row.get(k) for k in ('identity','model','profile','policy_id','start','complete','source_converged')]
        if row['complete']:
            for mode in MODES:
                v=row['modes'][mode];writer.writerow(prefix+[mode,v['baseline_cost'],v['corrected_cost'],
                    v['relative_cost_change'],max(v['position_max_abs_neu_m'])])
        else:writer.writerow(prefix+['Incomplete','','','',''])
    return stream.getvalue()


def render(report):
    lines=['# Precision matters in the ESA stopping calculation','',
        f"**{report['complete']}/{report['total']} saved-point diagnostics completed and verified.**",'',
        'Each row uses the same saved calibration and the same bounded correction.',
        'No calibration was fitted again. The binary64 legacy path reproduces',
        'both original residual vectors exactly. All earlier observations, physical',
        'equations, clock scheduling and acceptance limits remain fixed.','',
        'Cost-change values below are in units of **1e-8**, the existing cost-stability',
        'limit. A value below 1 passes this component only; no original fit is reclassified.','',
        '| Candidate | Removal | Working errors | Start | Original numerical pass | Legacy | Stable wrap | Extended precision |',
        '|---|---|---|---:|---|---:|---:|---:|']
    labels=dict(sphere_rotating='Globe + field',sphere_still='Globe + zero field',flat_still='Disc')
    for row in report['rows']:
        prefix=[labels[row['model']],'Profiled' if row['profile'] else 'Zero',
            'Short memory' if row['policy_id']=='reported-short-v1' else 'Persistent',str(row['start']),
            'Yes' if row.get('source_converged') else 'No']
        values=[format(row['modes'][m]['relative_cost_change']*1e8,'.4g') for m in MODES] if row['complete'] else ['Incomplete']*3
        lines.append('| '+' | '.join(prefix+values)+' |')
    lines+=['','Stable wrapping avoids rounding already-small longitude differences.',
        'Extended precision also reduces rounding accumulated during integration;',
        'receiver coordinates are subtracted before conversion back to binary64.',
        'The packet clock, parameter products and processing-fraction mapping retain',
        'their original binary64 conventions.','',
        'These results diagnose precision sensitivity at fixed points. They do not',
        'prove a global optimum, certify a roundoff bound or qualify a revised solver.',
        'The next gate is independent qualification of the wider-precision derivative',
        'and stopping path. All original labels and seven protected confirmation',
        'groups remain unchanged.','',
        f"The run used {report['charged']['native_calls']} value calculations in {report['elapsed_s']/60:.2f} minutes.",
        'The audit uses saved arrays and performs no trajectory propagation.','',
        '[Every point and mode](precision.csv) · [Frozen plan](PLAN.md) ·',
        '[Original stopping diagnostic](../esa-stopping-resolution/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).','']
    return '\n'.join(lines)


def publish(root,prefix='data/esa-precision-diagnostic-v2-20261024',output='docs/esa-precision-diagnostic',*,qualification=None):
    import json
    from pathlib import Path
    from .studies.artifacts import safe_path,atomic,digest,encoded
    root=Path(root).resolve();public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('precision publication already sealed')
    if qualification is None:raise ValueError('source-bound publication qualification required')
    from .airquantumgrav_inventory import environment
    from .airquantumgrav_precision_report import inspect
    from .ilvis0_control_publication import publish as package
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.publication import archive_publication
    request,tests=checked(root,qualification,sources=qualification_sources(),environment=environment(),
        required_tests=required_tests(),minimum_tests=2)
    report=inspect(root,prefix);study=ClosedStudy(root,prefix)
    try:plan=study.manifest['sources']['docs/esa-precision-diagnostic/PLAN.md']
    finally:study.close()
    if digest((public/'PLAN.md').read_bytes())!=plan:raise ValueError('frozen precision plan changed')
    data=safe_path(root,prefix);package(data,public,render(report),plan='docs/esa-precision-diagnostic/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    additions=[('artifacts/publication/verified-report.json',encoded(report)),('precision.csv',table(report).encode()),
        ('artifacts/publication/publication-request.json',request),('artifacts/publication/publication-tests.xml',tests)]
    additions.extend(('artifacts/publication/presentation-source/'+name,(root/name).read_bytes()) for name in qualification_sources())
    for name,raw in additions:atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,native_calls=0)
