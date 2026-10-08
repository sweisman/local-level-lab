# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate settings/receiver/clock evidence audit; no empirical Earth-model fitting."""
from collections import Counter
import hashlib
import math

import numpy as np

from . import applanix as ap, ilvis0 as il, ilvis0_followup as follow
from . import ilvis0_assessment as assessment, trimble_receiver as trimble

VERSION = 'ilvis0-processing-evidence-v1'


def statistics(values):
    return dict(samples=len(values), min=float(np.min(values)), median=float(np.median(values)),
                max=float(np.max(values))) if values else dict(samples=0, min=None, median=None, max=None)


def scan(path, expected_hash, expected_frame_counts, leap_seconds):
    counts, sizes, versions, raw_status, imu_status, receiver_types = (Counter() for _ in range(6))
    settings = {}
    clock_bases = Counter()
    gyro_t1, gyro_t2, gyro_tags = [], [], []
    uncertainties = []
    receiver = trimble.ReceiverStream()
    pages = trimble.SurveyPages()
    receiver_errors, page_errors = [], []
    binary_types, subtypes, records, flags, sentence_types = (Counter() for _ in range(5))
    examples = {}
    raw_record_hash = hashlib.sha256()
    ascii_examples = []
    gps_hdop, gps_satellites, receipt_delays = [], [], []
    gst, gsof_packets = [], 0
    receiver_enabled = assembly_enabled = True
    independent_nmea = ap.NMEA()
    old_sentence_counts = Counter()
    with il.open_source(path) as original:
        source = follow.HashedReader(original)
        for frame in ap.frames(source):
            key = f'{frame.tag}:{frame.group}'
            counts[key] += 1
            sizes[f'{key}:{len(frame.packet)}'] += 1
            if frame.tag == '$MSG':
                payload = frame.packet[10:-4]
                signature = hashlib.sha256(payload).hexdigest()
                identity = f'{frame.group}:{signature}'
                if identity not in settings:
                    if len(settings) >= 2000:
                        raise ValueError('bounded unique settings capacity exceeded')
                    settings[identity] = dict(message_id=frame.group, payload_sha256=signature,
                        payload_hex=payload.hex(), packet_size=len(frame.packet),
                        first_packet_offset=frame.offset, last_packet_offset=frame.offset, count=0,
                        interpretation='opaque logged message; ID alone does not establish legacy processing semantics')
                settings[identity]['last_packet_offset'] = frame.offset
                settings[identity]['count'] += 1
                continue
            header = ap.time_header(frame)
            clock_bases[f'{frame.group}:{header["time_types"]}'] += 1
            if frame.group == 99:
                versions[ap.group99(frame)] += 1
            elif frame.group == 4:
                row = ap.group4(frame)
                raw_status[str(row['data_status'])] += 1
                imu_status[str(row['imu_status'])] += 1
                gyro_t1.append(row['time1_s'])
                gyro_t2.append(row['time2_s'])
                gyro_tags.append(row['time_types'])
                if len(gyro_t1) > 1000000:
                    raise ValueError('bounded IMU clock capacity exceeded')
            elif frame.group == 2:
                row = assessment.navigation_uncertainty(frame)
                if row['usable']:
                    uncertainties.append(row)
            elif frame.group == 10001:
                kind, payload = ap.group10001(frame)
                receiver_types[str(kind)] += 1
                for item in independent_nmea.feed(payload):
                    if item['valid']:
                        old_sentence_counts[item['fields'][0]] += 1
                if not receiver_enabled:
                    continue
                try:
                    items = receiver.feed(payload)
                except ValueError as exc:
                    receiver_errors.append(dict(packet_offset=frame.offset, reason=str(exc)))
                    receiver_enabled = False
                    continue
                for item in items:
                    if item['kind'] == 'binary':
                        binary_types[f'{item["packet_type"]:02x}'] += 1
                        if item['packet_type'] == 0x40:
                            gsof_packets += 1
                        elif item['packet_type'] == 0x57:
                            if len(item['payload']) >= 4:
                                subtypes[str(item['payload'][0])] += 1
                                flags[str(item['payload'][3])] += 1
                            if assembly_enabled:
                                try:
                                    record = pages.feed(item)
                                except ValueError as exc:
                                    page_errors.append(dict(stream_offset=item['stream_offset'], reason=str(exc)))
                                    assembly_enabled = False
                                    continue
                                if record:
                                    records[str(record['subtype'])] += 1
                                    raw_record_hash.update(bytes([record['subtype']])+len(record['payload']).to_bytes(4,'little')+record['payload'])
                                    if str(record['subtype']) not in examples:
                                        examples[str(record['subtype'])] = {k:v for k,v in record.items() if k!='payload'} | dict(payload_hex=record['payload'].hex())
                    elif item['kind'] == 'ascii_unchecksummed':
                        if len(ascii_examples) < 3:
                            ascii_examples.append(dict(line=item['line'], stream_offset=item['stream_offset'], scientific_timing_usable=False))
                    else:
                        fields = item['fields']
                        sentence_types[fields[0]] += 1
                        if fields[0].endswith('GGA'):
                            try:
                                satellites, hdop = int(fields[7]), float(fields[8])
                                if not 0 <= satellites <= 255 or not math.isfinite(hdop) or hdop < 0:
                                    raise ValueError('invalid receiver quality fields')
                                gps_satellites.append(satellites)
                                gps_hdop.append(hdop)
                                sod = follow.utc_sod(fields[1])
                                tag = header['time_types'] & 15
                                if tag in (1, 2):
                                    utc = header['time1_s']-(leap_seconds if tag==1 else 0)
                                    delay = (utc-sod+43200)%86400-43200
                                    receipt_delays.append(delay)
                            except (ValueError, IndexError):
                                pass
                        elif fields[0].endswith('GST'):
                            # Reported receiver sigmas are evidence, not calibrated
                            # cross-epoch covariance or inertial/navigation uncertainty.
                            try:
                                sigmas = [float(fields[k]) for k in (6,7,8)]
                                if all(math.isfinite(v) and v >= 0 for v in sigmas):
                                    gst.append(dict(receiver_sod=follow.utc_sod(fields[1]),
                                        sigma_latitude_longitude_height_m=sigmas,
                                        sentence=item['sentence'], stream_offset=item['stream_offset']))
                            except (ValueError, IndexError):
                                pass
    if source.digest.hexdigest() != expected_hash or dict(counts) != expected_frame_counts:
        raise ValueError('strict original hash/frame correspondence failed')
    if receiver_enabled:
        try:
            receiver.finish()
        except ValueError as exc:
            receiver_errors.append(dict(reason=str(exc)))
    if assembly_enabled:
        try:
            pages.finish()
        except ValueError as exc:
            page_errors.append(dict(reason=str(exc)))
    dt1, dt2 = np.diff(gyro_t1), np.diff(gyro_t2)
    same_base = len(set(gyro_tags)) == 1
    clock = dict(time_types=dict(Counter(map(str,gyro_tags))), time1_dt_s=statistics(dt1.tolist()),
        time2_dt_s=statistics(dt2.tolist()),
        maximum_dual_interval_difference_s=float(np.max(abs(dt1-dt2))) if len(dt1) else None,
        timestamp_reversals=int(np.sum(dt1<=0)),
        clock_base_changes=sum(a!=b for a,b in zip(gyro_tags,gyro_tags[1:])),
        nominal_200Hz_duration_difference_s=float(sum(dt1)-len(dt1)*.005),
        same_recorded_base=same_base, physical_integration_clock_established=False,
        receipt_minus_sentence_epoch_s=statistics(receipt_delays),
        receipt_delay_interpretation='last containing receiver packet timestamp minus sentence epoch; not IMU latency or fitted clock offset')
    return dict(version=VERSION, source_sha256=expected_hash, source_bytes=source.size,
        frame_counts=dict(counts), packet_sizes=dict(sizes), versions=dict(versions),
        clock_bases=dict(clock_bases), settings=list(settings.values()), clock=clock,
        raw_status_counts=dict(raw_status), imu_status_counts=dict(imu_status),
        fused_uncertainty=dict(samples=len(uncertainties), source_kind='internal fused navigation, not independent accuracy',
            fields={name:statistics([r[name] for r in uncertainties]) for name in assessment.UNCERTAINTY_FIELDS}),
        receiver=dict(types=dict(receiver_types), binary_packet_types=dict(binary_types),
            survey_packet_subtypes=dict(subtypes), survey_record_counts=dict(records),
            survey_flags=dict(flags), survey_record_sequence_sha256=raw_record_hash.hexdigest(),
            survey_examples=examples, stream_errors=receiver_errors, page_errors=page_errors,
            bytes=independent_nmea.received, parser_received_bytes=receiver.received,
            accounted_bytes=receiver.offset,
            ascii_unchecksummed_examples=ascii_examples, nmea_sentence_counts=dict(sentence_types),
            prior_extractor_sentence_counts=dict(old_sentence_counts),
            satellites=statistics(gps_satellites), hdop=statistics(gps_hdop), gst=gst,
            gsof_packets=gsof_packets, receiver_covariance_established=False,
            surveyed_measurements_decoded=False, raw_satellite_record_envelopes_present=any(records.get(str(x),0)>0 for x in (0,6))),
        independence=dict(earth_rate_retention_established=False, processing_independence_established=False,
            calibration_bounds_established=False, missing_direct_group10002_is_not_proof=True,
            fused_navigation_used_as_science=False),
        empirical_earth_fit_attempts=0, scientific_eligibility_changes=0, originals_deleted=0)
