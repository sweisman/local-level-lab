# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separately bounded recovery of cached reports lost by a format comparison."""
import json
from pathlib import Path
from lll.studies.artifacts import atomic,digest,encoded,safe_path


def regression_gate(root,prefix):
    import xml.etree.ElementTree as ET
    root=Path(root);p=safe_path(root,prefix)
    request=json.loads((p/'request.json').read_bytes());completion=json.loads((p/'completion.json').read_bytes())
    required={'analysis/tests/test_ilvis0_native_prefix_long.py',
        'analysis/tests/test_ilvis0_native_prefix_recovery.py',
        'analysis/tests/test_ilvis0_summary_error_controls.py::test_dense_lineage_accepts_the_actual_numerical_error_family'}
    if (completion.get('state')!='complete' or completion.get('exit_code')!=0
            or completion.get('numerical_threads')!=0 or completion.get('request_sha256')!=digest(encoded(request))
            or request.get('numerical_threads')!=1 or request.get('reserved_threads')!=3
            or not required<=set(request['arguments'])):
        raise ValueError('completed bound numerical regression required')
    if not request['sources'] or any(digest(safe_path(root,p).read_bytes())!=h for p,h in request['sources'].items()):
        raise ValueError('qualified regression source changed')
    raw=(p/'results.xml').read_bytes();suites=list(ET.fromstring(raw).iter('testsuite'))
    count=sum(int(s.get('tests','0')) for s in suites)
    if count<45 or any(int(s.get(k,'0'))!=0 for s in suites for k in ('errors','failures','skipped')):
        raise ValueError('complete passing numerical regression required')
    return dict(tests=count,request_sha256=digest(encoded(request)),results_sha256=digest(raw),
        threads=1,reserved_threads=3,source_hashes=request['sources'])


def auxiliary_limits():
    from lll.ilvis0_native_prefix_long import recipe,batch_limits
    return dict(reference_setups=1,conditional_proofs=1,exact_supports=6,
        reused_cold_reports=2,reused_native_records=2,report_comparisons=2,design_comparisons=2,
        **batch_limits(recipe()['packets']))


def verify_parent_publication(root,parent):
    """Use the complete hash receipt after the closed parent is compacted."""
    from lll.studies.closed import ClosedStudy
    root=Path(root);study=ClosedStudy(root,parent)
    try:
        public='docs/ilvis0-native-prefix-long-v2'
        receipt=json.loads((root/public/'evidence-receipt.json').read_bytes())
        if (receipt['artifacts']['manifest.json']!=study.completion['manifest_sha256']
                or receipt['artifacts']['summary.json']!=study.completion['summary_sha256']):
            raise ValueError('published parent identity differs from the closed study')
        for name,sha in receipt['artifacts'].items():
            study.reference(dict(path=public+'/'+name,sha256=sha),raw=True)
        return len(receipt['artifacts'])
    finally:study.close()


