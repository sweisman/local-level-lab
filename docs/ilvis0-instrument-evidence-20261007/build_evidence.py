# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inventory hash-verified cached metadata; never read originals or fit models."""
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    with gzip.open(path, 'rt') if path.suffix == '.gz' else path.open() as stream:
        return json.load(stream)


def main():
    evidence = Path(__file__).resolve().parent
    root = evidence.parents[1]
    prior = root/'docs/ilvis0-processing-v2-20261007'
    completion = load(prior/'completion.json')
    if completion['state'] != 'complete' or completion['source_audit_errors'] != 0:
        raise ValueError('completed error-free preceding metadata audit required')
    for name,key in (('manifest.json','manifest_sha256'), ('summary.json.gz','summary_sha256')):
        if sha(prior/name) != completion[key]:
            raise ValueError('preceding evidence hash mismatch')
    manifest = load(prior/'manifest.json'); summary = load(prior/'summary.json.gz')
    tasks = {r['task_id']:r for r in manifest['tasks']}
    results = summary['results']
    if (len(tasks) != 6 or len(results) != 6
            or len({r['task_id'] for r in results}) != 6
            or {r['task_id'] for r in results} != set(tasks)):
        raise ValueError('exact six cached representatives required')
    rows = []
    for r in results:
        task = tasks[r['task_id']]
        if (r['filename'] != task['filename'] or r['source_sha256'] != task['source_sha256']
                or r['frame_counts'] != task['expected_frame_counts']):
            raise ValueError('metadata identity mismatch')
        if (any(r['independence'][k] for k in ('calibration_bounds_established',
                'earth_rate_retention_established','processing_independence_established'))
                or r['clock']['physical_integration_clock_established']):
            raise ValueError('unexpected promoted historical evidence')
        if len(r['versions']) != 1:
            raise ValueError('unexpected version change')
        version = next(iter(r['versions']))
        if not version.startswith('AV-510,VER5,') or ',IMU6,' not in version:
            raise ValueError('unexpected instrument scope')
        rows.append(dict(task_id=r['task_id'], filename=r['filename'],
            embedded_dates=';'.join(task['embedded_dates']), source_sha256=r['source_sha256'],
            version_string=version, hardware_family_inference='consistent with LN-200 family',
            exact_installed_variant_verified=False, calibration_bounds_established=False,
            processing_independence_established=False, physical_integration_clock_established=False,
            earth_rate_retention_established=False, empirical_earth_fit_attempts=0))
    with (evidence/'inventory.csv').open('w', newline='') as stream:
        writer=csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    angle=math.pi/(180*9000); velocity=3.38e-5
    scales=dict(applanix_empirical_angle_rad_per_count=angle,
        applanix_empirical_velocity_mps_per_count=velocity,
        novatel_RAWIMUSX_LN200_angle_rad_per_count=2**-19,
        novatel_RAWIMUSX_LN200_velocity_mps_per_count=2**-14,
        angle_relative_difference=angle/(2**-19)-1,
        velocity_relative_difference=velocity/(2**-14)-1,
        identical_output_encoding=False, hardware_identity_disproved=False,
        manufacturer_scale_applied_to_legacy_decoder=False)
    inputs={str((prior/n).relative_to(root)):sha(prior/n)
            for n in ('manifest.json','completion.json','summary.json.gz')}
    local=['README.md','QUESTIONS.md','sources.json','build_evidence.py','inventory.csv']
    receipt=dict(version='ilvis0-instrument-evidence-review-v1', state='complete',
        reviewed_on='2026-10-07', verified_cached_files=len(rows),
        inputs_sha256=inputs, artifact_sha256={n:sha(evidence/n) for n in local},
        independent_hardware_family_support='published POS AV510/IMU-6 Litton-200 association',
        exact_installed_variants_verified=0, new_independent_calibration_bounds=0,
        numerical_scale_comparison=scales, originals_scanned=0, originals_deleted=0,
        empirical_earth_fit_attempts=0, scientific_eligibility_changes=0, messages_sent=0)
    (evidence/'evidence-receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(verified_cached_files=len(rows), empirical_earth_fit_attempts=0,
        angle_relative_difference=scales['angle_relative_difference'],
        velocity_relative_difference=scales['velocity_relative_difference'])))


if __name__ == '__main__':
    main()
