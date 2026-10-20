# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction
import sys

import pytest
import ilvis0_exact_scale_worker_v2 as worker


def test_large_rational_output_uses_finite_local_limit_and_restores_it(monkeypatch):
    original=sys.get_int_max_str_digits();value=Fraction(2**15000,3**9000)
    sys.set_int_max_str_digits(4300)
    try:
        with pytest.raises(ValueError,match='integer string conversion'):str(value)
        monkeypatch.setattr(worker.prior,'evaluate',lambda *args:{'exact':str(value),'roundtrip':Fraction(str(value))==value})
        result=worker.evaluate(None,None,None)
        assert result['roundtrip'] and len(result['exact'])>4300
        assert sys.get_int_max_str_digits()==4300
    finally:sys.set_int_max_str_digits(original)


def test_version_two_freeze_and_lifecycle(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path/'runtime');monkeypatch.setattr(worker,'PUBLIC',tmp_path/'public')
    monkeypatch.setattr(worker,'TASKS',[worker.TASKS[0]])
    worker.configure();worker.base.prepare();worker.base.run()
    summary=worker.base.load(worker.DATA/'summary.json')
    assert summary['passed'] and summary['charged']['identities']==1
    assert worker.base.load(worker.PUBLIC/'summary.json')['passed']
    with pytest.raises(ValueError):worker.base.run()
