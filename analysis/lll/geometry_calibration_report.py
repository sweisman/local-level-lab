# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only factorial audit of the sealed route/climb calibration control."""

import hashlib
import json
import math
import statistics
from pathlib import Path

from .geometry_calibration_study import ID,SCOPE,PLAN,recipe,tasks

NAMES=('gyro_bias_z','accel_bias_z')
SENSOR_NAMES=tuple(name+'_'+axis for name in
                   ('gyro_bias','accel_bias','gyro_gain','accel_gain','lever')
                   for axis in 'xyz')+('gravity_delta','time_offset')
CELLS=('straight-level','straight-climb','turning-level','turning-climb')


def factorial_ratios(values):
    if (set(values)!=set(CELLS) or any(type(values[key]) not in (int,float)
           or not math.isfinite(values[key]) or values[key]<=0 for key in CELLS)):
        raise ValueError('four finite positive factorial cells required')
    return dict(turning_vs_straight_at_level=values['turning-level']/values['straight-level'],
                turning_vs_straight_at_climb=values['turning-climb']/values['straight-climb'],
                climb_vs_level_on_straight=values['straight-climb']/values['straight-level'],
                climb_vs_level_on_turning=values['turning-climb']/values['turning-level'])


def _fit(fit,epochs,limits,truth):
    import numpy as np
    from .local_tangent import conditional_column_norm

    names=fit['active_parameters']
    local=fit['local_linearization']
    matrix=np.asarray(local['jacobian'],float)
    saved=np.asarray(fit['singular_values'],float)
    normalized=dict(zip(names,fit['normalized_parameters'],strict=True))
    parameters=fit['parameters']
    if (type(fit.get('converged')) is not bool or len(names)!=26
            or set(names)!=set(limits) or matrix.shape!=(3*epochs,26)
            or local.get('convention')!=
                'whitened residual derivative by normalized parameter'
            or saved.shape!=(26,) or np.any(saved<=0)
            or not np.all(np.isfinite(matrix))
            or not all(math.isfinite(normalized[name]) and
                       math.isclose(parameters[name],normalized[name]*limits[name],
                                    rel_tol=1e-8,abs_tol=1e-8*limits[name])
                       for name in names)):
        raise ValueError('complete saved 26-column generated tangent required')
    _,singular,vh=np.linalg.svd(matrix,full_matrices=False)
    if not np.allclose(singular,saved,rtol=1e-8,atol=1e-9):
        raise ValueError('saved singular values fail independent SVD')
    weak=np.abs(vh[-1])
    sensor_errors={name:(parameters[name]-truth[name])/limits[name]
                   for name in SENSOR_NAMES}
    return dict(weakest_singular=float(singular[-1]),
                weakest_to_strongest=float(singular[-1]/singular[0]),
                weakest_top_three=[names[i] for i in np.argsort(-weak)[:3]],
                weak_loading={name:float(weak[names.index(name)]) for name in NAMES},
                conditional_column_norm={name:conditional_column_norm(
                    matrix,names.index(name)) for name in NAMES},
                normalized_fit={name:float(normalized[name]) for name in NAMES},
                near_bound={name:abs(normalized[name])>=.99 for name in NAMES},
                known_sensor_error_rms_half_ranges=math.sqrt(
                    sum(value*value for value in sensor_errors.values())/
                    len(sensor_errors)),
                known_sensor_error_half_ranges=sensor_errors)


