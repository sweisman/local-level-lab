# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the RF04 development chain using only published repository evidence."""

from contextlib import closing
import gzip
import json
import math
from pathlib import Path

from .studies.artifacts import ArchiveStore, digest
from .studies.closed import ClosedStudy


FOLDER = 'docs/ilvis0-measurement-contribution'
RF04_HASH = '31fccac2fbc36473e8d1bdb158f067c832bf04e05f8d2fd5db137eaa02039d70'
APPLANIX_HASH = '02459608f57b1b266e25daefcd9e5190515e1a046c0f633474604d1877a3ac75'
REPORTS = {
    'motion-match': ('64213fd0ad7f06673683245c0f0df4a3768fc6f4ceda48a879ff302742a6f38b', 21, {}),
    'receiver-offset': ('6a6f5bd0ff028568305350ce6bd1a972c11e834f39a5023fdeb105fe0394d861', 5,
                        {'parent': 'motion-match'}),
    'force-direction': ('3c8c83c60d324969f065b453eb56dce5c97065f00a9d82b52490b5d04ba3f60f', 41,
                        {'motion': 'motion-match'}),
    'force-average': ('a687d34bdf03de7909985aa32704d12aeb1a4c63ea7d9356cadc0d705bb6d587', 81,
                      {'direction': 'force-direction'}),
    'reference-acceleration': ('073a07459f2322fec3cde01963c5efee1a4d6531d4c34087484e08a7471cd052', 19,
                               {'averaged': 'force-average', 'offset': 'receiver-offset'}),
    'velocity-resolution': ('f7d3b25dee6935d195a09d827ff3cabc3bf76fa9179660e3b969d2852337af26', 9,
                            {'previous': 'reference-acceleration'}),
    'antenna-motion': ('a73f186d7ad43333e2469484504dd7263923c427d246809c3d2e036ad5a96fa6', 7,
                       {'previous': 'reference-acceleration', 'resolution': 'velocity-resolution'}),
}
SHARED_INPUTS = ('rf04', 'layout', 'freeze', 'recorded', 'velocity', 'speed-course')


def bind_result(stage, report, envelope, completion, operations):
    public = {key: val for key, val in report.items() if key not in ('charged', 'completion')}
    charge = envelope['charged']
    if (completion['state'] != 'complete' or report['completion'] != completion
            or report['charged'] != charge or charge['bound_calls'] != operations
            or charge['native_calls'] != 0 or charge['packet_visits'] != 0
            or envelope['result'] != public or public['passed'] is not True
            or public['new_fits'] != 0 or public['reserved_reads'] != 0
            or public.get('original_imu_reads', 0) != 0 or public['scientific_decision'] != 'abstain'):
        raise ValueError(f'RF04 result or charge record differs for {stage}')


def finite_pair(pair):
    return len(pair) == 2 and all(type(value) in (int, float) and math.isfinite(value) for value in pair)


def compare_rows(attitude, velocity, epochs):
    if len(attitude) != epochs or len(velocity) != epochs or any(
        left['utc'] != right['utc'] or left['GGSTATUS'] != 1 or right['status'] != 1
        or not finite_pair(right['velocity_ne_mps'])
        for left, right in zip(attitude, velocity, strict=True)
    ):
        raise ValueError('the independent RF04 receiver rows differ')


def _verify_publication(study, identity, stage):
    receipt = study.read('evidence-receipt.json')['artifacts']
    if set(study.tasks) != {identity} or set(study.rows) != {identity}:
        raise ValueError(f'exactly one completed task required for {stage}')
    row, envelope = study.rows[identity], study.envelope(identity)
    if (row['charged'] != envelope['charged'] or study.summary['charged'] != envelope['charged']
            or study.tasks[identity]['limits'] != envelope['charged']
            or study.manifest['allocation'] != dict(workers=1, threads=1, reserved=0, total=1)):
        raise ValueError(f'RF04 allocation or accounting differs for {stage}')
    expected = {'manifest.json': study.completion['manifest_sha256'],
                'summary.json': study.completion['summary_sha256'], row['artifact']: row['artifact_sha256']}
    expected.update({'source-freeze/'+name: sha for name, sha in study.manifest['sources'].items()})
    expected.update({value['path']: value['sha256'] for value in study.manifest['inputs'].values()})
    expected.update(envelope['artifacts'])
    required = {'completion.json', 'authorization.json', 'start.json', 'start.seal.json',
                str(Path(row['artifact']).with_suffix('.seal.json'))}
    if not required <= receipt.keys() or any(receipt.get(name) != sha for name, sha in expected.items()):
        raise ValueError(f'RF04 evidence receipt is incomplete or mismatched for {stage}')
    for name, sha in receipt.items():
        study.read(name, sha, raw=True)
    return envelope, dict(receipt_members=len(receipt), sources=len(study.manifest['sources']),
                          inputs=len(study.manifest['inputs']))


