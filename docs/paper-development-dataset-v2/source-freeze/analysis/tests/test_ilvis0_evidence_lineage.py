# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest


def module():
    from lll import ilvis0_evidence_lineage
    return ilvis0_evidence_lineage


def acquisition():
    catalog=[dict(task_id=str(i),filename=f'{i}.013',url=f'https://archive/{i}.013',date='date',size_mib_reported=1.5) for i in range(4)]
    inventory=[dict(r,source_sha256=str(i)*64,source_bytes=123,state='unresolved',cleanup_pending=False) for i,r in enumerate(catalog)]
    inventory[1]['state']='discarded_no_level';inventory[3]['source_sha256']=inventory[0]['source_sha256']
    retained=[dict(task='0',filename='0.013',source_sha256='0'*64,state='segments_available',selected_stretches='1',
        selection_version='frozen',selection_sha256='f'*64)]
    follow=[dict(task_id='2',source_sha256='2'*64,state=s,reason='no level window') for s in ('prepared','removed')]
    duplicate=[dict(task_id='3',canonical_task_id='0',source_sha256='0'*64,state=s,reason='identical bytes') for s in ('prepared','removed')]
    selected=[dict(segment_id='selected',task='0',source_sha256='0'*64)]
    return dict(catalog=catalog,inventory=inventory,retained=retained,followup=follow,duplicates=duplicate,selected=selected)


def test_census_reconciles_all_sources_without_counting_alias_as_observation():
    source=acquisition();before=copy.deepcopy(source);result=module().reconcile_catalog(**source)
    assert source==before and len(result['rows'])==4
    assert result['summary']['catalog_rows']==4
    assert result['summary']['storage_counts']==dict(retained=1,discarded_no_level=2,duplicate_removed=1,unresolved=0)
    assert result['summary']['complete'] is True
    assert result['summary']['selected_stretches']==1
    assert result['rows'][3]['canonical_task_id']=='0'
    assert result['rows'][0]['source_bytes']==123
    assert result['rows'][0]['size_mib_reported']==1.5


def test_absence_from_retained_pool_does_not_prove_deletion():
    source=acquisition();source['followup']=[];result=module().reconcile_catalog(**source)
    assert result['summary']['complete'] is False
    assert result['rows'][2]['recorded_pipeline_storage']=='unresolved'


def test_missing_hash_stays_unknown_and_invalid_nonempty_hash_is_rejected():
    source=acquisition();source['inventory'][1]['source_sha256']=''
    result=module().reconcile_catalog(**source)
    assert result['rows'][1]['source_sha256']=='' and result['summary']['missing_source_hashes']==1
    assert result['summary']['complete'] is False
    source['inventory'][1]['source_sha256']='not-a-valid-source-hash'
    with pytest.raises(ValueError):module().reconcile_catalog(**source)


@pytest.mark.parametrize('bad',['alias_hash','journal_hash','prepared_missing','retained_conflict','catalog_url','selected_discarded'])
def test_conflicting_acquisition_evidence_is_rejected(bad):
    source=acquisition()
    if bad=='alias_hash':source['duplicates'][1]['source_sha256']='9'*64
    elif bad=='journal_hash':source['followup'][1]['source_sha256']='9'*64
    elif bad=='prepared_missing':source['followup']=source['followup'][1:]
    elif bad=='retained_conflict':source['retained'].append(dict(source['retained'][0],task='1',filename='1.013',source_sha256='1'*64))
    elif bad=='catalog_url':source['inventory'][0]['url']='https://different'
    else:source['selected'].append(dict(segment_id='bad',task='1',source_sha256='1'*64))
    with pytest.raises(ValueError):module().reconcile_catalog(**source)


def test_execution_owner_uses_own_results_instead_of_publisher_environment():
    owners=[dict(manifest='parent',tasks={'a','b'},owned_results={'a'},environment={'python':'older'}),
        dict(manifest='continuation',tasks={'b'},owned_results={'b'},environment={'python':'actual'})]
    result=module().resolve_owner('b',owners)
    assert result['manifest']=='continuation' and result['environment']['python']=='actual'
    with pytest.raises(ValueError):module().resolve_owner('b',owners+[dict(owners[1],manifest='conflicting')])


def test_interruption_preserves_unknown_result_and_reserved_owner():
    owners=[dict(manifest='parent',tasks={'interrupted'},owned_results=set(),environment={'python':'original'})]
    with pytest.raises(ValueError):module().resolve_owner('interrupted',owners)
    assert module().resolve_owner('interrupted',owners,interrupted=True)['manifest']=='parent'


def test_published_conditional_label_is_not_replaced_by_operation_pass():
    row=dict(segment_id='s',case_id='c',model='m',converged='False',cost='12.5',parameters='{"x": 1}',evaluations='4')
    fit=dict(converged=False,residual_sum_squares=12.5,parameters=dict(x=1),evaluations=4)
    module().validate_published(row,fit)
    with pytest.raises(ValueError):module().validate_published(dict(row,converged='True'),fit)
    with pytest.raises(ValueError):module().validate_published(dict(row,cost='13'),fit)