def prepare(root,*,identity='ilvis0-native-prefix-format-recovery-v2-20261023'):
    import subprocess
    from lll.ilvis0_control_shards import verify_completion,runtime_environment
    from lll.ilvis0_native_prefix_long import recipe
    from lll.ilvis0_native_prefix_audit import inspect,compatible_recovery_sources
    from lll.studies.closed import ClosedStudy
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    root=Path(root).resolve();parent='data/ilvis0-native-prefix-long-v2-20261022'
    base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh recovery freeze required')
    # A published parent has already passed the runner's full completion check.
    # Its source/inputs may now be archived; verify every published byte instead
    # of recreating hundreds of physical files just to repeat that check.
    if (root/parent/'source-freeze/analysis/lll/ilvis0_native_prefix_long.py').exists():
        verify_completion(root/parent)
    else:verify_parent_publication(root,parent)
    audit=inspect(root,parent)
    qualified=regression_gate(root,'data/ilvis0-source-point-development/prefix-format-regression-v1')
    needed=[r for r in audit['rows'] if r['needs_cached_recovery']]
    if (not 0<len(needed)<=4 or any(r['missing_queries']!=[1] or r['model'] not in (0,1) for r in needed)):
        raise ValueError('only the audited missing later globe reports belong to this repair')
    study=ClosedStudy(root,parent)
    try:
        if study.manifest['environment']!=runtime_environment():raise ValueError('parent numerical environment changed')
        adapter='analysis/lll/ilvis0_native_prefix_long.py';storage='analysis/lll/studies/artifacts.py'
        compatibility=compatible_recovery_sources(study.manifest['sources'],root,
            frozen_adapter=study.read('source-freeze/'+adapter,study.manifest['sources'][adapter],raw=True),
            frozen_storage=study.read('source-freeze/'+storage,study.manifest['sources'][storage],raw=True))
        compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
        base.mkdir(parents=True);gate=dict(audit=audit,regression=qualified,compatibility=compatibility,compiler=compiler)
        atomic(base/'gate.json',encoded(gate));inputs={'gate':str((base/'gate.json').relative_to(root))};tasks=[]
        regression='data/ilvis0-source-point-development/prefix-format-regression-v1/'
        for name in ('request.json','completion.json','results.xml','tests.log'):
            target=base/('regression-'+name);atomic(target,safe_path(root,regression+name).read_bytes())
            inputs['regression-'+name]=str(target.relative_to(root))
        for row in needed:
            old_id=row['identity'];task=study.tasks[old_id];spec=task['payload']
            reference=study.input(spec['reference_key']);cert=reference['certificate']
            if cert['compiler']!=compiler:raise ValueError('parent compiler changed')
            original_reports=[study.artifact(old_id,'cold-00.json'),study.artifact(old_id,'cold-01-reused.json')]
            native_records=[study.artifact(old_id,f'native-{i:02d}.json') for i in range(2)]
            material=dict(reference=reference,original_reports=original_reports,native_records=native_records,
                parent_identity=old_id,parent_manifest_sha256=audit['manifest_sha256'],
                parent_result_sha256=row['parent_result_sha256'])
            name='cached-'+old_id;case=study.input(task['input_key'],raw=True)
            atomic(base/(name+'.json'),case);atomic(base/(name+'-records.json'),encoded(material))
            inputs[name]=str((base/(name+'.json')).relative_to(root))
            inputs[name+'-records']=str((base/(name+'-records.json')).relative_to(root))
            tasks.append(dict(identity=name,input_key=name,
                payload=dict(model=spec['model'],profile=spec['profile'],records_key=name+'-records',
                    parent_identity=old_id,parent_manifest_sha256=audit['manifest_sha256'],
                    parent_result_sha256=row['parent_result_sha256'],auxiliary_limits=auxiliary_limits(),recipe=recipe()),
                limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=18*recipe()['packets'])))
        adapter='analysis/lll/ilvis0_native_prefix_repair_study.py'
        seeds=list(set(study.manifest['sources'])|set(qualified['source_hashes']))+[
            adapter,'analysis/tests/test_ilvis0_native_prefix_repair_study.py',
            'analysis/tests/test_ilvis0_native_prefix_recovery.py','analysis/tests/test_ilvis0_native_prefix_audit.py',
            'analysis/tests/test_ilvis0_native_prefix.py','analysis/tests/native_prefix_reference.py',
            'analysis/tests/ilvis0_native_prefix_reference.json',
            'docs/ilvis0-native-prefix-format-recovery/PLAN.md']
        definition=dict(id=identity,adapter=adapter,sources=source_closure(root,seeds),inputs=inputs,tasks=tasks,
            workers=len(tasks),threads=1,maximum_wall_s=21600.)
        atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
        return dict(path='data/'+identity,tasks=len(tasks),allocation=manifest['allocation'],limits=manifest['limits'],
            parent_manifest_sha256=audit['manifest_sha256'],saved_report_comparisons=audit['report_comparisons'],
            missing_reports=audit['missing_reports'],regression_tests=qualified['tests'])
    finally:study.close()


