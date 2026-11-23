# SPDX-License-Identifier: AGPL-3.0-or-later
"""Materialize earlier ESA receiver rows and only the query clock for later rows."""

import hashlib
import math
import re

from .airquantumgrav_receiver import records
from .esa_repeat_turn_inputs import clock_tag


QUERY_STRIDE = 2
QUERY_INTERVAL_S = 1.
QUERY_TOLERANCE_S = .02


def read_split(lines, *, indices, training_count, source_bytes, source_reports, source_sha256):
    """Return only earlier observations and the exact query times.

    The owning study verifies provenance and authorization before calling this
    reader. A separate scoring input must retain all later receiver values.
    """
    indices = tuple(indices)
    if (type(source_reports) is not int or not 2 <= source_reports <= 100_000
            or type(source_bytes) is not int or source_bytes <= 0
            or not isinstance(source_sha256, str) or not re.fullmatch('[0-9a-f]{64}', source_sha256)
            or type(training_count) is not int or not 2 <= training_count <= 1024
            or training_count >= len(indices)
            or any(type(index) is not int or not 0 <= index < source_reports for index in indices)
            or any(b-a != QUERY_STRIDE for a, b in zip(indices, indices[1:]))):
        raise ValueError('frozen receiver bounds and a complete stride-two split required')
    earlier = set(indices[:training_count])
    withheld = set(indices[training_count:])
    earlier_line_numbers = []
    later_tags = []
    count, byte_count = 0, 0
    stamp = hashlib.sha256()

    def training_lines():
        nonlocal count, byte_count
        for number, line in enumerate(lines, 1):
            byte_count += len(line)
            if byte_count > source_bytes:
                raise ValueError('receiver byte allowance exceeded')
            stamp.update(line)
            prefix = line.split(maxsplit=1)[:1]
            if not prefix or len(prefix[0]) != 8 or not prefix[0].isdigit():
                if count == 0:
                    yield line
                elif prefix:
                    raise ValueError('unexpected content after receiver records')
                continue
            index = count
            count += 1
            if count > source_reports:
                raise ValueError('receiver report allowance exceeded')
            if index in earlier:
                earlier_line_numbers.append(number)
                yield line
            elif index in withheld:
                later_tags.append(clock_tag(line.split()))

    training = list(records(training_lines()))
    if (count != source_reports or byte_count != source_bytes or stamp.hexdigest() != source_sha256
            or len(training) != training_count or len(later_tags) != len(withheld)):
        raise ValueError('complete original source and declared split did not verify')
    for row, original_number in zip(training, earlier_line_numbers, strict=True):
        row['line_number'] = original_number
    tags = [(row['sequence'], row['time_s'], row['gps_week']) for row in training] + later_tags
    if (len({tag[2] for tag in tags}) != 1
            or any(b[0]-a[0] != QUERY_STRIDE
                   or not math.isclose(b[1]-a[1], QUERY_INTERVAL_S, abs_tol=QUERY_TOLERANCE_S, rel_tol=0.)
                   for a, b in zip(tags, tags[1:]))):
        raise ValueError('original query sequence and one-second clock must be continuous')
    return dict(training_rows=training, query_times_s=[tag[1] for tag in tags], gps_week=tags[0][2])
