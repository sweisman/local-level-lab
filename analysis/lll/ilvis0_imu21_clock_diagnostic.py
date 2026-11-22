# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay failed IMU21 decoder checks with two fixed period conventions."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import platform

import numpy as np

from . import ilvis0
from .ilvis0_assessment import ANGLE_SCALE, VELOCITY_SCALE
from .ilvis0_followup import source_path
from .ilvis0_matched_observed_inputs import FOLDER, _write_equal
from .studies.artifacts import digest, encoded


SOURCE = 'analysis/lll/ilvis0_imu21_clock_diagnostic.py'
TEST = 'analysis/tests/test_ilvis0_imu21_clock_diagnostic.py'
PLAN = FOLDER+'NORTHERN_IMU21_CLOCK_PLAN.md'
FREEZE = FOLDER+'northern-imu21-clock-freeze.json'
RESULT = FOLDER+'northern-imu21-clock-receipt.json'
ENGINEERING = 'docs/ilvis0-imu21-assessment-20261007/summary.json.gz'
CORPUS = 'data/ilvis0-ready'
LIMIT = 4000
MAX_SOURCE_BYTES = 54_000_000
CLOCKS = ('header_elapsed', 'nominal_200Hz')
EXPECTED = ('d0e3a956ede05ba381c3', '6d07c5ae81f6c1fada88', '397f6c3a7f6f34592195', '803fc652962ade07d350')


def normalized(rows, clock):
    counts = np.asarray([row['raw_increments'] for row in rows], float)
    period = np.asarray([row['dt'] for row in rows], float)
    if (clock not in CLOCKS or counts.shape != (len(rows), 6) or not len(rows)
            or np.any(~np.isfinite(counts)) or np.any(~np.isfinite(period)) or np.any(period <= 0.)):
        raise ValueError('finite aligned raw increments and supported periods required')
    if clock == 'nominal_200Hz':
        period = np.full_like(period, .005)
    normalized_counts = counts/period[:, None]
    return normalized_counts[:, 3:], normalized_counts[:, :3]


def _inputs(root):
    raw = (root/ENGINEERING).read_bytes()
    evidence = json.loads(gzip.decompress(raw))
    config = next(row for row in evidence['configurations'] if 'S/N3456,' in row['configuration'])
    outcomes = {row['task_id']: row for row in evidence['physical_results'] if row['task_id'] in config['members']}
    failed = {key for key, value in outcomes.items() if not value['accepted']}
    if (failed != set(EXPECTED[:-1]) or config['representatives'] != [EXPECTED[0], EXPECTED[-1]]
            or config['reproduced_on_two_dates'] or not outcomes[EXPECTED[-1]]['accepted']):
        raise ValueError('unchanged failed northern decoder controls required')
    entries = {}
    for line in (root/CORPUS/'records.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row['task_id'] in EXPECTED and 'source_sha256' in row and not row['cleanup_pending']:
            entries[row['task_id']] = row
    if set(entries)!=set(EXPECTED) or sum(row['source_bytes'] for row in entries.values())>MAX_SOURCE_BYTES:
        raise ValueError('four bounded preserved engineering sources required')
    material = []
    for identity in EXPECTED:
        row, prior = entries[identity], outcomes[identity]
        path = source_path(root/CORPUS, row)
        if (row['source_sha256']!=prior['source_sha256'] or prior['reference_status']!='full_navigation'
                or not prior['mapping_matches_fixed'] or prior['dates']!=[row['date']]):
            raise ValueError('changed engineering source, reference or axis mapping')
        material.append((dict(identity=identity, date=row['date'], path=path.relative_to(root).as_posix(),
                              source_sha256=row['source_sha256'], original_bytes=row['source_bytes']), prior))
    return raw, material, config['mapping']


def _channel(result):
    return dict(accepted=result['accepted'], engineering_pass=result['engineering_checks_pass'],
        chronological_pass=result['holdout_scale_checks_pass'], scale_ratios=[row['scale_ratio'] for row in result['axes']],
        holdout_scale_ratios=[row['scale_ratios'] for row in result['chronological_holdouts']])


def _replay(root, source, prior, mapping):
    path = root/source['path']
    hashed = hashlib.sha256()
    size = 0
    with ilvis0.open_source(path) as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            size += len(chunk)
            if size>source['original_bytes']:
                raise ValueError('uncompressed source allowance exceeded')
            hashed.update(chunk)
    if size!=source['original_bytes'] or hashed.hexdigest()!=source['source_sha256']:
        raise ValueError('changed preserved decoder source')
    samples, total = ilvis0.matched_samples(path, limit=LIMIT, imu_types=(21,))
    if len(samples)!=prior['samples'] or total!=prior['matched_total'] or total>LIMIT:
        raise ValueError('changed full-navigation match or sample allowance')
    permutation, signs = mapping['permutation'], mapping['signs']
    target = np.asarray([row['gyro_reference'] for row in samples])
    force = np.asarray([row['acceleration_reference'] for row in samples])
    gravity = np.asarray([row['gravity'] for row in samples])
    results = {}
    for clock in CLOCKS:
        gyro_rate, force_rate = normalized(samples, clock)
        results[clock] = dict(
            gyro=_channel(ilvis0.validate_arrays(gyro_rate[:, permutation]*signs, target, ANGLE_SCALE)),
            accelerometer=_channel(ilvis0.validate_arrays(force_rate[:, permutation]*signs, force, VELOCITY_SCALE, gravity)))
    for channel in ('gyro', 'accelerometer'):
        original = _channel(prior[channel])
        replay = results[CLOCKS[0]][channel]
        if (any(replay[key]!=original[key] for key in ('accepted', 'engineering_pass', 'chronological_pass'))
                or not np.allclose(replay['scale_ratios'], original['scale_ratios'], rtol=1e-10, atol=1e-12)
                or not np.allclose(replay['holdout_scale_ratios'], original['holdout_scale_ratios'], rtol=1e-10, atol=1e-12)):
            raise ValueError('header-clock engineering result does not replay')
    scale = np.asarray([row['dt']/.005-1. for row in samples])*1e6
    return dict(source, samples=total, original_pass=prior['accepted'], clocks=results,
                period_difference_ppm=dict(minimum=float(scale.min()), median=float(np.median(scale)), maximum=float(scale.max())))


def main():
    from .studies.dependencies import source_closure

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    args = parser.parse_args()
    root = Path.cwd()
    raw, material, mapping = _inputs(root)
    config = encoded(dict(parent_sha256=digest(raw), originals=[row for row, _ in material], mapping=mapping,
        sources={name:digest((root/name).read_bytes()) for name in source_closure(root, (SOURCE, TEST, PLAN))},
        python=platform.python_version(), numpy=np.__version__, numerical_threads=1,
        source_byte_cap=MAX_SOURCE_BYTES, sample_cap=LIMIT, fit_starts=0, clocks=CLOCKS))
    if args.action=='freeze':
        _write_equal(root/FREEZE, config)
        print(digest(config))
        return
    if (root/FREEZE).read_bytes()!=config:
        raise ValueError('decoder comparison differs from the frozen controls')
    rows = [_replay(root, source, prior, mapping) for source, prior in material]
    receipt = dict(freeze_sha256=digest(config), by_file=rows, scientific_eligibility_changes=0,
                   fused_navigation_role='decoder engineering only', fit_starts=0, scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(receipt))
    print(json.dumps(dict(files=len(rows), receipt_sha256=digest(encoded(receipt)))))


if __name__=='__main__':
    main()
