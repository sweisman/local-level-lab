# SPDX-License-Identifier: AGPL-3.0-or-later
"""Four sealed gyro white/bias forecasts on two generated IMU draws."""

import argparse
import io
import json
from pathlib import Path

ID='esa-oracle-gyro-component-v1-20261115'
SCOPE=('four generated gyro white/bias forecasts; no observed or protected '
       'input, no refit and no Earth-model decision')
DIRECTORY='docs/prediction-observed-development/qualification/'
PLAN='docs/prediction-observed-development/ORACLE_GYRO_COMPONENT_DESIGN.md'
LAWS=('increment','point');COMPONENTS=('white','bias')
LIMITS=dict(native_calls=1,packet_visits=243_000_000,
            bound_calls=0,bound_steps=0)


def recipe():
    return dict(version='esa-oracle-gyro-component-v1',laws=list(LAWS),
        components=list(COMPONENTS),model='sphere_rotating',
        duration_s=900.,rate_hz=300,queries=900,training_epochs=600,
        workers=2,threads=1,maximum_wall_s=3600.,
        original_reads=0,protected_reads=0,refits=0,
        scientific_decision='abstain')


def tasks():
    return [dict(identity=law+'-'+component,input_key='recipe',
        native_kind='tangent',payload=dict(law=law,component=component,
        model='sphere_rotating'),limits=dict(LIMITS))
        for law in LAWS for component in COMPONENTS]


def mix_gyro_component(clean,white,bias,component):
    if component not in COMPONENTS:
        raise ValueError('declared gyro component required')
    return dict(theta=clean['theta']+(white if component=='white' else bias),
                dv=clean['dv'])


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/esa_oracle_gyro_component_study.py',
        'analysis/lll/esa_oracle_gyro_component_recovery.py',
        'analysis/lll/esa_oracle_noise_components.py',
        'analysis/lll/esa_oracle_control.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_wide_tangent.py',
        'analysis/lll/ilvis0_forecast.py',
        'analysis/tests/test_esa_oracle_gyro_component_study.py',
        'analysis/tests/test_esa_oracle_noise_components.py',
        'analysis/tests/test_esa_oracle_control.py',PLAN])


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    return request(Path(root).resolve(),sources=sources(root),
        environment=environment(),output=DIRECTORY+'oracle-gyro-component-request.json',
        report=DIRECTORY+'oracle-gyro-component-tests.xml')


