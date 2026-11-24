# SPDX-License-Identifier: AGPL-3.0-or-later
from io import BytesIO

import pytest

from lll.esa_nuuk_highrate_intake import select_epochs


def epoch(second):
    return f'> 2023 07 06 11 50 {second:2d}.0000000  0  1\nG03            1.000\n'.encode()


def test_nuuk_excerpt_preserves_complete_requested_blocks():
    body = b''.join(epoch(t) for t in range(14, 18))
    excerpt, summary = select_epochs(BytesIO(body), first=388215, last=388216)
    assert excerpt == epoch(15) + epoch(16)
    assert summary == dict(epochs=4, first_gps_s=388214, last_gps_s=388217)


def test_nuuk_excerpt_rejects_missing_and_truncated_epochs():
    with pytest.raises(ValueError, match='gap'):
        select_epochs(BytesIO(epoch(14) + epoch(16)), first=388214, last=388216)
    with pytest.raises(ValueError, match='truncated'):
        select_epochs(BytesIO(epoch(15).splitlines(keepends=True)[0]), first=388215, last=388215)
