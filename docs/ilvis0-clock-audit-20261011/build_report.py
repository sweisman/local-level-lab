# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit two frozen selected originals; no navigation predictions or observed fits."""
import csv
import gzip
import hashlib
import json
from pathlib import Path

from lll import applanix, ilvis0, ilvis0_followup, ilvis0_saved_audit, ilvis0_clock_audit as audit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
TARGETS=('570b37d23af5e245dd461051','b4e44ddc0f130ecd45674c78')


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def load(path):
    path=Path(path)
    data=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes()
    return json.loads(data)


def build():
    selection_path=ROOT/'docs/ilvis0-solver-trial-20261010/selection.json.gz'
    receipt_path=selection_path.parent/'evidence-receipt.json'
    receipt=load(receipt_path)
    if sha(selection_path)!=receipt['artifacts']['selection.json.gz']: raise ValueError('selection hash changed')
    selected=load(selection_path)['selected']
    if tuple(r['segment']['segment_id'] for r in selected)!=TARGETS: raise ValueError('preselected targets changed')
    context_path=ROOT/'data/ilvis0-followup-20261007/summary.json'
    contexts={r['task_id']:r for r in load(context_path)['results']}
    baseline_path=ROOT/'docs/ilvis0-highspeed-segments-20261008/summary.json.gz'
    baseline_receipt_path=baseline_path.parent/'evidence-receipt.json'
    if sha(baseline_path)!=load(baseline_receipt_path)['artifacts'][baseline_path.name]:
        raise ValueError('baseline provenance changed')
    original={r['segment_id']:r for r in load(baseline_path)['results']}
    inputs={str(p.resolve()):sha(p) for p in
        (selection_path,receipt_path,context_path,baseline_path,baseline_receipt_path)}
    calibration_path=ROOT/'docs/ilvis0-clock-calibration-audit-20261011/parameter-changes.csv'
    calibration_receipt=calibration_path.parent/'report-receipt.json'
    ilvis0_saved_audit.verify_artifacts(calibration_path.parent,load(calibration_receipt))
    for p in (calibration_path,calibration_receipt): inputs[str(p.resolve())]=sha(p)
    with calibration_path.open() as stream:
        calibration=[r for r in csv.DictReader(stream) if r['model']=='sphere_rotating'
            and r['parameter'] in ('gravity_delta','accel_bias_z','accel_gain_z')]
    if len(calibration)!=6: raise ValueError('unexpected saved calibration population')
    reports=[]; bins=[]
    for item in selected:
        source=Path(item['source_path']); segment=item['segment']; prior=original[segment['segment_id']]
        if segment!=prior['segment']: raise ValueError('frozen interval mismatch')
        inputs[str(source.resolve())]=sha(source)
        report,rows=audit.scan_selected(source,contexts[item['task']],segment)
        provenance=prior['provenance']
        for a,b in [('source_sha256','source_sha256'),('source_bytes','source_bytes'),
            ('first_packet_offset','first_packet_offset'),('last_packet_offset','last_packet_offset'),('intervals','native_packets')]:
            if report[a]!=provenance[b]: raise ValueError('selected native provenance mismatch: '+a)
        report['filename']=source.name.removesuffix('.gz')
        report['date']=contexts[item['task']]['timing']['dates'][0]
        report['interval']={k:v for k,v in segment.items() if k not in ('receiver_fixes','diagnostic_sections')}
        reports.append(report)
        for start in range(0,len(rows),200):
            block=rows[start:start+200]; periods=[r['header_dt_s'] for r in block]
            bins.append(dict(segment_id=segment['segment_id'],first_sample=start,last_sample=start+len(block)-1,
                packets=len(block),first_packet_offset=block[0]['packet_offset'],last_packet_offset=block[-1]['packet_offset'],
                interval_start_utc_s=block[0]['interval_start_utc_s'],interval_end_utc_s=block[-1]['utc_end_s'],
                header_elapsed_s=sum(periods),nominal_elapsed_s=len(block)*.005,
                minimum_dt_s=min(periods),maximum_dt_s=max(periods),
                cumulative_header_minus_nominal_s=block[-1]['cumulative_header_minus_nominal_s'],
                **{k+'_sum':sum(r[k] for r in block) for k in applanix.RAW_FIELDS}))
    controls=[audit.clock_control(k) for k in ('fixed_period_jitter','variable_period','clock_scale')]
    controls += [audit.calibration_control(varying=v) for v in (False,True)]
    if not all(r['passed'] for r in controls): raise ValueError('independent physical control failed')
    table='\n'.join(f"| {r['date']} | {r['interval']['duration_s']/60:.2f} | {r['intervals']} | "
        f"{r['interval_std_us']:.2f} | {r['mean_period_error_ppm']:.3f} | "
        f"{r['elapsed_minus_nominal_s']*1000:.3f} | {r['interval_lag_one_correlation']:.3f} |" for r in reports)
    control_table='\n'.join(f"| {r['control']} | {r['wrong_clock_max_velocity_error_mps']:.6g} | "
        f"{r['wrong_clock_max_height_error_m']:.6g} |" for r in controls[:3])
    secondary_table='\n'.join(f"| {r['date']} | {r['secondary_timing']['mean_period_error_ppm']:.3f} | "
        f"{r['primary_minus_secondary_elapsed_s']*1000:.3f} |" for r in reports)
    gravity_table='\n'.join(f"| {r['date']} | {r['stationary_nominal_increment_control']['header_final_height_m']:.3f} | "
        f"{r['stationary_nominal_increment_control']['mean_gravity_correction_mps2']:.8f} | "
        f"{r['stationary_nominal_increment_control']['mean_corrected_max_height_m']:.4f} |" for r in reports)
    text=f'''# Packet timing and independent calibration controls

**Both preselected recordings were reproduced from their original packet streams.**
This audit separates packet timestamp behavior from the unknown integration period of
the recorded increments. It identifies neither recording's physically correct clock.
Five small independently generated physical controls passed. There were **zero observed
fit starts and zero native navigation predictions**.

An **IMU (inertial measurement unit)** measures turning and acceleration. These two
recordings use IMU type 21 at declared rate code 2 (200 Hz), with the same previously
selected intervals. Their source hashes, native packet counts and first/last offsets
match the original fit provenance. Every source frame was checked for framing, declared
length and checksum. No timestamps or measurements were repaired or interpolated.
Group1 fused navigation was not used in this audit.

## Observed timing

The duration column is the public receiver-selected stretch. Native counts include
its frozen support guard. Mean period error compares header elapsed time with the
nominal period, not with an independently measured sensor integration period.

| Date | Selected minutes | Native increments | Interval scatter (µs) | Mean period error (ppm) | Total header − nominal (ms) | Adjacent interval correlation |
|---|---:|---:|---:|---:|---:|---:|
{table}

Both streams carry time-types code 2. The public [Applanix V6 ICD, Table 3 and
section 3.2.3](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf)
defines the primary tag as UTC and secondary type zero as POS time, elapsed since
power-on. Both tags describe validity time. Their differences provide a useful clock
comparison, although independent clock generation or the increment period is not established.

The roughly 22 ppm difference is about 0.0022%, around 900 times smaller than the
2% Z gyro-gain limit. It can matter greatly for accumulated height without directly
explaining the repeated large Z gain correction. Clock and calibration must be studied
together rather than treating the timestamp difference as the whole explanation.

| Date | POS-tag mean period error (ppm) | UTC elapsed − POS elapsed (ms) |
|---|---:|---:|
{secondary_table}

The report also retains interval extrema, cumulative drift extrema and effective rate. Compatibility
with a rounded time lattice is a diagnostic; it does not determine hardware resolution.

[Clock bins](clock-bins.csv) preserve every consecutive 200-packet block, including
partial final blocks, packet offsets, time span and sums of the original six signed
integers. These are compact timing checks, not new scientific fit intervals. Original
individual measurements remain in the retained source files. Detailed numerical values
and input/source/artifact hashes are retained beside this report.

## What the independent controls establish

Each timing control generates its increments from a known physical period, independently
of its packet tags. Stationary specific force cancels known gravity under the correct
integration convention. A known constant-rate angular prediction is checked against
the generated angle increments; raw angle increments are not multiplied by dt again.
All correct-clock maximum velocity and angular errors are below 10⁻¹⁰ in their units.

| Known construction | Wrong-clock maximum velocity error (m/s) | Wrong-clock maximum height error (m) |
|---|---:|---:|
{control_table}

The controls show that fixed-period measurements with packet jitter need nominal timing,
whereas measurements genuinely accumulated over variable periods need elapsed timing.
A timestamp scale error can also create accumulated velocity and height error. These
are 120-second one-dimensional physical controls; their errors are not estimates of
NASA instrument error.

A further stationary control uses the actual selected UTC timestamp series, but
**synthetic force increments** accumulated over exactly 5 ms. With header timing it
produces the height changes below. A single analytically calculated gravity adjustment
matches mean duration; it is not a fitted NASA calibration.

| Date | Synthetic header-clock final height (m) | Mean-duration gravity adjustment (m/s²) | Maximum height after adjustment (m) |
|---|---:|---:|---:|
{gravity_table}

This demonstrates a timing/gravity trade-off on the observed time grid. It does not
establish that NASA increments span exactly 5 ms, or explain the actual nine-metre
vertical discrepancy in full. No observed accelerometer values enter this control.

The actual reoptimized control's gravity correction moved by about **+0.040 to
+0.042 m/s²**, while Z accelerometer offset and gain also changed. That is much larger
and opposite in sign to the simple stationary mean-duration adjustment above. The
[saved calibration audit](../ilvis0-clock-calibration-audit-20261011/README.md)
and hashed parameter-change input preserve those values. The single-channel illustration
therefore cannot identify the actual compensation path. A coupled three-dimensional
control and the matched profile study remain necessary.

For the independent scalar gyro equation, constant rotation leaves gain and offset
with rank one. Varying the known rotation raises their rank to two when the clock is
known: direct least squares and QR both recover the known predictions and parameters.
When clock scale is also free, three parameters still have only rank two. A second
gain/offset/clock tuple reproduces the same measured rate exactly to numerical precision.
Heading variation can improve gain–offset separation without independently resolving
clock scale. This scalar result does not establish the rank of the full GPS/IMU fit;
receiver timing and other measured channels may supply additional constraints.

## Next test

The [reoptimized clock comparison](../ilvis0-clock-trial-20261010/README.md) already
shows that recalibration repairs most of the fixed-parameter vertical error on the
control. The present timing audit and controls do not choose a clock from that better
fit. Next inspect accumulated-force and gyro sensitivities under the same calibration,
and qualify numerical methods on coupled physical controls before budgeting matched
joint Z gain–offset profiles. Use the [focused plan](../ILVIS0_DIAGNOSTIC_PLAN.md).
Neither the failed stopping trial nor the original corpus is resumed.

Reproduce this bounded audit:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-clock-audit-20261011/build_report.py
```
'''
    HERE.mkdir(parents=True,exist_ok=True)
    with (HERE/'clock-bins.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(bins[0]),lineterminator='\n'); writer.writeheader(); writer.writerows(bins)
    payload=dict(version=audit.VERSION,recordings=reports,controls=controls,
        saved_rotating_calibration_changes=calibration,observed_fit_starts=0,
        native_predictions=0,scientific_decision='abstain',clock_independently_established=False)
    (HERE/'summary.json').write_text(json.dumps(payload,sort_keys=True,indent=2)+'\n')
    (HERE/'README.md').write_text(text)
    sources=[Path(__file__),Path(audit.__file__),Path(applanix.__file__),Path(ilvis0.__file__),
        Path(ilvis0_followup.__file__),Path(ilvis0_saved_audit.__file__)]
    receipt=dict(version=audit.VERSION,inputs=inputs,sources={str(p.resolve()):sha(p) for p in sources},
        artifacts={n:sha(HERE/n) for n in ('README.md','summary.json','clock-bins.csv')},
        observed_fit_starts=0,native_predictions=0)
    (HERE/'report-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    return payload


if __name__=='__main__':
    result=build()
    print(json.dumps(dict(recordings=len(result['recordings']),controls_passed=len(result['controls']),
        observed_fit_starts=0,native_predictions=0)))
