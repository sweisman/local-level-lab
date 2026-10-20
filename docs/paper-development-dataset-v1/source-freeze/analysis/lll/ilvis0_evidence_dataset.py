# SPDX-License-Identifier: AGPL-3.0-or-later
"""Join sealed development metadata without promoting scientific decisions."""
import csv
import hashlib
import io
import math
from pathlib import Path

MODELS=('sphere_rotating','sphere_still','flat_still')
CASES=('bias1_unsubtracted','bias1_profiled_removal')


def verify_artifacts(root,hashes):
    root=Path(root).resolve()
    for name,digest in hashes.items():
        path=(root/name).resolve()
        if Path(name).is_absolute() or not path.is_relative_to(root):raise ValueError('artifact path escapes its declared root')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('artifact hash changed: '+name)


def encode_csv(rows):
    if not rows:return b''
    output=io.StringIO(newline='');fields=list(dict.fromkeys(k for row in rows for k in row))
    writer=csv.DictWriter(output,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    return output.getvalue().encode()


def _unique(rows,key):
    result={}
    for row in rows:
        identity=row[key]
        if not identity or identity in result:raise ValueError('missing or duplicate '+key)
        result[identity]=row
    return result


def assemble(*,current,groups,eligible,gyro,history,files):
    population=_unique(current,'segment_id');selection=_unique(eligible,'segment_id')
    if not population or set(population)!=set(selection):raise ValueError('selection and current populations differ')
    group_rows=[dict(r,segment_id=r['record_id'].split(':',1)[1]) for r in groups if r['archive']=='ilvis0']
    grouped=_unique(group_rows,'segment_id')
    if set(grouped)!=set(population):raise ValueError('every stretch needs its conservative group')
    comparisons={}
    for row in gyro:
        key=(row['segment_id'],row['model'])
        if key in comparisons or key[0] not in population or key[1] not in MODELS:raise ValueError('unknown or duplicate gyro baseline')
        if any(float(row[k])!=0. for k in ('removal','crab_deg','roll_deg','pitch_deg')):raise ValueError('baseline contains a sensitivity scenario')
        comparisons[key]=row
    if set(comparisons)!={(sid,model) for sid in population for model in MODELS}:raise ValueError('incomplete gyro baseline population')
    joined=[];primaries=[]
    for sid,row in population.items():
        group=grouped[sid];original=selection[sid]
        if not group['group_id'] or group['source_sha256']!=row['source_sha256']:raise ValueError('group/source identity mismatch')
        for key in ('source_sha256','mounting_epoch','selection_sha256','selection_version'):
            if original[key]!=row[key]:raise ValueError('selected source/configuration identity mismatch: '+key)
        if group.get('mounting_configuration')!=row['mounting_epoch']:raise ValueError('group mounting configuration mismatch')
        if row.get('scientific_decision')!='abstain':raise ValueError('source unexpectedly asserts a calibrated detection')
        if row.get('all_required_repeat_checks_passed') not in ('','True',None):raise ValueError('required repeat gate failed')
        output=dict(row,conservative_split_group=group['group_id'],physical_instrument_id=group['physical_instrument_id'],
            installation_id=group['installation_id'],grouping_status='conservative_split_only',snapshot_role='retrospective_development',
            calibrated_detection=False,qualified_withheld_prediction=False,independent_replication_established=False)
        observed=[]
        for model in MODELS:
            baseline=comparisons[(sid,model)]
            if baseline['source_sha256']!=row['source_sha256'] or str(baseline['imu_type'])!=str(row['imu_type']):raise ValueError('gyro source/configuration mismatch')
            observed.append(float(baseline['observed_nose_down_dph']))
            for key in ('predicted_nose_down_dph','observed_minus_scenario_dph'):
                value=float(baseline[key])
                if not math.isfinite(value):raise ValueError('nonfinite descriptive gyro baseline')
                output['gyro_companion__'+model+'__'+key]=baseline[key]
        if not all(math.isfinite(v) and abs(v-observed[0])<=1e-12 for v in observed):raise ValueError('gyro baselines use different observations')
        output['gyro_companion_observed_nose_down_dph']=observed[0]
        for case in CASES:
            for model in MODELS:
                prefix=case+'__'+model+'__'
                if row.get(prefix+'converged')!='True':raise ValueError('latest primary numerical comparison is incomplete')
                cost=float(row[prefix+'cost'])
                if not math.isfinite(cost) or cost<0.:raise ValueError('invalid latest primary cost')
                primary=dict(segment_id=sid,source_sha256=row['source_sha256'],group_id=group['group_id'],case_id=case,model=model,
                    record_role='latest_primary',numerical_converged=True,scientific_decision='abstain',calibrated_detection=False)
                for key in ('cost','result_origin','stop_reason','stationarity','active_bounds','evaluations','maximum_evaluations'):
                    primary[key]=row.get(prefix+key,'')
                primaries.append(primary)
        joined.append(output)
    numerical=[]
    for index,row in enumerate(history,1):
        if row['segment_id'] not in population:raise ValueError('unknown stretch in numerical history')
        numerical.append(dict(row,history_row_id=f'history-{index:06d}',snapshot_row_ordinal=index,
            snapshot_row_id_is_original_worker_id=False))
    source_pairs={(r['filename'],r['source_sha256']) for r in files}
    if any((r['filename'],r['source_sha256']) not in source_pairs for r in current):raise ValueError('selected source missing from eligibility file ledger')
    groups_out=[dict(r) for r in group_rows]
    return dict(stretches=joined,primary_comparisons=primaries,numerical_history=numerical,groups=groups_out,
        files=[dict(r) for r in files],gyro_baselines=[dict(r) for r in gyro],summary=dict(
            stretches=len(joined),latest_primary_comparisons=len(primaries),numerical_history_records=len(numerical),
            history_rows_not_marked_converged=sum(r.get('converged')!='True' for r in numerical),
            conservative_split_groups=len({r['group_id'] for r in group_rows}),verified_independent_flights=None,
            retained_file_eligibility_rows=len(files),final_paper_dataset=False,calibrated_detections=0,
            snapshot_role='retrospective_development',original_reads=0,model_evaluations=0,optimizer_starts=0,
            preferences={k:sum(r.get('shape_preference')==k for r in current) for k in ('globe','flat','unresolved','ambiguous')}))
