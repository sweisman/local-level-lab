"""A later ground control keeps the first run sealed and reuses its rule."""


def rows():
    return [dict(sequence=i,time_s=i*.5,latitude_deg=55.,longitude_deg=0.,
                 height_m=100.,north_mps=0.,east_mps=0.,up_mps=0.,
                 position_variance_m2=[.01,.04,.09]) for i in range(30)]


def test_later_run_is_selected_without_reusing_first():
    from lll.esa_second_ground_interval import select_second
    data=rows()
    for i in range(6,15):data[i]['east_mps']=2.
    assert select_second(data,first_stop=6,min_reports=5)==(15,30)


def test_no_second_run_is_explicit():
    from lll.esa_second_ground_interval import select_second
    data=rows()
    for i in range(6,30):data[i]['east_mps']=2.
    assert select_second(data,first_stop=6,min_reports=5) is None
