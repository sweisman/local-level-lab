# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite two-cut forecast transfer across twenty unused NASA groups."""

import csv
import gzip
import io
import json
from pathlib import Path

from .ilvis0_remaining_prediction_layouts import OUTPUT as LAYOUTS

ID='ilvis0-remaining-prediction-transfer-20261118'
SCOPE=('twenty outcome-blind NASA development groups; specified-field globe '
       'two-cut descriptive forecast-error transfer only')
PLAN='docs/prediction-group-transfer/REMAINING_GROUPS_PREDICTION_PLAN.md'
REQUEST='docs/prediction-group-transfer/remaining-qualification-v2-request.json'
REPORT='docs/prediction-group-transfer/remaining-qualification-v2-tests.xml'
SELECTION='docs/prediction-group-transfer/remaining-groups.csv'
REFERENCE='docs/prediction-rolling-origin/result.csv'
WORKERS=4
THREADS=1
MAXIMUM_WALL_S=21600.
AUDITED_CHANGED_SOURCES=frozenset({
    'analysis/lll/airquantumgrav_noisy_inputs.py',
    'analysis/lll/airquantumgrav_observation_truth.py',
    'analysis/lll/airquantumgrav_prediction.py',
    'analysis/lll/airquantumgrav_receiver.py',
    'analysis/lll/airquantumgrav_training_controls.py',
    'analysis/lll/airquantumgrav_truth.py',
    'analysis/lll/ilvis0_control_shards.py',
    'analysis/lll/ilvis0_segments.py',
    'analysis/lll/structured_noisy_study.py',
    'analysis/lll/structured_noisy_training.py',
    'analysis/lll/studies/runtime.py',
    'analysis/lll/studies/testing.py',
})


def tasks(layouts):
    if (len(layouts)!=20 or len({row['segment_id'] for row in layouts})!=20
            or len({row['group_id'] for row in layouts})!=20):
        raise ValueError('twenty unique frozen prediction layouts required')
    result=[]
    for row in layouts:
        segment=row['segment_id']
        count=row['receiver_epochs']
        outer=row['training_epochs']
        packets=row['native_packets']
        if (not segment or type(count) is not int or count<9
                or type(outer) is not int or outer!=2*count//3
                or type(packets) is not int or packets<1):
            raise ValueError('complete exact native packet and receiver cut required')
        inner=count//3
        horizon=min(outer-inner,count-outer)
        for origin,cut in (('inner',inner),('outer',outer)):
            for start in (0,1):
                result.append(dict(identity=f'{segment}-{origin}-0-header_elapsed-{start}',
                    input_key=segment+'-common',
                    payload=dict(segment_id=segment,origin=origin,
                                 profile=False,clock='header_elapsed',start=start),
                    limits=dict(native_calls=201,
                                packet_visits=packets*(200*cut+cut+horizon),
                                bound_calls=0,bound_steps=0)))
    return result


def sources(root):
    from .ilvis0_group_transfer_study import sources as earlier_sources
    from .studies.dependencies import source_closure
    root=Path(root).resolve()
    extra=source_closure(root,[
        'analysis/lll/ilvis0_remaining_prediction_study.py',
        'analysis/lll/ilvis0_remaining_prediction_layouts.py',
        'analysis/lll/ilvis0_remaining_prediction_groups.py',
        'analysis/tests/test_ilvis0_remaining_prediction_study.py',
        'analysis/tests/test_ilvis0_remaining_prediction_layouts.py',PLAN])
    return sorted(set(earlier_sources(root))|set(extra))


def required_tests():
    return ('test_twenty_group_grid_has_eighty_finite_starts',
            'test_changed_task_is_rejected_before_established_fit',
            'test_changed_established_source_is_rejected',
            'test_historical_science_lock_accepts_only_audited_changes',
            'test_exact_twenty_unique_groups_and_cuts',
            'test_changed_receiver_cut_rejected',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure',
            'test_long_generated_both_cuts_meet_original_accuracy_screen[inner]',
            'test_long_generated_both_cuts_meet_original_accuracy_screen[outer]')


def verify_established_sources(root, sealed, source_names):
    from .studies.artifacts import digest,safe_path
    if any(sealed.get(name)!=digest(safe_path(root,name).read_bytes())
           for name in source_names):
        raise ValueError('unchanged sealed rolling-origin evaluator required')


