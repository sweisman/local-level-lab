"""Versioned observed publication reads its own study and links its plan."""

from lll import ilvis0_observed_method_report_v2 as report
from lll.ilvis0_observed_method_pilot_v2 import ID


def test_versioned_report_selects_new_study_and_plan(monkeypatch):
    seen={}
    def saved(root,*,study_id,recovery):
        seen['id']=study_id
        seen['recovery']=recovery
        return {'cuts':6,'source_sha256':'shared-source'}
    monkeypatch.setattr(report.shared,'build',saved)
    value=report.build('.')
    assert seen['id']==ID
    assert seen['recovery'] is None
    assert value['version']=='ilvis0-observed-method-report-v2'
    assert value['shared_report_sha256']=='shared-source'


def test_shared_renderer_accepts_versioned_links():
    value={'tasks':24,'numerical_stops':24,'technical_failures':0,
           'numerical_stops_by_solver':{'trust_v2':12,'scipy_trf':12},
           'method_agreement_within_diagnostic_scale':6,
           'cut_rows':[],'original_matched_starts':12,
           'selected_recordings':[{'filename':'survey.013','duration_s':600,
               'mean_latitude_deg':-63,'median_ground_speed_kmh':715}]}
    rendered=report.shared.render(value,
        plan='OBSERVED_METHOD_PILOT_V2_PLAN.md',
        task_file='observed-method-v2-tasks.csv')
    assert '(OBSERVED_METHOD_PILOT_V2_PLAN.md)' in rendered
    assert '(observed-method-v2-tasks.csv)' in rendered
    assert 'survey.013 | 10.0 min | -63.0° | 715 km/h' in rendered
