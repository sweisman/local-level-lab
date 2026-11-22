# SPDX-License-Identifier: AGPL-3.0-or-later
"""Summarize a sealed matched-candidate generated study without refitting."""

import hashlib
import json
from pathlib import Path

from .matched_candidate_generated_study import (
    ID,PREFLIGHT_ID,SCOPE,PREFLIGHT_SCOPE,PLAN,recipe,preflight_recipe,tasks)
from .matched_candidate_case import MODELS


def build(root,*,preflight=False):
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    name=PREFLIGHT_ID if preflight else ID
    expected_recipe=preflight_recipe() if preflight else recipe()
    expected_tasks={task['identity'] for task in tasks(expected_recipe)}
    study=ClosedStudy(root,'data/'+name)
    try:
        if (study.completion['state'] not in ('complete','terminal')
                or study.manifest.get('scope')!=
                    (PREFLIGHT_SCOPE if preflight else SCOPE)
                or study.input('recipe')!=expected_recipe
                or set(study.tasks)!=expected_tasks):
            raise ValueError('sealed exact matched-candidate study required')
        cases={}
        for identity in sorted(expected_tasks):
            row=study.rows.get(identity)
            if row is None or row['status']!='complete':
                cases[identity]=dict(technical_passed=False,
                                     status=None if row is None else row['status'])
                continue
            outcome=study.envelope(identity)['result']
            if (outcome.get('technical_passed') is not True
                    or outcome.get('passed') is not True
                    or outcome.get('candidate_fits')!=3
                    or outcome.get('original_reads')!=0
                    or outcome.get('protected_reads')!=0
                    or outcome.get('scientific_decision')!='abstain'):
                raise ValueError('changed matched-candidate outcome')
            comparison=study.artifact(identity,'matched-comparison.json')
            binding=study.artifact(identity,'input-binding.json')
            if (comparison.get('later_observations_opened_after_all_bounds') is not True
                    or comparison.get('scientific_decision')!='abstain'
                    or binding!=comparison.get('input_binding')
                    or binding.get('same_measurements_for_all_candidates') is not True
                    or set(comparison['convergence'])!=set(MODELS)
                    or set(comparison['contrast']['covered'])!=set(MODELS)):
                raise ValueError('changed common input or later-data isolation')
            for model in MODELS:
                for target in ('physical','receiver'):
                    bound=study.artifact(identity,
                                         'candidates/'+model+'/bounded-'+target+'.json')
                    if (bound.get('prediction_target')!=
                            ('physical_position' if target=='physical'
                             else 'receiver_measurement')
                            or bound.get('nominal_joint_coverage_lower_bound')!=.95
                            or bound.get('later_observations_used') is not False):
                        raise ValueError('changed three-model simultaneous bound')
            cases[identity]=dict(
                technical_passed=True,
                numerical_converged=comparison['convergence'],
                receiver_covered=comparison['contrast']['covered'],
                shape=comparison['shape_first']['shape'],
                background_field=comparison['shape_first']['background_field'],
                receiver_horizontal_rms_m={model:
                    comparison['receiver_target'][model]['point_horizontal_rms_m']
                    for model in MODELS},
                comparison_sha256=hashlib.sha256(study.artifact(
                    identity,'matched-comparison.json',raw=True)).hexdigest())
        complete=[row for row in cases.values() if row['technical_passed']]
        return dict(version='matched-candidate-generated-report-v1',
                    study='data/'+name,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    report_source_sha256=hashlib.sha256(
                        Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root/PLAN).read_bytes()).hexdigest(),
                    tasks_total=len(expected_tasks),technical_passing=len(complete),
                    candidate_fits_completed=3*len(complete),
                    candidate_fits_converged=sum(
                        sum(row['numerical_converged'].values()) for row in complete),
                    shape_globe=sum(row['shape']=='globe' for row in complete),
                    shape_flat=sum(row['shape']=='flat' for row in complete),
                    shape_abstain=sum(row['shape']=='abstain' for row in complete),
                    cases=cases,new_fits=0,original_reads=0,protected_reads=0,
                    empirical_coverage_calibrated=False,
                    aircraft_error_law_qualified=False,
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
    if output.exists():
        raise ValueError('fresh verified report required')
    result=build(args.root,preflight=args.preflight)
    atomic(output,encoded(result))
    print(json.dumps({key:result[key] for key in
                      ('tasks_total','technical_passing',
                       'candidate_fits_converged','shape_globe',
                       'shape_flat','shape_abstain')}))


if __name__=='__main__':
    main()
