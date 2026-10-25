# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only audit of generated known-correction forecasts and charge journals."""
import json
import math

from lll.airquantumgrav_geographic_report import error_metrics,_same_metrics,construction_counts


def _close(a,b):
    if not math.isfinite(a) or not math.isfinite(b) or not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-9):
        raise ValueError('saved comparison differs from its complete arrays')


def case_gate(result,forecast,comparison,correction,recipe):
    n=recipe['queries'];scale=[6378137.,6378137.,1.]
    arrays=[forecast['coordinates'],forecast['errors_neu_m'],forecast['uncorrected_errors_neu_m'],
        comparison['value_coordinates'],comparison['shifted_coordinates'],comparison['analytic_direction_scaled_m']]
    if any(len(a)!=n or any(len(v)!=3 or any(not math.isfinite(x) for x in v) for v in a) for a in arrays):
        raise ValueError('complete finite saved query arrays required')
    columns=correction['active_parameters']
    expected={name+'_'+a for name in ('attitude','velocity','position','gyro_bias','accel_bias','gyro_gain','accel_gain','lever') for a in 'xyz'}
    expected.update(('gravity_delta','time_offset','earth_removal'))
    if (len(columns)!=27 or set(columns)!=expected or len(comparison['direction'])!=27
            or not correction['known_corrections_supplied_not_estimated']
            or comparison['step']!=recipe['difference_step']):
        raise ValueError('complete nuisance columns and unchanged finite-difference rule required')
    corrected=error_metrics(forecast['errors_neu_m']);uncorrected=error_metrics(forecast['uncorrected_errors_neu_m'])
    for value,key in [(corrected,'corrected'),(uncorrected,'uncorrected')]:
        _same_metrics(value,result[key]);_same_metrics(value,forecast[key])
    value_error=max(abs((a[j]-b[j])*scale[j]) for a,b in zip(forecast['coordinates'],comparison['value_coordinates'],strict=True) for j in range(3))
    difference=max(abs(d[j]-(b[j]-a[j])*scale[j]/comparison['step'])
        for a,b,d in zip(comparison['value_coordinates'],comparison['shifted_coordinates'],comparison['analytic_direction_scaled_m'],strict=True) for j in range(3))
    size=max(abs(x) for v in comparison['analytic_direction_scaled_m'] for x in v)
    for measured,key in [(value_error,'value_disagreement_m'),(difference,'derivative_disagreement_m')]:
        _close(measured,result[key]);_close(measured,comparison[key])
    _close(size,comparison['derivative_size_m'])
    checks={k:corrected[k]<=limit for k,limit in recipe['accuracy'].items()}
    checks.update(value_agreement=value_error<=recipe['value_agreement_m'],all_columns_retained=True,
        mixed_derivative=difference<=recipe['derivative_absolute_m']+recipe['derivative_relative']*size)
    if (result['checks']!=checks or comparison['checks']!=checks
            or not result['all_columns_retained'] or result['passed']!=all(checks.values())):
        raise ValueError('saved observation gate labels differ from the frozen rules')
    return dict(passed=all(checks.values()),corrected=corrected,uncorrected=uncorrected,
        value_disagreement_m=value_error,derivative_disagreement_m=difference,derivative_size_m=size)


def native_accounting(raw,freeze,identities,*,per_call_visits=None):
    import sqlite3
    from lll.studies.journal import inspect_snapshot
    inspect_snapshot(raw,freeze);db=sqlite3.connect(':memory:')
    counts={i:dict(value=0,tangent=0,packet_visits=0) for i in identities}
    try:
        db.deserialize(raw);db.execute('PRAGMA query_only=ON')
        for (payload,) in db.execute('SELECT payload FROM events ORDER BY number'):
            row=json.loads(payload);identity=row['identity']
            if identity not in counts:raise ValueError('unknown native-accounting identity')
            if row['resource'] is None:continue
            record=row.get('record',{});kind=record.get('kind');visits=record.get('packet_visits')
            if (record.get('phase')!='fit' or kind not in ('value','tangent') or type(visits) is not int or visits<0
                    or (per_call_visits is not None and visits!=per_call_visits)):
                raise ValueError('complete declared native operation metadata required')
            counts[identity][kind]+=1;counts[identity]['packet_visits']+=visits
        return counts
    finally:db.close()