def prepare(root,*,qualification=None,recovery_qualification=None):
    if qualification is None or recovery_qualification is None:
        raise ValueError('source and recovery qualification required before staging')
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic,digest,encoded,safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import (qualification_sources as recovery_sources,
                                      REQUIRED_TESTS as recovery_tests)
    from .esa_oracle_channel_study import ID as CHANNEL_ID
    from .esa_oracle_control import load_case
    from .esa_oracle_noise_components import reconstruct_components
    from .esa_fit_adjusted_control_study import SEEDS

    root=Path(root).resolve();staged=safe_path(root,'data/'+ID+'-inputs')
    if staged.exists() or safe_path(root,'data/'+ID).exists():
        raise ValueError('fresh finite gyro component identity required')
    env=environment()
    if env['numerical_environment']!=numerical_environment(workers=2,threads=1):
        raise ValueError('guarded two-thread allocation required')
    checked(root,qualification,sources=sources(root),environment=env,
        required_tests=(
            'test_clean_known_calibration_forecasts_short_generated_trajectory',
            'test_reconstructed_components_sum_to_generated_measurements[increment]',
            'test_reconstructed_components_sum_to_generated_measurements[point]',
            'test_gyro_component_tasks_have_fixed_four_forecast_allowances',
            'test_gyro_component_study_requires_qualification',
            'test_gyro_component_mixture_adds_only_selected_gyro_error',
            'test_gyro_component_recovery_binds_four_tasks',
            'test_gyro_component_worker_prepays_exact_forecast',
            'test_gyro_component_worker_preserves_failure_charge'),minimum_tests=12)
    checked(root,recovery_qualification,sources=recovery_sources(root),
        environment=runtime_environment(),required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    channel=ClosedStudy(root,'data/'+CHANNEL_ID)
    try:
        if (channel.completion['state']!='complete' or
                channel.summary['completed']!=4):
            raise ValueError('complete sealed channel source required')
        clean_raw=channel.input('clean-increments',raw=True)
        parent_binding=channel.input('parent-binding')
        with np.load(io.BytesIO(clean_raw),allow_pickle=False) as raw:
            if set(raw.files)!={'theta','dv','dt','times'}:
                raise ValueError('complete clean source arrays required')
            clean={key:np.array(raw[key],dtype=float,copy=True)
                   for key in raw.files}
        channel_sha=channel.completion['manifest_sha256']
    finally:channel.close()
    arrays={key:clean[key] for key in ('theta','dv','dt','times')}
    component_hashes={};parent_inputs={}
    for law in LAWS:
        measured=load_case(root,law)
        if (measured['parent_manifest_sha256']!=parent_binding[
                'parent_manifest_sha256'] or
                measured['parent_input_sha256']!=parent_binding[
                    'noisy_input_sha256'][law] or
                not np.array_equal(clean['dt'],measured['dt']) or
                not np.array_equal(clean['times'],measured['times'])):
            raise ValueError('matched sealed noisy stream required')
        regenerated=reconstruct_components(clean,law,seed=SEEDS[law])
        if (not np.array_equal(regenerated['theta'],measured['theta']) or
                not np.array_equal(regenerated['dv'],measured['dv'])):
            raise ValueError('gyro components do not reproduce original input')
        parent_inputs[law]=measured['parent_input_sha256']
        component_hashes[law]={}
        for component in COMPONENTS:
            value=np.asarray(regenerated['noise']['gyro'][
                component+'_increments'],dtype=float)
            arrays[law+'-'+component]=value
            component_hashes[law][component]=digest(value.astype('<f8').tobytes())
    buffer=io.BytesIO();np.savez_compressed(buffer,**arrays)
    binding=dict(channel_manifest_sha256=channel_sha,
        clean_input_sha256=digest(clean_raw),parent_binding=parent_binding,
        parent_input_sha256=parent_inputs,
        gyro_component_sha256=component_hashes)
    staged.mkdir(parents=True)
    inputs={}
    for name,raw in (('recipe.json',encoded(recipe())),
                     ('binding.json',encoded(binding)),
                     ('numerical-environment.json',encoded(env)),
                     ('component-increments.npz',buffer.getvalue())):
        path=staged/name;atomic(path,raw)
        inputs[name.rsplit('.',1)[0]]=path.relative_to(root).as_posix()
    definition=dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/esa_oracle_gyro_component_study.py',
        sources=sources(root),inputs=inputs,tasks=tasks(),
        workers=2,threads=1,maximum_wall_s=3600.)
    atomic(staged/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,total=4,allocation=manifest['allocation'])


def evaluate(task,context):
    declared={key:value for key,value in task.items()
              if key not in ('index','shard')}
    if (context.manifest.get('scope')!=SCOPE or declared!=
            {row['identity']:row for row in tasks()}.get(task['identity'])):
        raise ValueError('unchanged gyro-component task required')
    from .airquantumgrav_inventory import environment
    if (json.loads(context.input_path('recipe').read_bytes())!=recipe() or
            json.loads(context.input_path(
                'numerical-environment').read_bytes())!=environment()):
        raise ValueError('unchanged gyro-component recipe or environment required')
    return run_case(task,context)


def run_case(task,context):
    if task['limits']!=LIMITS:
        raise ValueError('finite gyro-component allowance changed')
    budget=None
    try:
        with context.prepay_native(native_calls=1,
                                   packet_visits=243_000_000) as budget:
            result=execute_component(task,context,budget.reserve)
        if (budget.snapshot()['attempted']!=
                dict(native_calls=1,packet_visits=243_000_000) or
                result['scientific_decision']!='abstain'):
            raise ValueError('gyro-component charged work differs')
        return result
    finally:
        if budget is not None:context.save('native-prepayment.json',budget.snapshot())


