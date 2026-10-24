# SPDX-License-Identifier: AGPL-3.0-or-later
import csv
import gzip
import io
import json

import pytest

from lll.airquantumgrav_inventory_report import reconcile,render
from test_airquantumgrav_inventory import evaluation_fixture


def evidence(tmp_path,monkeypatch,count):
    mod,context,saved,_,_=evaluation_fixture(tmp_path,monkeypatch,count)
    result=mod.evaluate(mod.tasks()[0],context)
    table=lambda raw:list(csv.DictReader(io.StringIO(raw.decode())))
    return dict(selected=json.loads(gzip.decompress(saved['selection.json.gz'])),result=result,
        epochs=table(gzip.decompress(saved['epoch-reasons.csv.gz'])),
        eligible=table(saved['eligible.csv']),rejected=table(saved['rejected_runs.csv']))


@pytest.mark.parametrize('count',[10,2401])
def test_saved_inventory_report_covers_every_epoch_without_redecoding(tmp_path,monkeypatch,count):
    values=evidence(tmp_path,monkeypatch,count);report=reconcile(**values)
    assert report['verified'] and report['receiver_epochs']==count
    assert report['original_reads']==report['numerical_work']==0
    text=render(report)
    assert 'not straight, level legs' in text and 'No ESA shape' in text


@pytest.mark.parametrize('fault',['summary','csv','overlap','epoch','charge','protected'])
def test_saved_inventory_report_rejects_changed_or_incomplete_evidence(tmp_path,monkeypatch,fault):
    v=evidence(tmp_path,monkeypatch,2401)
    if fault=='summary':v['result']['eligible_count']=0
    elif fault=='csv':v['eligible'][0]['mean_speed_kmh']='999'
    elif fault=='overlap':v['selected']['eligible']*=2;v['eligible']*=2
    elif fault=='epoch':v['epochs'][0]['rejection_reasons']='speed'
    elif fault=='charge':v['result']['charged_work']['receiver_file_passes']=2
    else:v['result']['protected_reads']=1
    with pytest.raises(ValueError):reconcile(**v)
