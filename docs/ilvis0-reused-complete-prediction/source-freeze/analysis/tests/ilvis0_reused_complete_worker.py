# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish complete prediction covers from sealed reports only."""
import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner,ilvis0_control_publication as publication
from lll.ilvis0_reused_cover import combine
from lll.ilvis0_saved_prediction_audit import endpoint

DATA=ROOT/'data/ilvis0-reused-complete-prediction-20261021'
PUBLIC=ROOT/'docs/ilvis0-reused-complete-prediction'
PLAN='docs/ilvis0-reused-complete-prediction/PLAN.md'
ADAPTER='analysis/lll/ilvis0_reused_prediction.py'
OLD=ROOT/'docs/ilvis0-coupled-prediction'
INHERITED=ROOT/'docs/ilvis0-coupled-subdivision'
BASE=ROOT/'docs/ilvis0-projected-future-bounds'


def provider_eligible(row):
    return (row.get('passed') is True or
        (row.get('passed') is False and row.get('error_type')=='Unsupported'
         and row.get('reason')=='time allowance exhausted'))


def sealed(directory,*,passing,environment):
    receipt=runner._load(directory/'evidence-receipt.json')
    for name,digest in receipt['artifacts'].items():
        if runner._sha(runner.path_within(directory,name))!=digest:
            raise ValueError('sealed provider/prerequisite changed: '+str(directory/name))
    manifest=runner._load(directory/'manifest.json');summary=runner._load(directory/'summary.json')
    completion=runner._load(directory/'completion.json')
    if (completion['manifest_sha256']!=runner._sha(directory/'manifest.json')
            or completion['summary_sha256']!=runner._sha(directory/'summary.json')
            or completion['state']!=summary['state'] or manifest['environment']!=environment
            or (passing and summary.get('passed') is not True)):
        raise ValueError('qualified sealed completion in the same environment required')
    return manifest,summary


