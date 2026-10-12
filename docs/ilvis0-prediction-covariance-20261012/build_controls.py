# SPDX-License-Identifier: AGPL-3.0-or-later
"""Qualify the worker on software data only; never authorize or launch archive fits."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from lll import runtime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'analysis/tests'))
import ilvis0_prediction_covariance_worker as worker


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build():
    tests=['test_ilvis0_prediction_covariance_worker.py','test_ilvis0_prediction_comparison_plan.py',
        'test_ilvis0_uncertainty_adapter.py']
    source_names=['analysis/tests/ilvis0_prediction_covariance_worker.py',
        'analysis/lll/ilvis0_sweep_journal.py','analysis/lll/ilvis0_prediction_comparison_plan.py',
        'analysis/lll/ilvis0_uncertainty_adapter.py','analysis/lll/ilvis0_uncertainty_geometry.py',
        'analysis/lll/ilvis0_error_model.py','analysis/lll/ilvis0_shape.py',
        'analysis/lll/ilvis0_exploratory.py','analysis/lll/ilvis0_geographic_controls.py',
        'analysis/lll/ilvis0_latitude_controls.py','analysis/lll/ilvis0_estimator.py',
        'analysis/lll/ilvis0_native.c','analysis/lll/ilvis0_tangent.cpp',
        'analysis/tests/ilvis0_uncertainty_adapter_controls.py']
    source_names += ['analysis/tests/'+name for name in tests]+[str(Path(__file__).relative_to(ROOT))]
    sources={name:sha(ROOT/name) for name in source_names}
    result=subprocess.run([sys.executable,'-m','pytest','-q',
        *[str(ROOT/'analysis/tests'/name) for name in tests],'--tb=short'],cwd=ROOT,
        env={**os.environ,'PYTHONPATH':str(ROOT/'analysis'),'OPENBLAS_NUM_THREADS':'2',
            'OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2'},capture_output=True,text=True,timeout=90)
    if result.returncode or '39 passed' not in result.stdout:
        raise ValueError('worker qualification failed:\n'+result.stdout+result.stderr)
    with TemporaryDirectory(prefix='ilvis0-worker-control-') as directory:
        report=worker.software_control(Path(directory))
        if not (report['maximum_truth_error_m']<.002 and report['prefix_agreement']
                and report['diagnostic_native_sweeps']==13 and report['epochs_written']==24):
            raise ValueError('software prediction control failed')
        shutil.copyfile(report.pop('residual_path'),HERE/'software-epochs.csv.gz')
    if any(sha(ROOT/name)!=digest for name,digest in sources.items()):raise ValueError('qualification source changed')
    report.update(passed_checks=39,archive_records_loaded=0,observed_fit_starts=0,
        software_only=True,scientific_decision='abstain',archive_uncertainty_calibrated=False)
    (HERE/'control-results.json').write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n')
    (HERE/'test-output.txt').write_text(result.stdout)
    (HERE/'CONTROL.md').write_text(f'''# Worker software qualification

All 39 targeted checks passed. They cover durable pre-call charges, failed and
interrupted work, separate fit/diagnostic limits, changed authorization, duplicate
workers, journal integrity, failed-fit abstention, all 27 native derivative columns
and the actual fit-to-prediction artifact path.

An independent analytic geographic control exercises the real native value and
tangent implementations, fits a training subset, predicts the remaining epochs,
and writes compressed receiver-error output. Its maximum position error is
{report['maximum_truth_error_m']:.6g} m, below the predeclared 0.002 m control limit.
Training and full-record predictions agree on their shared prefix. The descriptive
probe stage charges exactly 13 native sweeps for this six-parameter software case.
The archive cases permit all 26 or 27 active directions and reserve at most 55.

The full worker-task check also verifies training-only initialization, saved
receiver/probe hashes and accounting against the on-disk journal. A changed charge
journal is refused even when its total count matches. Publication cannot launch
the worker; a completed worker cannot enter native integration again.

These are software controls, not NASA measurements or validation of archive
coverage. They do not prove global optima, unique calibration, calibrated receiver
error or nonlinear confidence intervals. No NASA originals were read and no
observed-data starts were made. Native scientific studies remain separately frozen.
''')
    receipt=dict(version=worker.VERSION,sources=sources,numerical_environment=runtime.numerical_environment(),
        artifacts={name:sha(HERE/name) for name in ('CONTROL.md','control-results.json',
            'test-output.txt','software-epochs.csv.gz')},observed_fit_starts=0,archive_records_loaded=0)
    (HERE/'control-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print('39 worker/planning/native checks passed; zero observed starts or archive reads.')


if __name__=='__main__':build()
