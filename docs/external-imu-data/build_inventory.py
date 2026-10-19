# SPDX-License-Identifier: AGPL-3.0-or-later
"""Inspect the explicitly downloaded source survey; no network or model fits."""
import csv
from datetime import date,timedelta,datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
DATA=ROOT/'data/external-imu-survey-20261018'
sys.path.insert(0,str(ROOT/'analysis'))
from lll import imr


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def write_json(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def write_csv(path,rows):
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def reference_context(path):
    """Describe a fused reference only; it cannot qualify independent evidence."""
    rows=[];columns=None
    with path.open() as stream:
        for line in stream:
            if line.startswith('Week   GPSTime'):columns=line.split();continue
            parts=line.split()
            if not columns or not re.match(r'^\d{4} ',line):continue
            rows.append(parts)
    if not rows:raise ValueError('missing reference trajectory')
    speed=[math.hypot(float(r[columns.index('VEast')]),float(r[columns.index('VNorth')]))*3.6 for r in rows]
    return dict(source='GNSS/INS Epochs (Smoothed TC Combined)',independent_gnss=False,
        use='motion context only; not admission or scientific evidence',epochs=len(rows),
        first_gps_sow=float(rows[0][1]),last_gps_sow=float(rows[-1][1]),
        median_ground_speed_kmh=statistics.median(speed),maximum_ground_speed_kmh=max(speed))


def rinex_context(path):
    metadata={};epochs=[]
    with path.open() as stream:
        first=next(stream)
        if 'OBSERVATION DATA' not in first or 'RINEX VERSION / TYPE' not in first:
            raise ValueError('RINEX observation header required')
        metadata['rinex_version']=first[:9].strip()
        for line in stream:
            label=line[60:].strip()
            if label in ('REC # / TYPE / VERS','INTERVAL','TIME OF FIRST OBS','TIME OF LAST OBS'):
                metadata[label]=line[:60].strip()
            if label=='END OF HEADER':break
        else:raise ValueError('truncated RINEX header')
        for line in stream:
            if line.startswith('> '):
                p=line.split()
                if int(p[7]) not in (0,1):continue
                base=datetime(*map(int,p[1:6]));epoch=base+timedelta(seconds=float(p[6]));epochs.append(epoch)
    if not epochs or any(b<=a for a,b in zip(epochs,epochs[1:])):raise ValueError('ordered RINEX epochs required')
    metadata.update(observation_epochs=len(epochs),first_epoch_time_scale_as_header=epochs[0].isoformat(),
        last_epoch_time_scale_as_header=epochs[-1].isoformat(),span_s=(epochs[-1]-epochs[0]).total_seconds(),
        contains_raw_receiver_observations=True,positions_computed=False,
        validation='header and epoch-order inspection, not complete RINEX observation validation')
    return metadata


def main():
    reference=DATA/'references';sample=DATA/'smartpnt-sample'
    text=(reference/'esa-final-report.txt').read_text()
    section=text[text.index('8 Appendix B: Line'):text.index('9 Appendix C: Daily')]
    lines=[]
    for m in re.finditer(r'^\s*(\d{4})\s+(\d{3})\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$',section,re.M):
        line_id,doy,start,end,_,_=map(int,m.groups())
        if end<=start:raise ValueError('nonpositive report line duration')
        lines.append(dict(line_id=line_id,survey_day=doy,date=str(date(2023,1,1)+timedelta(days=doy-1)),
            start_report_time_s=start,end_report_time_s=end,duration_s=end-start,duration_min=(end-start)/60,
            source='ESA final report Appendix B, printed page 44',raw_samples_verified=False,
            eligibility='not evaluated; report line definitions are not study admission'))
    if len(lines)!=50 or len({r['line_id'] for r in lines})!=50:raise ValueError('complete unique report line table required')
    write_csv(HERE/'esa-reported-lines.csv',lines)
    mappings={'178a':(178,'178a_rqh01.txt'),'178b':(178,'178b_rqh01.txt'),
        '179':(179,'179_rqh01.txt'),'180':(180,'180_rqh01.txt'),
        '182a':(182,'182_rqh01.txt'),'182b':(182,'182_rqh01.txt'),'182c':(182,'182_rqh01.txt'),
        '183':(183,'183_rqh01.txt'),'184':(184,'184_rqh01.txt'),'186':(186,'186_rqh01.txt'),
        '187a':(187,'187_rqh01.txt'),'187b':(187,'187_rqh01.txt')}
    files=[]
    for name in dict.fromkeys(v[1] for v in mappings.values()):
        ids=[k for k,v in mappings.items() if v[1]==name];doy=mappings[ids[0]][0]
        files.append(dict(filename=name,date=str(date(2023,1,1)+timedelta(days=doy-1)),
            flight_ids=';'.join(ids),size_bytes='',download_url='',source='ESA report Table 10, printed page 35',
            availability='reported; live FTPS catalog requires ESA access',downloaded=False))
    write_csv(HERE/'esa-reported-imu-files.csv',files)
    catalogs=[json.loads((reference/f'smartpnt-catalog-{n}.json').read_text()) for n in range(1,5)]
    if catalogs[-1].get('nextPageToken'):raise ValueError('incomplete catalog pagination')
    entries=[f for page in catalogs for f in page['datasetFiles']]
    if len({f['name'] for f in entries})!=len(entries):raise ValueError('duplicate catalog entry')
    rows=[]
    for item in entries:
        parts=item['name'].split('/');name=item['name'];group=parts[1] if len(parts)>2 else parts[0]
        match=re.match(r'Data\d+_(\d{8})_(.+)_(Vehicle|CAR|UAV|Marine)_(.+)',group)
        rows.append(dict(path=name,size_bytes=item['totalBytes'],group=group,
            date=match[1] if match else '',instrument_token=match[2] if match else '',
            platform_token=match[3] if match else '',raw_imu=name.lower().endswith('.imr'),
            raw_gnss=bool(re.search(r'\.[0-9]{2}[oO]$',name)),
            processed_reference='GroundTruth' in name,sample_downloaded=(sample/Path(name).name).exists()
                and group=='Data06_20210115_HG4930_UAV_Opensky',eligibility='not evaluated'))
    write_csv(HERE/'smartpnt-files.csv',rows)
    for name in ('HG4930.imr','README.xml','ROVE.21O','ROVE_GroundTruth.txt'):
        expected=next(f['totalBytes'] for f in entries if f['name']=='Dataset/Data06_20210115_HG4930_UAV_Opensky/'+name)
        if (sample/name).stat().st_size!=expected:raise ValueError('sample size mismatch: '+name)
    measured=imr.inspect(sample/'HG4930.imr')
    measured.update(dataset_id='Data06_20210115_HG4930_UAV_Opensky',
        raw_gnss=rinex_context(sample/'ROVE.21O'),reference_context=reference_context(sample/'ROVE_GroundTruth.txt'),
        eligibility='not evaluated; dataset-specific policy not frozen',selection='small airborne sample selected from file catalog before gyro/model inspection')
    write_json(HERE/'smartpnt-sample-report.json',measured)
    long_dir=DATA/'smartpnt-long-record'
    with (long_dir/'header.bin').open('rb') as stream:long_header=imr.read_header(stream)
    first=struct.unpack(long_header['byte_order']+'d6i',(long_dir/'first-record.bin').read_bytes())
    last=struct.unpack(long_header['byte_order']+'d6i',(long_dir/'last-record.bin').read_bytes())
    http=json.loads((long_dir/'range-receipts.json').read_text())
    if len({r['etag'] for r in http})!=1 or any(r['http_status']!=206 for r in http):
        raise ValueError('consistent partial-content source required')
    size=next(f['totalBytes'] for f in entries if f['name']=='POSMind_Software/AllanVarData/HG4930(600Hz).IMR')
    if [r['content_range'] for r in http]!=[f'bytes 0-511/{size}',f'bytes 512-543/{size}',f'bytes {size-32}-{size-1}/{size}']:
        raise ValueError('exact source ranges required')
    write_json(HERE/'smartpnt-long-record-report.json',dict(
        path='POSMind_Software/AllanVarData/HG4930(600Hz).IMR',catalog_size_bytes=size,
        header=long_header,first_time_s=first[0],last_time_s=last[0],endpoint_span_hours=(last[0]-first[0])/3600,
        expected_records_from_size=(size-512)//32,downloaded_bytes=576,full_file_downloaded=False,
        full_file_sha256=None,interior_continuity_verified=False,stationary_context_verified=False,
        mounting_verified=False,eligibility='not evaluated; sensor-characterization lead, not shape evidence',
        range_receipts=http,earth_model_fits=0))
    with (sample/'HG4930.imr').open('rb') as source:
        header=imr.read_header(source)
        with (sample/'imu-physical.csv.gz').open('wb') as target:
            import io
            with gzip.GzipFile(filename='',fileobj=target,mode='wb',mtime=0) as compressed:
                with io.TextIOWrapper(compressed,encoding='utf-8',newline='') as output:
                    writer=csv.writer(output);writer.writerow(['offset','time_raw_s','dt_s',
                        'raw_gx','raw_gy','raw_gz','raw_ax','raw_ay','raw_az',
                        'dtheta_x_rad','dtheta_y_rad','dtheta_z_rad','dv_x_mps','dv_y_mps','dv_z_mps'])
                    for r in imr.records(source,header):writer.writerow([r['packet_offset'],r['time_raw_s'],r['dt_s'],
                        *r['raw_gyro'],*r['raw_accel'],*(r['angle_increment_rad'] or [None]*3),
                        *(r['velocity_increment_mps'] or [None]*3)])
    inputs={str(p.relative_to(ROOT)):sha(p) for p in (*sorted(reference.iterdir()),*sorted(long_dir.iterdir()),
        *(sample/n for n in ('HG4930.imr','README.xml','ROVE.21O','ROVE_GroundTruth.txt')))}
    sources={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),ROOT/'analysis/lll/imr.py',ROOT/'analysis/tests/test_imr.py')}
    artifacts={n:sha(HERE/n) for n in ('esa-reported-lines.csv','esa-reported-imu-files.csv','smartpnt-files.csv',
        'smartpnt-sample-report.json','smartpnt-long-record-report.json')}
    write_json(HERE/'inventory-receipt.json',dict(inputs=inputs,sources=sources,artifacts=artifacts,
        physical_artifact=dict(path=str((sample/'imu-physical.csv.gz').relative_to(ROOT)),sha256=sha(sample/'imu-physical.csv.gz')),
        native_predictions=0,earth_model_fits=0,existing_study_criteria_changed=False))
    print(json.dumps(dict(esa_reported_files=len(files),esa_reported_lines=len(lines),
        esa_median_line_min=statistics.median(r['duration_min'] for r in lines),
        esa_max_line_min=max(r['duration_min'] for r in lines),smartpnt_files=len(entries),
        smartpnt_raw_imu_files=sum(r['raw_imu'] for r in rows),sample_records=measured['records'],
        sample_duration_min=measured['duration_s']/60,sample_gaps=measured['gap_count'],
        reference_max_speed_kmh=measured['reference_context']['maximum_ground_speed_kmh'])))


if __name__=='__main__':main()
