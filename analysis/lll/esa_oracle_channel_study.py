# SPDX-License-Identifier: AGPL-3.0-or-later
"""Four finite channel-isolation forecasts using sealed generated noise draws."""

import argparse
import hashlib
import io
import json
from pathlib import Path

ID='esa-oracle-channel-control-v1-20261115'
SCOPE=('four matched generated IMU channel forecasts; no observed or '
       'protected inputs, no refit and no Earth-model decision')
DIRECTORY='docs/prediction-observed-development/qualification/'
PLAN='docs/prediction-observed-development/ORACLE_CHANNEL_DESIGN.md'
LIMITS=dict(native_calls=1,packet_visits=243_000_000,
            bound_calls=0,bound_steps=0)
CONSTRUCTION=dict(generated_samples=270_601,constructed_intervals=270_000)
LAWS=('increment','point')
CHANNELS=('gyro','accel')


def recipe():
    return dict(version='esa-oracle-channel-v1',laws=list(LAWS),
        channels=list(CHANNELS),model='sphere_rotating',
        duration_s=900.,rate_hz=300,queries=900,training_epochs=600,
        workers=2,threads=1,maximum_wall_s=3600.,
        original_reads=0,protected_reads=0,refits=0,
        scientific_decision='abstain')


def tasks():
    return [dict(identity=law+'-'+channel,input_key='recipe',
        native_kind='tangent',payload=dict(law=law,channel=channel,
        model='sphere_rotating'),limits=dict(LIMITS))
        for law in LAWS for channel in CHANNELS]


def mix_channels(clean,noisy,channel):
    if channel not in CHANNELS:
        raise ValueError('declared single noisy IMU channel required')
    return dict(theta=noisy['theta'] if channel=='gyro' else clean['theta'],
                dv=noisy['dv'] if channel=='accel' else clean['dv'])


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/esa_oracle_channel_study.py',
        'analysis/lll/esa_oracle_channel_recovery.py',
        'analysis/lll/esa_oracle_control.py',
        'analysis/lll/airquantumgrav_training_controls.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_wide_tangent.py',
        'analysis/lll/ilvis0_forecast.py',
        'analysis/tests/test_esa_oracle_channel_study.py',PLAN])


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    return request(Path(root).resolve(),sources=sources(root),
        environment=environment(),output=DIRECTORY+'oracle-channel-request.json',
        report=DIRECTORY+'oracle-channel-tests.xml')


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
    from .airquantumgrav_training_controls import generated_training
    from .esa_fit_adjusted_control_study import recipe as parent_recipe
    from .esa_fit_adjusted_control_report import _study
    from .esa_oracle_control import load_case
    from .esa_oracle_clean_study import ID as CLEAN_ID

    root=Path(root).resolve();staged=safe_path(root,'data/'+ID+'-inputs')
    if staged.exists() or safe_path(root,'data/'+ID).exists():
        raise ValueError('fresh finite channel identity required')
    env=environment()
    if env['numerical_environment']!=numerical_environment(workers=2,threads=1):
        raise ValueError('guarded two-thread allocation required')
    checked(root,qualification,sources=sources(root),environment=env,
        required_tests=(
            'test_clean_known_calibration_forecasts_short_generated_trajectory',
            'test_channel_tasks_are_four_matched_finite_forecasts',
            'test_channel_study_requires_qualification',
            'test_channel_study_rejects_changed_task_before_input_read',
            'test_channel_recovery_binds_four_tasks',
            'test_channel_mixture_changes_only_the_declared_sensor_stream',
            'test_channel_worker_prepays_exact_forecast',
            'test_channel_worker_keeps_charged_failure'),minimum_tests=8)
    checked(root,recovery_qualification,sources=recovery_sources(root),
        environment=runtime_environment(),required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    parent,lineage=_study(root)
    try:
        name='analysis/lll/airquantumgrav_training_controls.py'
        if parent.manifest['sources'].get(name)!=hashlib.sha256(
                (root/name).read_bytes()).hexdigest():
            raise ValueError('clean generator differs from noisy parent')
        parent_sha=parent.completion['manifest_sha256']
    finally:parent.close()
    bindings={}
    for law in LAWS:
        case=load_case(root,law)
        if (case['parent_manifest_sha256']!=parent_sha or
                case['lineage_sha256']!=lineage):
            raise ValueError('matched frozen noisy parent required')
        bindings[law]=case['parent_input_sha256']
    clean_study=ClosedStudy(root,'data/'+CLEAN_ID)
    try:
        if (clean_study.completion['state']!='complete' or
                clean_study.summary['completed']!=1 or
                clean_study.envelope('clean')['result']['passed'] is not True):
            raise ValueError('complete clean source required')
        expected=clean_study.artifact('clean','clean-forecast.json')[
            'imu_array_sha256']
        clean_sha=clean_study.completion['manifest_sha256']
    finally:clean_study.close()
    counts={}
    def reserve(**work):
        for key,value in work.items():
            counts[key]=counts.get(key,0)+value
            if counts[key]>CONSTRUCTION[key]:
                raise ValueError('clean staging allowance exceeded')
    clean=generated_training(dict(model='sphere_rotating',latitude_deg=55.,
        profile=False,start=0),parent_recipe(),reserve=reserve,
        height_profile='climb',gravity_model='inverse_square_height')
    if (counts!=CONSTRUCTION or any(digest(np.asarray(clean[key],
            dtype='<f8').tobytes())!=expected[key]
            for key in ('theta','dv','dt'))):
        raise ValueError('clean staged input differs from sealed clean control')
    buffer=io.BytesIO()
    np.savez_compressed(buffer,**{key:clean[key] for key in
        ('theta','dv','dt','times')})
    staged.mkdir(parents=True)
    inputs={}
    records=(('recipe.json',encoded(recipe())),
        ('parent-binding.json',encoded(dict(
            parent_manifest_sha256=parent_sha,lineage_sha256=lineage,
            noisy_input_sha256=bindings,clean_manifest_sha256=clean_sha,
            clean_array_sha256=expected,staging_work=counts))),
        ('numerical-environment.json',encoded(env)),
        ('clean-increments.npz',buffer.getvalue()))
    for name,raw in records:
        path=staged/name;atomic(path,raw)
        inputs[name.rsplit('.',1)[0]]=path.relative_to(root).as_posix()
    definition=dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/esa_oracle_channel_study.py',sources=sources(root),
        inputs=inputs,tasks=tasks(),workers=2,threads=1,maximum_wall_s=3600.)
    atomic(staged/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,total=4,allocation=manifest['allocation'])


