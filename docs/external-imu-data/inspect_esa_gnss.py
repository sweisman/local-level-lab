# SPDX-License-Identifier: AGPL-3.0-or-later
"""Describe the selected GNSS PPP trajectory and reported lines, without fitting."""
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
DATA=ROOT/'data/external-imu-survey-20261018/esa-sample'


def main():
    source=DATA/'187_air1_ppp_2Hz_final.txt';rows=[];headers=[]
    with source.open() as stream:
        for line in stream:
            if not re.match(r'^\d{8}\s',line):
                if not rows:headers.append(line.rstrip())
                elif line.strip():raise ValueError('unexpected content after observation records')
                continue
            parts=line.split()
            if len(parts)!=30:raise ValueError('documented thirty-column GNSS export required')
            values=list(map(float,parts[:28]))
            if not all(math.isfinite(v) for v in values):raise ValueError('finite GNSS fields required')
            if rows and (values[0]<=rows[-1][0] or values[26]<=rows[-1][26]):raise ValueError('ordered GNSS sequence and time required')
            rows.append(values)
    if len(rows)<2:raise ValueError('GNSS epochs missing')
    imu=json.loads((DATA/'inspection.json').read_text())
    covered=[r for r in rows if imu['first_gps_sow_s']<=r[26]<=imu['last_gps_sow_s']]
    speed=lambda r:math.hypot(r[10],r[11])*3.6
    intervals=[]
    with (HERE/'esa-reported-lines.csv').open() as stream:
        for line in csv.DictReader(stream):
            if line['survey_day']!='187':continue
            start=float(line['start_report_time_s']);end=float(line['end_report_time_s'])
            selected=[r for r in covered if start<=r[26]<=end]
            intervals.append(dict(line_id=line['line_id'],report_start_s=start,report_end_s=end,
                report_duration_min=(end-start)/60,gnss_epochs=len(selected),
                raw_imu_time_span_covers_report_line=imu['first_gps_sow_s']<=start<end<=imu['last_gps_sow_s'],
                mean_ground_speed_kmh=statistics.mean(map(speed,selected)) if selected else None,
                min_ground_speed_kmh=min(map(speed,selected)) if selected else None,
                max_ground_speed_kmh=max(map(speed,selected)) if selected else None,
                mean_latitude_deg=statistics.mean(r[1] for r in selected) if selected else None,
                min_ellipsoid_height_m=min(r[3] for r in selected) if selected else None,
                max_ellipsoid_height_m=max(r[3] for r in selected) if selected else None,
                eligibility='not evaluated; report lines are descriptive, not a frozen study cohort'))
    result=dict(source_file=source.name,sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        epochs=len(rows),first_gps_sow_s=rows[0][26],last_gps_sow_s=rows[-1][26],span_hours=(rows[-1][26]-rows[0][26])/3600,
        observed_median_dt_s=statistics.median(b[26]-a[26] for a,b in zip(rows,rows[1:])),
        maximum_dt_s=max(b[26]-a[26] for a,b in zip(rows,rows[1:])),
        imu_overlap_epochs=len(covered),maximum_ground_speed_kmh=max(map(speed,covered)),
        latitude_range_deg=[min(r[1] for r in covered),max(r[1] for r in covered)],reported_lines=intervals,
        export_source_label=next(s.split(':',1)[1].strip() for s in headers if s.startswith('Source:')),
        processing_provenance='ESA report section 7.2.1: GNSS-only PPP using final CODE orbit/clock products; antenna positions',
        export_label_note='The software uses a generic GNSS/INS epoch label. GNSS-only attribution comes from the report, not that label.',
        raw_rinex_reprocessed=False,covariance_calibrated=False,gyro_used_for_selection=False,earth_model_fits=0,
        inspector_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    text=json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n'
    (DATA/'gnss-inspection.json').write_text(text);(HERE/'esa-gnss-report.json').write_text(text)
    with (HERE/'esa-selected-line-context.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(intervals[0]));writer.writeheader();writer.writerows(intervals)
    print(json.dumps({k:result[k] for k in ('epochs','span_hours','imu_overlap_epochs','maximum_ground_speed_kmh','latitude_range_deg')}))
    print(json.dumps(intervals))


if __name__=='__main__':main()