def verify(root):
    root = Path(root)
    reports, shared, inputs = {}, {}, {}
    counts = dict(receipt_members=0, sources=0, inputs=0, charged_operations=0)
    with closing(ArchiveStore(root)) as store:
        for stage, (sha, operations, parents) in REPORTS.items():
            base = 'rf04-'+stage
            raw = (root/FOLDER/(base+'-result.json')).read_bytes()
            if digest(raw) != sha:
                raise ValueError(f'RF04 public report digest differs for {stage}')
            report = json.loads(raw)
            prefix = f'{FOLDER}/{base}-evidence'
            with closing(ClosedStudy(root, prefix, store=store)) as study:
                identity = 'rf04' if stage == 'motion-match' else base
                envelope, members = _verify_publication(study, identity, stage)
                bind_result(stage, report, envelope, study.completion, operations)
                if stage == 'motion-match':
                    original = gzip.decompress(study.input('applanix', raw=True))
                    if digest(original) != APPLANIX_HASH or len(original) != report['source']['source_bytes']:
                        raise ValueError('archived Applanix source bytes differ')
                for key, upstream in parents.items():
                    if study.input(key, raw=True) != reports[upstream]:
                        raise ValueError(f'RF04 upstream report differs for {stage}: {key}')
                for key in SHARED_INPUTS:
                    if key in study.manifest['inputs']:
                        source_hash = study.manifest['inputs'][key]['sha256']
                        if shared.setdefault(key, source_hash) != source_hash:
                            raise ValueError(f'RF04 derived input changed across checks: {key}')
                        if key in ('rf04', 'velocity', 'speed-course') and key not in inputs:
                            inputs[key] = study.input(key)
                for key, value in members.items():
                    counts[key] += value
            counts['charged_operations'] += operations
            reports[stage] = raw

    motion = json.loads(reports['motion-match'])
    if (motion['source']['source_sha256'] != APPLANIX_HASH or motion['source']['group1_observations_used']
            or motion['matched_receiver_seconds'] != 443 or motion['rf04_sha256'] != RF04_HASH
            or inputs['rf04']['sha256'] != RF04_HASH or inputs['velocity']['source_sha256'] != RF04_HASH
            or inputs['speed-course']['source_sha256'] != RF04_HASH
            or inputs['rf04']['attitude_epochs'] != 443 or len(inputs['speed-course']['values']) != 443
            or not all(finite_pair(pair) and pair[0] > 0 and 0 <= pair[1] <= 360
                       for pair in inputs['speed-course']['values'])):
        raise ValueError('the two original RF04 recording identities and support are required')
    compare_rows(inputs['rf04']['rows'], inputs['velocity']['rows'], 443)
    average = json.loads(reports['force-average'])
    acceleration = json.loads(reports['reference-acceleration'])
    support = average['support'][0]['seconds_after_start']
    if (len(support) != 383 or len(average['scores']) != 32 or len(average['comparisons']) != 48
            or {row['width_s'] for row in average['support']} != {.25, 1.}
            or {row['width_s'] for row in acceleration['selection']} != {2, 6, 10}
            or any(row['earlier'] != 265 or row['seconds_after_start'] != support
                   for row in average['support']+acceleration['selection'])):
        raise ValueError('RF04 original earlier and later windows differ')
    return dict(counts, studies=len(reports), receiver_epochs=443, earlier_centers=265, later_centers=118,
                earth_model_fit_starts=0, reserved_esa_reads=0, scientific_decision='abstain')


if __name__ == '__main__':
    import argparse

    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(verify(Path.cwd()), sort_keys=True))
