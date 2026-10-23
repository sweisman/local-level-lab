# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only reporting of closed nonlinear calibration-witness searches."""
from fractions import Fraction as F
import json
from pathlib import Path
from .studies.artifacts import ArchiveStore,digest,encoded,safe_path


def point_spreads(problem,records):
    """Lower spreads from explicit feasible saved points; never an outer enclosure."""
    from .ilvis0_truth_probes import audit_pair
    feasible=[];rejected=[]
    for name,record in records.items():
        check=audit_pair(problem,record,record)
        (feasible if all(check['training_feasible']) else rejected).append(name)
    if not feasible:raise ValueError('at least one feasible saved witness required')
    axes=[]
    for axis in range(3):
        low=min(feasible,key=lambda k:F(records[k]['prediction'][-1][axis]))
        high=max(feasible,key=lambda k:F(records[k]['prediction'][-1][axis]))
        check=audit_pair(problem,records[low],records[high])
        axes.append(dict(pair=[low,high],separation_lower_exact=check['separation_lower_exact'][axis],
            exceeds_target=check['separation_exceeds_target'][axis]))
    return dict(feasible=feasible,rejected=rejected,axes=axes,outer_bound_qualified=False,
        numerical_error_bound_qualified=False,observational_coverage_qualified=False,
        interpretation='represented native predictions under the supplied numerical guard')


def calibration_trace(problem,origin,first,second,limits):
    """Describe coordinate changes and local tangent cancellations, without refitting."""
    from .ilvis0_truth_probes import audit_pair
    from .ilvis0_feasible_steps import audit_step
    if len(limits)!=27:raise ValueError('all27 physical scales required')
    audit_step(problem,origin,origin['point'],radius=.001)
    check=audit_pair(problem,first,second)
    if not all(check['training_feasible']):raise ValueError('two original feasible calibrations required')
    delta=[F(b)-F(a) for a,b in zip(first['point'],second['point'],strict=True)]
    coordinates=[];jac=origin['jacobian'][-1];units=list(map(F,problem['coordinate_scale']))
    for i,(d,limit) in enumerate(zip(delta,limits,strict=True)):
        physical=d*F(limit)
        if i==26:physical=physical/2 if problem['binding']['profile'] else F(0)
        coordinates.append(dict(index=i,normalized_change_exact=str(d),physical_change_exact=str(physical),
            linear_future_change_exact=[str(F(jac[j][i])*d*units[j]) for j in range(3)]))
    linear=[sum((F(c['linear_future_change_exact'][j]) for c in coordinates),F(0)) for j in range(3)]
    actual=[(F(second['prediction'][-1][j])-F(first['prediction'][-1][j]))*units[j] for j in range(3)]
    return dict(coordinates=coordinates,linear_change_exact=list(map(str,linear)),
        actual_change_exact=list(map(str,actual)),nonlinear_remainder_exact=list(map(str,[a-b for a,b in zip(actual,linear)])),
        tangent_only=True,causal_decomposition=False,outer_bound_qualified=False,observational_coverage_qualified=False)


def trace_first_steps(root,prefix='data/ilvis0-feasible-step-controls-20261022'):
    """Trace the saved north-extreme pairs; numerical imports only supply the schema."""
    from .ilvis0_shape import PARAMETERS
    from . import ilvis0_estimator,ilvis0_shape
    from .studies.closed import ClosedStudy
    report=inspect_first_steps(root,prefix);study=ClosedStudy(root,prefix);cases=[]
    try:
        for module in (ilvis0_estimator,ilvis0_shape):
            path=Path(module.__file__).resolve();name=path.relative_to(study.root).as_posix()
            if digest(path.read_bytes())!=study.manifest['sources'][name]:
                raise ValueError('parameter schema source differs from original freeze')
        for c in report['cases']:
            task=next(t for t in study.tasks.values() if
                (t['payload']['model'],t['payload']['profile'])==(c['model'],c['profile']))
            spec=task['payload'];bundle=study.input(spec['bundle_key']);case=study.input(spec['case_key'])
            pair=c['spread']['axes'][0]['pair']
            trace=calibration_trace(c['problem'],bundle['origin'],c['points'][pair[0]],c['points'][pair[1]],
                case['configuration']['limits'])
            for coordinate,name in zip(trace['coordinates'],PARAMETERS,strict=True):coordinate['name']=name
            cases.append(dict(model=c['model'],profile=c['profile'],pair=pair,trace=trace))
        return dict(cases=cases,source_study=prefix,source_manifest_sha256=study.completion['manifest_sha256'],
            renderer_sha256=digest(Path(__file__).read_bytes()),numerical_work=0,optimizer_starts=0,
            observations_created=0,observational_coverage_qualified=False)
    finally:study.close()


