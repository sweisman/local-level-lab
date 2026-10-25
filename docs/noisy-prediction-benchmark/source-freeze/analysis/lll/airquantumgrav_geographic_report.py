# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit sealed generated trajectories without propagation or truth generation."""
import json
import math
import re


def error_metrics(errors):
    if not errors or any(len(v)!=3 or any(not math.isfinite(x) for x in v) for v in errors):
        raise ValueError('complete finite three-axis saved errors required')
    rms=[math.sqrt(math.fsum(v[j]*v[j] for v in errors)/len(errors)) for j in range(3)]
    result=dict(rms_neu_m=rms,horizontal_rms_m=math.hypot(*rms[:2]),vertical_rms_m=rms[2],
        maximum_3d_m=max(math.hypot(*v) for v in errors),total_rms_m=math.hypot(*rms))
    if any(not math.isfinite(v) for v in rms+list(result.values())[1:]):raise ValueError('finite saved error metrics required')
    return result


def _same_metrics(actual,saved):
    for key,value in actual.items():
        pairs=zip(value,saved[key],strict=True) if isinstance(value,list) else [(value,saved[key])]
        if any(not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-9) for a,b in pairs):
            raise ValueError('saved metrics differ from the complete error series')


def case_gate(result,phases,recipe):
    if len(phases)!=2 or result['method'] not in recipe['refinement_factor']:
        raise ValueError('both resolutions and a declared sampling method required')
    measured=[]
    for label,phase in zip(('coarse','fine'),phases,strict=True):
        if len(phase['errors_neu_m'])!=recipe['queries']:raise ValueError('complete fixed query grid required')
        value=error_metrics(phase['errors_neu_m']);_same_metrics(value,phase['metrics']);_same_metrics(value,result[label])
        measured.append(value)
    coarse,fine=measured;method=result['method'];required=method=='linear_points'
    refinement=fine['maximum_3d_m']<=recipe['refinement_factor'][method]*coarse['maximum_3d_m']+recipe['refinement_allowance_m']
    accuracy={k:coarse[k]<=v for k,v in recipe['linear_accuracy'].items()}
    passed=refinement and (not required or all(accuracy.values()))
    if (result['passed']!=passed or result['refinement_passed']!=refinement
            or result['accuracy_required']!=required or result['accuracy_checks']!=accuracy):
        raise ValueError('saved gate labels differ from the frozen accuracy/refinement criteria')
    return dict(passed=passed,refinement_passed=refinement,accuracy_required=required,
        absolute_accuracy=all(accuracy.values()),coarse=coarse,fine=fine)


def construction_counts(raw,freeze,identity,limits,*,complete=True):
    import sqlite3
    from lll.studies.journal import inspect_snapshot
    verified=inspect_snapshot(raw,freeze)
    if verified['starts']!=1:raise ValueError('one charged construction identity required')
    db=sqlite3.connect(':memory:')
    try:
        db.deserialize(raw);db.execute('PRAGMA query_only=ON')
        spec=json.loads(db.execute('SELECT spec FROM metadata').fetchone()[0])
        if spec['limits']!={identity:limits}:raise ValueError('construction limits differ from the frozen recipe')
        rows=list(db.execute('SELECT identity,resource,total FROM counts'))
        if any(i!=identity or resource not in limits for i,resource,value in rows):raise ValueError('unknown construction charge')
        values={resource:value for i,resource,value in rows};counts={key:values.get(key,0) for key in limits}
        if complete and counts!=limits:raise ValueError('incomplete declared construction work')
        return counts
    finally:db.close()


