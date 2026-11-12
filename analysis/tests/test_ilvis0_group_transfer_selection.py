"""The next retrospective group selection must not use fitted outcomes."""

import csv
from pathlib import Path

import pytest

from lll.ilvis0_group_transfer_selection import build_layouts, select


ROOT = Path(__file__).resolve().parents[2]


def _rows(path):
    with (ROOT / path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def test_four_new_groups_are_fixed_by_saved_metadata():
    cohort = _rows("docs/ilvis0-current-findings-20261015/stretch-analytics.csv")
    provenance = _rows("docs/analysis-provenance/recording-groups.csv")
    pilot = _rows("docs/ilvis0-prediction-pilot-preparation/selection.csv")
    chosen = select(cohort, provenance, pilot)
    assert [row["segment_id"] for row in chosen] == [
        "b365bdf39150ee6afc303ac1",
        "b4ab6e128de963c2ce69aa51",
        "c16df82d514fc69d11d941d2",
        "2f7e37c48f3b4423c55662dd",
    ]
    assert len({row["group_id"] for row in chosen}) == 4
    assert not {row["group_id"] for row in chosen} & {row["group_id"] for row in pilot}
    for row in cohort:
        row["scientific_decision"] = "flat" if row["segment_id"] == chosen[0]["segment_id"] else "globe"
    assert select(cohort, provenance, pilot) == chosen


def test_missing_provenance_is_rejected():
    cohort = _rows("docs/ilvis0-current-findings-20261015/stretch-analytics.csv")
    provenance = _rows("docs/analysis-provenance/recording-groups.csv")
    pilot = _rows("docs/ilvis0-prediction-pilot-preparation/selection.csv")
    provenance = [row for row in provenance if row["record_id"] != "ilvis0:" + cohort[0]["segment_id"]]
    with pytest.raises(ValueError, match="provenance"):
        select(cohort, provenance, pilot)


def test_saved_split_has_four_disjoint_training_prefixes():
    receipt = build_layouts(ROOT)
    layouts = receipt["layouts"]
    assert len(layouts) == 4
    assert len({row["group_id"] for row in layouts}) == 4
    for row in layouts:
        n = row["receiver_epochs"]
        assert row["training_epochs"] == 2 * n // 3
        assert row["prediction_epochs"] == n - row["training_epochs"]
        assert row["last_training_utc_week_s"] < row["first_prediction_utc_week_s"]
        assert row["original_reads"] == row["observed_starts"] == 0
