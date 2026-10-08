# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import json
import csv
import pytest


def worker():
    try:return importlib.import_module('ilvis0_segment_worker')
    except ModuleNotFoundError:pytest.fail('all-segment runner is not implemented')


def test_finite_allowance_is_derived_from_all_selected_segments():
    w=worker();assert w.allowance(53)==dict(primary_starts=636,maximum_starts=742,
        maximum_starts_per_identity=2,maximum_evaluations_per_start=200)
    assert w.allowance(0)['maximum_starts']==0


def test_interrupted_starts_and_frozen_identity_set(tmp_path):
    w=worker();path=tmp_path/'starts.jsonl';digest='a'*64;tasks=['s::c::m']
    assert w.charge(path,tasks[0],digest,tasks,2)['start']==1
    assert w.charge(path,tasks[0],digest,tasks,2)['start']==2
    with pytest.raises(ValueError):w.charge(path,tasks[0],digest,tasks,2)
    with pytest.raises(ValueError):w.charge(path,'other',digest,tasks,3)
    assert len(path.read_text().splitlines())==2


def test_corrupt_cached_inventory_or_profile_is_rejected(tmp_path):
    w=worker();path=tmp_path/'cached.json';digest='a'*64
    w.save(path,dict(segments=[]),digest)
    assert w.cached(path,digest)==dict(segments=[])
    row=json.loads(path.read_text());row['result']['segments']=[dict(duration_s=999)]
    path.write_text(json.dumps(row))
    with pytest.raises(ValueError,match='integrity'):w.cached(path,digest)


def test_public_catalog_records_exact_dates_criteria_and_exclusions_before_fits(tmp_path):
    w=worker();segment=dict(segment_id='s',start_s=172810.,end_s=173050.,duration_s=240.,
        imu_type=8,time_types=2,signature='mount',raw_guard_s=.2,
        minimum_receiver_ground_speed_kmh=700.,median_receiver_ground_speed_kmh=710.)
    record=dict(task='a',filename='sample.013',state='segments_available',source_sha256='a'*64,
        timing=dict(dates=['2009-04-14']),segments=[segment],rejections={})
    excluded=dict(task='b',filename='slow.013',state='no_qualifying_segment',source_sha256='b'*64,
        segments=[],rejections=dict(below_ground_speed=70))
    selected=dict(segment=segment,task='a',filename='sample.013')
    selection=dict(records=[record,excluded],selected=[selected],segments=1,qualifying_seconds=240.,
        canonical_tasks_by_source_sha256={'a'*64:'a','b'*64:'b'})
    w.catalog(tmp_path,selection,'f'*64)
    with (tmp_path/'eligible-stretches.csv').open() as s:rows=list(csv.DictReader(s))
    assert rows[0]['start_utc']=='2009-04-14T00:00:10Z'
    assert rows[0]['end_utc']=='2009-04-14T00:04:10Z'
    assert rows[0]['filename']=='sample.013' and rows[0]['source_sha256']=='a'*64
    with (tmp_path/'files.csv').open() as s:files=list(csv.DictReader(s))
    assert len(files)==2 and files[1]['selected_stretches']=='0'
    assert 'below_ground_speed' in files[1]['rejection_counts']
    assert (tmp_path/'ELIGIBILITY.md').exists()


def test_completed_empty_run_can_be_audited_and_packaged_without_predictions(tmp_path):
    w=worker();out=tmp_path/'data';out.mkdir();(out/'source-freeze').mkdir()
    sources={};manifest=dict(sources=sources,inputs={},environment=w.runtime.numerical_environment())
    w.follow.atomic_json(out/'manifest.json',manifest)
    selection=dict(records=[],selected=[],segments=0,qualifying_seconds=0.,canonical_tasks_by_source_sha256={})
    w.observation.gzip_json(out/'selection.json.gz',selection)
    fit_manifest=dict(selection_manifest_sha256=w.il.sha256(out/'manifest.json'),
        selection_sha256=w.il.sha256(out/'selection.json.gz'),identities=[],segments=0,**w.allowance(0))
    w.follow.atomic_json(out/'fit-manifest.json',fit_manifest)
    summary=dict(results=[],starts=0,fitted_segments=0,unsupported_segments=0)
    w.observation.gzip_json(out/'summary.json.gz',summary)
    completion=dict(state='complete',manifest_sha256=w.il.sha256(out/'manifest.json'),
        fit_manifest_sha256=w.il.sha256(out/'fit-manifest.json'),summary_sha256=w.il.sha256(out/'summary.json.gz'))
    w.follow.atomic_json(out/'completion.json',completion)
    (tmp_path/'docs/research-next-stage-20261006').mkdir(parents=True)
    w.follow.atomic_json(tmp_path/'docs/research-next-stage-20261006/readiness.json',
        dict(ilvis0_physical_pipeline={},artifact_sha256={}))
    w.package_completed(tmp_path,out)
    assert (out/'package-status.json').exists()
    assert (tmp_path/'docs/ilvis0-highspeed-segments-20261008/eligible-stretches.csv').exists()
    w.follow.atomic_json(out/'completion.json',dict(completion,summary_sha256='0'*64))
    with pytest.raises(ValueError,match='completion'):w.package_completed(tmp_path,out)