def inspect(root,prefix):
    from itertools import product
    from lll.studies.closed import ClosedStudy
    study=ClosedStudy(root,prefix);rows=[];raw_hashes={};binaries=set()
    try:
        r=study.input('recipe');expected=set(product(r['models'],r['latitudes_deg'],r['removals'],r['patterns'],r['methods']))
        actual={(t['payload']['model'],t['payload']['latitude_deg'],t['payload']['removal'],t['payload']['pattern'],t['payload']['method'])
            for t in study.tasks.values()}
        if len(study.tasks)!=72 or len(expected)!=72 or actual!=expected:raise ValueError('complete frozen 72-case matrix required')
        intervals=sum(round(r['duration_s']*hz) for hz in r['rates_hz'])
        limits=dict(constructed_intervals=r['maximum_constructed_intervals'],generated_samples=r['maximum_generated_samples'])
        env=study.input('qualification-environment')
        charged={key:0 for key in study.summary['charged']}
        for identity,task in study.tasks.items():
            if identity not in study.rows:continue
            envelope=study.envelope(identity);result=envelope['result'];spec=task['payload']
            for key in charged:charged[key]+=envelope['charged'][key]
            for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
            complete='coarse' in result
            journal_path='artifacts/'+identity+'/construction.sqlite'
            counts=construction_counts(study.read(journal_path,envelope['artifacts'][journal_path],raw=True),
                study.completion['manifest_sha256'],identity,limits,complete=complete) if journal_path in envelope['artifacts'] else None
            row=dict(identity=identity,spec=spec,result=result,complete=complete,construction_counts=counts)
            if complete:
                if (any(result[k]!=v for k,v in spec.items()) or counts!=limits
                        or envelope['charged']['native_calls']!=2 or envelope['charged']['packet_visits']!=intervals*r['queries']
                        or result['constructed_intervals']!=limits['constructed_intervals']
                        or result['generated_samples']!=limits['generated_samples']):
                    raise ValueError('saved identity or work accounting differs')
                meta=study.artifact(identity,'compilation.json')
                if (meta['source_sha256']!=study.manifest['sources']['analysis/lll/ilvis0_native.c']
                        or meta['compiler']!=env['compilers']['cc']):raise ValueError('compiled source/environment differs')
                binaries.add(meta['binary_sha256']);phases=[]
                for hz in r['rates_hz']:
                    phase=study.artifact(identity,f'rate-{hz}.json');phases.append(phase)
                    times=[r['query_start_s']+i*r['query_step_s'] for i in range(r['queries'])]
                    if (phase['times']!=times or phase['packets']!=round(r['duration_s']*hz)
                            or phase['rate_hz']!=hz or not phase['constructed_not_logged_increments']
                            or len(phase['coordinates'])!=len(times)
                            or any(len(v)!=3 or any(not math.isfinite(x) for x in v) for v in phase['coordinates'])):
                        raise ValueError('saved phase support or units differ')
                    for key,fields in [('original_rate_samples_sha256',('times','angular_rate_rads','specific_force_mps2')),
                                       ('constructed_arrays_sha256',('theta','dv','dt'))]:
                        if set(phase[key])!=set(fields) or any(not re.fullmatch('[0-9a-f]{64}',s) for s in phase[key].values()):
                            raise ValueError('complete generated input/converted-array hashes required')
                    shared=(spec['model'],spec['latitude_deg'],spec['removal'],spec['pattern'],hz)
                    if shared in raw_hashes and raw_hashes[shared]!=phase['original_rate_samples_sha256']:
                        raise ValueError('sampling methods did not use the same generated samples')
                    raw_hashes[shared]=phase['original_rate_samples_sha256']
                row['checked']=case_gate(result,phases,r)
            elif result['passed']:raise ValueError('unfinished case cannot pass')
            rows.append(row)
        if len(binaries)>1:raise ValueError('native binary changed between cases')
        if charged!=study.summary['charged']:raise ValueError('closed work totals differ from the sealed case charges')
        families=[]
        for method in r['methods']:
            group=[v for v in rows if v['spec']['method']==method];full=[v for v in group if v['complete']]
            families.append(dict(method=method,returned=len(group),complete=len(full),
                passed=sum(v['result']['passed'] for v in group),
                accuracy_passed=sum(v['checked']['absolute_accuracy'] for v in full),
                accuracy_required=method=='linear_points',
                maximum_coarse_3d_m=max((v['checked']['coarse']['maximum_3d_m'] for v in full),default=None),
                maximum_coarse_horizontal_rms_m=max((v['checked']['coarse']['horizontal_rms_m'] for v in full),default=None),
                maximum_coarse_height_rms_m=max((v['checked']['coarse']['vertical_rms_m'] for v in full),default=None)))
        passing=sum(v['result']['passed'] for v in rows)
        return dict(prefix=prefix,total=72,returned=len(rows),passing=passing,qualified=len(rows)==passing==72,
            families=families,rows=rows,charged=study.summary['charged'],
            construction_totals={k:sum((v['construction_counts'] or {}).get(k,0) for v in rows) for k in limits},
            construction_accounting_complete=all(v['construction_counts'] is not None for v in rows),
            elapsed_s=study.summary['elapsed_s'],manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],numerical_work=0,
            original_reads=0,observed_starts=0,actual_sampling_established=False,scientific_decision='abstain')
    finally:study.close()


