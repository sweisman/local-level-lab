# SPDX-License-Identifier: AGPL-3.0-or-later
"""Versioned observed-method preparation after recovery-launcher repair.

The scientific task grid and evaluator are the frozen v1 definitions. This
version changes only study identity and the separately qualified recovery
source. No observed fit may start before the long generated gate passes.
"""

import csv
import io
import json
from pathlib import Path

from . import ilvis0_observed_method_pilot as base

ID='ilvis0-observed-method-pilot-v2-20261118'
PREFLIGHT_ID=ID+'-preflight'
PLAN='docs/prediction-group-transfer/OBSERVED_METHOD_PILOT_V2_PLAN.md'
REQUEST='docs/prediction-group-transfer/observed-method-v2b-qualification-request.json'
REPORT='docs/prediction-group-transfer/observed-method-v2b-qualification-tests.xml'
RECOVERY='docs/prediction-group-transfer/long-independent-recovery-repair-request.json'
SCOPE=base.SCOPE
PREFLIGHT_SCOPE=base.PREFLIGHT_SCOPE
tasks=base.tasks


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/ilvis0_observed_method_pilot_v2.py',
        'analysis/tests/test_ilvis0_observed_method_pilot_v2.py',
        PLAN,*base.sources(root)])


def required_tests():
    return (*base.required_tests(),
            'test_v2_reuses_preselected_recordings_and_scientific_tasks',
            'test_v2_requires_new_recovery_qualification_and_generated_gate')


def request_qualification(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    root=Path(root).resolve()
    return request(root,sources=sources(root),environment=runtime_environment(),
                   output=REQUEST,report=REPORT)


def prepare(root,*,preflight=False):
    import shutil
    from .ilvis0_control_shards import runtime_environment,verify_completion
    from .ilvis0_long_independent_solver_report import build as generated_report
    from .studies.artifacts import atomic,encoded,safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import qualification_sources,REQUIRED_TESTS
    root=Path(root).resolve();name=PREFLIGHT_ID if preflight else ID
    if generated_report(root)['passed'] is not True:
        raise ValueError('long independent generated gate did not pass')
    base_dir=safe_path(root,'data/'+name+'-inputs')
    if (base_dir.exists() or safe_path(root,'data/'+name).exists() or
            shutil.disk_usage(root).free<5*1024**3):
        raise ValueError('fresh observed study and five GiB free space required')
    if not preflight:
        prior=verify_completion(root/'data'/PREFLIGHT_ID)
        if (prior['state']!='complete' or prior['completed']!=1 or
                prior['passed'] is not True):
            raise ValueError('passing separate observed real-worker preflight required')
    env=runtime_environment()
    request,report=checked(root,REQUEST,sources=sources(root),
        environment=env,required_tests=required_tests(),
        minimum_tests=len(required_tests()))
    recovery,recovery_report=checked(root,RECOVERY,
        sources=qualification_sources(root),environment=env,
        required_tests=REQUIRED_TESTS,minimum_tests=len(REQUIRED_TESTS))
    selection_raw=(root/base.SELECTION).read_bytes()
    selected={row['segment_id']:row for row in
              csv.DictReader(io.StringIO(selection_raw.decode()))}
    if any(segment not in selected for segment in base.SEGMENTS):
        raise ValueError('preselected recording metadata changed')
    original=ClosedStudy(root,base.ORIGINAL)
    try:
        if (original.completion['state']!='terminal' or
                len(original.tasks)!=80 or len(original.rows)!=80 or
                original.manifest['limits']['maximum_identities']!=80):
            raise ValueError('exact sealed development input study required')
        layouts=[next(row for row in original.input('layouts')
                      if row['segment_id']==segment) for segment in base.SEGMENTS]
        recipe=original.input('recipe')
        if (recipe['model']!='sphere_rotating' or
                recipe['stopping']!='near_zero' or
                recipe['maximum_evaluations']!=200):
            raise ValueError('sealed original model or calibration differs')
        material=dict(recipe=encoded(recipe),layouts=encoded(layouts),
            selection=selection_raw,environment=encoded(env),
            original_completion=encoded(original.completion),
            qualification_request=request,qualification_report=report,
            recovery_request=recovery,recovery_report=recovery_report)
        for segment in base.SEGMENTS[:1 if preflight else 3]:
            for key in (segment+'-common',segment+'-provenance',
                        *(segment+'-'+origin+'-'+part
                          for origin in ('inner','outer')
                          for part in ('training','scoring'))):
                material[key]=original.input(key,raw=True)
    finally:original.close()
    base_dir.mkdir(parents=True)
    inputs={}
    for index,(key,raw) in enumerate(material.items()):
        path=base_dir/f'input-{index:03d}'
        atomic(path,raw)
        inputs[key]=path.relative_to(root).as_posix()
    definition=dict(id=name,scope=PREFLIGHT_SCOPE if preflight else SCOPE,
        adapter='analysis/lll/ilvis0_observed_method_pilot_v2.py',
        sources=sources(root),inputs=inputs,tasks=tasks(layouts,preflight=preflight),
        workers=1 if preflight else 4,threads=1,
        maximum_wall_s=900. if preflight else 21600.)
    atomic(base_dir/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+name,tasks=len(definition['tasks']),
                allocation=manifest['allocation'],limits=manifest['limits'])


def evaluate(task,context):
    return base.evaluate(task,context)


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare-preflight',
                                         'run-preflight','prepare','run'))
    args=parser.parse_args(argv);root=Path('.').resolve()
    if args.action=='request':result=request_qualification(root)
    elif args.action.startswith('prepare'):
        result=prepare(root,preflight=args.action=='prepare-preflight')
    else:
        from .ilvis0_control_shards import launch
        name=PREFLIGHT_ID if args.action=='run-preflight' else ID
        summary=launch(root/'data'/name,reserved_threads=0)
        result={key:summary[key] for key in
                ('state','completed','total','passed','charged')}
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
