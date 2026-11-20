# SPDX-License-Identifier: AGPL-3.0-or-later
"""Validate a declared PPP print-counter rollover before strict decoding."""

from collections import deque
import math
import re

from .airquantumgrav_receiver import records


def records_with_sequence_wrap(lines, *, expected_rollovers, audit):
    """Extend only the printed sequence; retain its original eight digits."""
    if expected_rollovers not in (0, 1) or not isinstance(audit, dict):
        raise ValueError('zero or one declared rollover and an audit required')
    pending = deque()
    state = dict(previous=None, rollovers=0, records=0)

    def normalized():
        for original in lines:
            try:
                text = original.decode('ascii') if isinstance(original, bytes) else original
            except UnicodeError as error:
                raise ValueError('ASCII PPP source required') from error
            match = re.match(r'^(\s*)(\d{8})(?=\s)', text)
            if match is None:
                yield original
                continue
            fields = text.split()
            if len(fields) != 30:
                yield original  # the strict parser reports malformed content
                continue
            raw = int(match.group(2))
            try:
                time, week = float(fields[26]), int(fields[27])
            except ValueError as error:
                raise ValueError('finite PPP counter time/week required') from error
            if not math.isfinite(time):
                raise ValueError('finite PPP counter time required')
            previous = state['previous']
            if previous is not None:
                old_raw, old_time, old_week = previous
                if time <= old_time or week != old_week:
                    raise ValueError('receiver time/week discontinuity at counter transition')
                if old_raw == 99999 and raw == 0:
                    state['rollovers'] += 1
                    if state['rollovers'] > expected_rollovers:
                        raise ValueError('unexpected receiver sequence rollover')
                elif raw <= old_raw:
                    raise ValueError('unexpected receiver sequence reset or duplicate')
            extended = raw + 100000 * state['rollovers']
            if extended > 99999999:
                raise ValueError('extended receiver sequence exceeds eight digits')
            state['previous'] = raw, time, week
            pending.append((match.group(2), state['rollovers']))
            yield (text[:match.start(2)] + f'{extended:08d}' +
                   text[match.end(2):])

    for row in records(normalized()):
        raw, rollovers = pending.popleft()
        row['raw_sequence_text'] = raw
        row['sequence_rollovers'] = rollovers
        state['records'] += 1
        yield row
    if state['rollovers'] != expected_rollovers or pending:
        raise ValueError('receiver sequence rollover count or record alignment differs')
    audit.update(records=state['records'], rollovers=state['rollovers'],
                 first_raw_sequence=None, last_raw_sequence=state['previous'][0]
                 if state['previous'] is not None else None)
