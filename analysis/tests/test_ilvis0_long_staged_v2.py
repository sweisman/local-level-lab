# SPDX-License-Identifier: AGPL-3.0-or-later
"""The corrected freeze changes counter handling, not physical calculations."""
import importlib.util
from pathlib import Path


def test_corrected_adapter_differs_only_in_checked_packet_boundary_handling():
    root=Path(__file__).parents[1]/'lll'
    original=(root/'ilvis0_long_staged.py').read_text()
    old="""        if code or flag.value:
            raise ValueError('native query failed or reported unsupported motion')
"""
    new="""        from lll.ilvis0_packet_boundary_flags import validate
        classification=validate(status=int(code),counter=flag.value,dt=dt,time_s=time_s,
            clock_offset_s=float(config['limits'][25])*float(parameters[25]))
        self.save(f'native-{self.native_calls:02d}-boundary.json',classification)
"""
    assert original.count(old)==1
    assert (root/'ilvis0_long_staged_v2.py').read_text()==original.replace(old,new)


def test_corrected_runtime_loads_standalone(tmp_path):
    from types import SimpleNamespace
    path=Path(__file__).parents[1]/'lll/ilvis0_long_staged_v2.py'
    spec=importlib.util.spec_from_file_location('_long_v2_runtime',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    runtime=module.Runtime(SimpleNamespace(root=tmp_path,manifest={},save=lambda *a:None),{'limits':module.limits()})
    assert runtime.bounds==runtime.native_calls==0


def test_corrected_saved_report_preserves_failure_and_width_gates():
    import pytest
    from test_ilvis0_long_staged_report import examples
    path=Path(__file__).parents[2]/'docs/ilvis0-long-staged-feasibility-v2/build_report.py'
    spec=importlib.util.spec_from_file_location('_long_v2_report',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    manifest,summary,row=examples();summary['completed']=1
    text=module.render(manifest,summary,{'long-0-0':row})
    assert 'Too wide' in text and text.count('Not started')==5
    row['passed']=row['useful']=True
    with pytest.raises(ValueError):module.render(manifest,summary,{'long-0-0':row})
