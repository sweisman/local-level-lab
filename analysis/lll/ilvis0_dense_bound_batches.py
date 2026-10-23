# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reusable physical-domain bounds at every fixed dense training epoch.

No observations or error laws enter these bounds. Conditioning and withheld
prediction are subsequent, separately budgeted stages of the same experiment.
"""
import json
import math
from pathlib import Path

NATIVE_SOURCES=('analysis/lll/ilvis0_source_prefix_reference.cpp',
                'analysis/lll/ilvis0_source_prefix_intervals.cpp')


def recipe():
    return dict(identities=6,packets=96000,times_s=list(map(float,range(2,291))),
        physical_parameters=27,expression_columns=51,workers=4,threads=1,
        clock_limit_s=1.,
        maximum_batch_s=43200.,maximum_wall_s=93600.,maximum_rss_bytes=1536*1024**2,
        maximum_record_bytes=1048576,oracle_arithmetic_allowance_m=1e-5,
        original_reads=0,optimizer_starts=0,new_native_calls=0)


def auxiliary_limits():
    n=recipe()['packets'];q=len(recipe()['times_s'])
    return dict(reference_setups=1,physical_proofs=1,reused_native_batches=1,
        preparation_packets=n,force_profile_packets=q*n,packet_steps=n+q*512,
        prefix_packet_steps=n,tail_packet_steps=q*512,cursor_copies=q,
        source_state_copies=3*q,source_query_checks=3*q,reports=q)


def selected_native(value,*,case_sha256,compiler,environment,native_source_sha256):
    """Select earlier epochs without reinterpreting an aggregate native counter."""
    from lll.ilvis0_training_density import recipe as saved_recipe
    from lll.studies.artifacts import digest,encoded
    old=saved_recipe();times=old['dense_s']+[old['future_s']];native=value['native'];n=len(times)
    if (value['case_sha256']!=case_sha256 or value['compiler']!=compiler or value['environment']!=environment
            or value['native_source_sha256']!=native_source_sha256 or value['point']!=[0.]*27
            or value['times_s']!=times or native['status']!=0 or type(native['counter']) is not int
            or not 0<=native['counter']<=n
            or native['classification']!=dict(counter_verified=True,expected_counter=native['counter'],
                query_count=n,derivative_smoothness_qualified=False)
            or len(native['prediction'])!=n or len(native['jacobian'])!=n
            or any(len(row)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in row)
                for row in native['prediction'])
            or any(len(matrix)!=3 or any(len(row)!=27 or any(type(v) not in (int,float)
                or not math.isfinite(v) for v in row) for row in matrix) for matrix in native['jacobian'])):
        raise ValueError('matching sealed native source, point, times, environment and complete batch required')
    indices=[times.index(t) for t in recipe()['times_s']]
    return dict(prediction=[native['prediction'][i] for i in indices],jacobian=[native['jacobian'][i] for i in indices],
        indices=indices,original_query_count=n,original_counter=native['counter'],
        original_batch_sha256=digest(encoded(native)),subset_counter_reinterpreted=False)


def observer_compatibility(current,qualified):
    """Prove that reporting plumbing is the sole change to qualified math."""
    import ast
    from lll.studies.artifacts import digest
    tree=ast.parse(current)
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='enclose_many')
    if (function.args.kwonlyargs[-1].arg!='on_report'
            or not isinstance(function.args.kw_defaults[-1],ast.Constant)
            or function.args.kw_defaults[-1].value is not None):
        raise ValueError('only optional report observer extension supported')
    function.args.kwonlyargs.pop();function.args.kw_defaults.pop();removed=[]
    class Strip(ast.NodeTransformer):
        def visit_If(self,node):
            test=ast.unparse(node.test)
            if test=='on_report is not None':
                if (len(node.body)!=1 or node.orelse
                        or ast.unparse(node.body[0])!='on_report(len(bounds) - 1, deepcopy(bounds[-1].report()))'):
                    raise ValueError('unexpected report observer action')
                removed.append(test);return None
            if test=='on_report is not None and (not callable(on_report))':
                if len(node.body)!=1 or node.orelse or not isinstance(node.body[0],ast.Raise):
                    raise ValueError('unexpected observer validation')
                removed.append(test);return None
            return self.generic_visit(node)
    tree=Strip().visit(tree)
    if len(removed)!=2 or ast.dump(tree,include_attributes=False)!=ast.dump(ast.parse(qualified),include_attributes=False):
        raise ValueError('qualified numerical source changed beyond report plumbing')
    return dict(current_sha256=digest(current),qualified_sha256=digest(qualified),numerical_ast_unchanged=True,
        observer_isolated_by_deepcopy=True)


def prepare(root,identity='ilvis0-dense-physical-bounds-20261023'):
    import subprocess
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.dependencies import source_closure
    from lll.studies.runtime import Definition
    from lll.ilvis0_control_shards import runtime_environment
    from lll.ilvis0_dense_root_controls import inspect as inspect_roots
    root=Path(root).resolve();base=safe_path(root,'data/ilvis0-source-point-development/'+identity+'-inputs')
    if base.exists() or safe_path(root,'data/'+identity).exists():raise ValueError('fresh dense bound freeze required')
    roots=inspect_roots(root)
    if not roots['complete']:raise ValueError('all independent physical roots required')
    starting=ClosedStudy(root,'data/ilvis0-dense-physical-roots-v1-20261023')
    saved=ClosedStudy(root,'data/ilvis0-training-density-20261021',store=starting.store)
    reuse=ClosedStudy(root,'data/ilvis0-native-prefix-format-recovery-v2-20261023',store=starting.store)
    try:
        environment=runtime_environment();compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
        if any(s.manifest['environment']!=environment for s in (starting,saved,reuse)):
            raise ValueError('saved numerical environment differs')
        prefix='analysis/lll/ilvis0_native_prefix.py'
        compatible=observer_compatibility((root/prefix).read_bytes(),
            reuse.read('source-freeze/'+prefix,reuse.manifest['sources'][prefix],raw=True))
        unchanged={}
        for name,sha in starting.manifest['sources'].items():
            if name.startswith('analysis/lll/') and '/studies/' not in name and name!=prefix:
                if digest((root/name).read_bytes())!=sha:raise ValueError('qualified numerical dependency changed: '+name)
                unchanged[name]=sha
        native_sha=digest((root/'analysis/lll/ilvis0_tangent.cpp').read_bytes())
        indexed={(t['payload']['model'],t['payload']['profile']):t for t in saved.tasks.values()}
        prepared=[]
        for task in starting.tasks.values():
            model,profile=(task['payload'][k] for k in ('model','profile'))
            old=indexed[model,profile];old_id=old['identity'];raw=starting.input(task['input_key'],raw=True)
            sha=digest(raw);pointer=saved.input(old['payload']['case_key']);kernel=saved.artifact(old_id,'kernel.json')
            if (pointer['sha256']!=sha or kernel['compiler']!=compiler or kernel['source_sha256']!=native_sha
                    or saved.input(old['input_key'])!=__import__('lll.ilvis0_training_density',fromlist=['recipe']).recipe()
                    or not saved.envelope(old_id)['result']['passed']):
                raise ValueError('complete sealed dense native record differs')
            material=dict(native=saved.artifact(old_id,'native-batch.json'),case_sha256=sha,
                compiler=compiler,environment=environment,native_source_sha256=native_sha,
                point=[0.]*27,times_s=list(map(float,range(2,294)))+[438.],
                coordinate_scale=old['payload']['coordinate_scale'],
                provenance=dict(parent=saved.prefix,manifest_sha256=saved.completion['manifest_sha256'],
                    result_sha256=saved.rows[old_id]['artifact_sha256'],kernel=kernel))
            selected_native(material,case_sha256=sha,compiler=compiler,environment=environment,native_source_sha256=native_sha)
            prepared.append((model,profile,raw,material))
        if len(prepared)!=6 or {(m,p) for m,p,_,_ in prepared}!={(m,p) for m in range(3) for p in (False,True)}:
            raise ValueError('all six model/processing histories required')
        # Validate every reuse and compatibility check before creating a freeze.
        base.mkdir(parents=True);inputs={};tasks=[]
        for model,profile,raw,material in prepared:
            name=f'dense-bounds-{model}-{int(profile)}';atomic(base/(name+'.json'),raw)
            atomic(base/(name+'-native.json'),encoded(material))
            inputs[name]=str((base/(name+'.json')).relative_to(root))
            inputs[name+'-native']=str((base/(name+'-native.json')).relative_to(root))
            tasks.append(dict(identity=name,input_key=name,payload=dict(model=model,profile=profile,
                case_sha256=digest(raw),native_key=name+'-native',compiler=compiler,recipe=recipe(),
                auxiliary_limits=auxiliary_limits()),limits=dict(native_calls=0,packet_visits=0,
                    bound_calls=1,bound_steps=9*auxiliary_limits()['packet_steps'])))
        provenance=dict(root_checks=roots,observer=compatible,unchanged_numerical_sources=unchanged,
            reuse_manifest_sha256=reuse.completion['manifest_sha256'],environment=environment)
        atomic(base/'qualification.json',encoded(provenance));inputs['qualification']=str((base/'qualification.json').relative_to(root))
        adapter='analysis/lll/ilvis0_dense_bound_batches.py';plan='docs/ilvis0-dense-physical-bounds/PLAN.md'
        sources=source_closure(root,[adapter,plan,*NATIVE_SOURCES,'analysis/tests/test_ilvis0_dense_bound_batches.py',
            'analysis/tests/test_ilvis0_native_prefix.py','analysis/tests/native_prefix_reference.py',
            'analysis/tests/ilvis0_native_prefix_reference.json','analysis/tests/test_study_series.py'])
        definition=dict(id=identity,adapter=adapter,sources=sources,inputs=inputs,tasks=tasks,
            workers=4,threads=1,maximum_wall_s=recipe()['maximum_wall_s'])
        atomic(base/'definition.json',encoded(definition));manifest=Definition.from_dict(definition,root).prepare(root)
        return dict(path='data/'+identity,identities=6,allocation=manifest['allocation'],limits=manifest['limits'],sources=len(sources))
    finally:starting.close()


def evaluate(task,context):
    import resource
    import subprocess
    import time
    import numpy as np
    from lll.ilvis0_dense_root_controls import setup
    from lll.ilvis0_native_prefix import enclose_many
    from lll.ilvis0_source_prefix import load_kernels
    from lll.ilvis0_batched_transport import configure_backend
    from lll.ilvis0_training_remainder_audit import scaled_design
    from lll.ilvis0_control_shards import _check_continue
    from lll.studies.artifacts import digest,encoded
    from lll.studies.journal import Journal
    from lll.studies.series import ReportStream
    spec=task['payload'];r=recipe();raw=context.input_path().read_bytes();case=json.loads(raw)
    if (spec['recipe']!=r or spec['auxiliary_limits']!=auxiliary_limits() or digest(raw)!=spec['case_sha256']
            or spec['compiler']!=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]
            or any(case['configuration'][k]!=spec[k] for k in ('model','profile'))
            or any(len(case[k])!=r['packets'] for k in ('theta','dv','dt'))
            or any(v!=.005 for v in case['dt']) or case['configuration']['limits'][25]!=r['clock_limit_s']):
        raise ValueError('fixed dense batch scope, source or compiler differs')
    material=json.loads(context.input_path(spec['native_key']).read_bytes())
    native=selected_native(material,case_sha256=spec['case_sha256'],compiler=spec['compiler'],
        environment=context.manifest['environment'],native_source_sha256=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp'])
    path=context.directory/'allowance.sqlite';limits=auxiliary_limits()
    journal=Journal(path,freeze=digest((context.root/'manifest.json').read_bytes()),limits={task['identity']:limits})
    journal.start(task['identity']);stream_path=context.directory/'training-bounds.jsonl';started=time.monotonic()
    errors=[];matrix_rows=[]
    def checkpoint():_check_continue(context.root,context.manifest)
    def reserve(**values):
        checkpoint()
        for key,n in values.items():journal.reserve(task['identity'],key,n)
    try:
        value=setup(case,reserve=reserve);ref=value['reference'];proof=value['conditioning'].report()
        context.save('reference.json',ref.report());context.save('physical-proof.json',proof)
        reserve(reused_native_batches=1);context.save('selected-native.json',native)
        source=context.root/'source-freeze/analysis/lll';directory=context.root/'shards'/f'{context.shard:03d}'/'kernels'
        backend=configure_backend(directory,source_directory=source);kernels,metadata=load_kernels(directory,source_directory=source)
        for meta in (backend,*metadata.values()):
            if meta['compiler']!=spec['compiler'] or any(context.manifest['sources'].get('analysis/lll/'+n)!=h for n,h in meta['sources'].items()):
                raise ValueError('compiled dense-bound dependency differs')
        context.save('compilation.json',dict(backend=backend,prefix=metadata))
        binding=digest(encoded(dict(manifest_sha256=digest((context.root/'manifest.json').read_bytes()),
            identity=task['identity'],case_sha256=spec['case_sha256'],reference_binding=ref.binding,times_s=r['times_s'])))
        context.save('series-binding.json',dict(binding=binding,records=len(r['times_s']),maximum_record_bytes=r['maximum_record_bytes']))
        with ReportStream(stream_path,binding=binding,maximum_records=len(r['times_s']),maximum_record_bytes=r['maximum_record_bytes']) as stream:
            def observe(index,report):
                # Preserve the raw answer before any acceptance check can fail.
                stream.append(index,report);reserve(reports=1)
                error=np.abs((np.asarray(report['center'])-native['prediction'][index])*np.array([6371000.,6371000.,1.]))
                if (report['time_s']!=r['times_s'][index] or report['reference_binding']!=ref.binding
                        or report['source_id']!=ref.parent.source_id or report['conditioning']!=proof
                        or report['lower']!=[-1.]*27 or report['upper']!=[1.]*27 or report['normalized_center']!=[0.]*27
                        or max(error)>r['oracle_arithmetic_allowance_m']
                        or resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024>r['maximum_rss_bytes']):
                    raise ValueError('dense bound/source/domain/native check failed')
                matrix=scaled_design(native['jacobian'][index],report,material['coordinate_scale'])
                if len(matrix)!=3 or any(len(row)!=51 for row in matrix):raise ValueError('every expression column required')
                matrix_rows.extend(matrix);errors.append(error.tolist())
            context.charge(bound_calls=1,bound_steps=9*limits['packet_steps'])
            result=enclose_many(value['configuration'],value['theta'],value['dv'],value['dt'],times=r['times_s'],
                lower=value['lower'],upper=value['upper'],reference=ref,conditioning=value['conditioning'],
                prefix_kernels=kernels,maximum_packet_steps=limits['packet_steps'],reserve=reserve,
                maximum_seconds=r['maximum_batch_s'],on_report=observe)
        counts={k:journal.count(task['identity'],k) for k in limits}
        if (len(errors)!=len(r['times_s']) or counts['reports']!=len(r['times_s']) or time.monotonic()-started>r['maximum_batch_s']
                or any(counts[k]!=v for k,v in result['work'].items())):
            raise ValueError('complete dense batch or accounting differs')
        context.save('columns.json',dict(design=matrix_rows,native_center_error_m=errors,coordinate_scale=material['coordinate_scale']))
        context.save('accounting.json',counts)
        outcome=dict(identity=task['identity'],passed=True,model=spec['model'],profile=spec['profile'],
            training_epochs=len(errors),physical_parameters=27,expression_columns=51,
            maximum_native_center_error_m=max(max(v) for v in errors),elapsed_s=time.monotonic()-started,
            work=result['work'],charged_auxiliary=counts,reused_native_batches=1,new_native_calls=0,
            whole_prediction_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')
        context.save('dense-bound-checks.json',outcome);return outcome
    finally:
        journal.verify();context.note_file(path)
        if stream_path.exists():context.note_file(stream_path)


def inspect(root,prefix='data/ilvis0-dense-physical-bounds-20261023'):
    from lll.studies.closed import ClosedStudy
    from lll.studies.series import read_report_bytes
    from lll.studies.artifacts import reports_equal
    study=ClosedStudy(root,prefix);rows=[];r=recipe()
    try:
        for identity,task in study.tasks.items():
            if identity not in study.rows:
                rows.append(dict(identity=identity,passed=False,reason='not started',**{k:task['payload'][k] for k in ('model','profile')}));continue
            envelope=study.envelope(identity);row=dict(envelope['result'])
            for name,sha in envelope['artifacts'].items():study.read(name,sha,raw=True)
            key='artifacts/'+identity+'/training-bounds.jsonl'
            count=0
            if key in envelope['artifacts']:
                binding=study.artifact(identity,'series-binding.json')
                reports=read_report_bytes(study.artifact(identity,'training-bounds.jsonl',raw=True),
                    binding=binding['binding'],maximum_records=len(r['times_s']),maximum_record_bytes=r['maximum_record_bytes'])
                count=len(reports)
                if [v['time_s'] for v in reports]!=r['times_s'][:count]:raise ValueError('saved report prefix changed')
            if row.get('passed'):
                if (count!=len(r['times_s']) or not reports_equal(row,study.artifact(identity,'dense-bound-checks.json'))
                        or envelope['charged']!=task['limits'] or row['charged_auxiliary']!=study.artifact(identity,'accounting.json')):
                    raise ValueError('complete saved dense batch or accounting changed')
                proof=study.artifact(identity,'physical-proof.json');ref=study.artifact(identity,'reference.json')
                if (proof['uses_training_data'] is not False or any(v['conditioning']!=proof or v['reference_binding']!=ref['binding']
                        or v['lower']!=[-1.]*27 or v['upper']!=[1.]*27 or v['normalized_center']!=[0.]*27 for v in reports)):
                    raise ValueError('independent physical-domain premise changed')
            row.update(identity=identity,saved_reports=count,model=task['payload']['model'],profile=task['payload']['profile']);rows.append(row)
        complete=len(rows)==6 and {(v['model'],v['profile']) for v in rows if v.get('passed')}=={(m,p) for m in range(3) for p in (False,True)}
        return dict(rows=rows,complete=complete,training_reports=sum(v['saved_reports'] for v in rows if 'saved_reports' in v),
            manifest_sha256=study.completion['manifest_sha256'],summary_sha256=study.completion['summary_sha256'],
            numerical_work=0,whole_prediction_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')
    finally:study.close()


def render(report):
    labels=['Globe + field','Globe, zero field','Stationary disc']
    lines=['# Prediction bounds at every training epoch','',
        'This software study keeps the complete physical calibration range and calculates '
        '289 training envelopes for each of six generated histories. No earlier one-metre '
        'training proof, aircraft original or withheld observation enters the calculation.',
        '', '| Candidate | Processing | Saved epochs | Result |','|---|---|---:|---|']
    for row in report['rows']:
        lines.append('| '+' | '.join([labels[row['model']],'Profiled removal' if row['profile'] else 'Zero removal',
            str(row.get('saved_reports',0)),'Passed' if row.get('passed') else 'Not qualified'])+' |')
    lines+=['',f"**{sum(v.get('passed') is True for v in report['rows'])}/6 complete batches passed; {report['training_reports']}/1,734 reports preserved.**",
        '', 'These are training bounds, not withheld forecasts or scientific detections. '
        'The next stage connects each of the four declared noise laws to fresh training '
        'constraints, then checks every later epoch under a separate finite allowance. '
        'Observed error-law adequacy and whole-program numerical coverage remain separate gates.',
        '', '[Limits and complete-experiment sequence](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md)']
    return '\n'.join(lines)+'\n'


def publish(root,prefix='data/ilvis0-dense-physical-bounds-20261023',output='docs/ilvis0-dense-physical-bounds'):
    from lll.ilvis0_control_publication import publish as package
    from lll.studies.artifacts import atomic,encoded,digest,safe_path
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();public=safe_path(root,output);data=safe_path(root,prefix)
    if (public/'evidence-receipt.json').exists():raise ValueError('dense-bound publication already sealed')
    report=inspect(root,prefix);package(data,public,render(report),plan='docs/ilvis0-dense-physical-bounds/PLAN.md')
    receipt=json.loads((public/'evidence-receipt.json').read_bytes());name='artifacts/publication/comparison.json'
    raw=encoded(report);atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,numerical_work=0)
