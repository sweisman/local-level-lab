# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only assembly of original and recovered validation evidence."""

from pathlib import Path

from .artifacts import ArchiveStore,encoded,digest,atomic,safe_path
from .closed import ClosedStudy
from .validation_continuation import next_stage_tasks
from .validation_resume import (_frozen,_stage_paths,_stage_manifest_matches,
                                _smoke_selection,_stop_reason,VERSION)
from lll import ilvis0_control_shards as runner


def final_sources(identities,source_rows):
    """Choose one sealed complete outcome per original fit identity."""
    expected=set(identities)
    if len(expected)!=len(identities):raise ValueError('duplicate planned identity')
    found={}
    for index,rows in enumerate(source_rows):
        for row in rows:
            identity=row['identity']
            if identity not in expected:raise ValueError('unplanned outcome')
            if row['status']=='interrupted':continue
            if row['status']!='complete':raise ValueError('invalid outcome status')
            if identity in found:raise ValueError('duplicate complete outcome')
            found[identity]=index
    if set(found)!=expected:raise ValueError('missing final outcome')
    return found


def release_native_bindings(policy, views):
    """Use the qualified release's compiled-source identity for every source."""
    provider = getattr(policy, 'native_bindings', None)
    if not callable(provider):
        raise ValueError('qualified release native binding required')
    return [provider(view) for view in views]


class _VerifiedOpenStudy(ClosedStudy):
    """Read sealed parent results without inventing a parent completion receipt."""
    def __init__(self,root,prefix,manifest,merged,store):
        self.root=Path(root).resolve();self.prefix=prefix.rstrip('/')
        self.store=store;self.owns_store=False;self.catalog=store.catalog()
        self.cache={};self.envelopes={}
        self.manifest=manifest;self.summary=merged
        self.completion=dict(manifest_sha256=runner._sha(self.root/self.prefix/'manifest.json'))
        self.tasks={task['identity']:task for task in manifest['tasks']}
        self.rows={row['identity']:row for row in merged['results']}


def _verified_views(project,output):
    """Bind each final task to its original or separately closed stage evidence."""
    plan,policy,parent_manifest=_frozen(project,output)
    parent=project/policy['parent'];parent_merged=runner.merge(parent)
    stages=[];paths=_stage_paths(output)
    smoke=[task['identity'] for task in plan['tasks'][:policy.get('smoke_task_count',0)]]
    for path in paths:
        manifest=runner.verify(path);_stage_manifest_matches(manifest,parent_manifest,policy)
        pending=next_stage_tasks(plan,stages,max_attempts_per_task=policy['max_attempts_per_task'],
                                 max_technical_interruptions=policy['max_technical_interruptions'])['tasks']
        assigned,gate=_smoke_selection(pending,stages,smoke)
        actual=[{key:value for key,value in task.items() if key not in ('index','shard')}
                for task in manifest['tasks']]
        if gate or actual!=assigned:raise ValueError('stage changes frozen pending task selection')
        summary=runner.verify_completion(path)
        if _stop_reason(path):raise ValueError('scientific stop request blocks combined validation')
        stages.append(dict(manifest=manifest,merged=summary))
    remaining=next_stage_tasks(plan,stages,max_attempts_per_task=policy['max_attempts_per_task'],
                               max_technical_interruptions=policy['max_technical_interruptions'])
    if remaining['tasks']:raise ValueError('continuation is incomplete')
    completion=runner._load(output/'completion.json')
    expected=dict(version=VERSION,scientific_decision='abstain',
        validation_coverage_qualified=False,state='all_tasks_finished',
        original_completed=plan['completed'],continuation_completed=remaining['completed'],
        completed_failures=plan['completed_failures']+remaining['completed_failures'],
        technical_interruptions=remaining['technical_interruptions'],stages=len(paths),
        parent_manifest_sha256=plan['parent_manifest_sha256'],
        parent_merged_sha256=plan['parent_merged_sha256'],
        policy_sha256=runner._sha(output/'policy.json'),
        stage_completion_sha256=[runner._sha(path/'completion.json') for path in paths])
    if encoded(completion)!=encoded(expected):
        raise ValueError('combined completion receipt differs from sealed evidence')
    identities=[task['identity'] for task in parent_manifest['tasks']]
    selected=final_sources(identities,[parent_merged['results'],
                                       *[stage['merged']['results'] for stage in stages]])
    store=ArchiveStore(project)
    try:
        views=[_VerifiedOpenStudy(project,policy['parent'],parent_manifest,parent_merged,store)]
        views.extend(ClosedStudy(project,path.relative_to(project).as_posix(),store=store) for path in paths)
        return views,selected,store,plan,policy,parent_manifest
    except BaseException:
        store.close();raise


