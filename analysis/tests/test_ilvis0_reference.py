# SPDX-License-Identifier: AGPL-3.0-or-later
"""Regression against compact, historical reference evidence; no Downloads dependency."""
from collections import Counter
import gzip
from pathlib import Path
import json
import numpy as np
from lll import applanix as ap
from lll.ilvis0 import validate_arrays

CORPUS = Path(__file__).resolve().parents[2] / 'docs' / 'research-next-stage-20261006' / 'airborne-sample-ilvis0'
VALIDATION = Path(__file__).resolve().parents[2] / 'docs' / 'ilvis0-physical-validation-20261007'


def test_reference_stream_framing_gps_counts_and_version():
    counts, versions, decoder, sentences = Counter(), Counter(), ap.NMEA(), Counter()
    with gzip.open(CORPUS / 'ILVIS0_gyro_54935_atm_applanix_14Apr09.013.gz', 'rb') as stream:
        for frame in ap.frames(stream):
            counts[f'{frame.tag}:{frame.group}'] += 1
            if frame.tag == '$GRP' and frame.group == 99:
                versions[ap.group99(frame)] += 1
            if frame.tag == '$GRP' and frame.group == 10001:
                _, chunk = ap.group10001(frame)
                for sentence in decoder.feed(chunk):
                    assert sentence['valid']
                    if sentence['valid']:
                        sentences[sentence['fields'][0]] += 1
    assert sum(counts.values()) == 143471
    assert counts['$GRP:4'] == 132444
    assert counts['$GRP:1'] == 662
    assert counts['$GRP:10001'] == 5934
    assert all(sentences['GP' + kind] == 660 for kind in ('GGA', 'VTG', 'ZDA'))
    assert decoder.finish()['invalid_checksums'] == 0
    assert all('AV-510' in version and 'SW04.60' in version and 'ICD15.00' in version for version in versions)


def test_reference_matched_increments_independent_validation():
    samples = json.loads((VALIDATION / 'reference-matches.json').read_text())['samples']
    assert len(samples) == 662
    gyro = validate_arrays([r['gyro'] for r in samples], [r['gyro_reference'] for r in samples], ap.DELTA_ANGLE_SCALE)
    force = validate_arrays([r['force'] for r in samples], [r['acceleration_reference'] for r in samples], ap.DELTA_V_SCALE, [r['gravity'] for r in samples])
    assert gyro['accepted'] and force['accepted']
    assert all(abs(r['error']) == 0 for r in samples)
    assert min(r['correlation'] for r in gyro['axes']) > .9999995
    assert min(r['correlation'] for r in force['axes']) > .999997
