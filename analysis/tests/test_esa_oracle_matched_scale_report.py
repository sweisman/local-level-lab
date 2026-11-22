"""The shared study summary records pass status as a boolean."""


def test_matched_scale_report_accepts_sealed_boolean_pass_status():
    from lll.esa_oracle_matched_scale_report import complete_study
    from lll.esa_oracle_matched_scale_study import SCOPE

    assert complete_study(dict(state='complete'),
                          dict(completed=2,passed=True),SCOPE,
                          {'increment','point'})
    assert not complete_study(dict(state='complete'),
                              dict(completed=2,passed=False),SCOPE,
                              {'increment','point'})
