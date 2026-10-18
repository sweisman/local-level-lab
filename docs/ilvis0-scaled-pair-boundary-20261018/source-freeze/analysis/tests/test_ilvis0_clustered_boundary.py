# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll.ilvis0_receipt_journal import Ledger
from test_ilvis0_boundary_adapter import Surface,geometry,physical


def test_full_cluster_search_reaches_true_knot_from_nonstationary_right_edge(tmp_path):
    from lll.ilvis0_clustered_boundary import check_endpoint
    s=Surface();point=np.array([0.,s.truth+1e-7]);saved=s.evaluate(point,fresh=True)[0];s.calls.clear()
    book=Ledger(tmp_path,'a'*64,['endpoint'],fit_limit=1,diagnostic_limit=26);book.start('endpoint')
    result=check_endpoint(book,'endpoint',lambda u,m:s.evaluate(u,fresh=True),'sphere_still',point,saved,physical,
        time_index=1,geometry_at=None,times=s.times,packet_count=s.count,scale=s.scale)
    assert result['passed'] and result['boundary_check']['passed']
    assert result['normalized_parameters']==pytest.approx([0.,s.truth],abs=0,rel=0)
    assert len(s.calls)==book.count('endpoint','diagnostic')<=26
    assert result['cumulative_from_source']['passed'] and result['center_native'] is not None


@pytest.mark.parametrize('kind',['maximum','discontinuous','unfinished_nuisance'])
def test_bad_sources_keep_the_original_abstention(kind,tmp_path):
    from lll.ilvis0_clustered_boundary import check_endpoint
    s=Surface(kind);point=np.array([0.,0.]);saved=s.evaluate(point,fresh=True)[0];s.calls.clear()
    book=Ledger(tmp_path,'a'*64,['endpoint'],fit_limit=1,diagnostic_limit=26);book.start('endpoint')
    result=check_endpoint(book,'endpoint',lambda u,m:s.evaluate(u,fresh=True),'sphere_still',point,saved,physical,
        time_index=1,geometry_at=None,times=s.times,packet_count=s.count,scale=s.scale)
    assert not result['passed'] and book.count('endpoint','diagnostic')<=26


def test_incompatible_source_is_rejected_after_one_charged_call(tmp_path):
    from lll.ilvis0_clustered_boundary import check_endpoint
    s=Surface();book=Ledger(tmp_path,'a'*64,['endpoint'],fit_limit=1,diagnostic_limit=26);book.start('endpoint')
    with pytest.raises(ValueError,match='source'):
        check_endpoint(book,'endpoint',lambda u,m:s.evaluate(u,fresh=True),'sphere_still',[0.,0.],np.array([100.,0.,40.]),physical,
            time_index=1,geometry_at=None,times=s.times,packet_count=s.count,scale=s.scale)
    assert book.count('endpoint','diagnostic')==1


def test_failed_native_call_remains_charged(tmp_path):
    from lll.ilvis0_clustered_boundary import check_endpoint
    s=Surface();book=Ledger(tmp_path,'a'*64,['endpoint'],fit_limit=1,diagnostic_limit=26);book.start('endpoint')
    def fail(*args):raise RuntimeError('native failure')
    with pytest.raises(RuntimeError,match='native failure'):
        check_endpoint(book,'endpoint',fail,'sphere_still',[0.,0.],np.array([1.,0.,40.]),physical,
            time_index=1,geometry_at=None,times=s.times,packet_count=s.count,scale=s.scale)
    assert book.count('endpoint','diagnostic')==1
