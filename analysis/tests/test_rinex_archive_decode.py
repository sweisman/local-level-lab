# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
from io import BytesIO
from pathlib import Path
import sys

import pytest

from lll.rinex_archive_decode import _decode, copy_bounded


def test_decode_copy_hashes_exact_output_up_to_limit():
    output = BytesIO()
    assert copy_bounded(BytesIO(b'original observations'), output, 30) == (
        21, hashlib.sha256(b'original observations').hexdigest())
    assert output.getvalue() == b'original observations'


def test_decode_copy_drains_oversize_stream_without_exceeding_storage(tmp_path):
    raw = BytesIO(b'12345678901234567890')
    target = tmp_path/'excess.rnx'
    with target.open('wb') as output, pytest.raises(ValueError, match='allowance'):
        copy_bounded(raw, output, 8)
    assert raw.tell() == 20
    assert target.stat().st_size <= 8


def test_decoder_exit_status_must_pass_even_if_it_printed_observations(tmp_path):
    input_path = tmp_path/'input.bin'
    input_path.write_bytes(b'input')
    with input_path.open('rb') as source, (tmp_path/'output.rnx').open('w+b') as output:
        with pytest.raises(ValueError, match='failed to decode'):
            _decode(Path(sys.executable), ['-c', 'print("partial data"); raise SystemExit(2)'], source, output, 16)