def build(root):
    from .airquantumgrav_observation_truth import sensor_parameters
    from .studies.closed import ClosedStudy

    root=Path(root).resolve();r=recipe()
    expected={task['identity']:task for task in tasks(r)}
    study=ClosedStudy(root,'data/'+ID)
    try:
        if (study.completion['state'] not in ('complete','terminal')
                or study.manifest.get('scope')!=SCOPE
                or study.input('recipe')!=r
                or set(study.tasks)!=set(expected)):
            raise ValueError('exact sealed four-case geometry study required')
        truth=sensor_parameters(1)
        cases={};noise_hashes=[]
        for identity in CELLS:
            task=expected[identity]
            if study.tasks[identity]['payload']!=task['payload']:
                raise ValueError('unchanged geometry task identity required')
            saved=study.rows[identity]
            if saved['status']!='complete':
                cases[identity]=dict(status=saved['status'],technical_passed=False,
                                     numerical_converged=False)
                continue
            result=study.envelope(identity)['result']
            geometry=study.artifact(identity,'case-geometry.json')
            if (result.get('technical_passed') is not True
                    or result.get('passed') is not True
                    or result.get('original_reads')!=0
                    or result.get('protected_reads')!=0
                    or result.get('scientific_decision')!='abstain'
                    or geometry.get('route')!=task['payload']['route']
                    or geometry.get('height_profile')!=task['payload']['height_profile']
                    or geometry.get('same_noise_seed')!=710101):
                raise ValueError('changed sealed geometry evidence')
            fit=study.artifact(identity,'fit.json')
            noise=study.artifact(identity,'input-binding.json')['noise']
            if noise['settings']['seed']!=710101:
                raise ValueError('changed matched IMU noise seed')
            noise_hashes.append(noise['noise_increment_sha256'])
            row=dict(status='complete',technical_passed=True,
                     numerical_converged=fit.get('converged') is True,
                     fit_termination=fit.get('termination'),
                     fit_message=fit.get('message'),
                     fit_evaluations=fit.get('evaluations'),
                     original_physical_passed=result['original_physical_passed'],
                     training_epochs=result['training_epochs'],
                     prediction_epochs=result['prediction_epochs'],
                     training_horizontal_rms_m=result['training']['horizontal_rms_m'],
                     prediction_horizontal_rms_m=result['prediction']['horizontal_rms_m'],
                     fit_sha256=hashlib.sha256(study.artifact(
                         identity,'fit.json',raw=True)).hexdigest())
            local=_fit(fit,result['training_epochs'],r['limits'],truth)
            row['local' if row['numerical_converged']
                else 'local_diagnostic']=local
            cases[identity]=row
        complete=[row for row in cases.values() if row['technical_passed']]
        if len(noise_hashes)==4 and any(value!=noise_hashes[0]
                                         for value in noise_hashes[1:]):
            raise ValueError('matched IMU noise increments differ across geometry')
        converged={key:row['local'] for key,row in cases.items()
                   if row['numerical_converged']}
        factors={}
        if len(converged)==4:
            factors['weakest_singular']=factorial_ratios({key:
                row['weakest_singular'] for key,row in converged.items()})
            for name in NAMES:
                factors[name]=factorial_ratios({key:
                    row['conditional_column_norm'][name]
                    for key,row in converged.items()})
        diagnostics={}
        if len(complete)==4:
            saved_local={key:row.get('local',row.get('local_diagnostic'))
                         for key,row in cases.items()}
            diagnostics['weakest_singular']=factorial_ratios({key:
                row['weakest_singular'] for key,row in saved_local.items()})
            for name in NAMES:
                diagnostics[name]=factorial_ratios({key:
                    row['conditional_column_norm'][name]
                    for key,row in saved_local.items()})
        return dict(version='generated-geometry-calibration-report-v1',
                    study='data/'+ID,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root/PLAN).read_bytes()).hexdigest(),
                    tasks_total=4,technical_passing=len(complete),
                    numerical_converged=len(converged),
                    physical_passing=sum(row['original_physical_passed'] for row in complete),
                    median_sensor_setting_rms_half_ranges=(float(statistics.median(
                        row['known_sensor_error_rms_half_ranges']
                        for row in converged.values())) if converged else None),
                    factorial_factors=factors,
                    diagnostic_factors=diagnostics,
                    diagnostic_includes_nonconverged=len(converged)<4,
                    same_imu_noise_increment_hashes=len(noise_hashes)==4,
                    common_noise_increment_hashes=(noise_hashes[0]
                                                   if len(noise_hashes)==4 else None),
                    cases=cases,new_fits=0,
                    original_reads=0,protected_reads=0,
                    aircraft_coverage_calibrated=False,
                    scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic,encoded

    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    target=Path(args.output)
    if target.exists():
        raise ValueError('fresh saved geometry report required')
    result=build(args.root)
    atomic(target,encoded(result))
    print(json.dumps({key:result[key] for key in
                      ('tasks_total','technical_passing','numerical_converged',
                       'physical_passing')}))


if __name__=='__main__':
    main()
