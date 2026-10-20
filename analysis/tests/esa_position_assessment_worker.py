# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and publish a bounded receiver-only ESA development assessment."""
import argparse
import csv
import gzip
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll import ilvis0_control_publication as publication

DATA=ROOT/'data/esa-position-assessment-20261020';PUBLIC=ROOT/'docs/esa-position-assessment'
QUALIFIED=ROOT/'docs/esa-position-motion';OLD=ROOT/'docs/esa-motion-diagnostic'
SOURCE='data/external-imu-survey-20261018/esa-sample/187_air1_ppp_2Hz_final.txt'
POLICY='docs/external-imu-data/ESA_CONFIRMATION_POLICY.json'
ADAPTER='analysis/lll/esa_position_assessment.py';PLAN='docs/esa-position-assessment/PLAN.md'
SOURCES=[ADAPTER,PLAN,'analysis/tests/esa_position_assessment_worker.py',
    'analysis/tests/test_esa_position_assessment.py','analysis/tests/ilvis0_control_shards.py',
    'analysis/tests/run_numerical.py','analysis/lll/airquantumgrav_motion.py','analysis/lll/airquantumgrav_receiver.py']


def prepare():
    if DATA.exists():raise ValueError('receiver-only position assessment already frozen')
    for directory in (QUALIFIED,OLD):
        for name,digest in runner._load(directory/'evidence-receipt.json')['artifacts'].items():
            if runner._sha(directory/name)!=digest:raise ValueError('sealed prerequisite changed')
    qualified=runner._load(QUALIFIED/'manifest.json');summary=runner._load(QUALIFIED/'summary.json')
    if not summary['passed'] or len(summary['results'])!=10 or qualified['environment']!=runner.runtime_environment():
        raise ValueError('complete generated qualification and unchanged environment required')
    sources=set(SOURCES)
    for name,digest in qualified['sources'].items():
        if name.startswith('analysis/lll/'):
            if runner._sha(ROOT/name)!=digest:raise ValueError('qualified source changed: '+name)
            sources.add(name)
    old=runner._load(OLD/'manifest.json');policy=runner._load(ROOT/POLICY)
    for name in ('analysis/lll/airquantumgrav_motion.py','analysis/lll/airquantumgrav_receiver.py'):
        if runner._sha(ROOT/name)!=old['sources'][name]:raise ValueError('qualified receiver reader changed')
    if ('187_rqh01.txt' not in policy['development_files']
            or '187_rqh01.txt' in policy['confirmation_files']):raise ValueError('recording 187 must remain development-only')
    path=ROOT/SOURCE;digest=runner._sha(path)
    if digest!=old['inputs'][SOURCE]:raise ValueError('original receiver identity changed')
    with (OLD/'observed-windows.csv').open() as handle:baseline=list(csv.DictReader(handle))
    indices=[int(r['index']) for r in baseline]
    if len(indices)!=2048 or len(set(indices))!=2048:raise ValueError('complete earlier center list required')
    reference=PUBLIC/'receiver-reference.json'
    runner._write(reference,dict(path=SOURCE,sha256=digest,bytes=path.stat().st_size,recording=187,
        group_id=old['group_id'],original_redistributed=False))
    definition=PUBLIC/'definition.json'
    runner._write(definition,dict(recording=187,group_id=old['group_id'],expected_epochs=64080,
        maximum_receiver_reads=1,maximum_windows=2048,indices=indices,
        degree=3,window_half_s=5.,alpha=.01,half_second_correlation=.8,
        instantaneous_motion_bound_supplied=False,eligibility_policy_changed=False))
    inputs=dict(definition=str(definition.relative_to(ROOT)),
        **{'receiver-reference':str(reference.relative_to(ROOT)),
           'old-windows':str((OLD/'observed-windows.csv').relative_to(ROOT)),
           'qualification':str((QUALIFIED/'evidence-receipt.json').relative_to(ROOT)),
           'confirmation-policy':POLICY})
    tasks=[dict(identity='receiver-position-windows-187',input_key='definition',
        payload=dict(maximum_windows=2048,maximum_epochs=100000),
        limits=dict(native_calls=0,packet_visits=0,bound_calls=0,bound_steps=0))]
    runner.prepare(DATA,project_root=ROOT,tasks=tasks,sources=sorted(sources),inputs=inputs,
        adapter=ADAPTER,workers=1,threads=4,maximum_wall_s=300,environment=runner.runtime_environment())


