# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and audit published prediction errors; never integrate or refit."""
import argparse
import csv
import gzip
import hashlib
import importlib.metadata
import io
import json
import math
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment as guarded_environment
if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in guarded_environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with one worker and four threads')
from lll import evidence_snapshot as snapshot,ilvis0_evidence_dataset as dataset,ilvis0_saved_prediction as audit

NAME='ilvis0-saved-prediction-comparison-20261019';GUIDE='docs/ilvis0-saved-prediction-comparison'
DATA=ROOT/'data'/NAME;PUBLIC=ROOT/GUIDE
SOURCES=[GUIDE+'/build_report.py',GUIDE+'/PLAN.md','analysis/lll/ilvis0_saved_prediction.py',
    'analysis/lll/evidence_snapshot.py','analysis/lll/ilvis0_evidence_dataset.py','analysis/lll/compute_budget.py',
    'analysis/tests/test_ilvis0_saved_prediction.py','analysis/tests/test_saved_prediction_report.py']
STUDIES=('docs/ilvis0-prediction-trial-20261011','docs/ilvis0-prediction-covariance-20261012')
MODELS=('sphere_rotating','sphere_still','flat_still')
LABELS=dict(sphere_rotating='Globe + specified field',sphere_still='Globe, zero field',flat_still='Flat disc')
FAMILIES={'original':'Original objective','h1_v3_tau10':'10-second correlation','h1_v3_tau300':'300-second correlation'}


def csv_rows(data):return list(csv.DictReader(io.StringIO(data.decode())))


def prepare():
    if (DATA/'input-freeze/manifest.json').exists():raise ValueError('input freeze already exists')
    inputs={};records=[];source_hashes=set();segment_ids=set()
    def read(name,expected=None):
        path=ROOT/name
        if Path(name).is_absolute() or '..' in Path(name).parts or not path.resolve().is_relative_to(ROOT):raise ValueError('source path escapes repository')
        data=path.read_bytes();digest=hashlib.sha256(data).hexdigest()
        if expected is not None and digest!=expected:raise ValueError('upstream artifact changed: '+name)
        if name in inputs and inputs[name]!=digest:raise ValueError('input changed during collection')
        inputs[name]=digest;return data
    def load(name,expected=None):return json.loads(read(name,expected))
    for index,directory in enumerate(STUDIES):
        receipt=load(directory+'/evidence-receipt.json')['artifacts']
        def named(name):
            if name not in receipt:raise ValueError('source missing from upstream receipt: '+name)
            return load(directory+'/'+name,receipt[name])
        summary=named('summary.json');manifest=named('manifest.json');completion=named('completion.json')
        if (summary['state']!='complete' or completion['summary_sha256']!=inputs[directory+'/summary.json']
                or completion['manifest_sha256']!=inputs[directory+'/manifest.json']):raise ValueError('source completion mismatch')
        provenance=summary['provenance'];segment_ids.add(provenance['segment_id']);source_hashes.add(provenance['source_sha256'])
        if provenance['group1_observations_used'] is not False:raise ValueError('unexpected fused observation source')
        fits=[(case['case_id'],f) for case in summary['cases'] for f in case['fits']] if index==0 else [(f['case_id'],f) for f in summary['results'].values()]
        if len(fits)!=(6 if index==0 else 12):raise ValueError('source fit count changed')
        for processing,fit in fits:
            model=fit['model'];family='original' if index==0 else fit['covariance'];epoch=fit['residual_file']
            if model not in MODELS or family not in FAMILIES or Path(epoch).name!=epoch:raise ValueError('unexpected fit/source identity')
            if type(fit['converged']) is not bool or fit['scientific_decision']!='abstain':raise ValueError('unexpected scientific/convergence policy')
            if fit['continuous_propagation_without_gps_reset'] is not True or fit['prediction_receiver_positions_used_in_training'] is not False:
                raise ValueError('source prediction dependency mismatch')
            read(directory+'/'+epoch,receipt[epoch])
            if fit['residual_sha256']!=receipt[epoch]:raise ValueError('fit/epoch hash mismatch')
            diagnostic=fit['prediction_diagnostics']
            records.append(dict(identity=family+'::'+processing+'::'+model,family=family,processing=processing,model=model,
                source_status='converged' if fit['converged'] else 'unresolved',source_study=directory,
                source_epoch_file=directory+'/'+epoch,source_sha256=provenance['source_sha256'],segment_id=provenance['segment_id'],
                expected_training={k:diagnostic['training'][k] for k in ('epochs','horizontal_rms_m','vertical_rms_m')},
                expected_prediction={k:diagnostic['prediction'][k] for k in ('epochs','horizontal_rms_m','vertical_rms_m')},
                gyro_gain_z=fit['parameters']['gyro_gain_z'],gyro_bias_z_dph=math.degrees(fit['parameters']['gyro_bias_z'])*3600.,
                gravity_delta_mps2=fit['parameters']['gravity_delta'],active_bounds=fit['active_bounds']))
    if len(records)!=18 or len({r['identity'] for r in records})!=18 or len(source_hashes)!=1 or len(segment_ids)!=1:
        raise ValueError('matched prediction population changed')
    groups_path='docs/analysis-provenance/recording-groups.csv'
    receipt=load('docs/analysis-provenance/provenance-receipt.json')['artifacts']
    groups=csv_rows(read(groups_path,receipt['recording-groups.csv']))
    group=[r for r in groups if r['record_id']=='ilvis0:'+next(iter(segment_ids))]
    eligible=csv_rows(read('docs/ilvis0-highspeed-segments-20261008/eligible-stretches.csv'))
    selection=[r for r in eligible if r['segment_id']==next(iter(segment_ids))]
    if len(group)!=1 or len(selection)!=1 or group[0]['source_sha256']!=selection[0]['source_sha256'] or group[0]['source_sha256'] not in source_hashes:
        raise ValueError('prediction source/group mismatch')
    metadata=dict(selection[0],conservative_group=group[0]['group_id'],physical_instrument_id=group[0]['physical_instrument_id'])
    sources={name:snapshot.sha(ROOT/name) for name in SOURCES}
    snapshot.create(ROOT,DATA/'input-freeze',version=NAME+'-inputs',inputs=inputs,sources=sources,
        outputs={'records.json':snapshot.encoded(records),'recording.json':snapshot.encoded(metadata)},
        summary=dict(stage='inputs_only',expected_records=18,maximum_saved_epochs=10000,training_epochs=292,prediction_epochs=147,
            new_native_calls=0,new_optimizer_starts=0,original_reads=0,
            environment={k:importlib.metadata.version(k) for k in ('numpy','matplotlib')}))
    return snapshot.check(DATA/'input-freeze')


