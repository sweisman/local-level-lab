import pytest

from lll.ilvis0_matched_extension_inputs import exact_join, original_path
from lll.ilvis0_receiver_overlap import WEEK_MS


def test_extension_join_keeps_original_training_cut_and_excludes_extra_epoch():
    original = [dict(time_s=1.), dict(time_s=2.), dict(time_s=3.)]
    tags = [3*WEEK_MS+15_000+t for t in (0, 1000, 2000, 3000)]
    result = exact_join(original, tags, cut=2, gps_minus_utc_s=15.)
    assert result == dict(receiver_position_pilot_epochs=4, exact_common_receiver_epochs=3,
        exact_common_training_epochs=2, exact_common_prediction_epochs=1)


def test_extension_join_refuses_missing_or_ambiguous_original_epochs():
    original = [dict(time_s=1.), dict(time_s=2.), dict(time_s=3.)]
    with pytest.raises(ValueError, match='exact'):
        exact_join(original, [1001, 2000, 3000], cut=2, gps_minus_utc_s=0.)
    with pytest.raises(ValueError, match='exact'):
        exact_join(original, [1000, 2000, 2000, 3000], cut=2, gps_minus_utc_s=0.)


def test_extension_original_path_resolves_absolute_and_relative_corpus_names(tmp_path):
    path = tmp_path/'data/ilvis0-ready/record.013.gz'
    path.parent.mkdir(parents=True)
    path.write_bytes(b'original')
    relative = path.relative_to(tmp_path).as_posix()
    assert original_path(tmp_path, str(path)) == original_path(tmp_path, relative) == relative
    with pytest.raises(ValueError, match='original'):
        original_path(tmp_path, 'data/another/record.013.gz')
