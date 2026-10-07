import gzip
import json
from pathlib import Path
import numpy as np
from lll import ilvis0_imu6 as audit

root=Path.cwd()
data=root/'data/ilvis0-imu6-cross-date-20261007'
summary=json.loads((data/'summary.json').read_text())
for source, expected in json.loads((data/'manifest.json').read_text())['sources'].items():
    assert audit.il.sha256(Path(source)) == expected, 'frozen decoder source changed'
reports=[]
for prior in summary['results']:
    artifact=data/prior['matched_artifact']
    assert audit.il.sha256(artifact)==prior['matched_artifact_sha256']
    with gzip.open(artifact,'rt') as source:
        samples=json.load(source)['samples']
    middle=len(samples)//2
    discovery=audit.validate_samples(samples[:middle])
    holdout=audit.validate_samples(samples[middle:], discovery['mapping'],
                                  discovery['frozen_empirical_velocity_scale_mps_per_count'])
    force=np.asarray([s['force'] for s in samples])[:,discovery['mapping']['permutation']]*discovery['mapping']['signs']
    gravity=np.asarray([s['gravity'] for s in samples])
    design=np.zeros((3*len(force),7))
    for j in range(3):
        design[j::3,j]=force[:,j]
        design[j::3,j+3]=1
    design[:,6]=gravity.reshape(-1)
    norms=np.linalg.norm(design,axis=0)
    singular=np.linalg.svd(design/norms,compute_uv=False)
    reports.append(dict(task_id=prior['task_id'],filename=prior['filename'],
                        original_fixed_mapping_gyro_pass=prior['gyro_scale_validated'],
                        original_fixed_mapping=prior['mapping'],
                        chronological_first_half_mapping=discovery['mapping'],
                        chronological_first_half_gyro_pass=discovery['gyro_scale_validated'],
                        chronological_second_half_gyro_pass=holdout['gyro_scale_validated'],
                        holdout_gyro=holdout['gyro'],
                        normalized_force_design_condition=float(singular[0]/singular[-1]),
                        scientific_eligible=False,original_failure_preserved=True))
result=dict(version='ilvis0-imu6-axis-change-diagnostic-v1',
            method='Each existing matched-sample artifact: discover mapping on first chronological half, test frozen mapping on second. Original cross-date result is unchanged.',
            input_manifest_sha256=audit.il.sha256(data/'manifest.json'),
            input_summary_sha256=audit.il.sha256(data/'summary.json'),
            generator_sha256=audit.il.sha256(Path(__file__)),
            diagnostic_only=True,results=reports,scientific_eligibility_changes=0)
audit.follow.atomic_json(data/'axis-change-supplement.json',result)
for r in reports:
    print(r['filename'],r['chronological_first_half_mapping'],r['chronological_second_half_gyro_pass'],r['normalized_force_design_condition'])