def figure(rows,epochs):
    os.environ.setdefault('MPLCONFIGDIR','/tmp/local-level-lab-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    colors=dict(sphere_rotating='#126b81',sphere_still='#ba7b25',flat_still='#99556a')
    family_colors=dict(original='#126b81',h1_v3_tau10='#8755a1',h1_v3_tau300='#be742a')
    fig,axes=plt.subplots(1,2,figsize=(12,5.5));fig.patch.set_facecolor('#fcfcfa')
    for record in rows:
        series=[r for r in epochs if r['identity']==record['identity'] and r['role']=='prediction']
        x=[r['elapsed_prediction_s'] for r in series];y=[math.hypot(r['north_direct_error_m'],r['east_direct_error_m']) for r in series]
        style='-' if record['processing']=='bias1_unsubtracted' else '--';alpha=.8 if record['source_status']=='converged' else .28
        axes[0].plot(x,y,style,color=colors[record['model']],alpha=alpha,linewidth=1.3)
        if record['model']=='sphere_rotating':axes[1].plot(x,y,style,color=family_colors[record['family']],alpha=alpha,linewidth=1.4)
    for ax,title in zip(axes,('All three model calculations','Zoom: globe + specified field')):
        ax.set(title=title,xlabel='Seconds after GPS fitting stops',ylabel='Horizontal error to receiver positions (metres)')
        ax.set_xlim(0,146);ax.set_ylim(bottom=0);ax.grid(alpha=.15);ax.spines[['top','right']].set_visible(False);ax.set_facecolor('#fcfcfa')
    axes[0].legend([Line2D([0],[0],color=colors[m]) for m in MODELS],[LABELS[m] for m in MODELS],frameon=False,fontsize=8)
    axes[1].legend([Line2D([0],[0],color=family_colors[f]) for f in FAMILIES],list(FAMILIES.values()),frameon=False,fontsize=8)
    fig.suptitle('Position errors after receiver fitting stops',fontsize=17,fontweight='bold',x=.08,ha='left')
    fig.text(.08,.02,'Same recording throughout. Solid: no removal. Dashed: removal allowed. Faint: unfinished source optimization.',fontsize=9)
    fig.subplots_adjust(left=.08,right=.98,bottom=.16,top=.82,wspace=.3)
    images={}
    for extension in ('png','svg'):
        stream=io.BytesIO();fig.savefig(stream,format=extension,dpi=160,metadata={'Date':None} if extension=='svg' else None)
        images['prediction-errors.'+extension]=stream.getvalue()
    plt.close(fig);return images


def build():
    if (DATA/'result/manifest.json').exists():raise ValueError('completed audit is immutable; use --check')
    frozen=snapshot.check(DATA/'input-freeze');root=DATA/'input-freeze/frozen-inputs'
    for name,digest in frozen['sources'].items():
        if snapshot.sha(ROOT/name)!=digest:raise ValueError('audit implementation changed after freeze')
    records=snapshot.load(DATA/'input-freeze/records.json');metadata=snapshot.load(DATA/'input-freeze/recording.json')
    rows=[];sections=[];epochs=[];grid=None;utc_grid=None
    for record in sorted(records,key=lambda r:(list(FAMILIES).index(r['family']),r['processing'],MODELS.index(r['model']))):
        raw=csv_rows(gzip.decompress((root/record['source_epoch_file']).read_bytes()))
        result=audit.summarize(raw,training_epochs=292,prediction_epochs=147)
        for role in ('training','prediction'):
            expected=record['expected_'+role]
            audit.check_rms(result[role],horizontal=expected['horizontal_rms_m'],vertical=expected['vertical_rms_m'])
        utc=[float(r['time_utc_week_s']) for r in raw]
        if grid is None:grid=result['grid'];utc_grid=utc
        if result['grid']!=grid or utc!=utc_grid:raise ValueError('prediction sources do not share one time grid')
        row={k:v for k,v in record.items() if not k.startswith('expected_') and k!='active_bounds'}
        row.update(filename=metadata['filename'],imu_type=metadata['imu_type'],conservative_group=metadata['conservative_group'],
            active_bounds=';'.join(record['active_bounds']),training_epochs=292,prediction_epochs=147,
            training_horizontal_rms_m=result['training']['horizontal_rms_m'],training_vertical_rms_m=result['training']['vertical_rms_m'],
            **{'prediction_'+k:v for k,v in result['prediction'].items()})
        rows.append(row);sections.extend(dict(identity=record['identity'],family=record['family'],processing=record['processing'],model=record['model'],**r) for r in result['sections'])
        origin=float(raw[292]['time_s'])
        for raw_row in raw:
            epochs.append(dict(identity=record['identity'],family=record['family'],processing=record['processing'],model=record['model'],
                source_status=record['source_status'],epoch=int(raw_row['epoch']),role=raw_row['role'],time_s=float(raw_row['time_s']),
                time_utc_week_s=float(raw_row['time_utc_week_s']),elapsed_prediction_s=float(raw_row['time_s'])-origin,
                **{axis+'_direct_error_m':float(raw_row[axis+'_direct_error_m']) for axis in ('north','east','up')}))
    if len(epochs)>10000:raise ValueError('saved epoch allowance exceeded')
    complete_sets=0
    for family in FAMILIES:
        for processing in ('bias1_unsubtracted','bias1_profiled_removal'):
            matched=[r for r in rows if r['family']==family and r['processing']==processing]
            if len(matched)!=3:raise ValueError('matched model set incomplete')
            complete_sets+=all(r['source_status']=='converged' for r in matched)
    summary=dict(stage='saved_reductions_complete',fit_records=len(rows),source_converged_fits=sum(r['source_status']=='converged' for r in rows),
        source_unresolved_fits=sum(r['source_status']!='converged' for r in rows),source_recordings=1,conservative_groups=1,
        complete_three_model_sets=complete_sets,total_three_model_sets=6,saved_epochs=len(epochs),
        training_epochs=292,prediction_epochs=147,prediction_duration_s=146.,new_native_calls=0,new_optimizer_starts=0,original_reads=0,
        calibrated_detection=False,absolute_adequacy_criterion_calibrated=False,independent_confirmation=False,
        input_freeze_manifest_sha256=snapshot.sha(DATA/'input-freeze/manifest.json'))
    lines=['# What happens after GPS fitting stops?','',
        'The globe model with the specified field remains much closer horizontally to the withheld receiver positions. '
        'Their errors still grow to several metres; this is a useful prediction check, not a calibrated detection.','',
        '![Direct position errors during the withheld interval](prediction-errors.png)','',
        f"This is **one recording**, IMU type {metadata['imu_type']}: `{metadata['filename']}`. "
        f"Its selected stretch lasts {float(metadata['duration_s'])/60:.2f} minutes at median ground speed {float(metadata['median_ground_speed_kmh']):.1f} km/h. "
        'Calibration used the first 4.85 minutes of receiver positions. The calculation then continued for 2.43 minutes using the later IMU '
        '(inertial measurement unit) observations while withholding later GPS positions, with no GPS reset.','',
        '**Eighteen saved fits reuse those same measurements:** six from the earlier prediction study and twelve from the receiver-correlation comparison. '
        '**15/18 passed their original stopping checks; three remain unfinished.** Only three of six matched model sets are numerically complete. '
        'These are neither eighteen flights nor new independent replications.','',
        '| Fitting/error assumption | Processing | Model | Original stopping status | Prediction horizontal RMS | Vertical RMS | Final horizontal error |',
        '|---|---|---|---|---:|---:|---:|']
    for row in rows:
        lines.append(f"| {FAMILIES[row['family']]} | {'No removal' if row['processing']=='bias1_unsubtracted' else 'Removal allowed'} | "
            f"{LABELS[row['model']]} | {row['source_status']} | {row['prediction_horizontal_rms_m']:.2f} m | "
            f"{row['prediction_vertical_rms_m']:.2f} m | {row['prediction_final_horizontal_m']:.2f} m |")
    lines+=['','The globe model with the specified field has horizontal RMS from 2.22 to 3.35 m across these saved calculations; '
        'the zero-field globe and flat-disc trajectories diverge much farther horizontally. '
        'An unfinished fit has not established its model’s best result and is not equal support for competing models. '
        'No new model winner or background-field conclusion is assigned here.','',
        'The curves use direct errors, without a receiver-error conditioning adjustment. '
        'The common sign and growth patterns include calibration/model deficiencies and correlated receiver errors; '
        'their relative contributions remain unresolved. Uncertainty from nuisance fitting is not calibrated, '
        'and no absolute adequacy cutoff is chosen after examining these errors. '
        'The recording had already informed development, so the check is retrospective.','',
        '[All comparison metadata](comparisons.csv) · [Thirty-second error sections](sections.csv) · [Every saved epoch](epochs.csv.gz) · [Audit scope](PLAN.md).','',
        '[Original six-fit result](../ilvis0-prediction-trial-20261011/RESULTS.md) · '
        '[Original twelve-fit result](../ilvis0-prediction-covariance-20261012/RESULTS.md) · '
        '[All selected stretches](../ilvis0-current-findings-20261015/STRETCHES.md) · [Next analyses](../NEXT_STEPS.md).']
    outputs=dict(figure(rows,epochs),**{'README.md':('\n'.join(lines)+'\n').encode(),'PLAN.md':(DATA/'input-freeze/source-freeze'/GUIDE/'PLAN.md').read_bytes(),
        'comparisons.csv':dataset.encode_csv(rows),'sections.csv':dataset.encode_csv(sections),'epochs.csv.gz':gzip.compress(dataset.encode_csv(epochs),mtime=0),
        'audit.json':snapshot.encoded(dict(summary=summary,recording=metadata,comparisons=rows,sections=sections))})
    snapshot.create(ROOT,DATA/'result',version=NAME,inputs=frozen['inputs'],sources=frozen['sources'],outputs=outputs,summary=summary)
    snapshot.publish(DATA/'result',PUBLIC)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','build','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:prepare();print('Frozen the two studies and eighteen saved prediction identities; no reductions or model work.')
    elif args.build:build();print('Published saved prediction comparison; zero native calls or optimizer starts.')
    else:snapshot.check(DATA/'input-freeze');snapshot.check(DATA/'result');snapshot.check(PUBLIC);print('Verified input/result snapshots and public saved-error audit.')


if __name__=='__main__':main()
