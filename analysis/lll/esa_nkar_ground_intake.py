# SPDX-License-Identifier: AGPL-3.0-or-later
"""Screen archived Nuuk Museum coverage against the one sealed aircraft window."""
import argparse
from collections import Counter
from contextlib import ExitStack
import gzip
import json
from math import ceil, floor
from pathlib import Path

from . import esa_shared_motion_carrier as carrier
from .esa_calibration_conditioned_margin import _parent
from .esa_nkar_cadence_study import PARENT_SHA
from .esa_rinex_window import FIRST, LAST, WEEK, read_header as aircraft_header
from .fixed_reference_pair import coverage, observation_blocks
from .fixed_reference_rinex2 import lock_screen, observation_epochs, read_header
from .ilvis0_matched_observed_inputs import _write_equal
from .rinex_archive_decode import decode_archive
from .studies.artifacts import digest, encoded


SOURCE = ('https://data.earthscope.org/archive/gnss/highrate/1-Hz/rinex/'
          '2023/187/nkar/nkar1870.23d.Z?type=file')
TARGETS = tuple(range(ceil(FIRST), floor(LAST)+1))
SCORE_WINDOW = (388614, 388734)


def ground_window(stream, *, retain_measurements=False):
    layout = read_header(stream)
    week, start = layout['first']
    if (layout['marker'].upper() not in {'NKAR', 'NKAR00GRL'} or week != WEEK or not 345600 <= start < 432000
            or layout.get('interval_s', 1.) != 1.):
        raise ValueError('the declared Nuuk Museum station day and one-second cadence are required')
    stations = {}
    for row in observation_epochs(stream, layout, retain_measurements=retain_measurements):
        if (row['week'], row['seconds']) > (WEEK, TARGETS[-1]):
            break
        if (row['week'], row['seconds']) >= (WEEK, TARGETS[0]):
            if row['seconds'] % 1:
                raise ValueError('stated one-second schedule disagrees with recorded epochs')
            stations[(row['week'], row['seconds'])] = row
    return layout, stations


def build(root, original, converter, output):
    with decode_archive(original, converter) as (stream, decoding):
        layout, ground = ground_window(stream)
    with ExitStack() as stack:
        parent, _ = _parent(root, carrier.RESULT, PARENT_SHA, carrier.ID, carrier.TASK, carrier.ARTIFACT, stack)
        frozen_aircraft = parent.input('rinex', raw=True)
        original_completion = parent.completion
    air = gzip.decompress(frozen_aircraft)
    header, aircraft = aircraft_header(air)
    blocks = observation_blocks(air[len(header):], aircraft['observation_types']['G'])
    station = {time: dict(flag=row['flag'], satellites=lock_screen(row['satellites']))
               for time, row in ground.items()}
    rows = coverage(blocks, station, week=WEEK, times=TARGETS, station_interval_s=1.)
    labels = Counter(flag for row in ground.values() for flags in row['satellites'].values() for flag in flags)
    later = [row for row in rows if SCORE_WINDOW[0] <= row['time_s'] <= SCORE_WINDOW[1]]
    matched = [row for row in rows if row['status'] == 'matched']
    receipt = dict(version='esa-nkar-ground-coverage-v2', recording=187, ground_layout=layout, source=SOURCE,
                   original_sha256=decoding['original']['sha256'], expanded_sha256=decoding['expanded']['sha256'],
                   original_to_expanded_verified=True, decoding=decoding,
                   aircraft_input_sha256=digest(frozen_aircraft), aircraft_completion=original_completion,
                   status_counts=dict(Counter(row['status'] for row in rows)), possible_times=len(TARGETS),
                   minimum_common=min((len(row['common']) for row in matched), default=0),
                   maximum_common=max((len(row['common']) for row in matched), default=0),
                   raw_legacy_lock_digit_counts=dict(labels), later=len(later),
                   later_matched=sum(row['status'] == 'matched' for row in later), rows=rows,
                   exact_tracking_codes_established=False, aircraft_accuracy_established=False,
                   protected_reads=0, new_fits=0, scientific_decision='abstain')
    _write_equal(output, encoded(receipt))
    return {key: receipt[key] for key in ('status_counts', 'minimum_common', 'maximum_common', 'later_matched')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('--converter', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(Path.cwd(), args.original, args.converter, args.output), sort_keys=True))
