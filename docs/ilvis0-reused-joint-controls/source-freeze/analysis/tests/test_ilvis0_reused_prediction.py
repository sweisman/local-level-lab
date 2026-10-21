# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_reuse_allowance_charges_providers_and_keeps_training_and_truth_separate():
    from lll.ilvis0_reused_prediction import allowances
    limits=allowances(2,[2,2,1])
    assert limits==dict(setups=1,proofs=1,parent_supports=6,provenance_reads=4,provider_reads=5,report_merges=3,
        training_audits=12,contractions=1,proposals=6,supports=24,truth_audits=1)
    assert not any('native' in key or 'source_steps' in key for key in limits)


@pytest.mark.parametrize('epochs,counts',[(0,[1]),(7,[1]*8),(2,[2,2]),(2,[2,0,1]),(2,[2,True,1]),(2,[2,17,1])])
def test_reuse_allowance_rejects_incomplete_queries_and_unbounded_provider_lists(epochs,counts):
    from lll.ilvis0_reused_prediction import allowances
    with pytest.raises(ValueError):allowances(epochs,counts)
