# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exercise the provisional receiver evaluator with bounded operation reservations."""

import hashlib
import json
from types import SimpleNamespace

from test_airquantumgrav_inventory import text_rows


def test_receiver_worker_charges_complete_operations_before_decode(tmp_path, monkeypatch):
    from lll import esa_confirmation_receiver_inventory as receiver, ilvis0_control_shards

    key = '178a'
    data = text_rows(2401)
    monkeypatch.setitem(receiver.TARGETS, key, len(data))
    monkeypatch.setattr(ilvis0_control_shards, '_check_continue', lambda *args: None)
    source = tmp_path/receiver.INPUTS/receiver.filename(key)
    source.parent.mkdir(parents=True)
    source.write_bytes(data)
    receipt = tmp_path/'receipt.json'
    receipt.write_text(json.dumps({'records': {key: dict(filename=source.name, size_bytes=len(data),
                       sha256=hashlib.sha256(data).hexdigest(), group_id='example')}}))
    charges = []

    def reserve(*, bound_calls, bound_steps):
        assert bound_calls == 1
        charges.append(bound_steps)

    context = SimpleNamespace(root=tmp_path/'data'/receiver.ID, manifest={'scope': receiver.SCOPE},
                              input_path=lambda: receipt, charge=reserve)
    result = receiver.evaluate(receiver.tasks()[0], context)
    assert result['receiver_epochs'] == 2401
    assert len(result['receiver_candidates']) == 1
    assert result['raw_imu_reads'] == result['new_fits'] == 0
    assert charges == [1024, 1024, 1024, 1]
