# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll.ilvis0_receipt_journal import Ledger


def surface(kind='minimum'):
    calls=[]
    def native(u,model):
        calls.append(np.array(u));x,t=u;sign=-1. if t<0 else 1.
        factor=-1. if kind=='maximum' else 1.
        if kind=='exception':raise RuntimeError('native failed')
        return np.array([1.+factor*.01*abs(t),.005*x,40.]),np.array([[0.,factor*.01*sign],[.005,0.],[0.,0.]]),0
    return native,calls


def geometry(t):return dict(point=t,side_geometry_supported=True,knots=[-1.,0.,1.])


def test_exact_cusp_passes_real_ledger_and_preserves_source_relocation(tmp_path):
    from lll.ilvis0_exact_boundary import check_endpoint
    native,calls=surface();saved=native([0.,1e-8],'sphere_still')[0];calls.clear()
    book=Ledger(tmp_path,'a'*64,['endpoint'],fit_limit=1,diagnostic_limit=30);book.start('endpoint')
    result=check_endpoint(book,'endpoint',native,'sphere_still',[0.,0.],saved,
        lambda d:np.column_stack((d,np.zeros((len(d),2)))),time_index=1,geometry_at=geometry)
    assert result['passed'] and result['source_relocation']['passed'] and result['cumulative_from_source']['passed']
    assert len(calls)==book.count('endpoint','diagnostic')<=30
    assert all(r['kind']=='tangent' and r['phase']=='diagnostic' for r in book.read('sweeps'))
    assert result['center_native'] is not None


def test_boundary_maximum_cannot_be_accepted(tmp_path):
    from lll.ilvis0_exact_boundary import check_endpoint
    native,calls=surface('maximum');saved=native([0.,0.],'sphere_still')[0];calls.clear()
    book=Ledger(tmp_path,'a'*64,['endpoint'],fit_limit=1,diagnostic_limit=30);book.start('endpoint')
    result=check_endpoint(book,'endpoint',native,'sphere_still',[0.,0.],saved,
        lambda d:np.column_stack((d,np.zeros((len(d),2)))),time_index=1,geometry_at=geometry)
    assert not result['passed']


def test_large_relocation_stops_at_first_charged_call(tmp_path):
    from lll.ilvis0_exact_boundary import check_endpoint
    native,calls=surface();saved=native([0.,1e-8],'sphere_still')[0];calls.clear()
    book=Ledger(tmp_path,'a'*64,['endpoint'],fit_limit=1,diagnostic_limit=30);book.start('endpoint')
    with pytest.raises(ValueError,match='relocation'):
        check_endpoint(book,'endpoint',native,'sphere_still',[0.,0.],saved,
            lambda d:np.column_stack((d*1e14,np.zeros((len(d),2)))),time_index=1,geometry_at=geometry)
    assert len(calls)==book.count('endpoint','diagnostic')==1


def test_native_exception_is_preserved_and_charged(tmp_path):
    from lll.ilvis0_exact_boundary import check_endpoint
    native,calls=surface('exception')
    book=Ledger(tmp_path,'a'*64,['endpoint'],fit_limit=1,diagnostic_limit=30);book.start('endpoint')
    with pytest.raises(RuntimeError,match='native failed'):
        check_endpoint(book,'endpoint',native,'sphere_still',[0.,0.],np.array([1.,0.,40.]),
            lambda d:np.column_stack((d,np.zeros((len(d),2)))),time_index=1,geometry_at=geometry)
    assert book.count('endpoint','diagnostic')==1


def test_unsupported_geometry_does_not_invent_a_selected_native_value(tmp_path):
    from lll.ilvis0_exact_boundary import check_endpoint
    native,calls=surface();book=Ledger(tmp_path,'a'*64,['endpoint'],fit_limit=1,diagnostic_limit=30);book.start('endpoint')
    result=check_endpoint(book,'endpoint',native,'sphere_still',[0.,0.],np.array([1.,0.,40.]),
        lambda d:np.column_stack((d,np.zeros((len(d),2)))),time_index=1,
        geometry_at=lambda t:dict(geometry(t),side_geometry_supported=False))
    assert not result['passed'] and result['center_native'] is None and not calls