def render(report):
    labels=dict(left_hold='Hold previous sample',right_hold='Hold next sample',linear_points='Linear point samples')
    lines=['# Geographic rate-adapter qualification','',
        f"**{report['passing']}/{report['total']} generated cases passed the frozen checks.** "
        + ('The declared generated calculation qualified.' if report['qualified'] else 'The full generated calculation did not qualify.'),'',
        '**The hold rules are judged on numerical refinement; only linear points',
        'must also pass the metre-level accuracy screen.** A hold-rule pass does',
        'not mean its absolute errors are small.','',
        'Each case reconstructs a twenty-minute maneuvering trajectory from generated',
        'angular rates and specific force at 300 Hz, then repeats at 600 Hz.',
        'All three physical candidates, both latitude signs and both removal',
        'assumptions are retained. Initial state and zero antenna lever arm are known',
        'in these controls. Errors use each generating geometry in actual Cartesian',
        'metres, projected onto its true local axes.','',
        '| Sampling hypothesis | Checks passed | Met accuracy screen | Accuracy required | Largest horizontal RMS at 300 Hz | Largest height RMS at 300 Hz |',
        '|---|---:|---:|---|---:|---:|']
    for row in report['families']:
        number=lambda key:'Unavailable' if row[key] is None else f"{row[key]:.6g} m"
        lines.append('| '+' | '.join([labels[row['method']],f"{row['passed']}/24",
            f"{row['accuracy_passed']}/{row['complete']}",'Yes' if row['accuracy_required'] else 'No',
            number('maximum_coarse_horizontal_rms_m'),number('maximum_coarse_height_rms_m')])+' |')
    lines += ['', 'The frozen linear-point screen requires horizontal and height RMS at most',
        '1 m and maximum three-dimensional error at most 5 m. Refinement requires',
        'the finer-grid maximum error to shrink by the predeclared factor, allowing',
        '0.001 m for the numerical comparison. These are software targets, not',
        'instrument specifications or calibrated uncertainty.','',
        f"The run records {report['charged']['native_calls']} native propagations over "
        f"{report['elapsed_s']/60:.2f} minutes. Sealed construction journals record "
        f"{report['construction_totals']['constructed_intervals']:,} constructed intervals and "
        f"{report['construction_totals']['generated_samples']:,} generated samples.",
        'Saved-only verification checks all artifact hashes, error summaries, gate',
        'labels, shared generated inputs, compiled source and main/custom charges.',
        'It does not propagate again or generate new truth. Failures remain preserved.','',
        'This study reads no original recording and makes no Earth-model decision.',
        'It does not identify the instrument’s actual sampling phase, averaging or',
        'filtering. Receiver errors, antenna motion, uncertain initialization and',
        'calibration still require qualification before an observed ESA comparison.',
        'The version-1 zero-eligible inventory and confirmation reservation are unchanged.','',
        '[Frozen question and limits](PLAN.md) · [Implementation](IMPLEMENTATION.md) · '
        '[Earlier local checks](../esa-rate-qualification/INTERPRETATION.md) · '
        '[Motion limitations](../ESA_MOTION.md) · [Roadmap](../ANALYSIS_ROADMAP.md)']
    if not report['construction_accounting_complete']:
        lines+=['','Some failed cases lack a sealed construction journal. Their construction',
            'work is not represented by the sealed totals above; no complete accounting',
            'or qualification is claimed.']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/esa-geographic-rate-controls-20261023',output='docs/esa-geographic-rate-controls'):
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication is already sealed')
    report=inspect(root,prefix)
    package(data,public,render(report),plan='docs/esa-geographic-rate-controls/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in [('verified-report.json',encoded(report)),('reporter.py',Path(__file__).read_bytes())]:
        name='artifacts/publication/'+name;atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
