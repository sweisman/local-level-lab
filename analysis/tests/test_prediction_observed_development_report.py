"""Saved-only observed pilot reporting, including a sealed technical failure."""


def test_report_main_prints_technical_failure_without_missing_score(monkeypatch, capsys):
    from lll import prediction_observed_development_report as report

    def completed_failure(_root):
        return dict(technical_passed=False, error_type='wall_budget_exhausted',
                    scientific_decision='abstain')

    monkeypatch.setattr(report, 'publish', completed_failure)
    report.main(['--root', '.'])
    assert 'technical failure=wall_budget_exhausted' in capsys.readouterr().out


def test_failure_report_names_saved_reason_before_exception_class():
    from lll.prediction_observed_development_report import render

    text = render(dict(technical_passed=False,
                       reason='prepaid native allowance exceeded',
                       error_type='ValueError'))
    assert 'prepaid native allowance exceeded' in text
