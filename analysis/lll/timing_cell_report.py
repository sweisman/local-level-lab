# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independently audit saved linear predictions, without evaluating physics."""
import math


def summarize(matrix,proposal,*,index):
    names=matrix['active'];point=proposal['point'];lo=matrix['lower'];hi=matrix['upper']
    if (len(names)!=27 or proposal['active_parameters']!=names or len(point)!=27
            or proposal['lower']!=lo or proposal['upper']!=hi
            or proposal['maximum_iterations']!=100 or proposal['tolerance']!=1e-10
            or not 0<=proposal['iterations']<=100 or proposal['native_calls'] or proposal['nonlinear_fit_starts']
            or any(not math.isfinite(v) or v<a or v>b for v,a,b in zip(point,lo,hi))):
        raise ValueError('complete feasible proposal with original bounds and finite solve required')
    residual=[r+math.fsum(a*(x-u) for a,x,u in zip(row,point,matrix['point']))
              for row,r in zip(matrix['jacobian'],matrix['residual'])]
    cost=math.fsum(v*v for v in residual);anchor=math.fsum(v*v for v in matrix['residual'])
    if (len(residual)!=len(proposal['predicted_residual'])
            or any(not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)
                   for a,b in zip(residual,proposal['predicted_residual']))
            or not math.isclose(cost,proposal['predicted_cost'],rel_tol=1e-12,abs_tol=1e-12)
            or not math.isclose(anchor,proposal['anchor_cost'],rel_tol=1e-12,abs_tol=1e-12)):
        raise ValueError('saved objective differs from independent matrix arithmetic')
    column=names.index('time_offset')
    return dict(index=index,identity=matrix['identity'],side=matrix['side'],spacing_s=matrix['spacing_s'],
        original_fit_converged=matrix['original_fit_converged'],linear_success=proposal['linear_success'],
        iterations=proposal['iterations'],predicted_cost=cost,anchor_cost=anchor,
        predicted_delta_from_original=cost-matrix['original_cost'],
        proposed_time_offset_s=point[column]*matrix['time_offset_scale'],
        parameter_bounds_reached=len(proposal['parameter_bounds_reached']),actual_cost_evaluated=False,
        labels_changed=False)


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest,encoded
    from lll.timing_cell_study import configuration,task,SCOPE
    from lll.airquantumgrav_inventory import environment
    from lll.airquantumgrav_geographic_report import construction_counts
    s=ClosedStudy(root,prefix)
    try:
        selected=s.input('matrices');cfg=s.input('configuration');identity='all-saved-branches'
        if (cfg!=configuration() or s.manifest['scope']!=SCOPE or s.input('environment')!=environment()
                or len(selected['rows'])!=18 or digest(encoded(selected['rows']))!=selected['sha256']
                or {k:v for k,v in s.tasks[identity].items() if k not in ('index','shard')}!=task(selected['sha256'])
                or any(s.summary['charged'].values())):
            raise ValueError('same zero-native finite matrix review required')
        for name,sha in s.manifest['sources'].items():s.read('source-freeze/'+name,sha,raw=True)
        rows=[];proposals=[];failures=[];charges=0
        if identity in s.rows:
            envelope=s.envelope(identity);base='artifacts/'+identity+'/'
            for name,sha in envelope['artifacts'].items():s.read(name,sha,raw=True)
            if base+'linear-solves.sqlite' in envelope['artifacts']:
                charges=construction_counts(s.artifact(identity,'linear-solves.sqlite',raw=True),
                    s.completion['manifest_sha256'],identity,dict(linear_solves=18),complete=False)['linear_solves']
            for index,matrix in enumerate(selected['rows']):
                name=f'proposal-{index:03d}.json'
                if base+name not in envelope['artifacts']:
                    failures.append(dict(index=index,reason='no returned proposal'));continue
                saved=s.artifact(identity,name)
                if saved['index']!=index or saved['matrix_sha256']!=digest(encoded(matrix)):
                    raise ValueError('proposal and source matrix differ')
                row=summarize(matrix,saved['proposal'],index=index);rows.append(row);proposals.append(saved)
            if base+'proposals.json' in envelope['artifacts'] and s.artifact(identity,'proposals.json')!=proposals:
                raise ValueError('aggregate proposal inventory differs')
        else:failures=[dict(index=i,reason='unexecuted task') for i in range(18)]
        if charges<len(rows) or charges>18:raise ValueError('solve accounting differs from returned proposals')
        return dict(version='timing-cell-proposal-report-v1',verified=True,selected=18,complete=len(rows),
            linear_successes=sum(v['linear_success'] for v in rows),rows=rows,failures=failures,charged_linear_solves=charges,
            elapsed_s=s.summary['elapsed_s'],manifest_sha256=s.completion['manifest_sha256'],
            summary_sha256=s.completion['summary_sha256'],parent_completion=selected['parent_completion'],
            native_calls=0,nonlinear_fit_starts=0,actual_cost_evaluated=False,labels_changed=False,
            scientific_decision='abstain',confidence_calibrated=False)
    finally:s.close()


def render(report):
    lines=['# Linear steps constrained to timing intervals','',
        f"Computed {report['complete']}/18 proposals; {report['linear_successes']} linear solves succeeded.",
        'These are predictions from saved matrices. No proposed point has been evaluated in the physical model.',
        'Original fit labels and all physical bounds are unchanged.','',
        '| Original point | Side | Distance from boundary | Predicted cost change | Proposed timing offset |',
        '|---|---|---:|---:|---:|']
    for row in report['rows']:
        lines.append(f"| {row['identity']} | {row['side']} | {row['spacing_s']*1e6:g} µs | "
                     f"{row['predicted_delta_from_original']:.6g} | {row['proposed_time_offset_s']:.9g} s |")
    lines+=['','All feasible sides and spacings are retained. Related matrices are not independent trials.',
        'A native evaluation is a separate gate before any solver or uncertainty claim.','',
        '[Results CSV](results.csv) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).']
    return '\n'.join(lines)+'\n'


def publish(root,prefix,*,qualification,output='docs/saved-timing-cell-proposals'):
    import json
    from pathlib import Path
    from lll.timing_cell_study import sources,PLAN
    from lll.studies.qualification import checked
    from lll.airquantumgrav_inventory import environment
    from lll.studies.artifacts import atomic,encoded,digest
    from lll.ilvis0_control_publication import publish as package,check
    from lll.timing_arithmetic_report import csv_bytes
    root=Path(root).resolve();data=root/prefix;public=root/output
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    request,tests=checked(root,qualification,sources=sources(root),environment=environment(),minimum_tests=20,
        required_tests=['test_cell_report_independently_recomputes_objective_and_preserves_original_failure',
            'test_cell_step_matches_independent_face_enumeration[a0-b0]'])
    report=inspect(root,prefix);package(data,public,render(report),plan=PLAN)
    extras={'results.csv':csv_bytes(report['rows']),'artifacts/publication/verified-report.json':encoded(report),
        'artifacts/publication/qualification-request.json':request,'artifacts/publication/qualification-report.xml':tests,
        'artifacts/publication/reporter-source.py':Path(__file__).read_bytes(),
        'artifacts/publication/reporter-test.py':(root/'analysis/tests/test_timing_cell_report.py').read_bytes()}
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in extras.items():atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt));check(data,public)
    if encoded(inspect(root,output))!=encoded(report):raise ValueError('public replay differs')
    return dict(publication=output,artifacts=len(receipt['artifacts']),compaction_pending=True,native_calls=0)