def inspect(root,prefix='data/esa-observation-controls-20261023'):
    from itertools import product
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix);rows=[];native={};binaries={'value':set(),'tangent':set()}
    try:
        r=study.input('recipe');env=study.input('qualification-environment');n=round(r['duration_s']*r['rate_hz'])
        expected=set(product(r['models'],r['latitudes_deg'],r['removals'],r['signs']))
        actual={(t['payload']['model'],t['payload']['latitude_deg'],t['payload']['removal'],t['payload']['sign']) for t in study.tasks.values()}
        if len(study.tasks)!=24 or len(expected)!=24 or actual!=expected:
            raise ValueError('complete frozen 24-case observation matrix required')
        limits=dict(constructed_intervals=n,generated_samples=n+1+r['queries']);charged={k:0 for k in study.summary['charged']}
        for shard in range(study.manifest['allocation']['workers']):
            assigned={i for i,t in study.tasks.items() if t['shard']==shard}
            native.update(native_accounting(study.read(f'shards/{shard:03d}/charges/journal.sqlite',raw=True),
                study.completion['manifest_sha256'],assigned,per_call_visits=n*r['queries']))
        for identity,task in study.tasks.items():
            if identity not in study.rows:continue
            envelope=study.envelope(identity);result=envelope['result'];spec=task['payload']
            for k in charged:charged[k]+=envelope['charged'][k]
            for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
            full='corrected' in result;journal='artifacts/'+identity+'/construction.sqlite'
            counts=construction_counts(study.read(journal,envelope['artifacts'][journal],raw=True),
                study.completion['manifest_sha256'],identity,limits,complete=full) if journal in envelope['artifacts'] else None
            operations=native[identity]
            if (operations['value']+operations['tangent']!=envelope['charged']['native_calls']
                    or operations['packet_visits']!=envelope['charged']['packet_visits']):
                raise ValueError('saved operation kinds and envelope charges differ')
            row=dict(identity=identity,spec=spec,result=result,complete=full,construction_counts=counts,native=operations)
            if full:
                if (any(result[k]!=v for k,v in spec.items()) or counts!=limits
                        or operations!=dict(value=3,tangent=1,packet_visits=4*n*r['queries'])
                        or not result['known_corrections_supplied_not_estimated'] or result['initialization_estimator_qualified']
                        or result['constructed_intervals']!=n or result['generated_samples']!=limits['generated_samples']):
                    raise ValueError('observation identity, scope or exact charged work differs')
                meta=study.artifact(identity,'compilation.json')
                for kind,filename,compiler in [('value','ilvis0_native.c','cc'),('tangent','ilvis0_tangent.cpp','c++')]:
                    if (meta[kind]['source_sha256']!=study.manifest['sources']['analysis/lll/'+filename]
                            or meta[kind]['compiler']!=env['compilers'][compiler]):
                        raise ValueError('observation compiled source/environment differs')
                    binaries[kind].add(meta[kind]['binary_sha256'])
                forecast=study.artifact(identity,'forecast.json')
                if forecast['times_s']!=[r['query_start_s']+i*r['query_step_s'] for i in range(r['queries'])]:
                    raise ValueError('observation query grid differs')
                row['checked']=case_gate(result,forecast,study.artifact(identity,'comparison.json'),study.artifact(identity,'corrections.json'),r)
            elif result['passed']:raise ValueError('unfinished observation control cannot pass')
            rows.append(row)
        if any(len(v)>1 for v in binaries.values()) or charged!=study.summary['charged']:
            raise ValueError('compiled binaries or sealed charge totals differ')
        passing=sum(v['result']['passed'] for v in rows);families=[]
        for model in r['models']:
            group=[v for v in rows if v['spec']['model']==model];full=[v for v in group if v['complete']]
            families.append(dict(model=model,returned=len(group),complete=len(full),passed=sum(v['result']['passed'] for v in group),
                maximum_horizontal_rms_m=max((v['checked']['corrected']['horizontal_rms_m'] for v in full),default=None),
                maximum_height_rms_m=max((v['checked']['corrected']['vertical_rms_m'] for v in full),default=None),
                maximum_spatial_error_m=max((v['checked']['corrected']['maximum_3d_m'] for v in full),default=None)))
        return dict(prefix=prefix,total=24,returned=len(rows),passing=passing,qualified=len(rows)==passing==24,
            rows=rows,families=families,charged=charged,elapsed_s=study.summary['elapsed_s'],
            construction_totals={k:sum((v['construction_counts'] or {}).get(k,0) for v in rows) for k in limits},
            construction_accounting_complete=all(v['construction_counts'] is not None for v in rows),
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            numerical_work=0,original_reads=0,observed_starts=0,known_corrections_supplied_not_estimated=True,
            initialization_estimator_qualified=False,scientific_decision='abstain')
    finally:study.close()


