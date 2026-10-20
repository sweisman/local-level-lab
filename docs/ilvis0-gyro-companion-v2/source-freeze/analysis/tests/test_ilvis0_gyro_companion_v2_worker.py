# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import pytest


def module():
    import ilvis0_gyro_companion_v2_worker
    return ilvis0_gyro_companion_v2_worker


def test_actual_control_lifecycle_persists_identity_without_duplicate_keywords(tmp_path,monkeypatch):
    w=module();data=tmp_path/'study';base=tmp_path/'selection';data.mkdir();base.mkdir()
    manifest=dict(tasks=w.CONTROLS,sources={})
    w.write(data/'manifest.json',manifest);w.write(base/'selection.json.gz',dict(selected=[]))
    monkeypatch.setattr(w,'DATA',data);monkeypatch.setattr(w,'BASE',base)
    # Isolate the result-writing path; mathematical controls run unmodified.
    monkeypatch.setattr(w,'verify',lambda:manifest);monkeypatch.setattr(w,'publish',lambda:None)
    w.run();summary=w.load(data/'summary.json')
    assert len(summary['results'])==48 and all(r['passed'] for r in summary['results'])
    for row in summary['results']:
        result=w.load(data/row['artifact'])
        assert result['identity']==row['identity'] and result['kind']=='control'
        assert result['passed'] is True
    assert summary['charged']['controls']==48 and summary['charged']['observed']==0


def test_corrected_freeze_has_its_own_identity_and_finite_allowance():
    w=module()
    assert w.NAME=='ilvis0-gyro-companion-v2-20261019'
    assert len(w.CONTROLS)==48 and w.LIMITS['maximum_observed_summaries']==53
    assert w.LIMITS['maximum_scenarios']==12879
    assert w.LIMITS['optimizer_starts']==0
