# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bind an empirical transfer reference to saved first-cut forecast errors.

The source CSV also contains later-cut scores. This reader deliberately ignores
them. The output is descriptive and cannot be used as a coverage threshold.
"""
import csv
import hashlib
import io
import math
import re


AXES = ('north', 'east', 'vertical')
CLOCKS = ('header_elapsed', 'nominal_200Hz')
PROFILES = ('False', 'True')


def from_saved_csv(raw, *, expected_sha256):
    if (not isinstance(raw, bytes) or not isinstance(expected_sha256, str)
            or re.fullmatch('[0-9a-f]{64}', expected_sha256) is None):
        raise ValueError('saved bytes and frozen SHA-256 required')
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise ValueError('saved rolling-origin result differs from freeze')
    try:
        reader = csv.DictReader(io.StringIO(raw.decode('utf-8')))
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError('valid saved rolling-origin CSV required') from error
    required = {'segment_id', 'profile', 'clock', 'inner_identity',
                *(axis + '_inner_rms_m' for axis in AXES)}
    if (reader.fieldnames is None or not required.issubset(reader.fieldnames)
            or len(rows) != 12):
        raise ValueError('complete twelve-setting development result required')
    keys = set()
    segments = set()
    selected = {}
    for row in rows:
        segment = row['segment_id']
        profile = row['profile']
        clock = row['clock']
        key = segment, profile, clock
        if (not segment or profile not in PROFILES or clock not in CLOCKS
                or key in keys):
            raise ValueError('distinct complete development setting grid required')
        keys.add(key)
        segments.add(segment)
        if (profile, clock) != ('False', 'header_elapsed'):
            continue
        identity = row['inner_identity']
        if not identity:
            raise ValueError('passing first-cut primary required')
        values = {}
        for axis in AXES:
            try:
                value = float(row[axis + '_inner_rms_m'])
            except (TypeError, ValueError) as error:
                raise ValueError('complete first-cut errors required') from error
            if not math.isfinite(value) or value <= 0:
                raise ValueError('finite positive first-cut errors required')
            values[axis] = value
        selected[segment] = dict(identity=identity, rms_m=values)
    if (len(segments) != 3 or len(selected) != 3 or
            keys != {(segment, profile, clock)
                     for segment in segments for profile in PROFILES for clock in CLOCKS}):
        raise ValueError('three complete development recordings required')
    return dict(version='prediction-transfer-reference-v1',
                source_sha256=actual, recordings=3, settings=12,
                chosen_clock='header_elapsed', chosen_processing_case='no_removal',
                selected_inner_identities={key: selected[key]['identity']
                                           for key in sorted(selected)},
                reference_rms_m={axis: max(row['rms_m'][axis]
                                           for row in selected.values())
                                 for axis in AXES},
                rule='axiswise maximum of three training-selected first-cut RMS errors',
                later_cut_scores_used=False, coverage_calibrated=False,
                scientific_decision='abstain')
