# SPDX-License-Identifier: AGPL-3.0-or-later
"""Seal a previously acquired AIR1 GPS excerpt inside the selected iMAR ground stop."""

import argparse
import gzip
import json
from pathlib import Path

from . import esa_apron_carrier as apron
from . import esa_rinex_window as rinex
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


PLAN = rinex.FOLDER+'ESA_APRON_IMU_OVERLAP_ACQUISITION_PLAN.md'
REPORT = rinex.FOLDER+'esa-apron-imu-overlap-acquisition.json'
LOCAL = rinex.LOCAL+'/apron-imu-overlap'
FIRST, LAST = 385020., 385140.
PROBE, START = 15_100_000, 15_750_000
SECOND = START+rinex.CHUNK-rinex.OVERLAP
GROUND_SHA = 'e587348ea92fd3918183bd2b7986e959b4038e77134fc1ded72396fd4e8a12e3'
NAMES = {offset: f'lll-esa187-apron-rest-{offset}.bin' for offset in (PROBE, START, SECOND)}


def join_overlap(left, right, *, length, overlap):
    if (not 0 < overlap < length or len(left) != length or len(right) != length
            or left[-overlap:] != right[:overlap]):
        raise ValueError('fixed-length transfers with exact and identical overlap required')
    return left+right[overlap:]


def seal(root, cache, exits):
    if len(exits) != 3 or any(code not in (0, 28) for code in exits):
        raise ValueError('only successful or final-reply-timeout transfers are qualified')
    prefix = (root/apron.PREFIX).read_bytes()
    ground_raw = (root/apron.GROUND).read_bytes()
    listing = (root/rinex.LOCAL/'catalog/lvl0-187-air1-list.txt').read_bytes()
    if digest(prefix) != rinex.PREFIX_SHA or digest(ground_raw) != GROUND_SHA or digest(listing) != rinex.LISTING_SHA:
        raise ValueError('the original header, ground stop and source listing must reproduce')
    ground = json.loads(ground_raw)
    if not ground['imu_overlap_time_s'][0] <= FIRST < LAST <= ground['imu_overlap_time_s'][1]:
        raise ValueError('the window must remain inside the published ground IMU overlap')
    header, layout = rinex.read_header(prefix)
    transfers = {}
    reports = []
    for (offset, name), code in zip(NAMES.items(), exits, strict=True):
        requested = rinex.PROBE if offset == PROBE else rinex.CHUNK
        path = cache/name
        if path.stat().st_size != requested:
            raise ValueError('complete requested transfer bytes required: '+name)
        raw = path.read_bytes()
        if raw[:rinex.PROBE] == prefix:
            raise ValueError('FTP transfer echoed the file prefix: '+name)
        markers = rinex.epoch_offsets(raw, offset=offset)
        if (len(markers) < 2 or any(row[1] != rinex.WEEK for row in markers)
                or not ground['receiver_selection_time_s'][0] <= markers[0][2] < markers[-1][2]
                       <= ground['receiver_selection_time_s'][1]):
            raise ValueError('the byte span must resolve to the unchanged earlier Nuuk stop')
        transfers[offset] = raw
        reports.append(dict(offset=offset, bytes=requested, sha256=digest(raw),
                            first_marker_gps_s=markers[0][2], last_marker_gps_s=markers[-1][2],
                            transfer_exit_code=code, local_source=LOCAL+'/'+name))
    if not reports[0]['last_marker_gps_s'] < FIRST:
        raise ValueError('the locating probe should end before the fixed interval')
    joined = join_overlap(transfers[START], transfers[SECOND], length=rinex.CHUNK, overlap=rinex.OVERLAP)
    body, retained = rinex.inspect_window(joined, offset=START, first=FIRST, last=LAST,
                                         observation_types=layout['observation_types'])
    following = next(row for row in rinex.epoch_offsets(joined, offset=START)
                     if row[0] == retained['byte_end_exclusive'])
    if following[2] != LAST+.5 or retained['epochs'] != 241:
        raise ValueError('a distinct following marker must complete the final half-second record')
    payload = header+body
    payload_path = LOCAL+'/air10706a-apron-with-imu.23o.gz'
    for offset, data in transfers.items():
        _write_equal(root/LOCAL/NAMES[offset], data)
    _write_equal(root/payload_path, gzip.compress(payload, mtime=0))
    result = dict(source=rinex.SOURCE, source_bytes=rinex.SIZE, source_listing_sha256=rinex.LISTING_SHA,
                  header_sha256=digest(header), ground_receipt_sha256=GROUND_SHA, plan_sha256=digest((root/PLAN).read_bytes()),
                  first_gps_s=FIRST, last_gps_s=LAST, following_marker_gps_s=following[2],
                  prefix_sha256=rinex.PREFIX_SHA, transfers=reports, overlap_bytes=rinex.OVERLAP,
                  retained=retained, retained_source=payload_path, retained_bytes=len(payload),
                  retained_sha256=digest(payload), initial_size_guard_rejection=dict(exit_code=63, bytes=0),
                  original_model_fits=0, protected_reads=0, scientific_decision='abstain')
    _write_equal(root/REPORT, encoded(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path)
    parser.add_argument('--transfer-exits', nargs=3, required=True, type=int)
    args = parser.parse_args()
    root = Path.cwd()
    print(json.dumps(seal(root, args.cache or root/LOCAL, args.transfer_exits), sort_keys=True))