def inspect_first_steps(root,prefix):
    from .ilvis0_feasible_step_controls import inspect as inspect_controls
    from .studies.closed import ClosedStudy
    controls=inspect_controls(root,prefix);study=ClosedStudy(root,prefix);cases=[]
    try:
        for model in range(3):
            for profile in (False,True):
                points={};problem=None
                for identity,task in study.tasks.items():
                    spec=task['payload']
                    if (spec['model'],spec['profile'])!=(model,profile):continue
                    bundle=study.input(spec['bundle_key'])
                    if problem is not None and problem!=bundle['problem']:raise ValueError('different source problems')
                    problem=bundle['problem'];points['origin']=bundle['origin']
                    if identity not in study.rows or not study.rows[identity]['passed']:continue
                    envelope=study.envelope(identity);path='artifacts/'+identity+'/candidate-audit.json'
                    if path in envelope['artifacts']:
                        points[identity]=study.artifact(identity,'candidate-audit.json')['record']
                if problem is None:raise ValueError('complete six-case matrix required')
                cases.append(dict(model=model,profile=profile,problem=problem,points=points,
                    spread=point_spreads(problem,points)))
        return dict(controls=controls,cases=cases,manifest_sha256=study.completion['manifest_sha256'],
            numerical_work=0,observational_coverage_qualified=False)
    finally:study.close()


def render_first_step_spreads(report):
    labels=['Globe + field','Globe, zero field','Stationary disc'];cases=report['cases']
    exceeded=sum(any(a['exceeds_target'] for a in c['spread']['axes']) for c in cases)
    text=['# What the accepted alternatives show','',
        'These are generated-data sensitivity checks, not measured aircraft position errors.',
        '',f"**{exceeded}/6 cases** contain accepted saved alternatives whose later predictions differ "
        'by more than at least one original width target. The limits are 20 m north, 20 m east and 50 m height.',
        '', '| Model | Processing case | Feasible saved points | North spread (m) | East spread (m) | Height spread (m) |',
        '|---|---|---:|---:|---:|---:|']
    for c in cases:
        spread=c['spread'];values=[f"{float(F(a['separation_lower_exact'])):.3f}" for a in spread['axes']]
        text.append('| '+' | '.join([labels[c['model']],'Profiled removal' if c['profile'] else 'Zero removal',
            str(len(spread['feasible']))]+values)+' |')
    text+=['', 'Each number is a **lower spread among sampled feasible calibrations**, with the declared '
        'numerical guard subtracted. It is not an upper uncertainty bound. Different axes may use different '
        'pairs; the exact records and pair identities are preserved in the evidence.',
        '', 'All alternatives use the same earlier observations, physical bounds and input measurements. '
        'If two allowed calibrations exceed a width target, a more efficient enclosure or optimizer cannot '
        'make a valid range containing both narrower than that separation. Whether the declared calibration '
        'and error assumptions adequately describe aircraft recordings is a separate question.',
        '', 'The numerical guard has not been independently qualified for the entire recording. These '
        'results describe the saved native calculation under that assumption; they do not establish '
        'statistical confidence or qualify V01. The 53-stretch model preferences are unchanged.',
        '', '[First-step outcomes](README.md) · [Fixed method](PLAN.md) · '
        '[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md)']
    return '\n'.join(text)+'\n'


def publish_first_steps(root,prefix,output='docs/ilvis0-feasible-step-controls'):
    from .ilvis0_control_publication import publish as package
    from .ilvis0_feasible_step_controls import render as render_controls
    from .studies.artifacts import atomic
    from .studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    report=inspect_first_steps(root,prefix)
    package(data,public,render_controls(report['controls']),plan='docs/ilvis0-feasible-step-controls/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_text())
    artifacts={'INTERPRETATION.md':render_first_step_spreads(report).encode(),
        'artifacts/publication/comparison.json':encoded(report),
        'artifacts/publication/renderer.py':Path(__file__).read_bytes()}
    for name,content in artifacts.items():atomic(public/name,content);receipt['artifacts'][name]=digest(content)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)


