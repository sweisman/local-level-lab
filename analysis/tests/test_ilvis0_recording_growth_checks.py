# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
import importlib.util


def test_recording_checks_preserve_qualified_tolerances_and_use_original_coordinate_units():
    spec=importlib.util.find_spec('lll.ilvis0_recording_case_checks')
    assert spec is not None,'recording-frame control checks are missing'
    old=Path(importlib.util.find_spec('lll.ilvis0_transform_control_case').origin).read_text()
    source='scale=np.array([6371000.,6371000.*np.cos(config["initial_c"][0]),1.])'
    assert old.count(source)==1
    assert Path(spec.origin).read_text()==old.replace(source,'scale=np.array(case["coordinate_scale"])')
