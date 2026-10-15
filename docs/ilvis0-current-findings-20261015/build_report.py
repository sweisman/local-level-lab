# SPDX-License-Identifier: AGPL-3.0-or-later
"""Combine sealed recovery ledgers; retain prior publications and measured summaries."""
import csv
import importlib.util
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE='docs/ilvis0-position-stability-trial-20261013'
STAGES=('ilvis0-budget-continuation-20261014','ilvis0-remaining-precision-20261014',
        'ilvis0-trust-trial-20261015')
CASES={'bias1_unsubtracted','bias1_profiled_removal'}
MODELS={'sphere_rotating','sphere_still','flat_still'}


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def load(path): return json.loads(path.read_text())


def csv_rows(path):
    with path.open(newline='') as stream: return list(csv.DictReader(stream))


def write_csv(path,rows):
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)


def qualified_updates(previous,summary,plan):
    rows=summary['comparisons'];updates={r['segment_id']:r for r in rows}
    if summary['state']!='complete' or len(rows)!=len(updates) or set(updates)!=set(plan['target_segment_ids']):
        raise ValueError('complete frozen target population required')
    q=summary['qualification'];repeats=q['repeatability']
    repeated={r['identity'].split('::')[0]:r['passed'] for r in repeats}
    if len(repeated)!=len(repeats) or set(repeated)!=set(updates): raise ValueError('scheduled repeats required')
    for sid,row in updates.items():
        if previous.get(sid)!='unresolved': raise ValueError('cannot replace a resolved or absent stretch')
        if row['profile']['conditional_shape_preference'] not in ('globe','flat'): continue
        cases=row['cases']
        if (not q['controls_passed'] or len(q['controls'])!=2 or not all(r['passed'] for r in q['controls'])
                or not repeated[sid] or len(cases)!=2 or {c['case_id'] for c in cases}!=CASES
                or any(len(c['fits'])!=3 or {f['model'] for f in c['fits']}!=MODELS
                       or not all(f['converged'] for f in c['fits']) for c in cases)):
            raise ValueError('resolved comparison lacks six primaries, controls or repeat')
    return updates


def verified_rows(root):
    helper=module(root/'docs/build_current_status.py','publication_status_helpers')
    helper.load_snapshot(root,findings=BASE)
    report=module(root/BASE/'build_findings.py','previous_publication')
    rows=csv_rows(root/BASE/'current-stretches.csv');by_id={r['segment_id']:r for r in rows}
    for stage in STAGES:
        summary,manifest=report.sealed_precision(root/'docs'/stage)
        updates=qualified_updates({sid:r['shape_preference'] for sid,r in by_id.items()},summary,manifest['plan'])
        for sid,result in updates.items():
            profile=result['profile'];rotation=profile['rotation_diagnostics'];shape=profile['conditional_shape_preference']
            background=bool(shape=='globe' and rotation and all(r['conditional_still_minus_rotating_cost']>0 for r in rotation))
            by_id[sid].update(shape_preference=shape,specified_background_preferred=str(background),
                             result_origin='completed_'+stage)
    return rows


def stop_reason(fit):
    if fit.get('error'): return 'execution_error'
    if fit.get('converged'): return 'passed'
    text=fit.get('message','').lower()
    if any(s in text for s in ('maximum','budget','evaluation limit','exhaust')): return 'budget'
    if 'stability' in text: return 'stability_check'
    if any(s in text for s in ('no decreasing','stall','no feasible','no progress')): return 'stall'
    if 'stationar' in text: return 'stationarity_check'
    return 'other_numerical_stop'


