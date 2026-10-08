# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cheap metadata-only controls for the completion evidence auditor."""
import gzip
import importlib.util
import json
from pathlib import Path
import pytest
from lll import ilvis0 as il, ilvis0_shape as shape, runtime

path=Path(__file__).resolve().parents[2]/'docs/ilvis0-refinement-20261008/package_results.py'
spec=importlib.util.spec_from_file_location('shape_package',path)
package=importlib.util.module_from_spec(spec);spec.loader.exec_module(package)


def dump(path,value):path.write_text(json.dumps(value,sort_keys=True,allow_nan=False))


def save_result(path,value,digest):
    dump(path,dict(manifest_sha256=digest,result=value,result_sha256=package.result_hash(value)))


def persist(source,summary):
    digest=il.sha256(source/'manifest.json')
    for row in summary['results']:
        save_result(source/(row['task']+'.json'),row,digest)
        for case in row['cases']:
            for fit in case['fits']:
                identity=row['task']+'::'+case['case_id']+'::'+fit['model']
                save_result(source/(identity.replace('::','-')+'.json'),fit,digest)
    with gzip.open(source/'summary.json.gz','wt') as stream:json.dump(summary,stream,allow_nan=False)
    dump(source/'completion.json',dict(state='complete',files=6,starts=72,
        converged_fits=72,failed_fits=0,manifest_sha256=digest,summary_sha256=il.sha256(source/'summary.json.gz')))


@pytest.fixture
def evidence(tmp_path):
    cases=[dict(case_id=f'bias{b:g}_'+str(p),constant_gyro_bias_bound_dph=b,fit_earth_removal=p)
           for b in (.1,1.) for p in (False,True)]
    tasks=[f't{i}' for i in range(6)]
    identities=[t+'::'+c['case_id']+'::'+m for t in tasks for c in cases for m in shape.explore.MODELS]
    manifest=dict(maximum_files=6,primary_starts=72,maximum_starts=84,maximum_starts_per_identity=2,
        maximum_evaluations_per_start=200,sources={},inputs={},environment=runtime.numerical_environment(),
        tasks=tasks,cases=cases,identities=identities)
    dump(tmp_path/'manifest.json',manifest);digest=il.sha256(tmp_path/'manifest.json')
    starts=[dict(start=i+1,identity=identity,manifest_sha256=digest,maximum_evaluations=200)
            for i,identity in enumerate(identities)]
    (tmp_path/'starts.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in starts))
    results=[];index=0
    for task in tasks:
        per_file=[]
        for case in cases:
            fits=[]
            for model,cost in zip(shape.explore.MODELS,(3.,5.,10.)):
                fits.append(dict(model=model,case_id=case['case_id'],evaluations=4,
                    residual_sum_squares=cost,converged=True,solver_reported_success=True,
                    exact_projected_gradient_relative=1e-6,scientific_decision='abstain',start_charge=starts[index]))
                index+=1
            per_file.append(dict(case_id=case['case_id'],fits=fits))
        results.append(dict(task=task,filename=task+'.013',cases=per_file,
            profile=shape.hierarchical_profile(per_file),original_preserved=True))
    summary=dict(state='complete',files=6,starts=72,converged_fits=72,failed_fits=0,results=results,
        scientific_shape_decision='abstain',scientific_rotation_decision='abstain',originals_deleted=0)
    persist(tmp_path,summary)
    return tmp_path,summary


def test_audits_complete_matched_profiles_and_charged_starts(evidence):
    source,_=evidence
    assert package.audit(source)[3]==dict(fits=72,charged_starts=72,
        unreferenced_interrupted_starts=0,converged_fits=72,failed_fits=0)


def test_rejects_internally_consistent_over_budget_fit(evidence):
    source,summary=evidence
    summary['results'][0]['cases'][0]['fits'][0]['evaluations']=201
    persist(source,summary)
    with pytest.raises(ValueError,match='budget'):package.audit(source)


def test_rejects_tampered_result_even_when_summary_hash_valid(evidence):
    source,_=evidence
    path=source/'t0.json';row=package.load(path);row['result']['original_preserved']=False
    dump(path,row)
    with pytest.raises(ValueError,match='integrity'):package.audit(source)


def test_rejects_forged_rotation_stage_in_a_consistent_saved_report(evidence):
    source,summary=evidence
    summary['results'][0]['profile']['rotation_diagnostics'][0]['conditional_still_minus_rotating_cost']=999.
    persist(source,summary)
    with pytest.raises(ValueError,match='hierarchy'):package.audit(source)
