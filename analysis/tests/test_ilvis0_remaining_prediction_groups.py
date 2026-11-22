# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only selection of unused conservative NASA groups."""

import csv
import io
from pathlib import Path

import pytest

from lll.ilvis0_remaining_prediction_groups import (
    INPUTS, OUTPUT_FIELDS, build, select)


ROOT = Path(__file__).resolve().parents[2]


def saved_tables():
    return {key: list(csv.DictReader((ROOT/path).open(newline='')))
            for key, path in INPUTS.items()}


def test_remaining_groups_are_unique_and_outcome_blind():
    tables = saved_tables()
    original = select(**tables)
    assert len(original) == len({row['group_id'] for row in original}) == 20
    assert {row['imu_type'] for row in original} == {'21'}
    for row in tables['cohort']:
        row['shape_preference'] = 'arbitrary-changed-outcome'
        row['raw_native_mean_z_dph'] = 'arbitrary-changed-gyro'
    assert select(**tables) == original


def test_prior_group_or_source_change_is_rejected():
    tables = saved_tables()
    tables['transfer'][0]['group_id'] = 'different'
    with pytest.raises(ValueError, match='selection differs'):
        select(**tables)
    tables = saved_tables()
    tables['cohort'][0]['source_sha256'] = 'different'
    with pytest.raises(ValueError, match='provenance'):
        select(**tables)


def test_inventory_binds_four_tables_and_selector():
    result = build(ROOT)
    assert result['receipt']['groups'] == 20
    assert len(result['receipt']['input_sha256']) == 4
    assert result['receipt']['observed_fits'] == 0
    assert result['receipt']['model_outcomes_used'] is False
    reader = csv.DictReader(io.StringIO(result['csv'].decode()))
    assert tuple(reader.fieldnames) == OUTPUT_FIELDS
    assert list(reader) == result['rows']
