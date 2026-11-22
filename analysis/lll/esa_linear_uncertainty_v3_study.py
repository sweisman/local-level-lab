# SPDX-License-Identifier: AGPL-3.0-or-later
"""Base-bounds corrected local ESA calibration-uncertainty check."""
from pathlib import Path

from . import esa_linear_uncertainty_v2_study as previous


ID='esa-linear-uncertainty-development-v3-20261115'
PARENT='data/'+previous.ID
REQUEST='docs/prediction-observed-development/qualification/linear-uncertainty-v3-request.json'
REPORT='docs/prediction-observed-development/qualification/linear-uncertainty-v3-tests.xml'


def tasks():return previous.tasks()


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),previous.sources(root)+[
        'analysis/lll/esa_linear_uncertainty_v3_study.py',
        'docs/prediction-observed-development/LINEAR_UNCERTAINTY_V3_PLAN.md'])


def required_tests():
    return previous.required_tests()+(
        'test_forecast_problem_uses_base_bounds_accepted_by_native_constructor',)


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import require_guarded_environment
    from .studies.qualification import request
    root=Path(root).resolve()
    return request(root,sources=sources(root),
        environment=require_guarded_environment(environment()),
        output=REQUEST,report=REPORT)


def prepare(root,*,qualification=None):
    if qualification is None:raise ValueError('new source-bound qualification required')
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import require_guarded_environment
    from .studies.artifacts import atomic,encoded,safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    root=Path(root).resolve();base=safe_path(root,'data/'+ID+'-inputs')
    if base.exists() or safe_path(root,'data/'+ID).exists():
        raise ValueError('fresh corrected bounds identity required')
    env=require_guarded_environment(environment())
    request,report=checked(root,qualification,sources=sources(root),
        environment=env,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    parent=ClosedStudy(root,PARENT)
    try:
        envelope=parent.envelope('single-pass-receiver-conditional')
        if (parent.completion['state']!='terminal' or
                parent.completion['manifest_sha256']!=
                    '72cb5cdd962eb0c4e01549aa9610ab03943041933867a6d7b45b37aad6888160' or
                envelope['result'].get('reason')!='explicit nuisance bounds required' or
                envelope['charged']['native_calls']!=450_000 or
                set(parent.manifest['inputs'])!=set(previous.INPUT_KEYS)):
            raise ValueError('exact preserved bounds-interface failure required')
        staged={key:parent.input(key,raw=True) for key in previous.INPUT_KEYS[:11]}
        staged.update({'qualification-environment':encoded(env),
                       'qualification-request':request,'qualification-report':report})
    finally:parent.close()
    if set(staged)!=set(previous.INPUT_KEYS):
        raise ValueError('exact early-only input set required')
    base.mkdir(parents=True);inputs={}
    for number,key in enumerate(previous.INPUT_KEYS):
        path=base/f'input-{number:03d}';atomic(path,staged[key])
        inputs[key]=path.relative_to(root).as_posix()
    definition=dict(id=ID,scope=previous.SCOPE,
        adapter='analysis/lll/esa_linear_uncertainty_v3_study.py',
        sources=sources(root),inputs=inputs,tasks=tasks(),workers=1,threads=1,
        maximum_wall_s=3600.)
    atomic(base/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,total=1,allocation=manifest['allocation'])


def evaluate(task,context):
    return previous.evaluate(task,context)


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare','run'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv);root=Path(args.root).resolve()
    if args.action=='request':result=request_qualification(root)
    elif args.action=='prepare':result=prepare(root,qualification=REQUEST)
    else:
        from .ilvis0_control_shards import launch
        result=launch(root/'data'/ID,reserved_threads=0)
    print(result);return result


if __name__=='__main__':main()
