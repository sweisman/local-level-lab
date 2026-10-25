# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded complete-source streaming with charges made before decoder calls."""
import hashlib
import re


def consume(lines,*,decoder,expected_sha256,expected_bytes,maximum_records,block_size,
            reserve,check_continue,accept):
    if (not isinstance(expected_sha256,str) or not re.fullmatch('[0-9a-f]{64}',expected_sha256)
            or type(expected_bytes) is not int or expected_bytes<1
            or type(maximum_records) is not int or maximum_records<1
            or type(block_size) is not int or not 1<=block_size<=65536
            or any(not callable(v) for v in (decoder,reserve,check_continue,accept))):
        raise ValueError('complete-source identity, finite caps and callbacks required')
    digest=hashlib.sha256();size=0;exhausted=False
    def hashed():
        nonlocal size,exhausted
        for line in lines:
            if not isinstance(line,bytes):raise ValueError('binary original source required')
            size+=len(line)
            if size>expected_bytes:raise ValueError('original exceeds frozen byte size')
            digest.update(line);yield line
        exhausted=True
    def decoded():yield from decoder(hashed())
    iterator=iter(decoded());count=0;calls=0;reserved=0
    while reserved<maximum_records+1:
        check_continue();amount=min(block_size,maximum_records+1-reserved)
        reserve(amount);reserved+=amount
        for _ in range(amount):
            calls+=1
            try:row=next(iterator)
            except StopIteration:
                if not exhausted or size!=expected_bytes or digest.hexdigest()!=expected_sha256:
                    raise ValueError('complete source bytes and hash must match frozen reference')
                return dict(records=count,decoder_calls=calls,reserved_calls=reserved,
                    source_bytes=size,source_sha256=digest.hexdigest())
            if count>=maximum_records:raise ValueError('record allowance exhausted; no source trimming')
            count+=1;accept(row)
    raise ValueError('decoder allowance exhausted without complete source')
