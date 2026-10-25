# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only comparison of the matched ESA gravity revision and original pilot."""


def verify_gravity(binding,compilation,*,anchor):
    expected=dict(gravity_model='inverse-square-height-v1',gravity_anchor_height_m=anchor,
        gravity_anchor_source='first_training_receiver_height',predicted_midpoint_height=True,
        extra_parameters=0,later_receiver_heights_used=False)
    if binding!=expected:raise ValueError('unchanged earlier-only height-gravity binding required')
    if any(compilation[k].get('gravity_model')!=expected['gravity_model']
            or compilation[k].get('gravity_anchor_height_m')!=anchor for k in ('value','tangent')):
        raise ValueError('both compiled kernels must use the same earlier-only gravity anchor')


def matched_changes(report,baseline):
    old={v['identity']:v for v in baseline['rows']};new={v['identity']:v for v in report['rows']}
    if (old.keys()!=new.keys() or len(old)!=len(baseline['rows']) or len(new)!=len(report['rows'])):
        raise ValueError('same distinct identities required for baseline comparison')
    result=[]
    for identity,current in new.items():
        previous=old[identity];row=dict(identity=identity)
        for label,value in [('baseline',previous),('revised',current)]:
            row[label+'_complete']=bool(value['complete']);row[label+'_qualified']=bool(value['passed'])
            for key in ('horizontal_rms_m','vertical_rms_m','total_rms_m'):
                row[label+'_prediction_'+key]=value.get('prediction',{}).get(key)
        result.append(row)
    return result


def inspect(root,prefix='data/esa-observed-height-pilot-20261023'):
    import gzip
    import json
    from lll.studies.closed import ClosedStudy
    from lll.airquantumgrav_observed_height import UNCHANGED_INPUTS,recipe,require_qualification
    from lll.airquantumgrav_observed_report import inspect as base
    # ClosedStudy rejects unfinished data before numerical components are loaded.
    study=ClosedStudy(root,prefix)
    try:
        if study.input('recipe')!=recipe():raise ValueError('declared gravity-only revision required')
        require_qualification(study.input('qualified-controls'))
        original=ClosedStudy(root,'docs/esa-development-pilot')
        try:
            receipt=original.read('evidence-receipt.json');name='artifacts/publication/verified-report.json'
            baseline=original.read(name,receipt['artifacts'][name]);expected=dict(
                manifest_sha256=original.completion['manifest_sha256'],summary_sha256=original.completion['summary_sha256'],
                unchanged_input_sha256={key:original.manifest['inputs'][key]['sha256'] for key in UNCHANGED_INPUTS})
            if (baseline.get('verified') is not True or baseline.get('total')!=24
                    or baseline['manifest_sha256']!=expected['manifest_sha256']
                    or baseline['summary_sha256']!=expected['summary_sha256']
                    or study.input('baseline-binding')!=expected
                    or {key:study.manifest['inputs'][key]['sha256'] for key in UNCHANGED_INPUTS}!=expected['unchanged_input_sha256']):
                raise ValueError('exact original measurements, split and verified baseline required')
        finally:original.close()
        training=json.loads(gzip.decompress(study.input('training',raw=True)));anchor=training[0]['height_m']
        report=base(root,prefix)
        for row in report['rows']:
            if not row['returned']:continue
            identity=row['identity'];envelope=study.envelope(identity);paths=envelope['artifacts']
            gb='artifacts/'+identity+'/gravity-binding.json';cm='artifacts/'+identity+'/compilation.json'
            if row['complete'] or (gb in paths and cm in paths):
                verify_gravity(study.artifact(identity,'gravity-binding.json'),study.artifact(identity,'compilation.json'),anchor=anchor)
            if row['complete'] and any(row.get(key)!=value for key,value in
                    [('gravity_model','inverse-square-height-v1'),('gravity_anchor_height_m',anchor),
                     ('gravity_anchor_source','first_training_receiver_height')]):raise ValueError('result gravity binding differs')
        report.update(gravity_model='inverse-square-height-v1',gravity_anchor_height_m=anchor,
            gravity_anchor_source='first_training_receiver_height',baseline_binding=expected,
            matched_baseline_changes=matched_changes(report,baseline),original_measurements_and_split_unchanged=True)
        return report
    finally:study.close()


def render(report):
    from lll.airquantumgrav_observed_report import render as base
    text=base(report).replace('# ESA: predicting the later flight','# ESA: height-dependent gravity prediction',1)
    explanation=('The original twenty-minute recording, earlier/later split, calibration bounds,\n'
        'starts, receiver-error policies and accuracy limits are unchanged. This run\n'
        'changes only the declared gravity law: gravity varies with the predicted\n'
        'height, anchored to the first earlier receiver height. Later receiver heights\n'
        'are opened only after the complete forecast has been saved.\n\n'
        '[Original pilot](../esa-development-pilot/README.md) · '
        '[Matched changes for every start](baseline-changes.csv).\n\n')
    text=text.replace('\n\n','\n\n'+explanation,1)
    return text.replace('[Frozen fitting plan](FIT_PLAN.md)','[Frozen fitting plan](PLAN.md)')


def publish(root,prefix='data/esa-observed-height-pilot-20261023',output='docs/esa-observed-height-pilot'):
    import csv
    import io
    import json
    from pathlib import Path
    from lll.ilvis0_control_publication import publish as package
    from lll.airquantumgrav_observed_report import csv_tables
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.publication import archive_publication
    root=Path(root).resolve();data=safe_path(root,prefix);public=safe_path(root,output)
    if (public/'evidence-receipt.json').exists():raise ValueError('height publication already sealed')
    report=inspect(root,prefix)
    study=ClosedStudy(root,prefix)
    try:plan_hash=study.manifest['sources']['docs/esa-observed-height-pilot/PLAN.md']
    finally:study.close()
    if digest((public/'PLAN.md').read_bytes())!=plan_hash:raise ValueError('preserved plan differs from frozen source')
    selector=(root/'analysis/lll/ilvis0_forecast_publication.py').read_bytes()
    if digest(selector)!=report['primary_selector_source_sha256']:raise ValueError('selector changed during reporting')
    stream=io.StringIO(newline='');rows=report['matched_baseline_changes']
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    package(data,public,render(report));receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    receipt['artifacts']['PLAN.md']=plan_hash
    additions=[('artifacts/publication/verified-report.json',encoded(report)),
        ('artifacts/publication/reporter.py',Path(__file__).read_bytes()),
        ('artifacts/publication/source-freeze/analysis/lll/ilvis0_forecast_publication.py',selector),
        ('baseline-changes.csv',stream.getvalue().encode()),*csv_tables(report).items()]
    for name,raw in additions:atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt))
    return dict(archive_publication(root,data,public),published=output,original_reads=0,native_calls=0)
