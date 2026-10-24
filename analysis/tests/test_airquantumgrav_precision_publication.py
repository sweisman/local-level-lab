# SPDX-License-Identifier: AGPL-3.0-or-later
import copy


def test_precision_publication_separates_diagnostic_resolution_from_fit_acceptance():
    from lll.airquantumgrav_precision_publication import render,table
    modes={k:dict(relative_cost_change=v,baseline_cost=1.,corrected_cost=1.+v,
        position_rms_neu_m=[0.,0.,0.],position_max_abs_neu_m=[0.,0.,0.]) for k,v in
        [('double-legacy',4e-8),('double-stable',3.9e-8),('long-double-stable',1e-10)]}
    report=dict(verified=True,total=24,complete=1,elapsed_s=60.,charged=dict(native_calls=4),
        rows=[dict(identity='source',model='sphere_rotating',profile=False,policy_id='reported-short-v1',
            start=0,complete=True,source_converged=False,modes=modes)])
    text=render(report);csv=table(report)
    assert 'no original fit is reclassified' in text.lower()
    assert 'Incomplete' not in text and 'Original numerical pass' in text
    assert '0.01' in text and '1e-8' in text
    assert 'long-double-stable' in csv and 'False' in csv
    assert report['rows'][0]['source_converged'] is False
    other=copy.deepcopy(report);other['rows'][0]=dict(other['rows'][0],complete=False,reason='reference mismatch')
    assert 'Incomplete' in render(other)


def test_precision_publication_refuses_to_overwrite_a_sealed_report(tmp_path):
    import pytest
    from lll.airquantumgrav_precision_publication import publish
    output=tmp_path/'docs/esa-precision-diagnostic';output.mkdir(parents=True)
    (output/'evidence-receipt.json').write_text('{}')
    with pytest.raises(ValueError,match='sealed'):publish(tmp_path)
