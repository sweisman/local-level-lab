# SPDX-License-Identifier: AGPL-3.0-or-later
"""Six finite ESA fits changing only the earlier PPP coordinate source."""

import gzip
import json
from pathlib import Path

from .esa_alternate_training_material import PLAN as MATERIAL_PLAN
from .esa_rolling_origin_400_model_matrix import run_fit, sources as matrix_sources

ID='esa-alternate-training-refit-20261118'
SCOPE=('six ESA 187 development fits using two alternate GNSS-only PPP '
       'training coordinate sources on reports 0-399; forecast 400-519')
PLAN='docs/prediction-observed-development/ESA_ALTERNATE_TRAINING_REFIT_PLAN.md'
MATERIAL='docs/prediction-observed-development/esa-alternate-training-material.json.gz'
REQUEST=('docs/prediction-observed-development/qualification/'
         'esa-alternate-training-refit-request.json')
REPORT=('docs/prediction-observed-development/qualification/'
        'esa-alternate-training-refit-tests.xml')
MODELS=('sphere_rotating','sphere_still','flat_still')
SOURCES=('mosaic03','pwrpak7')
SOURCE_NAMES={'mosaic03':'187_mosaic03_ppp_5Hz_final.txt',
              'pwrpak7':'187_pwrpak7_ppp_1Hz_final.txt'}
INPUTS={'interval','forecast_times','recipe','saved-input-binding',
        'parent_identity','qualification_environment','qualification_request',
        'qualification_report','alternate-material-binding',
        'training_mosaic03','training_pwrpak7'}


def tasks():
    return [dict(identity=f'{source}-{model}',input_key='interval',
                 native_kind='tangent',
                 payload=dict(source=source,training_key='training_'+source,
                              model=model,profile=True,law='increment',start=0),
                 limits=dict(native_calls=700000,packet_visits=45000000000,
                             bound_calls=0,bound_steps=0))
            for source in SOURCES for model in MODELS]


def sources(root):
    from .studies.dependencies import source_closure
    paths=list(matrix_sources(root))
    paths.extend(['analysis/lll/esa_alternate_training_refit.py',
                  'analysis/lll/esa_alternate_training_material.py',
                  'analysis/tests/test_esa_alternate_training_refit.py',
                  PLAN,MATERIAL_PLAN])
    return source_closure(Path(root).resolve(),paths)


def required_tests():
    return ('test_six_refits_have_exact_finite_allowances',
            'test_refit_rejects_changed_task_before_running_fit',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    root=Path(root).resolve()
    return request(root,sources=sources(root),environment=environment(),
                   output=REQUEST,report=REPORT)


def prepare(root,*,qualification=None):
    if qualification is None:
        raise ValueError('source-bound qualification required before staging')
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .esa_alternate_ppp_scoring import PARENT
    from .esa_rolling_origin_400_model_matrix import ID as MATRIX_ID
    from .esa_full_parallel_gnss import _sha
    from .studies.artifacts import atomic,encoded,digest,safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition

    root=Path(root).resolve()
    base=safe_path(root,'data/'+ID+'-inputs')
    if base.exists() or safe_path(root,'data/'+ID).exists():
        raise ValueError('fresh finite refit identity required')
    env=environment()
    if env['numerical_environment']!=numerical_environment(workers=4,threads=1):
        raise ValueError('guarded four-worker allocation required')
    request,report=checked(root,qualification,sources=sources(root),
        environment=env,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    material_bytes=(root/MATERIAL).read_bytes()
    material=json.loads(gzip.decompress(material_bytes))
    if (material.get('version')!='esa-alternate-training-material-v1'
            or material.get('plan_sha256')!=_sha(root/MATERIAL_PLAN)
            or material.get('code_sha256')!=_sha(root/'analysis/lll/esa_alternate_training_material.py')
            or material.get('training_epochs')!=400
            or material.get('future_receiver_positions_read') is not False
            or material.get('changed_fields')!=['latitude_deg','longitude_deg','height_m']
            or material.get('protected_group_reads')!=0
            or len(material.get('sources',[]))!=2):
        raise ValueError('exact alternate training material required')
    parent=ClosedStudy(root,PARENT)
    matrix=ClosedStudy(root,'data/'+MATRIX_ID)
    try:
        if (material['parent_manifest_sha256']!=parent.completion['manifest_sha256']
                or material['matrix_manifest_sha256']!=matrix.completion['manifest_sha256']):
            raise ValueError('sealed parent or original matrix differs')
        staged={key:matrix.input(key,raw=True) for key in (
            'interval','forecast_times','recipe','saved-input-binding','parent_identity')}
        bindings={}
        for source in SOURCES:
            name=SOURCE_NAMES[source]
            item=next((row for row in material['sources']
                       if row['filename']==name),None)
            if (item is None or len(item['training_rows'])!=400
                    or item['training_rows_sha256']!=digest(encoded(item['training_rows']))):
                raise ValueError('complete bound alternate training rows required')
            raw=gzip.compress(encoded(item['training_rows']),mtime=0)
            key='training_'+source
            staged[key]=raw
            bindings[key]=dict(filename=name,source_sha256=item['source_sha256'],
                               training_rows_sha256=item['training_rows_sha256'],
                               staged_sha256=digest(raw))
        staged['alternate-material-binding']=encoded(dict(
            material_sha256=digest(material_bytes),sources=bindings))
        staged.update(qualification_environment=encoded(env),
                      qualification_request=request,qualification_report=report)
        if set(staged)!=INPUTS:
            raise ValueError('refit staged unexpected input or later positions')
        base.mkdir(parents=True)
        inputs={}
        for index,key in enumerate(sorted(staged)):
            path=base/f'input-{index:03d}'
            atomic(path,staged[key])
            inputs[key]=path.relative_to(root).as_posix()
        definition=dict(id=ID,scope=SCOPE,
            adapter='analysis/lll/esa_alternate_training_refit.py',
            sources=sources(root),inputs=inputs,tasks=tasks(),
            workers=4,threads=1,maximum_wall_s=7200.)
        atomic(base/'definition.json',encoded(definition))
        manifest=Definition.from_dict(definition,root).prepare(root)
        return dict(path='data/'+ID,total=len(tasks()),
                    allocation=manifest['allocation'],
                    later_receiver_positions_staged=False)
    finally:
        matrix.close();parent.close()


def evaluate(task,context):
    from .studies.artifacts import digest
    declared={key:value for key,value in task.items() if key not in ('index','shard')}
    if (context.manifest.get('scope')!=SCOPE or
            declared!={row['identity']:row for row in tasks()}.get(task['identity'])
            or set(context.manifest.get('inputs',{}))!=INPUTS):
        raise ValueError('unchanged finite alternate refit task required')
    binding=json.loads(context.input_path('alternate-material-binding').read_bytes())
    key=task['payload']['training_key']
    if (set(binding['sources'])!={'training_'+source for source in SOURCES}
            or digest(context.input_path(key).read_bytes())
                !=binding['sources'][key]['staged_sha256']
            or binding['sources'][key]['filename']!=SOURCE_NAMES[task['payload']['source']]):
        raise ValueError('bound alternate training rows differ')
    return run_fit(task,context)


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


if __name__=='__main__': main()