def evaluate(task,context):
    import subprocess
    from lll.ilvis0_control_shards import _check_continue,runtime_environment
    from lll.ilvis0_native_prefix_long import restore,recipe
    from lll.ilvis0_native_prefix_recovery import recover
    from lll.ilvis0_source_prefix import load_kernels
    from lll.ilvis0_batched_transport import configure_backend
    from lll.studies.journal import Journal
    spec=task['payload'];allowance=auxiliary_limits()
    if spec['recipe']!=recipe() or spec['auxiliary_limits']!=allowance:raise ValueError('fixed recovery scope required')
    gate=json.loads(context.input_path('gate').read_bytes());record=json.loads(context.input_path(spec['records_key']).read_bytes())
    certificate=record['reference']['certificate'];case=context.input_path().read_bytes()
    if (any(record[k]!=spec[k] for k in ('parent_identity','parent_manifest_sha256','parent_result_sha256'))
            or record['parent_manifest_sha256']!=gate['audit']['manifest_sha256']
            or certificate['environment']!=runtime_environment() or context.manifest['environment']!=certificate['environment']
            or digest(case)!=certificate['case_sha256'] or certificate['compiler']!=gate['compiler']
            or gate['compiler']!=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]):
        raise ValueError('reused parent records, history, compiler or environment changed')
    path=context.directory/'allowance.sqlite';journal=Journal(path,
        freeze=digest((context.root/'manifest.json').read_bytes()),limits={task['identity']:allowance})
    journal.start(task['identity'])
    def checkpoint():_check_continue(context.root,context.manifest)
    def reserve(**values):
        checkpoint()
        for key,n in values.items():journal.reserve(task['identity'],key,n)
    try:
        value=restore(record['reference']['material'],json.loads(case),reserve=reserve)
        if value['configuration']['model']!=spec['model'] or bool(value['configuration']['profile'])!=spec['profile']:
            raise ValueError('fixed candidate identity differs')
        reserve(reused_cold_reports=2,reused_native_records=2,report_comparisons=2,design_comparisons=2)
        directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';source=context.root/'source-freeze/analysis/lll'
        backend=configure_backend(directory,source_directory=source);kernels,metadata=load_kernels(directory,source_directory=source)
        metadata['backend']=backend
        for meta in metadata.values():
            if meta['compiler']!=gate['compiler'] or any(context.manifest['sources'].get('analysis/lll/'+n)!=h
                    for n,h in meta['sources'].items()):raise ValueError('compiled recovery source differs')
        context.save('compilation.json',metadata)
        result=recover(value,original_reports=record['original_reports'],native_records=record['native_records'],
            prefix_kernels=kernels,reserve=reserve,charge=context.charge,save=context.save,
            maximum_seconds=recipe()['maximum_batch_seconds'],maximum_packet_steps=allowance['packet_steps'],
            maximum_rss_bytes=recipe()['maximum_rss_bytes'],checkpoint=checkpoint)
        counts={k:journal.count(task['identity'],k) for k in allowance}
        if counts!=allowance:raise ValueError('recovery reservations differ from the frozen limits')
        context.save('accounting.json',counts)
        result=dict(result,identity=task['identity'],model=spec['model'],profile=spec['profile'],
            parent_identity=spec['parent_identity'],parent_manifest_sha256=spec['parent_manifest_sha256'],
            charged_auxiliary=counts)
        context.save('recovery-checks.json',result);return result
    finally:journal.verify();context.note_file(path)


def inspect(root,prefix='data/ilvis0-native-prefix-format-recovery-v2-20261023'):
    from lll.studies.closed import ClosedStudy
    from lll.ilvis0_native_prefix_audit import check_saved_pair
    from lll.ilvis0_native_prefix_long import recipe
    study=ClosedStudy(root,prefix)
    try:
        gate=study.input('gate');audit=gate['audit'];old={r['identity']:r for r in audit['rows']};rows=[]
        tasks={t['payload']['parent_identity']:t for t in study.tasks.values()}
        if (len(old)!=6 or set(tasks)!=set(audit['cached_recovery_identities'])
                or len(tasks)!=len(study.tasks) or set(study.rows)!=set(study.tasks)):
            raise ValueError('complete, exactly matched missing-output recovery required')
        for parent,row in old.items():
            result=dict(row)
            if parent in tasks:
                task=tasks[parent];identity=task['identity'];envelope=study.envelope(identity)
                result['recovery_result']=envelope['result'];result['complete']=False
                # Verify every recorded artifact, including failures, before
                # describing either acceptance or missing evidence.
                for path,sha in envelope['artifacts'].items():study.read(path,sha,raw=True)
                if envelope['result'].get('passed'):
                    if (envelope['result']!=study.artifact(identity,'recovery-checks.json')
                            or envelope['charged']!=task['limits']
                            or study.artifact(identity,'accounting.json')!=auxiliary_limits()):
                        raise ValueError('saved recovery result or accounting differs')
                    records=study.input(task['payload']['records_key']);checks=[]
                    for i,t in enumerate(recipe()['times_s']):
                        checked=check_saved_pair(records['original_reports'][i],
                            study.artifact(identity,f'batched-{i:02d}.json'),records['native_records'][i],expected_time=t)
                        if checked!=study.artifact(identity,f'design-{i:02d}.json'):
                            raise ValueError('reconstructed saved design differs')
                        checks.append(checked)
                    result.update(complete=True,recovery_checks=checks)
            else:
                if row['missing_queries'] or not row['all_queries_verified']:
                    raise ValueError('uncovered missing parent evidence')
                result['complete']=True
            rows.append(result)
        return dict(rows=rows,complete=all(r['complete'] for r in rows),
            complete_histories=sum(r['complete'] for r in rows),original_histories=6,
            parent_manifest_sha256=audit['manifest_sha256'],manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],new_cached_calls=len(study.rows),
            new_native_calls=0,new_original_cold_calls=0,numerical_work=0,
            long_history_qualified=all(r['complete'] for r in rows),
            observational_coverage_qualified=False,scientific_decision='abstain')
    finally:study.close()


