# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest


def module():
    p=Path(__file__).resolve().parents[2]/'docs/ilvis0-remainder-native-controls/build_report.py'
    spec=importlib.util.spec_from_file_location('_remainder_report_test',p)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def example():
    from lll.ilvis0_remainder_controls import limits
    tasks=[dict(identity=f'{m}-{int(p)}-{s}',payload=dict(model=m,profile=p,scope=s))
        for m in range(3) for p in (False,True) for s in ('physical','conditioned')]
    summary=dict(completed=1,total=12,elapsed_s=2.,charged=dict(native_calls=4,packet_visits=3200,bound_calls=2,bound_steps=14400))
    row=dict(passed=True,native_evaluations=4,bound_evaluations=2,physical_parameter_count=27,parameter_count=51,
        probe_count=4,all_probes_contained=True,maps_preserved=True,remainders_nonwidening=True,
        force_remainder_reduced=True,original_force_remainder=53.,conditional_force_remainder=25.,
        original_unshared_m=[100.,100.,100.],candidate_unshared_m=[90.,90.,90.],
        work=limits('physical'),original_reads=0,optimizer_starts=0)
    return dict(tasks=tasks),summary,{tasks[0]['identity']:row}


def test_report_distinguishes_native_component_from_long_record_coverage():
    text=module().render(*example())
    assert '1/12' in text and 'four-second' in text and 'not recording-length' in text


@pytest.mark.parametrize('field',('maps_preserved','all_probes_contained','force_remainder_reduced','parameter_count'))
def test_report_rejects_unsupported_pass(field):
    manifest,summary,rows=example();next(iter(rows.values()))[field]=False
    with pytest.raises(ValueError):module().render(manifest,summary,rows)
