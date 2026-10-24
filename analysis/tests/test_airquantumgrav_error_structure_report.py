# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def test_error_structure_report_rejects_open_before_numerical_imports(tmp_path):
    from lll.airquantumgrav_error_structure_report import inspect
    with pytest.raises(ValueError,match='closed study'):inspect(tmp_path)


def test_error_structure_render_separates_error_dependence_from_noise_or_confidence():
    from lll.airquantumgrav_error_structure_report import render
    report=dict(verified=True,result=dict(records=22,missing_records=2),statistics=[])
    text=render(report)
    for phrase in ('22','two deadline','not raw receiver noise','not calibrated confidence','one development recording',
            'first differences','No new fit','Seven confirmation groups'):
        assert phrase.lower() in text.lower()


def test_error_structure_report_rejects_changed_labels_before_statistics():
    from lll.airquantumgrav_error_structure_report import verify_statistics
    parent=dict(rows=[dict(identity='saved',model='sphere_rotating',profile=False,policy_id='short',start=1,
        complete=False,passed=False,reason='deadline')],primaries=[])
    row=dict(parent['rows'][0],model='flat_still',selected_primary=False,parent_reason='deadline',statistics=None)
    with pytest.raises(ValueError,match='labels'):verify_statistics(parent,{},[row],{})
