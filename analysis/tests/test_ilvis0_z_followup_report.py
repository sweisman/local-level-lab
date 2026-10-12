# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]


def report():
    path=ROOT/'docs/ilvis0-z-followup-audit-20261012/build_report.py'
    spec=importlib.util.spec_from_file_location('z_followup_report',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_full_report_uses_saved_artifacts_only(tmp_path,monkeypatch):
    r=report();monkeypatch.setattr(r,'HERE',tmp_path)
    from lll import ilvis0_segments,ilvis0_shape,ilvis0_exploratory
    def forbidden(*a,**kw):pytest.fail('saved audit must not extract, predict or fit')
    monkeypatch.setattr(ilvis0_segments,'extract_segment',forbidden)
    monkeypatch.setattr(ilvis0_shape,'fit_shape_candidate',forbidden)
    monkeypatch.setattr(ilvis0_shape,'load_tangent',forbidden)
    monkeypatch.setattr(ilvis0_exploratory,'load_kernel',forbidden)
    r.build()
    receipt=r.load(tmp_path/'report-receipt.json')
    assert receipt['optimizer_starts']==receipt['native_predictions']==0
    for name,digest in receipt['artifacts'].items():assert r.sha(tmp_path/name)==digest
    out=r.load(tmp_path/'summary.json')
    assert len(out['residuals'])==243 and len(out['failures'])==2
    assert out['studies'][2]['shape_preference']=='unresolved'


@pytest.mark.parametrize('corruption',['hash','rms','cost','escape'])
def test_bad_saved_epoch_evidence_is_rejected(corruption):
    r=report();data=r.read_inputs();fit=data['original'][0]['fits'][0]
    if corruption=='hash':fit['residual_sha256']='0'*64
    if corruption=='rms':fit['residual_rms_neu_m'][0]+=1
    if corruption=='cost':fit['residual_sum_squares']+=1
    if corruption=='escape':fit['residual_file']='../outside.csv.gz'
    with pytest.raises(ValueError):r.residual_table(data)


@pytest.mark.parametrize('corruption',['inventory_hash','source_hash'])
def test_interval_provenance_is_checked_before_publication(tmp_path,monkeypatch,corruption):
    import csv
    import json
    r=report();monkeypatch.setattr(r,'HERE',tmp_path)
    inventory_dir=tmp_path/'inventory';inventory_dir.mkdir()
    path=inventory_dir/'eligible-stretches.csv'
    with r.INVENTORY.open(newline='') as stream:
        reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
    if corruption=='source_hash':
        next(x for x in rows if x['segment_id']==r.analysis.TARGETS['original'])['source_sha256']='0'*64
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    digest='0'*64 if corruption=='inventory_hash' else r.sha(path)
    (inventory_dir/'evidence-receipt.json').write_text(json.dumps({'artifacts':{path.name:digest}}))
    monkeypatch.setattr(r,'INVENTORY',path)
    with pytest.raises(ValueError):r.build()
