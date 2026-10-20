# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import airquantumgrav_motion as motion
from test_airquantumgrav_receiver import stream


def test_stream_extension_preserves_base_fields_and_full_velocity_covariance():
    row=list(motion.velocity_records(stream({13:1.,14:2.,15:3.,16:.1,17:.2,18:.3})))[0]
    np.testing.assert_array_equal(row['velocity_covariance_m2_s2'],[[1.,.1,.2],[.1,2.,.3],[.2,.3,3.]])
    assert row['north_mps']==60. and row['source_covariance_fields']==[1.,2.,3.,.1,.2,.3]


def test_extension_inherits_strict_base_checksumless_text_validation():
    with pytest.raises(ValueError):list(motion.velocity_records(stream({13:'nan'})))
    with pytest.raises(ValueError):list(motion.velocity_records(stream() + ['bad trailer\n']))
