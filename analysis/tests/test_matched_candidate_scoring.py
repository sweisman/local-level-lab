"""Descriptive shape-first scoring cannot turn an incomplete fit into evidence."""

from lll.matched_candidate_scoring import shape_first


def test_shape_first_requires_complete_candidates_and_shape_before_rotation():
    all_done=dict.fromkeys(('sphere_rotating','sphere_still','flat_still'),True)
    assert shape_first(dict(sphere_rotating=True,sphere_still=False,
                            flat_still=False),all_done)==dict(
        shape='globe',background_field='specified_nonzero',
        scientific_decision='abstain')
    assert shape_first(dict(sphere_rotating=False,sphere_still=False,
                            flat_still=True),all_done)['background_field']=='abstain'
    assert shape_first(dict(sphere_rotating=True,sphere_still=False,
                            flat_still=True),all_done)['shape']=='abstain'
    incomplete=dict(all_done,flat_still=False)
    assert shape_first(dict(sphere_rotating=True,sphere_still=False,
                            flat_still=False),incomplete)==dict(
        shape='abstain',background_field='abstain',
        scientific_decision='abstain')
