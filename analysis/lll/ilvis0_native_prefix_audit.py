# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact saved-report checks, with no integration or numerical-library imports.

Reconstructing a saved design is bookkeeping, not a fresh derivative or an
independent qualification of the oracle that originally produced it.
"""
import math
from .studies.artifacts import digest,encoded,reports_equal


def _vector(value,n):
    if (not isinstance(value,(list,tuple)) or len(value)!=n
            or any(type(x) not in (int,float) or not math.isfinite(x) for x in value)):
        raise ValueError('finite saved vector with the declared shape required')
    return list(value)


def _matrix(value,n):
    if not isinstance(value,(list,tuple)) or len(value)!=3:raise ValueError('three saved axes required')
    return [_vector(row,n) for row in value]


def check_saved_pair(original,cached,native,*,expected_time):
    """Check exact serialized equality and all 51 retained coefficient columns."""
    from .ilvis0_native_prefix_long import recipe
    if not reports_equal(original,cached):raise ValueError('complete saved reports differ')
    if (original['time_s']!=expected_time or native['time_s']!=expected_time
            or type(native['status']) is not int or native['status']!=0
            or type(native['warning']) is not int or native['warning'] not in (0,1)
            or not reports_equal(native['point'],original['normalized_center'])):
        raise ValueError('saved oracle point, time or status differs')
    _vector(native['point'],27)
    blocks=[_matrix(native['jacobian'],27),_matrix(original['previous_coefficients'],6),
        _matrix(original['acceleration_coefficients'],9),_matrix(original['transform_coefficients'],9)]
    matrix=[sum((b[i] for b in blocks),[]) for i in range(3)]
    center=_vector(original['center'],3);point=_vector(native['prediction'],3)
    error=[abs((c-p)*s) for c,p,s in zip(center,point,(6371000.,6371000.,1.),strict=True)]
    if max(error)>recipe()['oracle_arithmetic_allowance_m']:
        raise ValueError('saved center differs from independent native oracle')
    return dict(report_equal=True,report_sha256=digest(encoded(original)),matrix=matrix,
        design_sha256=digest(encoded(matrix)),native_center_error_m=error,
        design_columns_checked=51,numerical_work=0)


def check_saved_reports(originals,cached,natives):
    """Never infer a missing query from an earlier equal query."""
    from .ilvis0_native_prefix_long import recipe
    times=recipe()['times_s']
    if (len(originals)!=2 or len(natives)!=2 or not cached
            or any(type(k) is not int or k not in (0,1) for k in cached)):
        raise ValueError('two fixed queries and at least one saved cached report required')
    checks={i:check_saved_pair(originals[i],cached[i],natives[i],expected_time=times[i]) for i in sorted(cached)}
    missing=[i for i in range(2) if i not in cached]
    return dict(checks=checks,report_comparisons=len(checks),missing_queries=missing,
        all_queries_verified=not missing,numerical_work=0)


def check_case(task,envelope,reference,artifacts):
    """Admit missing-output recovery only after a returned, within-budget batch.

    The caller must first verify the closed study and each artifact hash. No
    failure is relabeled, and no equality is inferred for an absent report.
    """
    from .ilvis0_native_prefix_long import recipe,batch_limits
    r=recipe();spec=task['payload'];result=envelope['result']
    if (spec['recipe']!=r or type(spec['reused_early']) is not bool
            or result.get('passed') is not False or result.get('error_type')!='ValueError'
            or result.get('reason')!='complete long report differs from sealed cold reference'
            or envelope['charged']!=task['limits']):
        raise ValueError('only the complete, fully charged report-format failure is repairable here')
    if not reports_equal(reference['certificate'],artifacts['compatibility.json']):
        raise ValueError('saved source and input certificate differs')
    originals=[artifacts['cold-00.json'],artifacts['cold-01-reused.json']]
    if (not reports_equal(originals[1],reference['report'])
            or digest(encoded(originals[1]))!=reference['certificate']['saved_report_sha256']
            or (spec['reused_early'] and not reports_equal(originals[0],reference['early_reference']['report']))):
        raise ValueError('original reference report differs from frozen input')
    batch=artifacts['batch-progress.json'];work=artifacts['cold-work.json']
    for value,maximum in ((batch,r['maximum_batch_seconds']),(work,r['maximum_cold_seconds'])):
        elapsed=value['elapsed_s'];rss=value['peak_rss_bytes']
        if (type(elapsed) not in (int,float) or not math.isfinite(elapsed) or not 0<=elapsed<=maximum
                or type(rss) is not int or not 0<rss<=r['maximum_rss_bytes']):
            raise ValueError('completed calculation exceeded a frozen resource limit')
    reserved=batch_limits(r['packets']);used=batch['actual_prepaid_work']
    if (batch['reservations']!=reserved or set(used)!=set(reserved)
            or any(type(v) is not int or not 0<v<=reserved[k] for k,v in used.items())
            or used['packet_steps']!=used['prefix_packet_steps']+used['tail_packet_steps']
            or any(used[k]!=reserved[k] for k in ('preparation_packets','force_profile_packets',
                'cursor_copies','source_state_copies','source_query_checks'))):
        raise ValueError('completed batch work differs from frozen reservations')
    cached={i:artifacts[f'batched-{i:02d}.json'] for i in range(2) if f'batched-{i:02d}.json' in artifacts}
    if 0 not in cached:raise ValueError('no retained evidence that the two-query batch returned')
    natives=[artifacts[f'native-{i:02d}.json'] for i in range(2)]
    # Check both original centers even when the cached later report was lost.
    oracle=[check_saved_pair(old,old,native,expected_time=t)
        for old,native,t in zip(originals,natives,r['times_s'],strict=True)]
    compared=check_saved_reports(originals,cached,natives)
    return dict(compared,identity=task['identity'],original_result=result,
        needs_cached_recovery=bool(compared['missing_queries']),oracle_comparisons=2,
        maximum_native_center_error_m=max(max(row['native_center_error_m']) for row in oracle),
        batch_elapsed_s=batch['elapsed_s'],peak_rss_bytes=batch['peak_rss_bytes'],
        actual_prepaid_work=used,reservations=reserved,original_reads=0,optimizer_starts=0,
        long_history_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def compatible_recovery_sources(previous,root,*,frozen_adapter,frozen_storage):
    """Keep every numerical helper unchanged during the report-format repair."""
    import ast
    from pathlib import Path
    root=Path(root);adapter='analysis/lll/ilvis0_native_prefix_long.py';storage='analysis/lll/studies/artifacts.py'
    def without(raw,function):
        tree=ast.parse(raw)
        tree.body=[v for v in tree.body if not isinstance(v,ast.FunctionDef) or v.name!=function]
        return ast.dump(tree,include_attributes=False)
    for path,old,allowed,label in ((adapter,frozen_adapter,'compare','helper'),
                                  (storage,frozen_storage,'reports_equal','encoder/storage')):
        if previous.get(path)!=digest(old) or without(old,allowed)!=without((root/path).read_bytes(),allowed):
            raise ValueError('unchanged '+label+' required outside the report comparison')
    tests={'analysis/tests/test_ilvis0_native_prefix_long.py','analysis/tests/test_study_runtime.py'}
    unchanged=[]
    for path,sha in previous.items():
        if path in tests|{adapter,storage}:continue
        if digest((root/path).read_bytes())!=sha:raise ValueError('saved numerical dependency changed: '+path)
        unchanged.append(path)
    return dict(unchanged_dependencies=sorted(unchanged),
        adapter_sha256=digest((root/adapter).read_bytes()),storage_sha256=digest((root/storage).read_bytes()),
        previous_adapter_sha256=previous[adapter],previous_storage_sha256=previous[storage])


def inspect(root,prefix='data/ilvis0-native-prefix-long-v2-20261022'):
    """Read only a closed six-case study, checking all declared evidence hashes."""
    from .studies.closed import ClosedStudy
    adapter='analysis/lll/ilvis0_native_prefix_long.py'
    expected_adapter='0121e570af57c33892dc65b7df711e742d817b76b0d2eef34d62047829db03f8'
    study=ClosedStudy(root,prefix)
    try:
        if (study.manifest['adapter']!=adapter or study.manifest['sources'].get(adapter)!=expected_adapter
                or len(study.tasks)!=6 or set(study.rows)!=set(study.tasks)
                or {(t['payload']['model'],t['payload']['profile']) for t in study.tasks.values()}!=
                    {(m,p) for m in range(3) for p in (False,True)}):
            raise ValueError('the complete unchanged six-case format-failure study is required')
        for name,sha in study.manifest['sources'].items():study.read('source-freeze/'+name,sha,raw=True)
        for key in study.manifest['inputs']:study.input(key,raw=True)
        rows=[]
        for identity,task in study.tasks.items():
            envelope=study.envelope(identity)
            if envelope['task_sha256']!=digest(encoded(task)):raise ValueError('sealed task differs')
            artifacts={}
            for path,sha in envelope['artifacts'].items():
                raw=study.read(path,sha,raw=True)
                if path.endswith('.json'):artifacts[path.rsplit('/',1)[-1]]=__import__('json').loads(raw)
            reference=study.input(task['payload']['reference_key'])
            if digest(study.input(task['input_key'],raw=True))!=reference['certificate']['case_sha256']:
                raise ValueError('frozen history differs from its source certificate')
            if study.manifest['environment']!=reference['certificate']['environment']:
                raise ValueError('recorded environment differs from the reused reference')
            row=check_case(task,envelope,reference,artifacts)
            rows.append(dict(row,model=task['payload']['model'],profile=task['payload']['profile'],
                parent_result_sha256=study.rows[identity]['artifact_sha256']))
        return dict(version='lll-prefix-saved-format-audit-v1',parent=prefix,
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            rows=rows,report_comparisons=sum(r['report_comparisons'] for r in rows),
            missing_reports=sum(len(r['missing_queries']) for r in rows),
            oracle_comparisons=sum(r['oracle_comparisons'] for r in rows),
            cached_recovery_identities=[r['identity'] for r in rows if r['needs_cached_recovery']],
            numerical_work=0,original_reads=0,optimizer_starts=0,long_history_qualified=False,
            observational_coverage_qualified=False,scientific_decision='abstain')
    finally:study.close()


if __name__=='__main__':
    import argparse
    import json
    from pathlib import Path
    from .studies.artifacts import atomic,safe_path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--study',default='data/ilvis0-native-prefix-long-v2-20261022')
    parser.add_argument('--output',required=True)
    args=parser.parse_args();path=safe_path(args.root,args.output)
    if path.exists():raise ValueError('fresh saved-audit output required')
    report=inspect(args.root,args.study);atomic(path,encoded(report))
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},sort_keys=True))