def step_diagnostics(problem,initial,trial):
    """Compare a saved tangent prediction with a saved nonlinear output."""
    observations=problem['observations'];n=len(observations);units=list(map(F,problem['coordinate_scale']))
    p=list(map(F,initial['point']));q=list(map(F,trial['point']))
    old=initial['prediction'];new=trial['prediction'];jac=initial['jacobian']
    if (not n or len(p)!=27 or len(q)!=27 or len(units)!=3 or any(u<=0 for u in units)
            or len(old)!=n+1 or len(new)!=n+1 or len(jac)!=n+1
            or any(len(row)!=3 for row in observations+old+new+jac)
            or any(len(row)!=27 for epoch in jac for row in epoch)):
        raise ValueError('complete saved positions and all27 tangent columns required')
    delta=[b-a for a,b in zip(p,q,strict=True)]
    linear=[];actual=[]
    for i in range(n):
        for j in range(3):
            change=sum((F(c)*d for c,d in zip(jac[i][j],delta,strict=True)),F(0))
            linear.append((F(old[i][j])+change-F(observations[i][j]))*units[j])
            actual.append((F(new[i][j])-F(observations[i][j]))*units[j])
    future_linear=sum((F(c)*d for c,d in zip(jac[-1][0],delta,strict=True)),F(0))*units[0]
    return dict(maximum_normalized_step_exact=str(max(map(abs,delta))),
        linear_training_max_exact=str(max(map(abs,linear))),native_training_max_exact=str(max(map(abs,actual))),
        nonlinear_discrepancy_max_exact=str(max(abs(a-b) for a,b in zip(actual,linear,strict=True))),
        linear_north_change_exact=str(future_linear),
        native_north_change_exact=str((F(new[-1][0])-F(old[-1][0]))*units[0]))


