# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
from extract_flightaware_track import utc_rows


def page(time, lat='1.2345'):
    cells = [f'<span class="show-for-medium-up">{time}</span><span class="hide-for-medium-up">21:00</span>',
        f'<span class="show-for-medium-up">{lat}</span><span class="hide-for-medium-up">1.23</span>',
        '103.5', '180&deg;', '300', '345', '35,000', '<img alt="Level">', 'ADS-B']
    return '<p>All times are in EDT time</p><table id="tracklogTable"><tr class="smallrow1">'+''.join(
        '<td>'+value+'</td>' for value in cells)+'</tr></table>'


def test_desktop_precision_and_utc_date_crossing():
    rows, provenance = utc_rows(page('Thu 09:30:00 PM'),
        'https://www.flightaware.com/live/flight/SIA938/history/20261002/0125Z/WSSS/WADD/tracklog')
    assert rows[0][0] == 'Fri 01:30:00'
    assert rows[0][1] == '1.2345'
    assert rows[0][6] == '35000' and rows[0][7] == 'Level'
    assert provenance['first_observation_utc'] == '2026-10-02T01:30:00+00:00'


def test_empty_or_unknown_timezone_page_is_rejected():
    url = 'https://www.flightaware.com/live/flight/ICE680/history/20261002/2250Z/KSEA/BIKF/tracklog'
    with pytest.raises(ValueError, match='no public coordinate'):
        utc_rows('<p>All times are in EDT time</p>', url)
    with pytest.raises(ValueError, match='timezone'):
        utc_rows(page('Fri 06:30:00 PM').replace('EDT', 'unknown'), url)


def test_event_annotations_are_not_coordinate_rows():
    html = page('Fri 06:30:00 PM').replace('<tr class="smallrow1">',
        '<tr class="smallrow1 flight_event_facility"><td colspan="6">Airline</td></tr><tr class="smallrow1">')
    rows, _ = utc_rows(html, 'https://www.flightaware.com/live/flight/ICE680/history/20261002/2250Z/KSEA/BIKF/tracklog')
    assert len(rows) == 1
