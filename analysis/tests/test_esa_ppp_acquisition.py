"""Parallel ESA PPP downloads stay fixed, resumable and non-destructive."""

import hashlib

import pytest


def test_saved_listing_must_contain_exact_target_sizes():
    from lll.esa_ppp_acquisition import parse_target_listing, TARGETS

    listing = [f'-rwxr-xr-x 1 ftp ftp {size} Jul 08 2024 {name}'
               for name, size in TARGETS.items()]
    assert parse_target_listing(listing) == TARGETS
    with pytest.raises(ValueError, match='target size'):
        parse_target_listing([listing[0].replace(str(next(iter(TARGETS.values()))),
                                                '1'), listing[1]])
    with pytest.raises(ValueError, match='unique'):
        parse_target_listing(listing + [listing[0]])


def test_completed_file_requires_size_and_receipt_hash(tmp_path):
    from lll.esa_ppp_acquisition import verify_complete

    target = tmp_path / 'sample.txt'
    target.write_bytes(b'abc')
    digest = hashlib.sha256(b'abc').hexdigest()
    assert verify_complete(target, 3, dict(sha256=digest,
                                          size_bytes=3)) == digest
    with pytest.raises(ValueError, match='size'):
        verify_complete(target, 4, dict(sha256=digest, size_bytes=4))
    with pytest.raises(ValueError, match='hash'):
        verify_complete(target, 3, dict(sha256='0'*64, size_bytes=3))
