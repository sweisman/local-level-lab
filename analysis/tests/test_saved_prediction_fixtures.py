# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import math
from pathlib import Path
import pytest
from saved_prediction_fixtures import generated_context
from lll import ilvis0_column_orientation_prediction as candidate

ROOT=Path(__file__).resolve().parents[2]


def test_fresh_reference_has_a_portable_positive_adapter_path(tmp_path,monkeypatch):
    task,context,saved=generated_context(ROOT/'docs/ilvis0-orientation-gain-prediction',tmp_path,monkeypatch)
    result=candidate.evaluate(task,context)
    assert result['passed'] and result['native_evaluations']==0
    assert result['exact_supports_checked']==6 and 'independent-audit.json' in saved


def test_one_ulp_foreign_reference_is_rejected_before_any_outputs(tmp_path,monkeypatch):
    task,context,saved=generated_context(ROOT/'docs/ilvis0-orientation-gain-prediction',tmp_path,monkeypatch)
    path=context.input_path();bundle=json.loads(path.read_text())
    a=bundle['future']['reference']['acceleration']['center'];a[0]=math.nextafter(a[0],math.inf)
    path.write_text(json.dumps(bundle))
    with pytest.raises(ValueError,match='source/reference changed'):candidate.evaluate(task,context)
    assert not saved
