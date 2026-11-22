# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only bound and known-setting audit of the matched generated fits."""

import hashlib
import json
import math
import statistics
from pathlib import Path

from .matched_candidate_case import MODELS
from .matched_candidate_generated_report import build as primary_report
from .matched_candidate_generated_study import recipe,tasks

PLAN='docs/prediction-observed-development/MATCHED_CANDIDATE_CALIBRATION_AUDIT_PLAN.md'
SENSOR_NAMES=tuple(name+'_'+axis for name in
                   ('gyro_bias','accel_bias','gyro_gain','accel_gain','lever')
                   for axis in 'xyz')+('gravity_delta','time_offset')


def build(root):
    from .airquantumgrav_observation_truth import sensor_parameters
    from .studies.closed import ClosedStudy
    root=Path(root).resolve();r=recipe();primary=primary_report(root)
    if primary['technical_passing']!=12 or primary['candidate_fits_converged']!=36:
        raise ValueError('complete numerically converged matrix required')
    if r.get('sensor_case','interior')!='interior':
        raise ValueError('unchanged generated sensor case required')
    truth=sensor_parameters(1)
    declared={row['identity']:row['payload'] for row in tasks(r)}
    study=ClosedStudy(root,primary['study'])
    try:
        cases={};matched=[];all_rows=[]
        for identity in sorted(declared):
            payload=declared[identity]
            if payload['profile'] is not False or payload['start']!=0:
                raise ValueError('unchanged generator sign and fit start required')
            case={}
            for model in MODELS:
                fit=study.artifact(identity,'candidates/'+model+'/fit.json')
                names=fit['active_parameters']
                values=fit['normalized_parameters']
                parameters=fit['parameters']
                singular=fit['singular_values']
                if (fit.get('converged') is not True or len(names)!=26
                        or len(names)!=len(values) or len(singular)!=26
                        or len(set(names))!=26 or set(names)!=set(r['limits'])
                        or any(type(value) not in (int,float)
                               or not math.isfinite(value) or abs(value)>1+1e-9
                               for value in values)
                        or any(not math.isfinite(value) or value<=0
                               for value in singular)):
                    raise ValueError('complete finite 26-column converged fit required')
                normalized=dict(zip(names,values,strict=True))
                if any(not math.isclose(parameters[name],normalized[name]*r['limits'][name],
                                        rel_tol=1e-8,abs_tol=1e-8*r['limits'][name])
                       for name in names):
                    raise ValueError('saved normalized and physical fit settings disagree')
                near={name:abs(normalized[name])>=.99 for name in names}
                is_matched=model==payload['truth_model']
                row=dict(generating_model=payload['truth_model'],candidate_model=model,
                         matched_generating_model=is_matched,
                         normalized_parameters=normalized,
                         near_bound=near,
                         singular_condition=float(singular[0]/singular[-1]),
                         exact_active_bounds=fit['active_bounds'])
                if is_matched:
                    errors={name:(parameters[name]-truth[name])/r['limits'][name]
                            for name in SENSOR_NAMES}
                    row['known_sensor_error_in_half_ranges']=errors
                    row['known_sensor_error_rms_half_ranges']=math.sqrt(
                        sum(value*value for value in errors.values())/len(errors))
                    matched.append(row)
                case[model]=row;all_rows.append(row)
            cases[identity]=case
        if len(matched)!=12 or len(all_rows)!=36:
            raise ValueError('exact matched and mismatched fit counts required')
        summary={name:dict(
            near_bound_all=sum(row['near_bound'][name] for row in all_rows),
            near_bound_matched=sum(row['near_bound'][name] for row in matched),
            median_abs_matched_truth_error_half_ranges=(
                float(statistics.median(abs(row['known_sensor_error_in_half_ranges'][name])
                                        for row in matched))
                if name in SENSOR_NAMES else None))
                 for name in sorted(r['limits'])}
        return dict(version='matched-candidate-calibration-audit-v1',
                    study=primary['study'],
                    manifest_sha256=primary['manifest_sha256'],
                    summary_sha256=primary['summary_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root/PLAN).read_bytes()).hexdigest(),
                    matched_truth_fits=12,mismatched_candidate_fits=24,
                    near_bound_threshold_normalized=.99,
                    matched_sensor_rms_error_median_half_ranges=float(
                        statistics.median(row['known_sensor_error_rms_half_ranges']
                                          for row in matched)),
                    summary=summary,cases=cases,new_fits=0,original_reads=0,
                    protected_reads=0,scientific_decision='abstain')
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
        raise ValueError('fresh verified calibration audit required')
    result=build(args.root)
    atomic(target,encoded(result))
    print(json.dumps(dict(matched_truth_fits=result['matched_truth_fits'],
                          mismatched_candidate_fits=result['mismatched_candidate_fits'])))


if __name__=='__main__':
    main()