def inspect(project='.',output='data/prediction-validation-continuation-v2-20261109'):
    """Recheck every sealed forecast, then apply the original fixed calibration."""
    from lll.host_prediction_release import release
    from lll.prediction_calibration_study import _protocol
    from lll.prediction_calibration_report import check_handoff,method_verification
    from lll.prediction_calibration import aggregate_draws,validate
    from lll.independent_noisy_study import SCORE_INPUTS,score_records
    from lll.structured_noisy_publication import inspect_case
    from lll.airquantumgrav_inventory import environment
    project=Path(project).resolve();output=(project/output).resolve()
    views,selected,store,plan,policy,manifest=_verified_views(project,output)
    try:
        scientific=_protocol(release.policy());base=views[0]
        recipe=base.input('recipe');population=base.input('population');sha=population['sha256']
        if (recipe!=scientific.recipe('validation') or base.input('qualification-environment')!=environment()
                or manifest['scope']!=scientific.SCOPE
                or manifest['sources']!=population['descriptor']['sources']
                or population!=scientific.population(manifest['sources'],environment())
                or base.input('validation-policy')!=scientific.recipe('validation')):
            raise ValueError('original validation population or policy changed')
        expected={task['identity']:task for task in scientific.tasks('validation',sha)}
        if {identity:{key:value for key,value in task.items() if key not in ('index','shard')}
            for identity,task in base.tasks.items()}!=expected:
            raise ValueError('original full validation task matrix changed')
        handoff=base.input('calibration-handoff')
        check_handoff(handoff,population_sha256=sha,protocol=release.policy())
        bindings=release_native_bindings(scientific,views);rows=[]
        for identity,task in base.tasks.items():
            source=views[selected[identity]];spec=task['payload']['case'];seed=task['payload']['draw_seed']
            envelope=source.envelope(identity);outcome=envelope['result'];prefix='artifacts/'+identity+'/'
            row=dict(identity=identity,draw_seed=seed,role='validation',**spec,
                     complete=False,converged=False,accurate=False)
            draw=dict(seed=seed,role='validation',case=spec,population_sha256=sha,
                      calibration_draw=False,validation_draw=True,confidence_calibrated=False)
            checked=inspect_case(source,identity,payload=spec,r=scientific.case_recipe(seed),
                                 bindings=bindings[selected[identity]])
            marker=(source.artifact(identity,'family-outcome.json')
                    if prefix+'family-outcome.json' in envelope['artifacts'] else None)
            if checked is None:
                if marker is not None and marker['complete']:
                    raise ValueError('unfinished outcome carries a completed marker')
                rows.append(dict(row,reason=outcome.get('reason','Incomplete forecast')))
            else:
                records={name:source.artifact(identity,name) for name in SCORE_INPUTS}
                score=score_records(records,seed=seed);fit=records['fit.json']
                expected_marker=dict(manifest_sha256=source.completion['manifest_sha256'],
                    identity=identity,seed=seed,role='validation',population_sha256=sha,case=spec,
                    complete=True,converged=checked['converged'],
                    training_cost=fit['residual_sum_squares'],
                    maximum_score=score['maximum_standardized_error'])
                if (source.artifact(identity,'draw-identity.json')!=draw
                        or encoded(source.artifact(identity,'prediction-score.json'))!=encoded(score)
                        or marker!=expected_marker or outcome['draw_seed']!=seed
                        or outcome['role']!='validation' or outcome['population_sha256']!=sha
                        or outcome['maximum_standardized_error']!=score['maximum_standardized_error']
                        or outcome['confidence_calibrated']):
                    raise ValueError('saved validation score or selection marker changed')
                proof=method_verification(scientific,source,identity,spec,checked)
                rows.append(dict(row,complete=True,**checked,**proof,
                                 training_cost=fit['residual_sum_squares'],
                                 maximum_standardized_error=score['maximum_standardized_error']))
            artifact=source.rows[identity]['artifact'];case_prefix=source.prefix+'/'+prefix
            for name in tuple(source.cache):
                if name.startswith(case_prefix) or name==source.prefix+'/'+artifact:del source.cache[name]
            source.envelopes.pop(identity,None)
        draws=aggregate_draws(rows,base.tasks,role='validation',population_sha256=sha,
                              excluded_seeds=scientific.EXCLUDED_SEEDS)
        validation=validate(handoff['calibration'],draws,confidence=recipe['confidence'],
                            coverage=recipe['coverage'],population_sha256=sha)
        return dict(version='prediction-validation-combined-v1',verified=True,
            original_cohort_interrupted=True,prior_technical_release_failed=True,
            population_sha256=sha,total=len(rows),original_completed=plan['completed'],
            continuation_completed=len(rows)-plan['completed'],
            complete_forecasts=sum(row['complete'] for row in rows),
            numerically_converged=sum(row['converged'] for row in rows),
            raw_accuracy=sum(row['accurate'] for row in rows),
            returned_seed_families=len(draws),rows=rows,draws=draws,validation=validation,
            parent_manifest_sha256=plan['parent_manifest_sha256'],
            continuation_policy_sha256=runner._sha(output/'policy.json'),
            stage_completion_sha256=[runner._sha(output/f'stage-{index:03d}'/'completion.json')
                                     for index in range(len(views)-1)],
            scientific_decision='abstain',aircraft_coverage_established=False,
            native_calls_during_audit=0,optimizer_starts=0)
    finally:
        for view in views:view.close()
        store.close()