def verified_record():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    if len(summary['results'])!=1:raise ValueError('one bounded development assessment required')
    record=runner._load(DATA/summary['results'][0]['artifact']);row=record['result']
    if row.get('passed'):
        names=sorted(n for n in record['artifacts'] if Path(n).name.startswith('window-')
            and n.endswith('-reservation.json'))
        indices=runner._load(DATA/manifest['inputs']['definition']['path'])['indices']
        if len(names)!=2048 or row['windows_reserved']!=2048:raise ValueError('missing charged windows')
        for ordinal,(name,index) in enumerate(zip(names,indices,strict=True),1):
            if runner._load(DATA/name)!=dict(windows=ordinal,index=index,maximum_windows=2048,
                    maximum_calls=dict(position=1,point=1,residual=1)):
                raise ValueError('window reservation changed')
        if any(type(v)!=int or not 0<=v<=2048 for v in row['actual_stage_calls'].values()):
            raise ValueError('window stage allowance exceeded')
        reads=[n for n in record['artifacts'] if Path(n).name=='receiver-read-reservation.json']
        if len(reads)!=1 or runner._load(DATA/reads[0])!=dict(receiver_reads=1,maximum_epochs=100000):
            raise ValueError('receiver read reservation changed')
    return manifest,summary,record,row


def publish():
    manifest,summary,record,row=verified_record()
    text=['# Position and velocity on the same ESA receiver windows','']
    if row.get('passed'):
        text += [f"Completed all 2,048 fixed centers in {summary['elapsed_s']:.1f} seconds: "
            f"{row['supported_windows']} supported, {row['unsupported_windows']} unsupported; "
            f"{row['airborne_supported']} supported windows retain the earlier airborne classification.",'',
            '| Error assumption | Supported airborne intervals | Trend wholly within ±0.02°/s | Definitely outside |',
            '|---|---:|---:|---:|']
        for mode,title in (('independent','Independent epochs'),('supplied_correlation','Supplied correlation 0.8'),
                ('arbitrary_correlation','Arbitrary temporal correlation')):
            c=row['interval_counts'][mode]
            text.append(f"| {title} | {c['supported']} | {c['wholly_quiet']} | {c['definitely_turning']} |")
        text += ['',f"Point estimates flag {row['point_turn_flags']} of these windows for turning, "
            f"compared with {row['old_velocity_point_turn_flags']} in the earlier velocity-trend diagnostic.",'']
        name=next(n for n in record['artifacts'] if Path(n).name=='windows.json.gz')
        windows=json.loads(gzip.decompress((DATA/name).read_bytes()));csv_path=PUBLIC/'windows.csv'
        csv_path.parent.mkdir(parents=True,exist_ok=True)
        fields=['index','time_s','supported','reason','airborne_supported','epochs',
            'mean_reported_speed_kmh','position_course_rate_deg_s','old_velocity_course_rate_deg_s',
            'course_rate_difference_deg_s','median_abs_reported_vertical_mps',
            'position_minus_reported_north_mps','position_minus_reported_east_mps']
        for mode in ('independent','supplied_correlation','arbitrary_correlation'):
            fields += [mode+'_supported',mode+'_lower_deg_s',mode+'_upper_deg_s']
        for axis in ('north','east','height'):fields += ['residual_'+axis+'_rms_m','residual_'+axis+'_lag1']
        with csv_path.open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=fields,lineterminator='\n');writer.writeheader()
            for window in windows:
                output={k:window.get(k) for k in fields}
                if window['supported']:
                    difference=window['position_minus_reported_ne_mps']
                    if difference is not None:output.update(position_minus_reported_north_mps=difference[0],position_minus_reported_east_mps=difference[1])
                    for mode,value in window['position']['intervals'].items():
                        output.update({mode+'_supported':value['supported'],mode+'_lower_deg_s':value.get('lower_deg_s'),
                            mode+'_upper_deg_s':value.get('upper_deg_s')})
                    for axis,rms,lag in zip(('north','east','height'),window['residual']['rms_m'],window['residual']['lag1']):
                        output['residual_'+axis+'_rms_m']=rms;output['residual_'+axis+'_lag1']=lag
                writer.writerow(output)
    else:text += ['The bounded assessment failed or did not complete. Its charged identity and failure are preserved; no retry follows.','']
    text += ['These are noise-free cubic-trend intervals under supplied error assumptions. '
        'They are not guarantees of quiet instantaneous flight. Real covariance remains '
        'uncalibrated; position and velocity belong to the same receiver solution. '
        'The independent cubic residual calculation is a consistency check, not '
        'independent position truth.','',
        'The original ESA inventory still has **zero eligible intervals**. No revised '
        'selection or model decision is created here. There were no raw-IMU reads, '
        'native trajectories, Earth-model fits or protected confirmation reads.','',
        '[Every sampled window](windows.csv) · [Frozen scope](PLAN.md) · '
        '[Software qualification](../esa-position-motion/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    publication.publish(DATA,PUBLIC,'\n'.join(text),plan=PLAN)
    receipt=runner._load(PUBLIC/'evidence-receipt.json')
    if (PUBLIC/'windows.csv').exists():receipt['artifacts']['windows.csv']=runner._sha(PUBLIC/'windows.csv')
    runner._replace(PUBLIC/'evidence-receipt.json',receipt)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen one development receiver file / 2048 fixed windows; zero IMU reads or model fits.')
    elif args.package_only:publish();print('Published receiver-only position assessment.')
    else:publication.check(DATA,PUBLIC);verified_record();print('Verified receiver-only assessment evidence.')

if __name__=='__main__':main()
