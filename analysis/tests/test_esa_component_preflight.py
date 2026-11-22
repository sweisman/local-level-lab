# SPDX-License-Identifier: AGPL-3.0-or-later
import io

import numpy as np

from lll.airquantumgrav import HEADER
from lll.esa_component_preflight import rate_slice


def fixed(text):
    return text.encode().ljust(119)+b'\n'


def test_rate_slice_uses_next_timestamp_without_decoding_post_cut_rate():
    header=fixed(HEADER)
    rows=[fixed(f'{t} 0 0 9.81 0 0 {r} 35') for t,r in
          [(1.,.1),(1.003,.2),(1.006,.3),(1.009,.4)]]
    rows[-1]=fixed('1.009 deliberately invalid measurements after the cut')
    store=io.BytesIO(header+b''.join(rows))
    times,rates=rate_slice(store,header,4,lower=1.001,upper=1.008)
    np.testing.assert_allclose(times,[1.,1.003,1.006,1.009])
    np.testing.assert_allclose(rates[:,2],[.1,.2,.3])
