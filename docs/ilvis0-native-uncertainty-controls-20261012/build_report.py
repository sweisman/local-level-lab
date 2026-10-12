# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reproduce six bounded geographic software controls; no archive input or fitting."""
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from lll import ilvis0_exploratory as explore, ilvis0_shape as shape, runtime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'analysis/tests'))
import ilvis0_uncertainty_adapter_controls as controls


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build():
    names=['analysis/tests/ilvis0_uncertainty_adapter_controls.py',
        'analysis/tests/test_ilvis0_uncertainty_adapter.py',
        'analysis/lll/ilvis0_uncertainty_adapter.py',
        'analysis/lll/ilvis0_uncertainty_geometry.py',
        'analysis/lll/ilvis0_error_model.py','analysis/lll/ilvis0_geographic_controls.py',
        'analysis/lll/ilvis0_latitude_controls.py','analysis/lll/ilvis0_exploratory.py',
        'analysis/lll/ilvis0_shape.py','analysis/lll/ilvis0_estimator.py',
        'analysis/lll/ilvis0_forward.py','analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp','analysis/lll/runtime.py']
    sources={name:sha(ROOT/name) for name in names}
    sources[str(Path(__file__).relative_to(ROOT))]=sha(__file__)
    with TemporaryDirectory(prefix='ilvis0-uncertainty-controls-') as directory:
        value,vmeta=explore.load_kernel(directory)
        tangent,tmeta=shape.load_tangent(directory)
        cases=[controls.run_case(model,degrees,(value,tangent))
            for model in explore.MODELS for degrees in (-45.,45.)]
    if not all(row['passed'] for row in cases):raise ValueError('native control failed')
    if any(sha(ROOT/name)!=digest for name,digest in sources.items()):
        raise ValueError('control source changed')
    summary=dict(version='ilvis0-native-uncertainty-controls-v1',cases=cases,
        native_sweeps=sum(sum(row['native_sweeps'].values()) for row in cases),
        observed_fit_starts=0,archive_records_loaded=0,software_controls_only=True,
        confidence_calibrated=False,scientific_decision='abstain')
    (HERE/'summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2,allow_nan=False)+'\n')
    rows=['| Candidate | Latitude | Known-path error (m) | Largest derivative discrepancy (m) | Training rank / parameters |',
        '|---|---:|---:|---:|---:|']
    for row in cases:
        rows.append(f"| {row['model']} | {row['latitude_deg']:+g}° | "
            f"{row['truth_maximum_position_error_m']:.3g} | "
            f"{row['maximum_derivative_error_m_per_normalized_parameter']:.3g} | "
            f"{row['geometry']['rank']}/27 |")
    readme='''# Native prediction uncertainty controls

The uncertainty adapter now consumes the existing inertial measurement unit (IMU)
integration and its derivatives. Six independently constructed short geographic
paths check both hemispheres and all three physical candidates. All 27 parameter
columns, including a possible upstream rotation-removal fraction, agree with
separate central differences of the native value implementation.

'''+ '\n'.join(rows)+'''

Derivative discrepancies are per unit of a normalized parameter. Acceptance limits
were fixed at 0.002 m for known-path error and 0.0002 m for derivative discrepancy.
The paths include receiver observations between packet boundaries and two clock
constructions. Training uses the first 16 receiver epochs; prediction uses the last
eight. Future predictions cannot change the training rank calculation.

The six-case matrix uses exactly 348 native software sweeps, with zero optimizer
starts and no NASA originals read. Failed calls remain charged; allowances are
checked before execution. Boundary parameters remain in the rank calculation.

These 12-second controls verify interfaces and derivatives. They do not validate
archive uncertainty, recover unknown processing, establish confidence coverage or
prove a scientific model. Their limited calibration rank is reported explicitly.
The adapter reports local unconstrained geometry and sampled prediction changes;
neither is a calibrated interval or a reoptimized profile.

Reproduce from the repository root:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-native-uncertainty-controls-20261012/build_report.py
```

The numerical comparison will be prepared separately before any archive fits run.
'''
    (HERE/'README.md').write_text(readme)
    receipt=dict(version=summary['version'],sources=sources,
        numerical_environment=runtime.numerical_environment(),native_builds=dict(value=vmeta,tangent=tmeta),
        artifacts={name:sha(HERE/name) for name in ('summary.json','README.md')},
        observed_fit_starts=0,archive_records_loaded=0)
    (HERE/'report-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print('Six native controls passed: 27 columns each, 348 software sweeps, zero archive fits or reads.')


if __name__=='__main__':build()