def verify_historical_science(root,prior):
    """Bind the unchanged forecast equations while auditing later plumbing edits."""
    import ast
    from .ilvis0_rolling_origin_study import sources as established_sources
    from .studies.artifacts import digest,safe_path

    names=established_sources(root)
    sealed=prior.manifest['sources']
    if not set(names)<=set(sealed):
        raise ValueError('sealed rolling-origin source inventory differs')
    changed={name for name in names if sealed[name]!=digest(safe_path(root,name).read_bytes())}
    if changed!=AUDITED_CHANGED_SOURCES:
        raise ValueError('unaudited historical source change')
    verify_established_sources(root,sealed,
        [name for name in names if name not in AUDITED_CHANGED_SOURCES])
    segment_source='analysis/lll/ilvis0_segments.py'
    def extractor(raw):
        matches=[node for node in ast.parse(raw).body
                 if isinstance(node,ast.FunctionDef) and node.name=='extract_segment']
        if len(matches)!=1:
            raise ValueError('one historical segment extractor required')
        return ast.dump(matches[0],include_attributes=False)
    if extractor(prior.read('source-freeze/'+segment_source,raw=True))!=extractor(
            safe_path(root,segment_source).read_bytes()):
        raise ValueError('historical segment extraction changed')
    return sorted(changed)


