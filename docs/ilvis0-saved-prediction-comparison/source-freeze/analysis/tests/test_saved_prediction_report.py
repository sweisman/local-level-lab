# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest


def test_real_saved_sources_freeze_reconcile_and_publish_without_refitting(tmp_path,monkeypatch):
    monkeypatch.setenv('MPLCONFIGDIR',str(tmp_path/'matplotlib'))
    pytest.importorskip('matplotlib')
    path=Path(__file__).resolve().parents[2]/'docs/ilvis0-saved-prediction-comparison/build_report.py'
    spec=importlib.util.spec_from_file_location('saved_prediction_report',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    monkeypatch.setattr(m,'DATA',tmp_path/'runtime');monkeypatch.setattr(m,'PUBLIC',tmp_path/'public')
    m.prepare();m.build();report=m.snapshot.check(m.PUBLIC)
    assert report['summary']['fit_records']==18
    assert report['summary']['source_converged_fits']==15
    assert report['summary']['source_unresolved_fits']==3
    assert report['summary']['source_recordings']==1 and report['summary']['conservative_groups']==1
    assert report['summary']['new_native_calls']==0
    with pytest.raises(ValueError):m.build()