def prepare():
    from lll.ilvis0_reused_prediction import allowances
    if DATA.exists():raise ValueError('saved complete-cover study already frozen')
    environment=runner.runtime_environment()
    environment_hash=hashlib.sha256(json.dumps(environment,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    sources={PLAN,ADAPTER,'analysis/lll/ilvis0_reused_cover.py',
        'analysis/tests/test_ilvis0_reused_cover.py','analysis/tests/test_ilvis0_reused_complete_worker.py',
        'analysis/tests/ilvis0_reused_complete_worker.py','analysis/tests/ilvis0_control_shards.py',
        'analysis/tests/run_numerical.py'}
    qualified=ROOT/'docs/ilvis0-reused-joint-controls'
    qualified_manifest,_=sealed(qualified,passing=True,environment=environment)
    for name,digest in qualified_manifest['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    old_manifest,old_summary=sealed(OLD,passing=True,environment=environment)
    inherited_manifest,_=sealed(INHERITED,passing=True,environment=environment)
    sealed(BASE,passing=True,environment=environment)
    if inherited_manifest['inputs']['previous-comparison']['sha256']!=runner._sha(OLD/'comparison.json'):
        raise ValueError('complete inherited cover has different parent ancestry')
    inputs={};providers={}
    for label,study in (('earlier','ilvis0-taylor-complete-prediction'),('direct','ilvis0-direct-complete-prediction')):
        directory=ROOT/'docs'/study;manifest,summary=sealed(directory,passing=False,environment=environment)
        if (manifest['inputs']['inherited']['sha256']!=runner._sha(INHERITED/'comparison.json')
                or manifest['inputs']['baseline']['sha256']!=runner._sha(BASE/'case-unions.json')):
            raise ValueError('provider baseline or complete inherited ancestry differs')
        for name,digest in manifest['sources'].items():
            if name.startswith('analysis/lll/'):
                if runner._sha(ROOT/name)!=digest:raise ValueError('provider source changed: '+name)
                sources.add(name)
        records={r['identity']:runner._load(directory/r['artifact']) for r in summary['results']}
        if len(records)!=48 or any(not provider_eligible(r['result']) for r in records.values()):
            raise ValueError('all source failures must be solely time limits')
        providers[label]=dict(directory=directory,manifest=manifest,records=records)
        inputs['source-manifest-'+label]=str((directory/'manifest.json').relative_to(ROOT))
        inputs['source-receipt-'+label]=str((directory/'evidence-receipt.json').relative_to(ROOT))
    provider_sources=[dict(name=name,manifest_key='source-manifest-'+name,
        receipt_key='source-receipt-'+name) for name in providers]
    direct=providers['direct'];inventory=[];frames={};prepared={}
    parent_records={r['identity']:runner._load(OLD/r['artifact'])['result'] for r in old_summary['results']}
    for task in direct['manifest']['tasks']:
        original=task['identity'];spec=task['payload'];key=task['input_key']
        bundle_path=direct['directory']/direct['manifest']['inputs'][key]['path']
        bundle=runner._load(bundle_path);parent=bundle['result'];tag=parent['task']
        if (parent_records[original]!=parent or parent.get('passed') is not True or parent['excluded']
                or bundle['training']!=runner._load(OLD/'artifacts'/original/'training.json')
                or bundle['future']!=runner._load(OLD/'artifacts'/original/'future.json')):
            raise ValueError('fresh providers must use the unchanged qualified parent')
        case_key=spec['case_key'];case_record=direct['manifest']['inputs'][case_key]
        if (old_manifest['inputs'][case_key]['sha256']!=case_record['sha256']
                or inherited_manifest['inputs'][case_key]['sha256']!=case_record['sha256']):
            raise ValueError('parent/child/inherited source case differs')
        region=bundle['training']['region']
        frame=dict(case_sha256=case_record['sha256'],origin=region['origin'],coordinate_scale=region['coordinate_scale'])
        frame_hash=hashlib.sha256(json.dumps(frame,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        group=(tag['model'],tag['profile'])
        if group in frames and frames[group]!=frame_hash:raise ValueError('region frames differ within group')
        frames[group]=frame_hash;queries=[]
        for ordinal in range(1,8):
            descriptors=[]
            for label,provider in providers.items():
                source_task=next(t for t in provider['manifest']['tasks'] if t['identity']==original)
                for input_key in (source_task['input_key'],case_key,spec['condition_key']):
                    if provider['manifest']['inputs'][input_key]['sha256']!=direct['manifest']['inputs'][input_key]['sha256']:
                        raise ValueError('provider bundle/case/conditioning differs')
                record=provider['records'][original];basename=f'bound-{ordinal:02d}.json'
                names=[name for name in record['artifacts'] if Path(name).name==basename]
                if len(names)>1:raise ValueError('ambiguous saved query')
                if not names:continue
                name=names[0];path=provider['directory']/name
                if runner._sha(path)!=record['artifacts'][name]:raise ValueError('query report changed')
                provider_key=original+'-'+label+f'-{ordinal:02d}'
                inputs[provider_key]=str(path.relative_to(ROOT))
                descriptors.append(dict(name=label+f'-{ordinal:02d}',source=label,key=provider_key,
                    sha256=runner._sha(path),qualified_path=name))
            queries.append(descriptors)
        meta=dict(identity='reuse-'+original,source_identity=original,model=tag['model'],profile=tag['profile'],
            sector=tag['sector'],frame_sha256=frame_hash,available_queries=[len(q) for q in queries])
        inventory.append(meta);prepared[original]=(task,bundle_path,queries)
    if len(inventory)!=48 or len(frames)!=6:raise ValueError('all original regions required')
    fresh_groups={group for group in frames if all(all(row['available_queries']) for row in inventory
        if (row['model'],row['profile'])==group)}
    if fresh_groups!={(0,False),(0,True),(1,False),(2,False),(2,True)}:
        raise ValueError('frozen provider availability recipe changed')
    tasks=[]
    for meta in inventory:
        group=(meta['model'],meta['profile']);meta['fresh']=group in fresh_groups
        if not meta['fresh']:continue
        task,bundle_path,queries=prepared[meta['source_identity']];spec=task['payload']
        inputs[meta['source_identity']]=str(bundle_path.relative_to(ROOT))
        for key in (spec['case_key'],spec['condition_key']):
            inputs[key]=str((direct['directory']/direct['manifest']['inputs'][key]['path']).relative_to(ROOT))
        limits=allowances(6,[len(q) for q in queries])
        tasks.append(dict(identity=meta['identity'],input_key=meta['source_identity'],
            payload=dict(meta,case_key=spec['case_key'],condition_key=spec['condition_key'],packets=1600,
                providers=queries,provider_sources=provider_sources,provider_environment_sha256=environment_hash,limits=limits),
            limits=dict(native_calls=0,packet_visits=0,bound_calls=7,bound_steps=0)))
    if len(tasks)!=40:raise ValueError('40 complete fresh-region calculations required')
    inventory_path=PUBLIC/'saved-inputs/inventory.json'
    runner._write(inventory_path,dict(regions=inventory,qualified_provider_manifest_sha256=runner._sha(qualified/'manifest.json'),
        parent_manifest_sha256=runner._sha(OLD/'manifest.json'),inherited_manifest_sha256=runner._sha(INHERITED/'manifest.json')))
    inputs.update(inventory=str(inventory_path.relative_to(ROOT)),baseline=str((BASE/'case-unions.json').relative_to(ROOT)),
        inherited=str((INHERITED/'comparison.json').relative_to(ROOT)))
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,adapter=ADAPTER,
        workers=4,threads=1,maximum_wall_s=600,environment=environment)


def comparison(manifest,rows):
    inventory=runner._load(DATA/manifest['inputs']['inventory']['path'])['regions']
    baseline=runner._load(DATA/manifest['inputs']['baseline']['path'])['cases']
    inherited=runner._load(DATA/manifest['inputs']['inherited']['path'])['cases']
    tasks={t['identity']:t for t in manifest['tasks']};records={}
    if len(tasks)!=40 or len(inventory)!=48:raise ValueError('complete frozen inventory required')
    for row in rows:
        identity=row.get('identity')
        if identity not in tasks or identity in records:raise ValueError('unique scheduled results required')
        meta=next(r for r in inventory if r['identity']==identity)
        spec=tasks[identity]['payload']
        if any(spec[key]!=meta[key] for key in ('model','profile','sector','frame_sha256','source_identity','fresh')):
            raise ValueError('result payload differs from frozen inventory')
        if row.get('passed') and any(row['task'][key]!=meta[key] for key in ('model','profile','sector')):
            raise ValueError('result source model/region differs')
        records[identity]=row
    all_passed=len(records)==len(tasks) and all(row.get('passed') is True for row in rows)
    cases=[]
    for model in range(3):
        for profile in (False,True):
            members=[r for r in inventory if (r['model'],r['profile'])==(model,profile)]
            if (len(members)!=8 or {r['sector'] for r in members}!=set(range(8))
                    or len({r['frame_sha256'] for r in members})!=1
                    or len({r['fresh'] for r in members})!=1):
                raise ValueError('eight unique sectors in one frame and one planned mode required')
            old=next(r for r in inherited if (r['model'],r['profile'])==(model,profile))
            original=next(r for r in baseline if (r['model'],r['profile'])==(model,profile))
            base=dict(case_id=f'{model}-{int(profile)}',frame_sha256=members[0]['frame_sha256'],
                complete=old['complete'],lower=old['union_lower_m'],upper=old['union_upper_m'])
            group=[records[m['identity']] for m in members if m['identity'] in records]
            planned=members[0]['fresh']
            if planned!=((model,profile)!=(1,True)):raise ValueError('planned fallback mode changed')
            known=[r for r in group if r.get('truth_in_sector')]
            truth_ok=bool(known) and all(r.get('known_truth_retained') for r in known)
            regions=[]
            for meta in members:
                if meta['identity'] not in records:continue
                row=records[meta['identity']];passed=row.get('passed') is True and truth_ok
                regions.append(dict(region_id=meta['sector'],case_id=base['case_id'],frame_sha256=base['frame_sha256'],
                    passed=passed,excluded=row.get('excluded',False),
                    lower=row.get('future_lower_m'),upper=row.get('future_upper_m')))
            result=combine(base,regions,expected_regions=8)
            widths=[F(b)-F(a) for a,b in zip(result['lower'],result['upper'],strict=True)]
            result.update(model=model,profile=profile,planned_fresh=planned,
                twofold=all(w<=F(v)/2 for w,v in zip(widths,original['union_width_m'],strict=True)),
                union_width_m=[endpoint(w,True) for w in widths])
            if result['fresh_complete']:
                result['fresh_width_m']=[endpoint(F(b)-F(a),True)
                    for a,b in zip(result['fresh_lower'],result['fresh_upper'],strict=True)]
            cases.append(result)
    all_twofold=all(c['combined_complete'] and c['twofold'] for c in cases)
    qualified=all_passed and all_twofold and all(c['fresh_complete'] for c in cases if c['planned_fresh'])
    return dict(cases=cases,qualified=qualified,all_cases_twofold=all_twofold,all_scheduled_passed=all_passed,
        native_evaluations=0,observational_coverage_qualified=False,scientific_decision='abstain')


def publish():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA);rows=[];accounts=[]
    for item in summary['results']:
        record=runner._load(DATA/item['artifact']);row=dict(record['result'],identity=item['identity']);rows.append(row)
        task=next(t for t in manifest['tasks'] if t['identity']==item['identity'])
        limits=task['payload']['limits'];counts=dict.fromkeys(limits,0)
        for name in sorted(n for n in record['artifacts'] if Path(n).name.startswith('reservation-')):
            event=runner._load(DATA/name);inc=event['increase']
            if not inc or any(k not in counts or type(v)!=int or v<1 for k,v in inc.items()):raise ValueError('invalid reservation')
            counts={k:v+inc.get(k,0) for k,v in counts.items()}
            if counts!=event['counts'] or any(v>limits[k] for k,v in counts.items()):raise ValueError('work reservation changed')
        if 'work' in row:
            expected=dict(limits,proposals=0 if row['excluded'] else 6,supports=0 if row['excluded'] else 24)
            if row['work']!=counts or counts!=expected or row['bound_evaluations']!=7:
                raise ValueError('saved-only work differs from finite recipe')
        if row.get('native_evaluations',0) or row.get('original_reads',0) or row.get('optimizer_starts',0):
            raise ValueError('unauthorized integration/original/fit work')
        accounts.append(dict(identity=item['identity'],passed=row.get('passed',False),**counts))
    comp=comparison(manifest,rows)
    text=['# Complete prediction covers from saved bounds','',
        f"{sum(r.get('passed',False) for r in rows)}/40 scheduled region calculations passed. "
        f"The complete-cover width target {'passed' if comp['qualified'] else 'did not pass'}.",'',
        '| Candidate / removal | Fresh cover | Final cover | Widths north / east / height (m) | Original target |',
        '|---|---|---|---:|---|']
    for c in comp['cases']:
        label=('Globe with specified field','Globe with zero field','Flat disc')[c['model']]+(' / profiled' if c['profile'] else ' / zero')
        text.append(f"| {label} | {c['completed_regions']}/8 | {c['mode']} | "+
            ' / '.join(f'{v:.4f}' for v in c['union_width_m'])+f" | {'Pass' if c['twofold'] else 'Fail'} |")
    text+=['',f"Elapsed {summary['elapsed_s']:.2f} seconds; {summary['charged']['bound_calls']}/280 saved-report merges, "
        'zero integrations, zero packet propagation, zero original-aircraft reads and zero optimizer starts.','',
        'Five groups have all eight fresh regions. The zero-field globe with profiled removal uses only its unchanged '
        'complete inherited cover: two missing saved future reports prevent a complete new cover. No partial new '
        'union contributes to that result. Both source studies retain their failed qualification labels.','',
        'This checks the existing generated 7.2-second examples, with unchanged physical bounds, observation allowance '
        'and arithmetic assumptions. Recording-scale qualification and the observation-error model remain unfinished. '
        'It adds no empirical model preferences or calibrated confidence.','',
        '[Frozen scope](PLAN.md) · [Adapter checks](../ilvis0-reused-joint-controls/INTERPRETATION.md) · '
        '[Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    runner._replace(PUBLIC/'comparison.json',comp)
    runner._replace(PUBLIC/'accounting.json',dict(cases=accounts,charged=summary['charged']))
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    for name in ('comparison.json','accounting.json'):receipt['artifacts'][name]=runner._sha(PUBLIC/name)
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check','run'):group.add_argument('--'+name,action='store_true')
    parser.add_argument('--reserved-threads',type=int);args=parser.parse_args()
    if args.prepare:prepare();print('Frozen 40 saved-only regions / 280 merges / zero integrations / 600 seconds.')
    elif args.run:
        if args.reserved_threads is None:parser.error('--run requires --reserved-threads')
        result=runner.launch(DATA,reserved_threads=args.reserved_threads);publish();print('Complete saved-cover comparison: '+result['state'])
    elif args.package_only:publish();print('Published complete saved-cover comparison.')
    else:publication.check(DATA,PUBLIC);print('Verified complete saved-cover evidence.')


if __name__=='__main__':main()