def request_qualification(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    root=Path(root).resolve()
    return request(root,sources=sources(root),environment=runtime_environment(),
                   output=REQUEST,report=REPORT)


def prepare(root,*,qualification=None):
    if qualification is None:
        raise ValueError('source-bound qualification required before originals')
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_prediction import split as numerical_split
    from .ilvis0_rolling_origin import split_origins
    from .ilvis0_rolling_origin_study import recipe as established_recipe
    from .ilvis0_segments import extract_segment
    from .ilvis0_remaining_prediction_layouts import build as rebuild_layouts
    from .prediction_transfer_reference import from_saved_csv
    from .studies.artifacts import ArchiveStore,atomic,digest,encoded,safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root=Path(root).resolve()
    base=safe_path(root,'data/'+ID+'-inputs')
    if base.exists() or safe_path(root,'data/'+ID).exists():
        raise ValueError('fresh finite twenty-group identity required')
    request,report=checked(root,qualification,sources=sources(root),
        environment=runtime_environment(),required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    prior=ClosedStudy(root,'data/ilvis0-rolling-origin-development-v1')
    try:
        if (prior.completion['state'] not in ('complete','terminal') or
                prior.completion['manifest_sha256']!=
                'dc7fded1b06b068f112e9915114e60b19dbd1ddd2022e84f3b173f19e35b2373'
                or len(prior.tasks)!=48 or len(prior.rows)!=48):
            raise ValueError('unchanged sealed rolling-origin evaluator required')
        verify_historical_science(root,prior)
    finally:
        prior.close()
    saved=(root/LAYOUTS).read_bytes()
    layout_receipt=json.loads(saved)
    if (rebuild_layouts(root)!=layout_receipt or
            layout_receipt['original_reads']!=0 or
            layout_receipt['observed_starts']!=0):
        raise ValueError('saved outcome-blind twenty-group layouts differ')
    layouts=layout_receipt['layouts']
    selection_raw=(root/SELECTION).read_bytes()
    if digest(selection_raw)!=layout_receipt['selection_sha256']:
        raise ValueError('saved twenty-group selection differs')
    selection=list(csv.DictReader(io.StringIO(selection_raw.decode())))
    if [row['segment_id'] for row in selection]!=[row['segment_id'] for row in layouts]:
        raise ValueError('twenty-group selection order differs')
    reference=from_saved_csv((root/REFERENCE).read_bytes(),
        expected_sha256='651ae7c87d28d4d5e2d4b9493d3f5a990fc550adc1972c30d970e3bc32ac4117')
    population_name='data/ilvis0-highspeed-segments-v2-20261008/selection.json.gz'
    context_name='data/ilvis0-followup-20261007/summary.json'
    store=ArchiveStore(root)
    try:
        population_raw=store.read(population_name)
        context_raw=store.read(context_name)
    finally:
        store.close()
    if (layout_receipt['input_sha256'][population_name]!=digest(population_raw)
            or layout_receipt['input_sha256'][context_name]!=digest(context_raw)):
        raise ValueError('frozen selection input hashes differ')
    population=json.loads(gzip.decompress(population_raw))
    selected={row['segment']['segment_id']:row for row in population['selected']}
    contexts={row['task_id']:row for row in json.loads(context_raw)['results']}
    material=dict(recipe=encoded(established_recipe()),
                  **{'transfer-recipe':encoded(dict(version='remaining-twenty-v1',
                        groups=20,starts=2,cuts=['inner','outer'],model='sphere_rotating',
                        profile=False,clock='header_elapsed',workers=WORKERS,
                        threads=THREADS,maximum_wall_s=MAXIMUM_WALL_S)),
                     'transfer-reference':encoded(reference),
                     'qualification-request':request,
                     'qualification-report':report,
                     'selection-receipt':saved})
    task_layouts=[]
    for row,saved_layout in zip(selection,layouts,strict=True):
        segment=row['segment_id']
        source=selected[segment]
        context=contexts[source['task']]
        original=Path(source['source_path'])
        relative=original.relative_to(root)
        if relative.parts[:2]!=('data','ilvis0-ready'):
            raise ValueError('documented retained original required')
        values,times,gps,provenance=extract_segment(
            safe_path(root,relative.as_posix()),context,source['segment'])
        cut=saved_layout['training_epochs']
        split=numerical_split(times)
        if (provenance['source_sha256']!=row['source_sha256']
                or split['training_epochs']!=cut
                or split['prediction_epochs']!=saved_layout['prediction_epochs']):
            raise ValueError('decoded measurement differs from frozen receiver cut')
        layout=dict(saved_layout,native_packets=len(values),
                    first_interval_start_utc_s=provenance['first_interval_start_utc_s'])
        task_layouts.append(layout)
        separated=split_origins(
            dict(segment_id=segment,layout=layout,values=values.tolist(),
                 times=times.tolist(),training_gps=gps[:cut].tolist()),
            dict(segment_id=segment,prediction_gps=gps[cut:].tolist()))
        material[segment+'-common']=gzip.compress(encoded(separated['common']),mtime=0)
        for origin in ('inner','outer'):
            material[segment+'-'+origin+'-training']=encoded(separated[origin]['training'])
            material[segment+'-'+origin+'-scoring']=encoded(separated[origin]['scoring'])
        material[segment+'-provenance']=encoded(provenance)
    material['layouts']=encoded(task_layouts)
    base.mkdir(parents=True)
    inputs={}
    for index,(key,raw) in enumerate(material.items()):
        path=base/f'input-{index:03d}'
        atomic(path,raw)
        inputs[key]=path.relative_to(root).as_posix()
    definition=dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/ilvis0_remaining_prediction_study.py',
        sources=sources(root),inputs=inputs,tasks=tasks(task_layouts),
        workers=WORKERS,threads=THREADS,maximum_wall_s=MAXIMUM_WALL_S)
    atomic(base/'definition.json',encoded(definition))
    return Definition.from_dict(definition,root).prepare(root)


def evaluate(task,context):
    from .ilvis0_rolling_origin_study import evaluate as established_evaluate
    layouts=json.loads(context.input_path('layouts').read_bytes())
    declared={key:value for key,value in task.items() if key not in ('index','shard')}
    if (context.manifest.get('scope')!=SCOPE
            or declared!={row['identity']:row for row in tasks(layouts)}.get(task['identity'])):
        raise ValueError('unchanged twenty-group transfer task required')
    return established_evaluate(task,context)


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare','run'))
    parser.add_argument('--root',default='.')
    parser.add_argument('--qualification',default=None)
    args=parser.parse_args(argv)
    root=Path(args.root).resolve()
    if args.action=='request':
        value=request_qualification(root)
    elif args.action=='prepare':
        value=prepare(root,qualification=args.qualification)
    else:
        from .ilvis0_control_shards import launch
        value=launch(root/'data'/ID,reserved_threads=0)
    print(json.dumps(value,sort_keys=True,default=str))


if __name__=='__main__':main()
