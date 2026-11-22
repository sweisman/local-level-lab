from itertools import product

from lll.esa_attitude_cover_score import attitude_cover
from lll.esa_attitude_refinement_score import refine_range


def test_attitude_cover_preserves_corners_and_shared_boundaries():
    lower, upper = [-.5]*27, [.75]*27
    cover = attitude_cover(lower, upper)['cells']
    mid = .125
    assert len(cover) == 8
    for cell in cover:
        assert cell['lower'][3:] == lower[3:]
        assert cell['upper'][3:] == upper[3:]
    for attitude in product((-.5, mid, .75), repeat=3):
        assert any(all(lo<=value<=hi for lo,value,hi in
                       zip(cell['lower'][:3],attitude,cell['upper'][:3],strict=True))
                   for cell in cover)
    assert all(all(a<=mid<=b for a,b in zip(cell['lower'][:3],cell['upper'][:3],strict=True))
               for cell in cover)


def test_refining_either_vertical_half_keeps_its_children_inside():
    cover = attitude_cover([-.5]*27,[.75]*27)['cells']
    for parent in cover:
        refined = refine_range(parent)['children']
        assert len(refined)==4
        for i in range(27):
            assert min(child['lower'][i] for child in refined)==parent['lower'][i]
            assert max(child['upper'][i] for child in refined)==parent['upper'][i]
        assert all(child['lower'][1]==parent['lower'][1] and child['upper'][1]==parent['upper'][1]
                   for child in refined)