def render(report):
    """Plain-language status with the original and successor kept separate."""
    if (report.get('verified') is not True or report['total']!=
            report['original_completed']+report['continuation_completed']):
        raise ValueError('verified complete-source report required')
    result=report['validation'];verdict=('passed' if result['passed'] else 'did not pass')
    return ('# Recovered prediction validation\n\n'
        f"The original validation was interrupted after {report['original_completed']:,} completed fits. "
        f"A separate continuation completed the other {report['continuation_completed']:,}. "
        'The original run remains interrupted.\n\n'
        f"All {report['total']:,} prescribed fits have saved outcomes; "
        f"{report['numerically_converged']:,} passed numerical checks and "
        f"{report['complete_forecasts']:,} produced complete forecasts.\n\n"
        f"Across {result['draws']} preselected simulated cases, {result['failures']} exceeded "
        f"the fixed calibration limit or were unavailable. The one-sided failure upper bound "
        f"is {result['failure_upper']:.6g}. The combined validation {verdict} its declared "
        'coverage rule.\n\n'
        'This is a generated-data validation of the analysis procedure. It does not establish '
        'aircraft error coverage or Earth-model significance.\n')


def publish(project='.',output='data/prediction-validation-continuation-v2-20261109',
            public='docs/prediction-validation-continuation'):
    """Write a fresh, hash-receipted result from saved outcomes only."""
    import os
    import shutil
    import tempfile
    from lll.prediction_calibration_report import result_csv
    project=Path(project).resolve();public=(project/public).resolve()
    if public.parent!=project/'docs' or public.exists():
        raise ValueError('fresh top-level docs publication required')
    report=inspect(project,output)
    artifacts={'README.md':render(report).encode(),
               'results.csv':result_csv(report).encode(),
               'verified-report.json':encoded(report),
               'report-source.py':Path(__file__).read_bytes(),
               'runtime-source.py':Path(__file__).with_name('validation_resume.py').read_bytes()}
    receipt=dict(version='prediction-validation-combined-publication-v1',
                 source=Path(output).as_posix(),
                 artifacts={name:digest(data) for name,data in sorted(artifacts.items())},
                 numerical_environment=runner.runtime_environment(),
                 native_calls_during_publication=0,optimizer_starts=0)
    public.parent.mkdir(parents=True,exist_ok=True)
    temporary=Path(tempfile.mkdtemp(prefix='.'+public.name+'-preparing-',dir=public.parent))
    try:
        for name,data in artifacts.items():atomic(temporary/name,data)
        atomic(temporary/'evidence-receipt.json',encoded(receipt))
        if public.exists():raise ValueError('fresh top-level docs publication required')
        os.rename(temporary,public)
        fd=os.open(public.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        if temporary.exists():shutil.rmtree(temporary)
    return receipt


def verify_publication(project,public,*,replay=False):
    """Check published hashes; optionally rerun every saved-data calculation."""
    project=Path(project).resolve();public=(project/public).resolve()
    if public.parent!=project/'docs':raise ValueError('top-level docs publication required')
    receipt=runner._load(public/'evidence-receipt.json')
    names=receipt.get('artifacts',{})
    if (receipt.get('version')!='prediction-validation-combined-publication-v1'
            or set(names)!={'README.md','results.csv','verified-report.json',
                              'report-source.py','runtime-source.py'}
            or type(receipt.get('numerical_environment')) is not dict
            or receipt.get('native_calls_during_publication')!=0
            or receipt.get('optimizer_starts')!=0
            or {path.name for path in public.iterdir()}!=set(names)|{'evidence-receipt.json'}):
        raise ValueError('publication receipt or artifact set changed')
    for name,sha in names.items():
        if digest(safe_path(public,name).read_bytes())!=sha:
            raise ValueError('publication artifact hash changed: '+name)
    if replay:
        if (safe_path(public,'report-source.py').read_bytes()!=Path(__file__).read_bytes()
                or safe_path(public,'runtime-source.py').read_bytes()!=
                    Path(__file__).with_name('validation_resume.py').read_bytes()
                or receipt['numerical_environment']!=runner.runtime_environment()):
            raise ValueError('report replay source or numerical environment differs')
        report=inspect(project,receipt['source'])
        if encoded(report)!=safe_path(public,'verified-report.json').read_bytes():
            raise ValueError('publication replay differs from sealed evidence')
    return dict(verified=True,replayed=replay,artifacts=len(names))


def main(argv=None):
    import argparse
    import json
    parser=argparse.ArgumentParser(description='Replay and publish combined sealed validation evidence')
    parser.add_argument('--project',default='.')
    parser.add_argument('--campaign',default='data/prediction-validation-continuation-v2-20261109')
    parser.add_argument('--public',default='docs/prediction-validation-continuation')
    parser.add_argument('--verify',action='store_true',help='replay and verify an existing publication')
    args=parser.parse_args(argv)
    if args.verify:
        print(json.dumps(verify_publication(args.project,args.public,replay=True),sort_keys=True))
        return 0
    result=publish(args.project,args.campaign,args.public)
    print(json.dumps(dict(public=args.public,artifacts=result['artifacts']),sort_keys=True))
    return 0


if __name__=='__main__':raise SystemExit(main())
