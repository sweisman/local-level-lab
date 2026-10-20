# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit behavior after a changed record has a valid replacement digest."""
import hashlib
import json
import pytest
from lll import ilvis0_coupled_prediction as prediction
from test_ilvis0_coupled_prediction import fixture


@pytest.mark.parametrize('change',['gradient','coefficient','endpoint'])
def test_exact_export_arithmetic_is_verified_independently_of_the_digest(change):
    _,saved,cuts,report=fixture()
    if change=='gradient':cuts['proof']['derivatives'][0][0][1]=1.
    elif change=='coefficient':cuts['design'][0][0]=1.
    else:cuts['upper'][0]=1.
    cuts['binding']=hashlib.sha256(json.dumps({k:v for k,v in cuts.items() if k!='binding'},
        sort_keys=True,allow_nan=False).encode()).hexdigest()
    with pytest.raises(ValueError,match='exact coupling export'):
        prediction.audit_cuts(cuts,report,saved['lower'][:27],saved['upper'][:27])


def test_future_certificate_is_checked_against_exact_support_not_just_metadata():
    from lll.ilvis0_product_prediction import rebuild
    training,saved,cuts,report=fixture();region=prediction.extend(training,saved,cuts)
    receipt=prediction.audit_cuts(cuts,report,saved['lower'][:27],saved['upper'][:27])
    future=rebuild(region,saved,region['lower'],region['upper'],reserve=lambda _:None)
    future['envelope']['coupled_map_binding']=cuts['binding']
    future['envelope']['certificates'][0]['upper']='1'
    with pytest.raises(ValueError,match='exact support mismatch'):
        prediction.audit_future(training,saved,region,future,cuts,cut_audit=receipt)
