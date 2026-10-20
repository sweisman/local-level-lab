# SPDX-License-Identifier: AGPL-3.0-or-later
"""Resolve published history to preserved operation metadata without executing it."""
import gzip
import hashlib
import json
from pathlib import Path

from .ilvis0_evidence_lineage import resolve_owner,validate_published


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def pointer(value):return str(value).replace('~','~0').replace('/','~1')
def tasks(manifest):return manifest.get('plan',manifest.get('proposal',{})).get('tasks',[])


class Reader:
    def __init__(self,root):
        self.root=Path(root).resolve();self.inputs={};self._json={};self._owners={}

    def named(self,name,expected=None):
        name=str(name);path=(self.root/name).resolve()
        if Path(name).is_absolute() or not path.is_relative_to(self.root):raise ValueError('lineage input escapes the declared repository')
        data=path.read_bytes();actual=hashlib.sha256(data).hexdigest()
        if expected is not None and actual!=expected:raise ValueError('lineage input hash changed: '+name)
        if name in self.inputs and self.inputs[name]!=actual:raise ValueError('lineage input changed during assembly')
        self.inputs[name]=actual;return data

    def json(self,name,expected=None):
        name=str(name)
        if name not in self._json:
            data=self.named(name,expected);self._json[name]=json.loads(gzip.decompress(data) if name.endswith('.gz') else data)
        elif expected is not None and self.inputs[name]!=expected:raise ValueError('conflicting lineage digest')
        return self._json[name]

    def sealed(self,directory,artifact='summary.json',key='summary_sha256'):
        directory=str(directory);receipt=self.json(directory+'/evidence-receipt.json')
        manifest_path=directory+'/manifest.json';completion_path=directory+'/completion.json';result_path=directory+'/'+artifact
        manifest=self.json(manifest_path,receipt['artifacts']['manifest.json'])
        completion=self.json(completion_path,receipt['artifacts']['completion.json'])
        result=self.json(result_path,receipt['artifacts'][artifact])
        if (completion.get('state','complete')!='complete' or completion['manifest_sha256']!=self.inputs[manifest_path]
                or completion[key]!=self.inputs[result_path]):raise ValueError('unsealed numerical/publication source: '+directory)
        return manifest,result,manifest_path,result_path

    def owner(self,path,manifest,owned=(),evidence=None):
        key=self.inputs[path]
        if key not in self._owners:
            self._owners[key]=dict(manifest=path,manifest_sha256=key,data=manifest,environment=manifest.get('environment',{}),
                tasks={t['identity'] for t in tasks(manifest)},owned_results=set(),evidence={})
        owner=self._owners[key];owner['owned_results'].update(owned)
        if evidence:owner['evidence'].update(evidence)
        return owner

    def original_records(self,directory):
        artifact='summary.json.gz' if (self.root/directory/'summary.json.gz').exists() else 'summary.json'
        manifest,summary,mp,sp=self.sealed(directory,artifact)
        completion=self.json(str(directory)+'/completion.json')
        if 'fit_manifest_sha256' in completion:
            fm=self.json(str(directory)+'/fit-manifest.json',completion['fit_manifest_sha256'])
            if fm['selection_manifest_sha256']!=self.inputs[mp]:raise ValueError('original fit start manifest changed')
        owner=self.owner(mp,manifest);records=[]
        for i,result in enumerate(summary['results']):
            for j,case in enumerate(result['cases']):
                for k,fit in enumerate(case['fits']):
                    records.append(dict(segment_id=result['segment_id'],case_id=case['case_id'],model=fit['model'],role='primary',identity='',fit=fit,
                        publication_manifest=mp,publication_record=sp,publication_locator=f'/results/{i}/cases/{j}/fits/{k}',
                        owner=owner,execution_task_role='primary',execution_record=sp,execution_locator=f'/results/{i}/cases/{j}/fits/{k}',
                        source_identity='',status='complete',operation=''))
        return records

    def trial_records(self,directory,*,published_role=None):
        manifest,summary,mp,sp=self.sealed(directory);results=summary['results'];records=[]
        if not isinstance(results,dict):raise ValueError('task-keyed fit summary required')
        declared=tasks(manifest);owned={t['identity'] for t in declared if t['identity'] in results}
        owner=self.owner(mp,manifest,owned,{i:(sp,'/results/'+pointer(i)) for i in owned})
        for task in declared:
            identity=task['identity']
            if identity not in results:raise ValueError('declared fit lacks a saved result')
            fit=results[identity]
            if fit.get('model',task['model'])!=task['model']:raise ValueError('saved model/task mismatch')
            records.append(dict(segment_id=task['segment_id'],case_id=task['case_id'],model=task['model'],role=published_role or task['role'],
                identity=identity,fit=fit,publication_manifest=mp,publication_record=sp,publication_locator='/results/'+pointer(identity),
                owner=owner,execution_task_role=task['role'],execution_record=sp,execution_locator='/results/'+pointer(identity),
                source_identity='',status='complete',operation=''))
        return records

    def review_records(self,directory):
        manifest,review,mp,rp=self.sealed(directory,'review.json','review_sha256');pool={};objects={}
        # Only named JSON metadata are parsed. Epoch/residual arrays and originals
        # are neither opened nor recomputed.
        for name,expected in manifest['inputs'].items():
            if name.endswith('.json'):
                objects[name]=self.json(name,expected)
        for name,obj in objects.items():
            if name.endswith('manifest.json') and isinstance(obj,dict) and tasks(obj):
                owner=self.owner(name,obj);pool[owner['manifest_sha256']]=owner
        hashes={self.inputs[name]:name for name in objects}
        for name,completion in objects.items():
            if not name.endswith('completion.json') or not isinstance(completion,dict):continue
            mh=completion.get('manifest_sha256');sh=completion.get('summary_sha256')
            if mh not in pool or sh not in hashes:continue
            if completion.get('state','complete')!='complete':continue
            source=hashes[sh];summary=objects[source];results=summary.get('results',{})
            if isinstance(results,dict):members={key:('/results/'+pointer(key)) for key in results}
            elif isinstance(results,list):members={row['identity']:f'/results/{i}' for i,row in enumerate(results) if 'identity' in row}
            else:continue
            owner=pool[mh]
            for identity,locator in members.items():
                if identity in owner['tasks']:
                    owner['owned_results'].add(identity);owner['evidence'][identity]=(source,locator)
        for name,envelope in objects.items():
            if not isinstance(envelope,dict) or not isinstance(envelope.get('result'),dict):continue
            mh=envelope.get('manifest_sha256')
            if mh not in pool:continue
            owner=pool[mh];result=envelope['result'];identity=result.get('identity')
            if identity is None:
                candidates=[i for i in owner['tasks'] if Path(name).name.endswith(i.replace('::','-')+'.json')]
                identity=candidates[0] if len(candidates)==1 else None
            if identity not in owner['tasks']:continue
            if envelope.get('result_sha256') and envelope['result_sha256']!=digest(result):raise ValueError('saved operation envelope changed')
            owner['owned_results'].add(identity);owner['evidence'][identity]=(name,'/result')
        records=[]
        for i,attempt in enumerate(review['attempts']):
            interrupted=attempt['status']=='interrupted';owner=resolve_owner(attempt['identity'],list(pool.values()),interrupted=interrupted)
            source,locator=owner['evidence'].get(attempt['identity'],(owner['manifest'],'/plan/tasks'))
            declared=next(t for t in tasks(owner['data']) if t['identity']==attempt['identity'])
            role=declared.get('role',declared.get('start_role',declared.get('kind','')))
            records.append(dict(segment_id=attempt['segment_id'],case_id=attempt['case_id'],model=attempt['model'],role=attempt['role'],
                identity=attempt['identity'],fit=attempt['fit'],publication_manifest=mp,publication_record=rp,publication_locator=f'/attempts/{i}',
                owner=owner,execution_task_role=role,execution_record=source,execution_locator=locator,
                source_identity=attempt['source_identity'],status=attempt['status'],operation=attempt['operation']))
        return records