def analytics(root,rows):
    helper=module(root/'docs/build_current_status.py','analytics_status_helpers')
    receipt=load(root/BASE/'analytics-receipt.json')
    helper.verify_inputs(root,{BASE+'/'+n:h for n,h in receipt['artifacts'].items()})
    stretches=csv_rows(root/BASE/'stretch-analytics.csv');fits=csv_rows(root/BASE/'fit-analytics.csv')
    by_id={r['segment_id']:r for r in stretches};dispositions={r['segment_id']:r for r in rows}
    for stage in STAGES:
        directory=root/'docs'/stage;summary=load(directory/'summary.json');manifest=load(directory/'manifest.json')
        origin='completed_'+stage
        for task in manifest['plan']['tasks']:
            fit=summary['results'][task['identity']];sid=task['segment_id']
            saved=dict(segment_id=sid,case_id=task['case_id'],model=task['model'],result_origin=origin,
                role=task['role'],identity=task['identity'],stop_reason=stop_reason(fit),converged=fit['converged'],
                cost=fit.get('residual_sum_squares'),evaluations=fit.get('evaluations'),
                maximum_evaluations=fit.get('maximum_evaluations'),message=fit.get('message',''),error=fit.get('error',''),
                stationarity=fit.get('exact_projected_gradient_relative'),active_bounds=';'.join(fit.get('active_bounds',[])),
                parameters=json.dumps(fit.get('parameters',{}),sort_keys=True))
            fits.append(saved)
            if sid not in by_id: continue
            if task['role']=='primary':
                prefix=task['case_id']+'__'+task['model']+'__'
                for k in ('result_origin','stop_reason','converged','cost','evaluations','maximum_evaluations','message','stationarity','active_bounds'):
                    by_id[sid][prefix+k]=str(saved[k]) if saved[k] is not None else ''
            if task['role']=='repeat':
                by_id[sid].update(latest_repeat_status=saved['stop_reason'],latest_repeat_origin=origin)
        repeats={r['identity'].split('::')[0]:r['passed'] for r in summary['qualification']['repeatability']}
        for sid in manifest['plan']['target_segment_ids']:
            r=by_id[sid];reasons={r[c+'__'+m+'__stop_reason'] for c in CASES for m in MODELS
                                 if r[c+'__'+m+'__converged']!='True'}
            r['unfinished_reasons']=';'.join(sorted(reasons))
            r['disposition_pending_reason']=('' if dispositions[sid]['shape_preference'] in ('globe','flat')
                else 'primary_fit_checks_incomplete' if reasons else 'scheduled_repeat_agreement_failed' if not repeats[sid]
                else 'shape_comparison_unresolved')
    for row in stretches:
        row.update(dispositions[row['segment_id']]);row['snapshot_utc']='2026-10-15'
    return stretches,fits