def render(report):
    lines=['# Antenna and calibration calculation checks','',
        f"**{report['passing']}/{report['total']} generated cases passed.**",'',
        'These controls add known sensor bias/gain errors, antenna displacement,',
        'starting-state errors, gravity offsets and latency to the earlier',
        'independent twenty-minute maneuvering trajectories. The existing forecast',
        'receives the exact correction vector and retains all 27 nuisance columns.','',
        '**The corrections are supplied, not estimated.** Passing checks their',
        'application; it does not show that real observations can determine them.',
        'No ESA recording is read and no Earth-model decision is made.','',
        '| Generating geometry | Passed | Largest horizontal RMS | Largest height RMS | Largest spatial error |',
        '|---|---:|---:|---:|---:|']
    labels=dict(sphere_rotating='Globe with specified field',sphere_still='Globe with zero field',flat_still='Tested disc')
    for row in report['families']:
        number=lambda k:'Unavailable' if row[k] is None else f"{row[k]:.6g} m"
        lines.append('| '+' | '.join([labels[row['model']],f"{row['passed']}/8",number('maximum_horizontal_rms_m'),
            number('maximum_height_rms_m'),number('maximum_spatial_error_m')])+' |')
    lines+=['', 'The unchanged screen requires horizontal and height RMS at most 1 m',
        'and maximum spatial error at most 5 m. Separate checks compare value',
        'and derivative predictions and one mixed calibration direction.',
        'Zero sensor/state-correction errors are preserved as diagnostics.',
        'All use the declared linear-point sampling hypothesis.','',
        f"The run used {report['charged']['native_calls']} native calls in {report['elapsed_s']/60:.2f} minutes.",
        'Saved-only verification checks artifact hashes, complete error series,',
        'comparison labels, compiled sources and construction journals. The main',
        'journal distinguishes one derivative and three value calls per full case.',
        'Publication performs no propagation or new fitting.','',
        'Training-only initialization and estimation of unknown calibration remain',
        'open, as do receiver-error assessment, actual sampling behavior and revised',
        'selection. The original zero-eligible inventory and all reserved confirmation',
        'groups remain unchanged.','',
        '[Frozen plan](PLAN.md) · [Earlier geographic checks](../esa-geographic-rate-controls/README.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md)']
    if not report['construction_accounting_complete']:
        lines+=['','Some failed cases lack a sealed construction journal; no complete construction accounting is claimed.']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/esa-observation-controls-20261023',output='docs/esa-observation-controls'):
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('observation publication is already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/esa-observation-controls/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in [('verified-report.json',encoded(report)),('reporter.py',Path(__file__).read_bytes())]:
        name='artifacts/publication/'+name;atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