def render(report):
    labels=['Globe + field','Globe, zero field','Stationary disc']
    lines=['# Recovering the complete long-history comparison','',
        'This software check recovers reports lost when a Python tuple/list comparison '
        'rejected numerically identical JSON data. Earlier failure records remain unchanged.',
        '', '| Candidate | Processing | Evidence | Result |','|---|---|---|---|']
    for row in report['rows']:
        lines.append('| '+' | '.join([labels[row['model']],
            'Profiled removal' if row['profile'] else 'Zero removal',
            'New cached reports; saved original and point checks' if 'recovery_result' in row else 'Both cached reports retained previously',
            'Complete reports equal' if row['complete'] else 'Incomplete'])+' |')
    lines+=['',f"**{report['complete_histories']}/6 histories have complete verified comparisons.**",
        '', 'Each history has 96,000 generated IMU packets and queries at 290 and 438 seconds. '
        'Complete reports must match exactly, all 51 coefficient columns must agree, '
        'and the saved independent point checks retain their original arithmetic tolerance.',
        '', f"The recovery used {report['new_cached_calls']} new two-query cached batches, "
        'zero new original calculations and zero new point-oracle calls. It changes no '
        'physical model, calibration bound, prediction target or scientific finding.',
        '', 'This qualifies long-history reuse only when all six comparisons pass. '
        'Whole-record prediction uncertainty and observational coverage remain separate gates.',
        '', '[Frozen limits](PLAN.md) · [Original run and failures](../ilvis0-native-prefix-long-v2/README.md) · '
        '[Prediction gates](../ilvis0-joint-projection-controls/NEXT_PLAN.md)']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/ilvis0-native-prefix-format-recovery-v2-20261023',output='docs/ilvis0-native-prefix-format-recovery'):
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();public=safe_path(root,output);data=safe_path(root,prefix)
    if (public/'evidence-receipt.json').exists():raise ValueError('publication already sealed')
    report=inspect(root,prefix)
    package(data,public,render(report),plan='docs/ilvis0-native-prefix-format-recovery/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes());name='artifacts/publication/comparison.json'
    raw=encoded(report);atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)


def publish_parent(root):
    """Preserve failed labels and publish the complete saved-only audit."""
    from lll.ilvis0_native_prefix_long import inspect as old_inspect,render as old_render
    from lll.ilvis0_native_prefix_audit import inspect as saved_audit
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();prefix='data/ilvis0-native-prefix-long-v2-20261022'
    public=root/'docs/ilvis0-native-prefix-long-v2'
    if (public/'evidence-receipt.json').exists():raise ValueError('parent publication already sealed')
    report=old_inspect(root,prefix);audit=saved_audit(root,prefix)
    text=old_render(report)+'\n## Saved-output audit\n\n'
    text+=(f"All six histories finished. {audit['report_comparisons']} retained original/cached report pairs "
        f"match exactly; all {audit['oracle_comparisons']} saved independent point checks pass the unchanged "
        f"arithmetic allowance. {audit['missing_reports']} later cached reports were not saved after the "
        'tuple/list comparison stopped their tasks. Both disc histories already retain every report.\n\n'
        'These saved checks preserve the original failure labels. A separately bounded '
        '[recovery](../ilvis0-native-prefix-format-recovery/README.md) reuses all original and point '
        'records and calculates only the missing cached outputs. Its numerical repair passed 45 regression checks.\n')
    package(root/prefix,public,text,plan='docs/ilvis0-native-prefix-long/V2_PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,value in (('comparison.json',report),('saved-audit.json',audit)):
        alias='artifacts/publication/'+name;raw=encoded(value);atomic(public/alias,raw);receipt['artifacts'][alias]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,root/prefix,public),published=str(public.relative_to(root)),numerical_work=0)
