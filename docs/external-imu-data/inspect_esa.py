# SPDX-License-Identifier: AGPL-3.0-or-later
"""One streaming format/timing inspection of the selected ESA original; no fits."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis'))
from lll.airquantumgrav import VERSION,records
DATA=ROOT/'data/external-imu-survey-20261018/esa-sample'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def main():
    source=DATA/'187_rqh01.txt';receipt=json.loads((DATA/'download-completion.json').read_text())
    if source.stat().st_size!=receipt['size_bytes']:raise ValueError('download size changed')
    output=DATA/'inspection.json'
    if output.exists():raise ValueError('inspection already exists; preserve the completed report')
    began=time.monotonic();digest=hashlib.sha256();count=0;first=None;last=None;gap_count=0
    dt_counts=Counter();minimum_dt=math.inf;maximum_dt=0.;minimum_temp=math.inf;maximum_temp=-math.inf
    low_force_count=0;first_low_force=[]
    with source.open('rb') as stream:
        def hashed():
            for line in stream:digest.update(line);yield line
        for row in records(hashed()):
            count+=1;last=row['gps_time_s']
            if first is None:first=last
            dt=row['dt_s']
            if dt is not None:
                minimum_dt=min(minimum_dt,dt);maximum_dt=max(maximum_dt,dt)
                dt_counts[round(dt*1e6)]+=1;gap_count+=row['gap_above_1p5_nominal_periods']
            minimum_temp=min(minimum_temp,row['temperature_c']);maximum_temp=max(maximum_temp,row['temperature_c'])
            force=math.sqrt(sum(v*v for v in row['acceleration_mps2']))
            if force<1.:
                low_force_count+=1
                if len(first_low_force)<10:first_low_force.append(dict(line_number=row['line_number'],gps_time_s=last,force_norm_mps2=force))
    if digest.hexdigest()!=receipt['sha256']:raise ValueError('download hash changed')
    if count<2:raise ValueError('multiple observations required for cadence')
    # Histogram units are microseconds; extrema above retain timestamp precision.
    ranks=((count-2)//2,(count-1)//2);median_values=[];cumulative=0
    for dt,n in sorted(dt_counts.items()):
        for rank in ranks:
            if cumulative<=rank<cumulative+n:median_values.append(dt)
        cumulative+=n
    report=dict(source_file=source.name,source_sha256=digest.hexdigest(),byte_size=source.stat().st_size,
        decoder_version=VERSION,records=count,first_gps_sow_s=first,last_gps_sow_s=last,span_s=last-first,
        span_hours=(last-first)/3600,effective_hz=(count-1)/(last-first),minimum_dt_s=minimum_dt,maximum_dt_s=maximum_dt,
        median_dt_microsecond_histogram_s=sum(median_values)/len(median_values)/1e6,
        dt_microsecond_counts={str(k):v for k,v in sorted(dt_counts.items())},gaps_above_1p5_nominal_periods=gap_count,
        reported_nominal_hz=300,temperature_min_c=minimum_temp,temperature_max_c=maximum_temp,
        force_norm_below_1_mps2_count=low_force_count,first_low_force_rows=first_low_force,
        low_force_rows_use='preserved startup/quality flags; not automatically excluded or repaired',
        layout='GPS seconds-of-week; three accelerations m/s^2; three angular rates rad/s; temperature C',
        axes_source='ESA report: aircraft forward, starboard, through-floor',
        units_status='header and report agree; no independent per-unit calibration established',
        original_preserved=True,interpolation=False,corrections_applied=False,scientific_eligibility='not evaluated',
        earth_model_fits=0,elapsed_s=time.monotonic()-began,
        inspector_sha256=sha(Path(__file__)),decoder_sha256=sha(ROOT/'analysis/lll/airquantumgrav.py'))
    write(output,report);write(Path(__file__).resolve().parent/'esa-sample-report.json',report)
    print(json.dumps({k:report[k] for k in ('records','span_hours','effective_hz','gaps_above_1p5_nominal_periods','elapsed_s')}))


if __name__=='__main__':main()
