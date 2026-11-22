# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
import pytest


def test_passing_margin_includes_rms_and_peak_screens():
    from lll.ilvis0_forecast_accuracy_margin import margins

    row = margins([[6., 0., 12.], [0., 6., -12.]])
    assert row['accuracy_screen_passed']
    assert row['first_limit'] == 'horizontal_rms_m'
    assert row['screen_boundary_radius_m'] == pytest.approx(4.)


def test_joint_rescue_bounds_respect_both_axes():
    from lll.ilvis0_forecast_accuracy_margin import margins

    row = margins(np.tile([12., 0., -33.], (4, 1)))
    assert not row['accuracy_screen_passed']
    assert row['joint_needed_m'] == pytest.approx([3., math.hypot(2., 3.)])


def test_peak_constraint_can_set_a_failing_forecast_radius():
    from lll.ilvis0_forecast_accuracy_margin import axis_margin

    row = axis_margin(np.r_[54., np.zeros(99)], rms_limit=10., peak_limit=50.)
    assert row['rms'] == pytest.approx(5.4)
    assert row['rescue_radius_m'] == pytest.approx([4., 4.])


def test_saved_audit_returns_explicit_scientific_abstention(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace

    from lll import ilvis0_control_shards as runner
    from lll import ilvis0_forecast_accuracy_margin as audit

    monkeypatch.setattr(audit, 'COHORTS', {'transfer':(1,0,'unused','unused')})
    row = dict(identity='example', segment_id='segment', origin='outer', start=0, solver='original',
               numerical_stop=False, archived_scores_sha256='archived', errors_neu_m=[[10.,0.,30.]],
               score=dict(horizontal_rms_m=10.,maximum_horizontal_m=10.,vertical_rms_m=30.,maximum_absolute_up_m=30.))
    path = tmp_path/'input.json'
    path.write_text(json.dumps(dict(records=[row],source_manifest='manifest',source_summary='summary')))
    task = audit.tasks()[0]
    context = SimpleNamespace(manifest={'scope':audit.SCOPE}, input_path=lambda:path,
                              charge=lambda **_:None, save=lambda *_:None)
    result = audit.evaluate(task, context)
    monkeypatch.setattr(runner, '_seal', lambda *args:args[4])
    receipt_context = SimpleNamespace(_writable=lambda:None, root=tmp_path, manifest={}, shard=0, task=task, artifacts={})
    assert runner.TaskContext.finish(receipt_context, result)['scientific_decision'] == 'abstain'
