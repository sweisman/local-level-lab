import pytest

from lll.esa_apron_imu_overlap import join_overlap


def test_overlap_keeps_the_complete_byte_stream_once():
    assert join_overlap(b'abcd', b'cdef', length=4, overlap=2) == b'abcdef'


@pytest.mark.parametrize(('left', 'right'), [(b'abc', b'cdef'), (b'abcd', b'feed')])
def test_bad_or_short_transfers_cannot_make_an_excerpt(left, right):
    with pytest.raises(ValueError, match='exact and identical'):
        join_overlap(left, right, length=4, overlap=2)
