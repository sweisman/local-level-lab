# SPDX-License-Identifier: AGPL-3.0-or-later
from dataclasses import replace

import numpy as np
import pytest


def fixture():
    from test_ilvis0_native_box_bounds import configuration
    from lll import ilvis0_remainder_native as candidate
    from lll.ilvis0_directional_acceleration import DirectionalAcceleration
    from lll.ilvis0_conditional_remainder import enclose
    from lll.ilvis0_shared_reference_terms import SharedCoefficients
    from lll.ilvis0_reference_acceleration import AccelerationCoefficients
    from lll.ilvis0_common_force_transform import ForceTransformCoefficients
    config=configuration();dt=np.full(4,.005);lo=-np.ones(27);hi=np.ones(27)
    ref=candidate.make_reference(config,np.zeros((4,3)),np.tile([0.,0.,-.04905],(4,1)),dt,
        lower=lo,upper=hi,center=np.zeros(27))
    proof=DirectionalAcceleration(ref,lo,hi);r=ref.parent
    certificate=enclose(ref.acceleration.jacobian,lo,hi,r.center,proof.component_changes,ref.acceleration.remainder)
    meta=dict(lower=lo.tolist(),upper=hi.tolist(),conditioning=proof.report(),source_id=r.source_id,
        reference_binding=ref.binding,normalized_center=r.center.tolist(),
        retained_acceleration_remainder=ref.acceleration.remainder,
        force_integrals=dict(source_id=r.source_id),
        clock_transform=dict(source_id=r.source_id,matrix_binding=ref.transform.binding),
        transform_reference=ref.transform.report(),conditional_acceleration_remainder=certificate)
    report=candidate.TransformEnclosure(config['initial_c'],np.ones(3),
        SharedCoefficients(np.zeros((3,6)),r.binding),
        AccelerationCoefficients(np.zeros((3,9)),ref.acceleration.binding),
        ForceTransformCoefficients(np.zeros((3,9)),ref.transform.binding),meta)
    return report,ref,proof


def test_bridge_rechecks_certificate_and_preserves_shared_coordinates():
    from lll.ilvis0_remainder_interface import bridge
    report,reference,proof=fixture()
    result=bridge(report,reference,proof,report.center,[6371000.,6371000.,1.])
    assert result.metadata['native_candidate_version']=='ilvis0-conditional-remainder-native-v1'
    assert result.metadata['bridge_version']=='ilvis0-conditional-remainder-joint-schema-v1'
    assert result.previous_coefficients is report.previous_coefficients
    assert result.acceleration_coefficients is report.acceleration_coefficients
    assert result.transform_coefficients is report.transform_coefficients
    np.testing.assert_array_equal(result.unshared_remainder,report.unshared_remainder)


@pytest.mark.parametrize('change',('missing','radius','domain','components','retained','center','source'))
def test_bridge_rejects_changed_or_incomplete_certificate(change):
    from copy import deepcopy
    from lll.ilvis0_remainder_interface import bridge
    report,reference,proof=fixture();meta=deepcopy(report.metadata);center=report.center.copy()
    if change=='missing':del meta['conditional_acceleration_remainder']
    if change=='radius':meta['conditional_acceleration_remainder']['remainder_upper']*=.5
    if change=='domain':meta['lower'][0]=-.5
    if change=='components':meta['conditional_acceleration_remainder']['component_upper'][0]=0.
    if change=='retained':meta['retained_acceleration_remainder']*=.5
    if change=='center':center[2]+=.01
    if change=='source':meta['source_id']='0'*64
    with pytest.raises(ValueError):
        bridge(replace(report,metadata=meta),reference,proof,center,[6371000.,6371000.,1.])