def inspect(root,prefix):
    from .ilvis0_truth_probes import audit_pair
    safe_path(root,prefix);store=ArchiveStore(root);catalog=store.catalog();cache={}
    def raw(name,expected=None):
        safe_path(root,prefix+'/'+name)
        if name not in cache:cache[name]=store._read(prefix+'/'+name,catalog)
        value=cache[name]
        if expected is not None and digest(value)!=expected:raise ValueError('closed artifact hash mismatch: '+name)
        return value
    def read(name,expected=None):return json.loads(raw(name,expected))
    try:completion=read('completion.json')
    except FileNotFoundError as exc:raise ValueError('closed study required before reporting') from exc
    manifest=read('manifest.json',completion['manifest_sha256']);summary=read('summary.json',completion['summary_sha256'])
    if completion['state'] not in ('complete','terminal') or summary['state']!=completion['state']:
        raise ValueError('matching closed completion and summary required')
    tasks=manifest['tasks'];matrix={(t['payload']['model'],t['payload']['profile'],t['payload']['sign']) for t in tasks}
    if (len(tasks)!=12 or len({t['identity'] for t in tasks})!=12
            or matrix!={(m,p,s) for m in range(3) for p in (False,True) for s in (-1,1)}):
        raise ValueError('complete twelve-direction matrix required')
    if digest(Path(audit_pair.__code__.co_filename).read_bytes())!=manifest['sources']['analysis/lll/ilvis0_truth_probes.py']:
        raise ValueError('saved-pair arithmetic source changed since the freeze')
    results={r['identity']:r for r in summary['results']}
    if (len(results)!=len(summary['results']) or not set(results)<={t['identity'] for t in tasks}
            or summary['total']!=12 or summary['completed']!=len(results)
            or summary['passed']!=(len(results)==12 and all(r['passed'] for r in results.values()))
            or (summary['state']=='complete')!=summary['passed']):
        raise ValueError('closed outcome counts differ')
    witnesses={};directions=[]
    for task in tasks:
        identity=task['identity'];spec=task['payload'];row=results.get(identity);result=None;feasible=None;proposals=None
        step=None;parent_values=None;parent_jacobians=None
        if row is not None:
            envelope=read(row['artifact'],row['artifact_sha256']);result=envelope['result']
            if (envelope['identity']!=identity or envelope['manifest_sha256']!=completion['manifest_sha256']
                    or digest(encoded(result))!=envelope['result_sha256'] or row['passed']!=result['passed']):
                raise ValueError('result identity or hash differs')
            for name,sha in envelope['artifacts'].items():raw(name,sha)
            if result['passed']:
                for key in ('model','profile','sign'):
                    if result[key]!=spec[key]:raise ValueError('reported candidate differs from its task')
                base='artifacts/'+identity+'/'
                witness=read(base+'verified-witness.json',envelope['artifacts'][base+'verified-witness.json'])
                kernel=read(base+'kernel.json',envelope['artifacts'][base+'kernel.json'])
                inp=manifest['inputs'][spec['bundle_key']];bundle=read(inp['path'],inp['sha256'])
                problem=witness['problem'];binding=problem['binding']
                if (problem!=bundle['problem'] or witness['source_hashes_verified'] is not True
                        or witness['bitwise_native_replay'] is not True
                        or binding['case_sha256']!=manifest['inputs'][spec['case_key']]['sha256']
                        or binding['source_sha256']!=manifest['sources']['analysis/lll/ilvis0_tangent.cpp']
                        or kernel['source_sha256']!=binding['source_sha256'] or kernel['compiler']!=spec['compiler']
                        or (binding['model'],binding['profile'])!=(spec['model'],spec['profile'])):
                    raise ValueError('verified witness source, input or replay binding differs')
                check=audit_pair(problem,witness['record'],witness['record'])
                if not all(check['training_feasible']):raise ValueError('saved witness fails exact training check')
                names=[name for name in envelope['artifacts'] if name.startswith(base+'feasibility-')]
                if 'search_batches' in result and len(names)!=result['search_batches']:
                    raise ValueError('saved proposal feasibility counts differ')
                proposals=len(names) if names else None
                feasible=sum(all(read(name,envelope['artifacts'][name])['audit']['training_feasible'])
                    for name in names) if names else None
                first=base+'native-001.json';second=base+'native-002.json'
                if first in envelope['artifacts'] and second in envelope['artifacts']:
                    origin=read(first,envelope['artifacts'][first])['output']
                    trial=read(second,envelope['artifacts'][second])['output']
                    step=step_diagnostics(problem,origin,trial)
                    old=bundle['initial_records']
                    parent_values=origin['prediction'][:5]==[r['prediction'] for r in old]
                    parent_jacobians=origin['jacobian'][:5]==[r['jacobian'] for r in old]
                witnesses[(spec['model'],spec['profile'],spec['sign'])]=dict(witness,initial=bundle['initial'])
        directions.append(dict(identity=identity,model=spec['model'],profile=spec['profile'],sign=spec['sign'],
            verified=result is not None and result['passed'],native_calls=result.get('native_evaluations',0) if result else 0,
            feasible_proposals=feasible,proposals=proposals,
            first_step=step,initial_values_match_parent=parent_values,initial_jacobians_match_parent=parent_jacobians,
            stopping=result.get('stopping_reason',result.get('reason','Rejected')) if result else 'Not completed'))
    cases=[]
    for model in range(3):
        for profile in (False,True):
            a=witnesses.get((model,profile,-1));b=witnesses.get((model,profile,1));audit=None
            if a is not None and b is not None:
                if a['problem']!=b['problem']:raise ValueError('pair uses different original observation problems')
                audit=audit_pair(a['problem'],a['record'],b['record'])
            cases.append(dict(model=model,profile=profile,complete=audit is not None,
                distinct=audit is not None and a['record']['point']!=b['record']['point'],
                initial_only=audit is not None and a['record']['point']==a['initial'] and b['record']['point']==b['initial'],
                separation_lower_m=list(map(lambda v:float(F(v)),audit['separation_lower_exact'])) if audit else None,
                audit=audit,target_exceeded=audit is not None and any(audit['separation_exceeds_target'])))
    return dict(prefix=prefix,state=summary['state'],cases=cases,directions=directions,
        complete_pairs=sum(c['complete'] for c in cases),target_exceedances=sum(c['target_exceeded'] for c in cases),
        distinct_pairs=sum(c['distinct'] for c in cases),initial_only_pairs=sum(c['initial_only'] for c in cases),
        completed=len(results),native_calls=summary['charged']['native_calls'],elapsed_s=summary['elapsed_s'],
        manifest_sha256=completion['manifest_sha256'],summary_sha256=completion['summary_sha256'],numerical_work=0)