def evaluate(task,context):
    declared={key:value for key,value in task.items()
              if key not in ('index','shard')}
    if (context.manifest.get('scope')!=SCOPE or declared!=
            {row['identity']:row for row in tasks()}.get(task['identity'])):
        raise ValueError('unchanged channel task required')
    from .airquantumgrav_inventory import environment
    if (json.loads(context.input_path('recipe').read_bytes())!=recipe() or
            json.loads(context.input_path(
                'numerical-environment').read_bytes())!=environment()):
        raise ValueError('unchanged channel recipe or environment required')
    return run_case(task,context)


def run_case(task,context):
    if task['limits']!=LIMITS:
        raise ValueError('finite channel native allowance changed')
    budget=None
    try:
        with context.prepay_native(native_calls=1,
                                   packet_visits=243_000_000) as budget:
            result=execute_channel(task,context,budget.reserve)
        if (budget.snapshot()['attempted']!=
                dict(native_calls=1,packet_visits=243_000_000) or
                result['scientific_decision']!='abstain'):
            raise ValueError('channel forecast charged work differs')
        return result
    finally:
        if budget is not None:context.save('native-prepayment.json',budget.snapshot())


def execute_channel(task,context,reserve):
    import numpy as np
    from .esa_oracle_control import load_case,oracle_problem
    from .airquantumgrav_observation_truth import receiver_samples
    from .esa_fit_adjusted_forecast_report import position_errors_neu,_metrics
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_forecast import native_forecast
    from .ilvis0_wide_tangent import load
    from .studies.artifacts import digest

    _check_continue(context.root,context.manifest)
    law=task['payload']['law'];channel=task['payload']['channel']
    case=load_case(context.root.parent.parent,law)
    binding=json.loads(context.input_path('parent-binding').read_bytes())
    if (case['parent_manifest_sha256']!=binding['parent_manifest_sha256'] or
            case['parent_input_sha256']!=binding['noisy_input_sha256'][law] or
            case['lineage_sha256']!=binding['lineage_sha256']):
        raise ValueError('sealed noisy channel input differs')
    with np.load(context.input_path('clean-increments'),allow_pickle=False) as raw:
        if set(raw.files)!={'theta','dv','dt','times'}:
            raise ValueError('complete clean staged input required')
        clean={key:np.array(raw[key],dtype=float,copy=True) for key in raw.files}
    if (any(digest(np.asarray(clean[key],dtype='<f8').tobytes())!=
            binding['clean_array_sha256'][key] for key in ('theta','dv','dt')) or
            not np.array_equal(clean['dt'],case['dt']) or
            not np.array_equal(clean['times'],case['times'])):
        raise ValueError('clean and noisy channel inputs differ in timing')
    mixture=mix_channels(clean,case,channel)
    theta,dv=mixture['theta'],mixture['dv']
    source='analysis/lll/ilvis0_tangent.cpp'
    kernel,compilation=load(context.directory/'kernel',
        expected_source_sha256=context.manifest['sources'][source],
        gravity_anchor_height_m=float(case['earlier_coordinates'][0,2]))
    context.save('compilation.json',compilation)
    problem,point=oracle_problem(theta,dv,case['dt'],case['times'],
        case['earlier_coordinates'],case['known_state'],case['limits'],
        kernel,rate_hz=300)
    forecast=native_forecast(problem,point,'sphere_rotating',
        theta=theta,dv=dv,dt=case['dt'],times=case['times'],
        maximum_interval_s=1.5/300,reserve=reserve)
    _check_continue(context.root,context.manifest)
    truth=receiver_samples('sphere_rotating',case['times'][600:],
        latitude_deg=55.,pattern='fast',removal=0.,sign=1,
        height_profile='climb',gravity_model='inverse_square_height')
    score=_metrics(position_errors_neu(
        forecast['coordinates'][600:],truth['coordinates']))
    context.save('channel-forecast.json',dict(
        coordinates=forecast['coordinates'].tolist(),
        times_s=case['times'].tolist(),future_metrics=score,
        noisy_channel=channel,noise_law=law,
        future_receiver_positions_used_to_forecast=False,
        later_truth_used_for_scoring_only=True,
        original_reads=0,protected_reads=0))
    return dict(passed=True,scientific_decision='abstain',
        law=law,channel=channel,future_metrics=score,native_calls=1,
        original_reads=0,protected_reads=0)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv);root=Path(args.root).resolve()
    if args.action=='request':result=request_qualification(root)
    else:
        from .esa_oracle_channel_recovery import SPEC
        result=prepare(root,qualification=DIRECTORY+'oracle-channel-request.json',
            recovery_qualification=SPEC.request)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
