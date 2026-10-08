# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded six-file satellite decoding/context; no Earth-model inference."""
from bisect import bisect_right
from collections import Counter
from contextlib import contextmanager
import csv
import datetime
import gzip
import hashlib
import io
import json
import os
from pathlib import Path

import numpy as np

from . import applanix as ap, ilvis0 as il, ilvis0_followup as follow
from . import trimble_receiver as framing, trimble_observations as decode

VERSION = 'ilvis0-receiver-observations-v1'


def statistics(values):
    return dict(samples=len(values), min=float(np.min(values)), median=float(np.median(values)),
        p95=float(np.percentile(values,95)), max=float(np.max(values))) if values else dict(samples=0)


@contextmanager
def compressed_text(path):
    """Deterministic owned derivative, committed atomically only on success."""
    temporary = path.with_name(path.name+'.partial')
    with temporary.open('wb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as compressed:
            with io.TextIOWrapper(compressed,encoding='utf-8',newline='') as stream:
                yield stream
        # Text wrapper has closed gzip, but raw remains open here.
        raw.flush()
        os.fsync(raw.fileno())
    os.replace(temporary,path)
    descriptor=os.open(path.parent,os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


CSV_FIELDS = ('source_file','source_sha256','task_id','payload_sha256','first_packet_offset',
    'last_packet_offset','first_stream_offset','last_stream_offset','gps_week','gps_week_seconds',
    'utc_epoch','format','receiver_clock_offset_s','system','antenna','sv_id','channel',
    'elevation_deg','azimuth_deg','sv_flags','code_smoothed','phase_smoothed','sv_unhealthy','raim_fault',
    'band','track_type','snr_dbhz','pseudorange_m','pseudorange_difference_m','phase_cycles',
    'phase_units','doppler_hz','slip_counter','cycle_slip','half_cycle','range_loaded','phase_loaded',
    'signal_unhealthy','measurement_flags','raw_snr','raw_range','raw_phase','raw_doppler')


def csv_rows(record):
    base={k:record.get(k) for k in CSV_FIELDS[:13]}
    for satellite in record['satellites']:
        sv={k:satellite.get(k) for k in ('system','antenna','sv_id','channel','elevation_deg',
            'azimuth_deg','code_smoothed','phase_smoothed','raim_fault')}
        sv.update(sv_flags=json.dumps(satellite['flags'],separators=(',',':')),
            sv_unhealthy=satellite.get('unhealthy',False))
        for signal in satellite['signals']:
            row=base | sv
            row.update({k:signal.get(k) for k in CSV_FIELDS[24:]})
            row.update(signal_unhealthy=signal.get('unhealthy',False),
                measurement_flags=json.dumps(signal.get('measurement_flags',signal.get('raw_flags')),
                    separators=(',',':')),
                phase_units=signal.get('phase_units','receiver cycles; original sign retained'))
            yield row


def scan(task, prior, output):
    counts=Counter(); records=Counter(); satellite_types=Counter(); signal_types=Counter()
    eph_types=Counter(); smoothing=Counter(); slips=Counter()
    frames=Counter(); ephemerides=[]; unknown_ephemerides=[]; epochs=[]; errors=[]
    receiver=framing.ReceiverStream(); pages=framing.SurveyPages()
    sequence=hashlib.sha256()
    boundaries=[]; offsets=[]
    enabled=assembly=True
    source_path=Path(task['path'])
    reference=prior['receiver']['gsof_records']
    weeks={r['gps_week'] for r in reference}
    if len(weeks)!=1:
        raise ValueError('initial RT17 week mapping requires one recorded GPS week; no guessed rollover')
    week=next(iter(weeks))
    json_path=output/(task['task_id']+'.observations.jsonl.gz')
    csv_path=output/(task['task_id']+'.observations.csv.gz')
    with compressed_text(json_path) as log, compressed_text(csv_path) as table:
        writer=csv.DictWriter(table,fieldnames=CSV_FIELDS,lineterminator='\n'); writer.writeheader()
        with il.open_source(source_path) as original:
            source=follow.HashedReader(original)
            for frame in ap.frames(source):
                frames[f'{frame.tag}:{frame.group}']+=1
                if frame.tag!='$GRP' or frame.group!=10001:
                    continue
                _,payload=ap.group10001(frame)
                if not enabled:
                    continue
                boundaries.append(receiver.received); offsets.append(frame.offset)
                try:
                    items=receiver.feed(payload)
                except ValueError as exc:
                    errors.append(dict(kind='receiver_stream',reason=str(exc),packet_offset=frame.offset))
                    enabled=False
                    continue
                for item in items:
                    if item['kind']!='binary':
                        continue
                    counts[f'{item["packet_type"]:02x}']+=1
                    if item['packet_type']==0x55:
                        subtype=item['payload'][0] if item['payload'] else None
                        eph_types[str(subtype)]+=1
                        evidence=dict(stream_offset=item['stream_offset'],
                            packet_offset=offsets[bisect_right(boundaries,item['stream_offset'])-1],
                            payload_sha256=hashlib.sha256(item['payload']).hexdigest())
                        if subtype==1:
                            ephemerides.append(decode.decode_gps_ephemeris(item) | evidence)
                        else:
                            unknown_ephemerides.append(evidence | dict(subtype=subtype,
                                payload_hex=item['payload'].hex(),status='preserved unsupported subtype'))
                    elif item['packet_type']==0x57 and assembly:
                        try:
                            record=pages.feed(item)
                        except ValueError as exc:
                            errors.append(dict(kind='survey_pages',reason=str(exc),stream_offset=item['stream_offset']))
                            assembly=False
                            continue
                        if record is None:
                            continue
                        records[str(record['subtype'])]+=1
                        sequence.update(bytes([record['subtype']])+len(record['payload']).to_bytes(4,'little')+record['payload'])
                        if record['subtype'] not in (0,6):
                            continue
                        # A payload layout failure stops this task; it is never skipped
                        # or repaired to increase the decoded count.
                        decoded=(decode.decode_rt17(record,week) if record['subtype']==0 else decode.decode_rt27(record))
                        utc=datetime.datetime(1980,1,6,tzinfo=datetime.timezone.utc)+datetime.timedelta(
                            weeks=decoded['gps_week'],seconds=decoded['gps_week_seconds']-task['leap_seconds'])
                        if utc.date().isoformat() not in task['embedded_dates']:
                            raise ValueError('survey epoch disagrees with frozen embedded date')
                        decoded.update(utc_epoch=utc.isoformat(),source_file=task['filename'],
                            source_sha256=task['source_sha256'],task_id=task['task_id'],
                            **{k:record[k] for k in ('payload_sha256','first_stream_offset','last_stream_offset')},
                            first_packet_offset=offsets[bisect_right(boundaries,record['first_stream_offset'])-1],
                            last_packet_offset=offsets[bisect_right(boundaries,record['last_stream_offset'])-1])
                        log.write(json.dumps(decoded,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n')
                        writer.writerows(csv_rows(decoded))
                        for satellite in decoded['satellites']:
                            satellite_types[str(satellite['system'])]+=1
                            smoothing['code_smoothed_satellite_epochs']+=int(satellite['code_smoothed'])
                            smoothing['phase_smoothed_satellite_epochs']+=int(satellite.get('phase_smoothed',False))
                            for signal in satellite['signals']:
                                signal_types[f'{satellite["system"]}:{signal["band"]}:{signal["track_type"]}']+=1
                                slips['flagged_signal_epochs']+=int(signal['cycle_slip'])
                        # Raw encodings are already in the durable export; keep only
                        # measured fields needed for the bounded diagnostics in RAM.
                        decoded.pop('encoded_payload_hex')
                        epochs.append(decoded)
        if source.digest.hexdigest()!=task['source_sha256'] or dict(frames)!=task['expected_frame_counts']:
            raise ValueError('strict source hash/frame audit failed')
        if enabled:
            try:
                receiver.finish()
            except ValueError as exc:
                errors.append(dict(kind='receiver_tail',reason=str(exc),retained_hex=receiver.buffer.hex()))
        if assembly:
            try:
                pages.finish()
            except ValueError as exc:
                errors.append(dict(kind='survey_tail',reason=str(exc)))
        if (dict(records)!=prior['receiver']['survey_record_counts'] or
                sequence.hexdigest()!=prior['receiver']['survey_record_sequence_sha256'] or
                dict(counts)!=prior['receiver']['binary_packet_types']):
            raise ValueError('complete receiver record sequence differs from frozen audit')
    if not epochs:
        raise ValueError('no decoded observation epochs')
    times=[r['gps_week']*604800+r['gps_week_seconds'] for r in epochs]
    intervals=np.diff(times)
    if np.any(intervals<=0):
        raise ValueError('survey timestamp reversal/duplicate; no ordering repair')
    median_interval=float(np.median(intervals))
    receiver_epochs={}
    for row in reference:
        key=(row['gps_week'],round(row['gps_week_seconds']*1000))
        if key in receiver_epochs:
            raise ValueError('ambiguous same-epoch receiver position')
        receiver_epochs[key]=row
    angles=[]; coverage=[]; geometry=[]; common=0
    phase_comparisons=[]; previous={}; slip_transitions=0
    for row in epochs:
        time=row['gps_week']*604800+row['gps_week_seconds']
        key=(row['gps_week'],round(row['gps_week_seconds']*1000))
        context=receiver_epochs.get(key)
        geometry.append(decode.geometry_diagnostic(row['satellites']))
        covered=0
        if context:
            common+=1
        for satellite in row['satellites']:
            if satellite['system']==0 and satellite['antenna']==0:
                candidates=[e for e in ephemerides if e['sv_id']==satellite['sv_id'] and not e['health']
                    and abs((row['gps_week']-e['gps_week'])*604800+row['gps_week_seconds']-e['toe_s'])<=7200]
                if candidates:
                    selected=min(candidates,key=lambda e:abs((row['gps_week']-e['gps_week'])*604800+row['gps_week_seconds']-e['toe_s']))
                    covered+=1
                    if context:
                        az,el=decode.sky_angles(decode.gps_position(selected,row['gps_week'],row['gps_week_seconds']),context)
                        angles.append(dict(elevation_difference_deg=el-satellite['elevation_deg'],
                            azimuth_difference_deg=(az-satellite['azimuth_deg']+180)%360-180))
            for signal in satellite['signals']:
                identity=(satellite['system'],satellite['antenna'],satellite['sv_id'],signal['band'],signal['track_type'])
                last=previous.get(identity)
                counter=signal.get('slip_counter',satellite.get('l1_slip_counter' if signal['band']==0 else 'l2_slip_counter'))
                usable=signal['phase_loaded'] and signal.get('doppler_hz') is not None and not signal['cycle_slip'] and not signal.get('unhealthy') and not satellite.get('unhealthy')
                if last:
                    changed=counter is not None and last['counter'] is not None and counter!=last['counter']
                    slip_transitions+=int(changed)
                    dt=time-last['time']
                    if usable and last['usable'] and not changed and 0<dt<=3*median_interval:
                        rate=(signal['phase_cycles']-last['phase'])/dt
                        doppler=(signal['doppler_hz']+last['doppler'])/2
                        phase_comparisons.append((rate-doppler,rate+doppler))
                previous[identity]=dict(time=time,phase=signal['phase_cycles'],doppler=signal.get('doppler_hz'),
                    usable=usable,counter=counter)
        coverage.append(covered)
    angular=dict(matched_gps_satellite_epochs=len(angles),
        elevation_difference_deg=statistics([r['elevation_difference_deg'] for r in angles]),
        azimuth_difference_deg=statistics([r['azimuth_difference_deg'] for r in angles]),
        maximum_absolute_elevation_difference_deg=max((abs(r['elevation_difference_deg']) for r in angles),default=None),
        maximum_absolute_azimuth_difference_deg=max((abs(r['azimuth_difference_deg']) for r in angles),default=None),
        interpretation='broadcast-GPS geometry versus rounded receiver sky angles under WGS84; not independent Earth evidence')
    return dict(version=VERSION,task_id=task['task_id'],filename=task['filename'],
        source_sha256=task['source_sha256'],source_bytes=source.size,frame_counts=dict(frames),
        complete_record_counts=dict(records),survey_sequence_sha256=sequence.hexdigest(),
        decoded_epochs=len(epochs),decoded_signal_epochs=sum(signal_types.values()),
        gps_week=week,first_gps_time=times[0],last_gps_time=times[-1],
        duration_s=times[-1]-times[0],sample_intervals_s=statistics(intervals.tolist()),
        gaps_over_1_5_median=int(np.sum(intervals>1.5*median_interval)),
        satellite_systems=dict(satellite_types),signal_types=dict(signal_types),smoothing=dict(smoothing),
        slip_flags=dict(slips),slip_counter_transitions=slip_transitions,
        phase_doppler_diagnostic=dict(samples=len(phase_comparisons),
            rate_minus_doppler_hz=statistics([abs(r[0]) for r in phase_comparisons]),
            rate_plus_doppler_hz=statistics([abs(r[1]) for r in phase_comparisons]),
            semantics='two sign hypotheses reported; no slip repair, ambiguity solution or accuracy claim'),
        ephemeris_subtypes=dict(eph_types),gps_ephemerides=ephemerides,
        unsupported_ephemerides=unknown_ephemerides,
        healthy_recent_gps_satellites_per_epoch=statistics(coverage),
        same_epoch_receiver_positions=common,sky_angle_check=angular,
        geometry=dict(full_rank_epochs=sum(r['full_rank'] for r in geometry),
            hdop=statistics([r['hdop'] for r in geometry if r['full_rank']]),
            vdop=statistics([r['vdop'] for r in geometry if r['full_rank']]),
            assumed_range_sigma_m=1.,calibrated_covariance=False,
            rank_counts=dict(Counter(str(r['rank']) for r in geometry))),
        boundary_failures=errors,
        artifacts_sha256={p.name:il.sha256(p) for p in (json_path,csv_path)},
        source_audit_errors=0,empirical_earth_fit_attempts=0,gnss_position_fits=0,
        scientific_eligibility_changes=0,originals_deleted=0)