def execute_component(task,context,reserve):
    import numpy as np
    from .esa_oracle_control import load_case,oracle_problem
    from .airquantumgrav_observation_truth import receiver_samples
    from .esa_fit_adjusted_forecast_report import position_errors_neu,_metrics
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_forecast import native_forecast
    from .ilvis0_wide_tangent import load
    from .studies.artifacts import digest

    _check_continue(context.root,context.manifest)
    law=task['payload']['law'];component=task['payload']['component']
    binding=json.loads(context.input_path('binding').read_bytes())
    case=load_case(context.root.parent.parent,law)
    if case['parent_input_sha256']!=binding['parent_input_sha256'][law]:
        raise ValueError('original noisy draw changed')
    with np.load(context.input_path('component-increments'),
                 allow_pickle=False) as raw:
        if set(raw.files)!=set(('theta','dv','dt','times',
                'increment-white','increment-bias','point-white','point-bias')):
            raise ValueError('complete frozen gyro components required')
        clean={key:np.array(raw[key],dtype=float,copy=True)
               for key in ('theta','dv','dt','times')}
        white=np.array(raw[law+'-white'],dtype=float,copy=True)
        bias=np.array(raw[law+'-bias'],dtype=float,copy=True)
    if (not np.array_equal(clean['dt'],case['dt']) or
            not np.array_equal(clean['times'],case['times']) or
            digest(white.astype('<f8').tobytes())!=binding[
                'gyro_component_sha256'][law]['white'] or
            digest(bias.astype('<f8').tobytes())!=binding[
                'gyro_component_sha256'][law]['bias'] or
            not np.array_equal(clean['theta']+white+bias,case['theta'])):
        raise ValueError('frozen gyro component binding differs')
    mixed=mix_gyro_component(clean,white,bias,component)
    source='analysis/lll/ilvis0_tangent.cpp'
    kernel,compilation=load(context.directory/'kernel',
        expected_source_sha256=context.manifest['sources'][source],
        gravity_anchor_height_m=float(case['earlier_coordinates'][0,2]))
    context.save('compilation.json',compilation)
    problem,point=oracle_problem(mixed['theta'],mixed['dv'],case['dt'],
        case['times'],case['earlier_coordinates'],case['known_state'],
        case['limits'],kernel,rate_hz=300)
    forecast=native_forecast(problem,point,'sphere_rotating',
        theta=mixed['theta'],dv=mixed['dv'],dt=case['dt'],times=case['times'],
        maximum_interval_s=1.5/300,reserve=reserve)
    _check_continue(context.root,context.manifest)
    truth=receiver_samples('sphere_rotating',case['times'][600:],
        latitude_deg=55.,pattern='fast',removal=0.,sign=1,
        height_profile='climb',gravity_model='inverse_square_height')
    score=_metrics(position_errors_neu(
        forecast['coordinates'][600:],truth['coordinates']))
    context.save('component-forecast.json',dict(
        coordinates=forecast['coordinates'].tolist(),
        times_s=case['times'].tolist(),future_metrics=score,
        law=law,gyro_component=component,
        future_receiver_positions_used_to_forecast=False,
        later_truth_used_for_scoring_only=True,
        original_reads=0,protected_reads=0))
    return dict(passed=True,scientific_decision='abstain',law=law,
        gyro_component=component,future_metrics=score,native_calls=1,
        original_reads=0,protected_reads=0)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv);root=Path(args.root).resolve()
    if args.action=='request':result=request_qualification(root)
    else:
        from .esa_oracle_gyro_component_recovery import SPEC
        result=prepare(root,qualification=DIRECTORY+'oracle-gyro-component-request.json',
            recovery_qualification=SPEC.request)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