def main():
    helper=module(ROOT/'docs/build_current_status.py','status_publication_helpers')
    report=module(ROOT/BASE/'build_findings.py','table_publication_helpers')
    rows=verified_rows(ROOT);snapshot=helper.summarize(rows)
    if snapshot['tally']!=dict(globe=46,flat=0,unresolved=7,ambiguous=0): raise ValueError('unexpected combined tally')
    if snapshot['background']!=snapshot['tally']['globe']: raise ValueError('background preferences require explicit review')
    write_csv(HERE/'current-stretches.csv',rows)
    table_rows=[dict(r,**{k:float(r[k]) for k in ('mean_course_deg','mean_latitude_deg','minimum_latitude_deg','maximum_latitude_deg','gps_track_km')}) for r in rows]
    (HERE/'STRETCHES.md').write_text(report.stretch_report(table_rows))
    stretches,fits=analytics(ROOT,rows);write_csv(HERE/'stretch-analytics.csv',stretches);write_csv(HERE/'fit-analytics.csv',fits)
    shutil.copyfile(ROOT/BASE/'shared-leg-pairs.csv',HERE/'shared-leg-pairs.csv')
    text='# Updated airborne findings\n\n'+helper.headline(snapshot)+'\n\n'
    text+='The completed nine-stretch assessment added three complete globe preferences, bringing the tally '
    text+='to 44/0/9. The subsequent hybrid-solver trial resolves two more. Every added result passed '
    text+='six primary fits, its predetermined repeat and both controls. These are numerical preferences, '
    text+='without a calibrated significance level. All 46 globe-preferred stretches also favor the '
    text+="specified background field; its cause is not determined.\n\n"
    text+='## Latest matched comparison\n\n'
    text+='The eight-start hybrid trial used 471 native sweeps; six fits passed, including both controls. '
    text+='Two targets pass their full comparisons and repeats. '
    text+='The third target fails its primary and repeat stability checks and remains unresolved. '
    text+='The run did not qualify every target; individually complete comparisons are reported separately.\n\n'
    text+='| Newly completed source | UTC interval | IMU type | Minutes | Ground speed min / median |\n'
    text+='|---|---|---:|---:|---:|\n'
    for row in rows:
        if row['result_origin']=='completed_ilvis0-trust-trial-20261015' and row['shape_preference']=='globe':
            text+=f"| `{row['filename']}` | {row['start_utc']} to {row['end_utc']} | {row['imu_type']} | {float(row['duration_s'])/60:.2f} | {float(row['minimum_ground_speed_kmh']):.1f} / {float(row['median_ground_speed_kmh']):.1f} km/h |\n"
    text+='\n'
    text+='## Seven unresolved stretches\n\n'
    text+='Six stretches from the earlier nine-stretch assessment have not yet been tested with the hybrid '
    text+='solver. Their latest ledgers contain eleven unfinished primary fits. The seventh is the third '
    text+='hybrid-trial target: its primary and repeat stop before their evaluation caps. Their endpoints '
    text+='closely agree, but fresh corrections still move receiver predictions beyond the fixed objective '
    text+='and one-millimetre axis-RMS stability limits. More iterations alone do not explain that stop. '
    text+='A separately frozen assessment of the other six and a focused diagnosis of that last target '
    text+='are the next numerical work. No previous allowance is reopened.\n\n'
    text+='[All stretches and source tracks](STRETCHES.md) · [Comprehensive metadata](ANALYTICS.md)\n\n'
    for name in STAGES: text+=f'- [Preserved {name} results](../{name}/RESULTS.md).\n'
    text+='\nEarlier [41/0/12 findings](../ilvis0-position-stability-trial-20261013/FINDINGS.md) remain an unchanged historical snapshot. '
    text+='No observations, intervals, physical bounds, receiver weights or clocks were changed by this metadata publication.\n'
    (HERE/'FINDINGS.md').write_text(text)
    (HERE/'ANALYTICS.md').write_text('# Current stretch analytics\n\n'+helper.headline(snapshot)+'\n\n'
        +f'The [stretch CSV](stretch-analytics.csv) contains all 53 stretches; the [fit history](fit-analytics.csv) retains all {len(fits)} attempts. '
        +'The 81 continuation and hybrid-trial attempts are appended; repeats and controls never replace primary fits. '
        +'Raw gyro summaries, receiver trajectories and [paired-recorder differences](shared-leg-pairs.csv) are copied unchanged '
        +'from the verified preceding snapshot. Only dispositions and saved numerical outcomes are updated.\n\n'
        +'The [column definitions and measurement limitations](../ilvis0-position-stability-trial-20261013/ANALYTICS.md) '
        +'continue to apply. Group-1 attitude remains a context diagnostic, never independent shape evidence. '
        +'No original recordings or numerical predictions were read or generated.\n')
    inputs={BASE+'/'+n:helper.sha(ROOT/BASE/n) for n in ('findings-receipt.json','analytics-receipt.json')}
    for stage in STAGES:
        for n in ('manifest.json','summary.json','completion.json','evidence-receipt.json','starts.jsonl','sweeps.jsonl'):
            name='docs/'+stage+'/'+n;inputs[name]=helper.sha(ROOT/name)
    outputs=('FINDINGS.md','STRETCHES.md','current-stretches.csv','stretch-analytics.csv','fit-analytics.csv','shared-leg-pairs.csv','ANALYTICS.md')
    receipt=dict(publication_builder=str(Path(__file__).relative_to(ROOT)),inputs=inputs,
        sources={str(p.relative_to(ROOT)):helper.sha(p) for p in (Path(__file__),ROOT/'docs/build_current_status.py')},
        artifacts={n:helper.sha(HERE/n) for n in outputs},tally=snapshot['tally'],observed_starts=0,native_predictions=0,original_files_read=0)
    (HERE/'findings-receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(tally=snapshot['tally'],fit_attempts=len(fits),observed_starts=0)))


if __name__=='__main__': main()
