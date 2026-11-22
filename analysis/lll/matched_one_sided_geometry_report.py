# SPDX-License-Identifier: AGPL-3.0-or-later
"""Summarize sealed matched one-sided geometry results without refitting."""

import hashlib
import json
from pathlib import Path


def build(root,*,preflight=False):
    from .matched_candidate_case import MODELS
    from .matched_one_sided_geometry_study import (
        ID,PREFLIGHT_ID,SCOPE,PREFLIGHT_SCOPE,PLAN,recipe,preflight_recipe,tasks)
    from .one_sided_stopping import VERSION
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    name=PREFLIGHT_ID if preflight else ID
    r=preflight_recipe() if preflight else recipe()
    expected={row['identity'] for row in tasks(r)}
    study=ClosedStudy(root,'data/'+name)
    try:
        if (study.completion['state'] not in ('complete','terminal')
                or study.manifest.get('scope')!=(PREFLIGHT_SCOPE if preflight else SCOPE)
                or study.input('recipe')!=r or set(study.tasks)!=expected):
            raise ValueError('sealed exact matched one-sided study required')
        cases={}
        for identity in sorted(expected):
            row=study.rows.get(identity)
            if row is None or row['status']!='complete':
                cases[identity]=dict(technical_passed=False)
                continue
            outcome=study.envelope(identity)['result']
            if outcome.get('technical_passed') is not True:
                cases[identity]=dict(technical_passed=False,
                    reason=outcome.get('reason'),error_type=outcome.get('error_type'))
                continue
            comparison=study.artifact(identity,'matched-comparison.json')
            binding=study.artifact(identity,'input-binding.json')
            if (comparison.get('input_binding')!=binding
                    or binding.get('same_measurements_for_all_candidates') is not True
                    or comparison.get('later_observations_opened_after_all_bounds') is not True):
                raise ValueError('shared input or sealed later-data order changed')
            fits={model:study.artifact(identity,'candidates/'+model+'/fit.json')
                  for model in MODELS}
            if (any(fit.get('model')!=model or fit.get('custom_stability_verifier') is not True
                    or fit.get('stability_probe',{}).get('version')!=VERSION
                    for model,fit in fits.items())
                    or comparison.get('convergence')!={model:bool(fits[model]['converged'])
                                                       for model in MODELS}):
                raise ValueError('candidate stop rule or convergence changed')
            target=comparison['receiver_target']
            cases[identity]=dict(technical_passed=True,
                fits={model:dict(converged=bool(fit['converged']),
                    original_full_probe_passed=bool(fit['stability_probe']['original_probe']['passed']),
                    evaluations=fit['evaluations'],cost=fit['residual_sum_squares'],
                    withheld_horizontal_rms_m=target[model]['point_horizontal_rms_m'],
                    withheld_vertical_rms_m=target[model]['point_vertical_rms_m'],
                    whole_path_contained=target[model]['all_later_coordinates_contained'])
                    for model,fit in fits.items()},
                shape=comparison['shape_first']['shape'],
                background_field=comparison['shape_first']['background_field'],
                matched_binding_sha256=hashlib.sha256(study.artifact(
                    identity,'input-binding.json',raw=True)).hexdigest())
        complete=[case for case in cases.values() if case['technical_passed']]
        return dict(version='matched-one-sided-geometry-report-v1',study='data/'+name,
            manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256'],
            report_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            plan_sha256=hashlib.sha256((root/PLAN).read_bytes()).hexdigest(),
            tasks_total=len(expected),technical_passing=len(complete),
            candidate_fits_completed=3*len(complete),
            candidate_fits_converged=sum(sum(fit['converged'] for fit in case['fits'].values())
                                         for case in complete),
            original_full_probes_passed=sum(sum(fit['original_full_probe_passed']
                                                for fit in case['fits'].values())
                                            for case in complete),
            shape_globe=sum(case['shape']=='globe' for case in complete),
            shape_flat=sum(case['shape']=='flat' for case in complete),
            shape_abstain=sum(case['shape']=='abstain' for case in complete),
            cases=cases,new_fits=0,original_reads=0,protected_reads=0,
            empirical_coverage_calibrated=False,aircraft_error_law_qualified=False,
            scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic,encoded
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',required=True)
    parser.add_argument('--preflight',action='store_true')
    args=parser.parse_args(argv)
    output=Path(args.output)
    if output.exists():raise ValueError('fresh verified report required')
    result=build(args.root,preflight=args.preflight)
    atomic(output,encoded(result))
    print(json.dumps({key:result[key] for key in
        ('tasks_total','technical_passing','candidate_fits_converged',
         'shape_globe','shape_flat','shape_abstain')}))


if __name__=='__main__':main()
