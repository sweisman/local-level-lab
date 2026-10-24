# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only tests: no numerical library, original source or fit is needed."""
import copy
import pytest


def fixtures():
    group='development-group';sha='a'*64
    rows=[dict(first_index=100,last_index=10099,epochs=10000,duration_s=4999.5,rejection_reasons=[]),
        dict(first_index=12000,last_index=17999,epochs=6000,duration_s=2999.5,rejection_reasons=[])]
    inventory=dict(verified=True,group_id=group,source_sha256=sha,receiver_epochs=20000,eligible=rows)
    previous=dict(verified=True,group_id=group,chosen=dict(first_index=100,last_index=2500),
        source_references=dict(imu=dict(filename='187_rqh01.txt'),
            receiver=dict(filename='187_air1_ppp_2Hz_final.txt',sha256=sha)))
    return inventory,previous


def test_window_plan_selects_fixed_first_last_support_and_marks_already_used_window():
    from lll.airquantumgrav_window_plan import plan
    inventory,previous=fixtures();result=plan(inventory,previous=previous)
    assert [(v['first_index'],v['last_index']) for v in result['windows']]==[(100,2500),(7699,10099),(12000,14400),(15599,17999)]
    assert [v['already_used_for_development'] for v in result['windows']]==[True,False,False,False]
    assert result['additional_windows']==3 and result['conservative_groups']==1
    assert result['independent_replications'] is None
    for row in result['windows']:
        assert row['support_epochs']==2401 and row['query_epochs']==1200
        assert row['query_first_index']==row['first_index']+1
        assert row['query_last_index']==row['last_index']-1
        assert row['training_last_index']==row['first_index']+1599
        assert row['prediction_first_index']==row['first_index']+1601
    assert result['original_reads']==result['protected_reads']==result['native_calls']==result['fit_starts']==0
    assert not result['preparation_authorized'] and not result['confirmation_authorized']


def test_window_plan_is_order_invariant_and_cannot_use_gyro_or_fit_outcomes():
    from lll.airquantumgrav_window_plan import plan
    inventory,previous=fixtures();original=copy.deepcopy(inventory);expected=plan(inventory,previous=previous)
    inventory['eligible'].reverse();inventory['gyro_means']=[999];inventory['model_winner']='flat'
    assert plan(inventory,previous=previous)==expected
    assert original['eligible']!=inventory['eligible']
    assert previous['chosen']==dict(first_index=100,last_index=2500)


def test_short_parent_run_does_not_create_overlapping_or_duplicate_windows():
    from lll.airquantumgrav_window_plan import plan
    inventory,previous=fixtures();inventory['eligible']=[dict(first_index=100,last_index=2500,
        epochs=2401,duration_s=1200.,rejection_reasons=[])]
    result=plan(inventory,previous=previous)
    assert len(result['windows'])==1 and result['additional_windows']==0
    assert result['skipped'][0]['reason']=='last window overlaps the first window'


@pytest.mark.parametrize('change',['unverified','group','source','previous','overlap','count','rejections'])
def test_window_plan_rejects_inconsistent_metadata_without_reselection(change):
    from lll.airquantumgrav_window_plan import plan
    inventory,previous=fixtures()
    if change=='unverified':inventory['verified']=False
    if change=='group':previous['group_id']='protected-group'
    if change=='source':inventory['source_sha256']='b'*64
    if change=='previous':previous['chosen']['last_index']+=1
    if change=='overlap':inventory['eligible'][1].update(first_index=9000,last_index=14999)
    if change=='count':inventory['eligible'][0]['epochs']-=1
    if change=='rejections':inventory['eligible'][0]['rejection_reasons']=['speed']
    with pytest.raises(ValueError):plan(inventory,previous=previous)


def test_window_freeze_requires_qualification_before_reading_parents_or_writing(tmp_path):
    from lll.airquantumgrav_window_plan import freeze
    with pytest.raises(ValueError,match='qualification'):freeze(tmp_path,qualification=None)
    assert not (tmp_path/'docs').exists()


def test_window_parent_reader_rejects_open_inputs_before_originals_or_numerical_imports(tmp_path):
    from lll.airquantumgrav_window_plan import read_parents
    with pytest.raises(ValueError,match='closed study'):read_parents(tmp_path)
