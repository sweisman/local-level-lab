# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path


def test_candidate_changes_only_operational_remainder_and_provenance():
    directory=Path(__file__).parents[1]/'lll'
    original=(directory/'ilvis0_direct_native.py').read_text()
    expected=original.replace("VERSION='ilvis0-direct-source-native-v1'",
        "VERSION='ilvis0-conditional-remainder-native-v1'")
    old='    acceleration=Value(reference.center,min(reference.change,conditioned_change),reference.remainder,component_change=component_changes)'
    new="""    from .ilvis0_conditional_remainder import enclose as remainder_bound
    conditional_remainder=remainder_bound(reference.jacobian,lo,hi,z,component_changes,reference.remainder)
    acceleration=Value(reference.center,min(reference.change,conditioned_change),conditional_remainder['remainder_upper'],component_change=component_changes)"""
    assert expected.count(old)==1
    expected=expected.replace(old,new)
    expected=expected.replace('metadata=dict(source_direct_remainder_installed=True,',
        'metadata=dict(conditional_acceleration_remainder=conditional_remainder,source_direct_remainder_installed=True,')
    assert (directory/'ilvis0_remainder_native.py').read_text()==expected
