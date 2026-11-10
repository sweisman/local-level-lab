# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-clock metadata controls; no native execution."""
import hashlib
import struct

import pytest


def test_query_alignment_requires_exact_saved_interval_hash():
    from lll.timing_precision_report import query_alignment
    dt=[(i+1)/300-i/300 for i in range(600)]
    sha=hashlib.sha256(struct.pack('<600d',*dt)).hexdigest()
    result=query_alignment([.5,1.5],-.01,packets=600,expected_dt_sha256=sha)
    assert result['queries']==result['exact_packet_end_queries']==2
    assert result['packet_end_distance_max_s']==0
    with pytest.raises(ValueError,match='interval hash'):
        query_alignment([.5],-.01,packets=600,expected_dt_sha256='0'*64)


def test_query_alignment_keeps_nonboundary_and_start_of_packet_distinct():
    from lll.timing_precision_report import query_alignment
    dt=[(i+1)/300-i/300 for i in range(600)]
    sha=hashlib.sha256(struct.pack('<600d',*dt)).hexdigest()
    result=query_alignment([.501,1.501],-.01,packets=600,expected_dt_sha256=sha)
    assert result['exact_packet_end_queries']==0
    assert result['packet_end_distance_max_s']>.001