def render(report):
    labels=('Globe, specified field','Globe, zero field','Flat disc')
    lines=['# Can the same observations allow different predictions?','',
        f'**{report["complete_pairs"]}/6 pairs checked; {report["distinct_pairs"]}/6 contain different calibrations.**',
        f'{report["target_exceedances"]}/6 exceed a width target.','',
        'These are generated software cases, not new aircraft findings. Each search',
        'uses the original five earlier observations and all original calibration',
        'limits. Future observations are excluded. The results are sampled spreads,',
        'not outer uncertainty bounds or global optima.','',
        '| Candidate | Removal | Lower sampled N / E / height spread, m | Outcome |',
        '|---|---|---|---|']
    for case in report['cases']:
        values=case['separation_lower_m']
        spread='Unavailable' if values is None else ' / '.join(f'{v:.3f}' for v in values)
        status=('Incomplete pair' if not case['complete'] else 'Same starting calibration' if case['initial_only']
            else 'Target exceeded' if case['target_exceeded'] else 'No target violation found')
        lines.append(f'| {labels[case["model"]]} | {"Profiled" if case["profile"] else "None"} | {spread} | {status} |')
    lines+=['',f'In {report["initial_only_pairs"]}/6 cases, both directions returned the same starting calibration.',
        'A zero displayed spread there means the search found no alternative; it is',
        'not zero uncertainty. Earlier accepted probes remain valid.','',
        'Displayed values are rounded; target comparisons use exact fractions.',
        'The lower spreads subtract the supplied 0.00001 m per-coordinate',
        'numerical-error allowance from both predictions. This allowance is a test',
        'assumption, not a qualified whole-program error bound. A physical impossibility',
        'claim needs that additional qualification. Finding no large spread proves',
        'neither uniqueness nor useful prediction ranges.','',
        '| Search | Native batches | Training-compatible proposals | Stopping reason |', '|---|---:|---:|---|']
    for row in report['directions']:
        proposals='Unavailable' if row['proposals'] is None else f'{row["feasible_proposals"]}/{row["proposals"]}'
        lines.append(f'| {row["identity"]} | {row["native_calls"]} | {proposals} | {row["stopping"]} |')
    steps=[r['first_step'] for r in report['directions'] if r['first_step'] is not None]
    if steps:
        def span(key):
            values=[float(F(s[key])) for s in steps]
            return f'{min(values):.2f}–{max(values):.2f}'
        matches=sum(r['initial_values_match_parent'] is True and r['initial_jacobians_match_parent'] is True
            for r in report['directions'])
        linear_failed=sum(F(s['linear_training_max_exact'])>1 for s in steps)
        native_failed=sum(F(s['native_training_max_exact'])>1 for s in steps)
        lines+=['',f'The initial batched values and Jacobians match the saved parent in {matches}/12 searches.',
            f'The first proposed moves predicted training errors of {span("linear_training_max_exact")} m',
            f'even in the local linear calculation; their actual errors were {span("native_training_max_exact")} m.',
            f'{linear_failed}/{len(steps)} linear predictions and {native_failed}/{len(steps)} actual outputs exceed the 1 m training limit.']
        if linear_failed or native_failed:
            lines+=['The next method needs controlled, training-compatible steps',
                'before another full-history search.']
    lines+=['',f'All {report["completed"]}/12 saved outcomes are retained; {report["native_calls"]} native batches',
        f'were charged over {report["elapsed_s"]/60:.2f} minutes. An optimizer stopping',
        'without success can still supply a checked point; it cannot establish an optimum.','',
        'The 53-stretch comparisons are unchanged. Aircraft prediction uncertainty,',
        'whole-period coverage and the real observation-error law remain unqualified.','',
        '[Method and limits](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md) ·',
        '[Previous bound comparison](../ilvis0-long-remainder-feasibility/README.md).','']
    return '\n'.join(lines)


def publish(root,prefix,output,*,plan):
    from .ilvis0_control_publication import publish as package
    from .studies.artifacts import atomic
    from .studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan=plan)
    receipt=json.loads((public/'evidence-receipt.json').read_text())
    source='artifacts/publication/renderer.py';source_bytes=Path(__file__).read_bytes()
    metadata='artifacts/publication/report-provenance.json'
    comparison='artifacts/publication/comparison.json';comparison_bytes=encoded(report)
    content=encoded(dict(renderer_sha256=digest(source_bytes),manifest_sha256=report['manifest_sha256'],
        summary_sha256=report['summary_sha256'],numerical_work=0,
        renderer_package_path='analysis/lll/ilvis0_witness_publication.py'))
    atomic(public/source,source_bytes);atomic(public/metadata,content);atomic(public/comparison,comparison_bytes)
    receipt['artifacts'].update({source:digest(source_bytes),metadata:digest(content),comparison:digest(comparison_bytes)})
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
