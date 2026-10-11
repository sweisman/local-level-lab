# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish deterministic coupled physical controls; no observed data or native kernel."""
import csv
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from lll import ilvis0_coupled_controls as controls, ilvis0_forward as forward

HERE=Path(__file__).resolve().parent


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def build():
    results=[controls.run_control(False),controls.run_control(True)]
    if not all(r['passed'] for r in results): raise ValueError('coupled control failed')
    traces=[]; table=[]
    fig,axes=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
    labels={'correct_clock':'Correct clock and calibration','wrong_clock':'50 ppm clock error',
        'coupled_compensation':'Clock error with coupled compensation',
        'external_time':'Same compensation, external observation times'}
    for ax,result in zip(axes,results):
        series={name:result[name]['trace'] for name in ('correct_clock','wrong_clock','coupled_compensation')}
        series['external_time']=result['external_time_trace']
        for name,rows in series.items():
            # Subsample only for display; numerical checks use every increment.
            sample=rows[::25]+[rows[-1]]
            errors=np.array([[r[k] for k in ('north_error_m','east_error_m','down_error_m')] for r in sample])
            norm=np.linalg.norm(errors,axis=1)
            ax.semilogy([r['time_by_packet_index_s'] for r in sample],np.maximum(norm,1e-12),
                label=labels[name],linestyle='--' if name=='coupled_compensation' else '-')
            traces.extend(dict(control=result['control'],variant=name,**{k:r[k] for k in
                ('time_by_packet_index_s','north_error_m','east_error_m','down_error_m')}) for r in sample)
        ax.set(title=result['control'].replace('_',' ').capitalize(),xlabel='Physical time (s)',ylabel='Position error (m)')
        ax.grid(alpha=.25)
        for name in ('correct_clock','wrong_clock','coupled_compensation'):
            r=result[name]
            table.append(f"| {result['control']} | {name} | {r['maximum_position_error_m']:.6g} | {r['maximum_attitude_error_rad']:.3g} |")
    axes[1].legend(fontsize=7,loc='lower right')
    fig.suptitle('Known 3-D motion: timing and calibration interaction')
    HERE.mkdir(parents=True,exist_ok=True)
    with matplotlib.rc_context({'svg.hashsalt':controls.VERSION}):
        fig.savefig(HERE/'position-errors.svg',metadata={'Date':None})
    plt.close(fig)
    with (HERE/'display-traces.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(traces[0]),lineterminator='\n'); writer.writeheader(); writer.writerows(traces)
    external=max(r['external_time_max_position_error_m'] for r in results)
    gain=max(r['calibration_recovery']['maximum_gain_error'] for r in results)
    bias=max(r['calibration_recovery']['maximum_bias_error'] for r in results)
    primitive=max(r['production_primitive_max_difference'] for r in results)
    text=f'''# Coupled three-dimensional clock and calibration controls

**Both independently generated controls passed.** Correct timing/calibration recovers
the known motion. A coordinated alternative can hide a clock error at packet endpoints,
but that particular alternative no longer predicts the same positions when observations
have independent time tags. This is software/physics evidence, not new NASA findings.
There were **zero observed-data fit starts and zero native navigation predictions**.

An **IMU (inertial measurement unit)** measures turning and acceleration. These controls
generate three-axis increments for a known moving and turning body in a Cartesian
frame, with explicit gravity and sensor mounting. No NASA measurements or Group1
fused navigation enter the controls. Background Earth/transport terms are zero; this
does not simulate or compare the three geographic Earth models.

## Known construction

Each control contains 2,400 samples at 200 Hz over 12 seconds, with six prescribed
rotation/acceleration legs. The initial velocity is 220 m/s north, 30 m/s east and
0.1 m/s down. One case uses interior calibration values; the second uses values near
the existing study's gain, offset and gravity allowances. Those injected values test
software behavior and are not manufacturer specifications or measured NASA calibration.

The generator integrates the rotating body's specific force analytically, separately
from the reconstruction's midpoint approximation. Numerical quadrature independently
checks that integral. Original physical angle increments are applied once. Known sensor
mounting, all three gain/offset pairs and gravity are explicit. The remaining small
correct-clock position error is the midpoint approximation's error in this control.

The existing Python strapdown primitive agrees with the independent reconstruction
within **{primitive:.3g}** in its component units. This check uses 4,800 Python primitive
steps in total, alongside 14,400 independent reconstruction steps. It does not exercise
the native geographic fitting kernel or qualify its nonlinear optimizer.

## Clock and calibration interaction

| Control | Reconstruction | Maximum position error (m) | Maximum attitude error (rad) |
|---|---|---:|---:|
{chr(10).join(table)}

For clock scale c = 1.00005, the coupled alternative keeps gyro gain unchanged, divides
gyro and accelerometer offsets by c, replaces accelerometer gain by c(1 + gain) − 1,
divides initial velocity by c and gravity by c². Corrected angle increments stay the
same and velocity increments scale by 1/c. Multiplying those velocities by c times the
interval restores almost identical positions at corresponding packet endpoints.
The alternative's physical velocity and calibration differ from the injected truth.

This is a specific possible compensation mechanism. It does not establish which
parameters compensated in the NASA fits. In particular, the observed clock discrepancy
is much smaller than the repeatedly saturated Z gyro-gain allowance.

![Position errors for both controls](position-errors.svg)

Correct-clock and packet-endpoint-compensated curves nearly coincide. The logarithmic
display uses a 10⁻¹² m floor for plotting only; numerical checks retain the actual errors.
Display traces contain every 25th sample plus the final endpoint, without interpolation.

## Independent observation times matter

The packet-endpoint equivalence associates observations by packet number. If receiver
positions instead refer to known physical times, the constructed alternative predicts
the original analytic path at t/c. Its maximum position discrepancy here is
**{external:.6g} m**. The check evaluates the exact piecewise-quadratic path, rather
than interpolating measured positions. It demonstrates that independent observation
time can expose this particular alternative; it does not prove all clock/calibration
ambiguities disappear when additional parameters are free.

An archival qualification control must therefore supply a separately time-tagged
receiver stream, latency assumptions and the actual packet/GPS association. Recovering
motion only at packet endpoints is insufficient. The logged NASA increment integration
period remains to be established or bracketed; these controls choose no real-data clock.

## Calibration recovery and remaining qualification

With the synthetic reference motion, mounting and clock known, SVD least squares and
QR independently recover all six gain/offset channels in both cases: 24 small linear
solves. Maximum gain error is {gain:.3g}; maximum offset error is {bias:.3g} in its
channel units (rad/s or m/s²). Each two-column system has rank two; conditioning is
saved per channel. This is a test with known reference attitude and acceleration,
not calibration recovery from receiver positions alone.

Next qualify the complete nonlinear geographic fitter on independently generated
increments and external receiver epochs, including initialization, latency, coupled
calibration and difficult optima. Then prepare matched observed profiles with their
own finite allowance. The failed six-fit stopping trial and all original NASA findings
stay unchanged. See the [focused plan](../ILVIS0_DIAGNOSTIC_PLAN.md).

Reproduce these bounded software controls:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-coupled-controls-20261011/build_report.py
```
'''
    (HERE/'README.md').write_text(text)
    summaries=[]
    for result in results:
        row={k:v for k,v in result.items() if k!='external_time_trace'}
        for key in ('correct_clock','wrong_clock','coupled_compensation'):
            row[key]={k:v for k,v in row[key].items() if k!='trace'}
        summaries.append(row)
    environment=dict(python=platform.python_version(),numpy=np.__version__,matplotlib=matplotlib.__version__)
    payload=dict(version=controls.VERSION,controls=summaries,environment=environment,
        observed_fit_starts=0,native_predictions=0,full_archival_solver_qualified=False)
    (HERE/'summary.json').write_text(json.dumps(payload,sort_keys=True,indent=2)+'\n')
    sources=[Path(__file__),Path(controls.__file__),Path(forward.__file__),HERE.parents[1]/'analysis/tests/test_ilvis0_coupled_controls.py']
    receipt=dict(version=controls.VERSION,environment=environment,inputs={},
        sources={str(p.resolve()):sha(p) for p in sources},
        artifacts={n:sha(HERE/n) for n in ('README.md','summary.json','display-traces.csv','position-errors.svg')},
        observed_fit_starts=0,native_predictions=0)
    (HERE/'report-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    return payload


if __name__=='__main__':
    result=build()
    print(json.dumps(dict(controls_passed=len(result['controls']),observed_fit_starts=0,native_predictions=0)))
