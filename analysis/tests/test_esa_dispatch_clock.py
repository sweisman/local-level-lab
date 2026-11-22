from io import BytesIO

import pytest

from lll.airquantumgrav import HEADER
from lll.studies.artifacts import digest, encoded


def test_receiver_clock_reader_ignores_position_and_velocity_fields():
    from lll.esa_dispatch_clock import receiver_clocks

    rows = []
    for sequence, stamp in enumerate((3.0, 3.5, 4.0, 4.5, 5.0)):
        fields = [b'not-a-coordinate']*30
        fields[0] = f'{sequence:08d}'.encode()
        fields[26] = str(stamp).encode()
        fields[27] = b'2345'
        rows.append(b' '.join(fields) + b'\n')
    raw = b''.join(rows)
    assert receiver_clocks(BytesIO(raw), first=1, last=3, total=5, sha256=digest(raw)) == [
        (1, 3.5, 2345), (2, 4.0, 2345), (3, 4.5, 2345),
    ]
    with pytest.raises(ValueError, match='source hash'):
        receiver_clocks(BytesIO(raw), first=1, last=3, total=5, sha256='0'*64)


def test_inertial_clock_reader_requires_uninterrupted_bracketing():
    from lll.esa_dispatch_clock import inertial_clocks

    def stream(stamps):
        lines = [HEADER, *(f'{stamp:.4f} other measurements' for stamp in stamps)]
        return BytesIO(b''.join(line.encode().ljust(119) + b'\n' for line in lines))

    stamps = (1., 1.003, 1.006, 1.009, 1.012)
    result = inertial_clocks(stream(stamps), row_count=len(stamps), lower=1.004, upper=1.010)
    assert result['first_time_s'] == 1.003
    assert result['last_time_s'] == 1.012
    assert result['clock_rows'] == 4
    gaps = (1., 1.003, 1.006, 1.013, 1.016)
    with pytest.raises(ValueError, match='gap'):
        inertial_clocks(stream(gaps), row_count=len(gaps), lower=1.004, upper=1.014)


def test_solver_inputs_do_not_decode_later_positions(monkeypatch):
    from lll import esa_dispatch_inputs as inputs
    from lll.airquantumgrav_receiver import COLUMNS

    monkeypatch.setattr(inputs, 'TRAINING', 2)
    monkeypatch.setattr(inputs, 'PREDICTION', 2)
    header = b'Datum: WGS84\n' + ' '.join(COLUMNS).encode() + b'\n'
    lines = []
    clocks = []
    for index in range(9):
        fields = ['0']*30
        fields[0] = f'{index:08d}'
        fields[1] = '10' if index in (1, 3) else 'withheld'
        fields[26], fields[27] = str(index/2), '2345'
        fields[28], fields[29] = '1/02/2025', '01:00:00'
        clocks.append((index, index/2, 2345))
        lines.append(' '.join(fields).encode() + b'\n')
    raw = header + b''.join(lines)
    binding = dict(receiver_sha256=digest(raw), receiver_clock_sha256=digest(encoded(clocks)),
                   receiver_query_sha256=digest(encoded(clocks[1:-1:2])),
                   selection={'window': {'first_index': 0, 'last_index': 8, 'query_stride': 2}})
    training, queries = inputs.training_and_times(BytesIO(raw), binding, total=9)
    assert [row['sequence'] for row in training] == [1, 3]
    assert queries == [.5, 1.5, 2.5, 3.5]
    with pytest.raises(ValueError, match='verified clock'):
        inputs.training_and_times(BytesIO(raw), dict(binding, receiver_query_sha256='0'*64), total=9)


def test_clock_selection_matches_after_json_round_trip(monkeypatch, tmp_path):
    from lll import esa_dispatch_inputs as inputs

    monkeypatch.setattr(inputs, 'preflight', lambda root: {'documented_exclusions': [(1, 2)]})
    assert inputs.selection_matches(tmp_path, {'documented_exclusions': [[1, 2]]})
    assert not inputs.selection_matches(tmp_path, {'documented_exclusions': [[1, 3]]})
