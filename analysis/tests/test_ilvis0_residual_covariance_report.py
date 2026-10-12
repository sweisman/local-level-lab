# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]


def report():
    path=ROOT/'docs/ilvis0-residual-covariance-20261012/build_report.py'
    spec=importlib.util.spec_from_file_location('residual_covariance_report',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_complete_report_is_saved_only_preserves_failures_and_checks_receipts(tmp_path,monkeypatch):
    r=report();monkeypatch.setattr(r,'HERE',tmp_path)
    from lll import ilvis0_segments,ilvis0_shape,ilvis0_exploratory
    def forbidden(*a,**kw):pytest.fail('covariance audit must not extract or refit')
    monkeypatch.setattr(ilvis0_segments,'extract_segment',forbidden)
    monkeypatch.setattr(ilvis0_shape,'fit_shape_candidate',forbidden)
    monkeypatch.setattr(ilvis0_shape,'load_tangent',forbidden)
    monkeypatch.setattr(ilvis0_exploratory,'load_kernel',forbidden)
    r.build()
    out=r.load(tmp_path/'summary.json')
    assert out['saved_fits']==81 and out['unique_recordings']==2
    assert out['optimizer_starts']==out['native_predictions']==0
    assert len(out['series'])==162
    assert sum(s['status']=='unresolved' for s in out['series'])==4
    assert all(not s['covariance_calibrated'] and not s['resampled'] for s in out['series'])
    receipt=r.load(tmp_path/'report-receipt.json')
    for name,digest in receipt['artifacts'].items():assert r.sha(tmp_path/name)==digest
    assert (tmp_path/'autocorrelation.svg').exists()
    assert (tmp_path/'cross-axis.svg').exists()
    assert (tmp_path/'spectra.svg').exists()


@pytest.mark.parametrize('error',['hash','rms','cost','escape'])
def test_saved_epoch_values_and_scope_are_verified(error):
    r=report();grids=r.read_inputs();fit=grids['original'][0]['fits'][0]
    if error=='hash':fit['residual_sha256']='0'*64
    if error=='rms':fit['residual_rms_neu_m'][0]+=1
    if error=='cost':fit['residual_sum_squares']+=1
    if error=='escape':fit['residual_file']='../not-in-scope.csv.gz'
    with pytest.raises(ValueError):r.epoch_values('original',fit)