def index_history(history,records_by_origin,reader):
    keyed={}
    for origin,records in records_by_origin.items():
        for record in records:
            key=(origin,*(record[k] for k in ('segment_id','case_id','model','role','identity')))
            if key in keyed:raise ValueError('ambiguous published history record')
            keyed[key]=record
    output=[]
    for ordinal,row in enumerate(history,1):
        key=(row['result_origin'],*(row[k] for k in ('segment_id','case_id','model','role','identity')))
        if key not in keyed:raise ValueError('published history row lacks exact source identity: '+str(key))
        record=keyed[key];validate_published(row,record['fit'],interrupted=record['status']=='interrupted')
        if (row.get('operation') or '')!=record['operation']:raise ValueError('published operation class changed')
        owner=record['owner'];env=owner['environment'];pub=reader.json(record['publication_manifest']);operation=record['operation']
        kind='full_fit' if not operation or operation=='full_free_timing' else 'conditional_profile' if operation=='conditional_timing_profile' else 'endpoint_diagnostic'
        kernels={k:v for k,v in owner['data'].items() if 'kernel' in k}
        output.append(dict(history_row_id=f'history-{ordinal:06d}',history_row_ordinal=ordinal,result_origin=row['result_origin'],
            segment_id=row['segment_id'],case_id=row['case_id'],model=row['model'],published_role=row['role'],
            original_worker_identity=row['identity'],published_converged=row['converged'],operation=operation,operation_class=kind,
            publication_manifest=record['publication_manifest'],publication_manifest_sha256=reader.inputs[record['publication_manifest']],
            publication_record=record['publication_record'],publication_locator=record['publication_locator'],publication_python=pub.get('environment',{}).get('python',''),
            execution_manifest=owner['manifest'],execution_manifest_sha256=owner['manifest_sha256'],execution_worker_identity=record['identity'],
            execution_task_role=record['execution_task_role'],execution_record=record['execution_record'],execution_locator=record['execution_locator'],
            execution_python=env.get('python',''),execution_numpy=env.get('numpy',''),execution_scipy=env.get('scipy',''),
            environment_id=digest(env),environment_json=json.dumps(env,sort_keys=True),kernel_metadata_json=json.dumps(kernels,sort_keys=True),
            execution_state=record['status'],parameter_point_source_identity=record['source_identity'],
            parameter_point_ancestry_fully_resolved=False if kind!='full_fit' else None,
            evaluated_count=row.get('evaluations',''),reserved_native_allowance=row.get('reserved_native_allowance',''),
            cost=row.get('cost',''),cost_provenance='reference_cost_not_newly_asserted' if record['status']=='interrupted' else 'published_saved_result',
            calibrated_detection=False,scientific_decision='abstain'))
    if len(output)!=len(keyed):raise ValueError('source records and published history do not have one-to-one coverage')
    return output
