# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare archived Greenland ground residuals on common 30-second intervals."""

import argparse
import json
import math
from pathlib import Path

from .esa_ground_reference_evidence import BASE, _public
from .studies.artifacts import digest, encoded


PLAN = 'ESA_GROUND_CADENCE_COMPARISON_PLAN.md'
OUTPUT = 'esa-ground-cadence-comparison-v1.json'
SOURCES = {
    'esa-nuuk-phase-transfer-result.json': '0779e5d7362e17176ade66268f45276b2158db7989ff4a1c1dacd01b48a4d58e',
    'esa-qaq-phase-transfer-result.json': '50508c8bc9a6777b44b27533dee56fd977c7874e4a3f1fc46d247f8a2493d61b',
    'esa-qaq-ground-score-result.json': '98251d43fbaed81aeb24cb3fd8555b74636fab0c1c982a296fb315772e68a185',
}
EARLIER = range(388230, 388530, 30)
LATER = range(388620, 388710, 30)
CHANNELS = ('nuuk_aircraft_m', 'nuuk_ground_m', 'qaq_aircraft_m', 'qaq_ground_m')


def index_seconds(rows, aircraft_key, ground_key):
    indexed = {}
    for row in rows:
        time = row['start_gps_s']
        satellites = row['satellites']
        aircraft, ground = row[aircraft_key], row[ground_key]
        if (not math.isfinite(time) or time != int(time) or time in indexed or not satellites
                or any(type(prn) is not int or prn <= 0 for prn in satellites)
                or len(set(satellites)) != len(satellites) or len(aircraft) != len(satellites)
                or len(ground) != len(satellites) or not all(map(math.isfinite, aircraft + ground))):
            raise ValueError('unique whole seconds, unique satellites and finite paired ranges required')
        indexed[time] = (dict(zip(satellites, aircraft, strict=True)),
                         dict(zip(satellites, ground, strict=True)))
    return indexed


def align_interval(start, near, far):
    seconds = range(start, start+30)
    if any(second not in far for second in seconds):
        return None
    pairs = [far[second] for second in seconds]
    prns = sorted(set.intersection(*(set(channel) for pair in (near, *pairs) for channel in pair)))
    if len(prns) < 5:
        return None

    def centered(values):
        average = math.fsum(values)/len(values)
        return [value-average for value in values]

    values = [centered([channel[prn] for prn in prns]) for channel in near]
    values.extend(centered([math.fsum(pair[index][prn] for pair in pairs) for prn in prns])
                  for index in range(2))
    return dict(start_gps_s=start, satellites=prns, **dict(zip(CHANNELS, values, strict=True)))


def _summarize(earlier, later):
    from .esa_qaq_phase_transfer import transfer

    def rows(block, station):
        return [(row['start_gps_s'], row[f'{station}_aircraft_m'], row[f'{station}_ground_m']) for row in block]

    def disagreement(block, kind):
        differences = [a-b for row in block for a, b in zip(row[f'nuuk_{kind}_m'], row[f'qaq_{kind}_m'], strict=True)]
        return math.sqrt(math.fsum(x*x for x in differences)/len(differences))

    return dict(stations={station: transfer(rows(earlier, station), rows(later, station))
                          for station in ('nuuk', 'qaq')},
                cross_report_rms_m={period: {kind: disagreement(block, kind) for kind in ('aircraft', 'ground')}
                                    for period, block in (('earlier', earlier), ('later', later))})


def replay(root):
    from .gnss_position import GAMMA

    near, far_earlier, far_later = [_public(root, name, sha) for name, sha in SOURCES.items()]
    if near['navigation_changes'] or far_earlier['later_sha256'] != SOURCES['esa-qaq-ground-score-result.json']:
        raise ValueError('the sealed continuous ground and paired aircraft ranges are required')
    if any(row['stop_gps_s'] != row['start_gps_s']+1 for row in far_later['intervals']):
        raise ValueError('the later carrier rows must cover one second each')
    far = index_seconds(far_earlier['training_rows'], 'aircraft_m', 'ground_m')
    far.update(index_seconds(far_later['intervals'], 'air_range_m', 'ground_range_m'))

    def ionosphere_free(rows):
        return [(GAMMA*l1-l2)/(GAMMA-1.) for l1, l2 in rows]

    blocks, unavailable = [], []
    for starts, indices in ((EARLIER, near['training_indices']), (LATER, near['withheld_indices'])):
        by_time = {near['times'][i]: i for i in indices}
        block = []
        for start in starts:
            i = by_time[start]
            if near['times'][i+1] != start+30:
                raise ValueError('the permanent Nuuk endpoint pairing differs')
            paired = tuple(dict(zip(near['satellites'], ionosphere_free(near[f'{kind}_band_residual_m'][i]), strict=True))
                           for kind in ('aircraft', 'ground'))
            row = align_interval(start, paired, far)
            if row is None:
                unavailable.append(start)
            else:
                block.append(row)
        blocks.append(block)
    earlier, later = blocks
    if not earlier or not later:
        raise ValueError('both planned blocks need usable common satellite support')
    return dict(version=1, inputs_sha256=SOURCES, plan_sha256=digest((root/BASE/PLAN).read_bytes()),
                source_sha256=digest(Path(__file__).read_bytes()), earlier=earlier, later=later,
                unavailable_starts_gps_s=unavailable, **_summarize(earlier, later), new_fits=0,
                protected_reads=0, scientific_decision='abstain')


def main():
    from .ilvis0_matched_observed_inputs import _write_equal

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('build', 'check'))
    args = parser.parse_args()
    root = Path.cwd()
    result = replay(root)
    path = root/BASE/OUTPUT
    raw = encoded(result)
    if args.action == 'build':
        _write_equal(path, raw)
    elif path.read_bytes() != raw:
        raise ValueError('the archived same-cadence comparison did not reproduce')
    print(json.dumps(dict(sha256=digest(raw), earlier_intervals=len(result['earlier']),
                          later_intervals=len(result['later']), stations=result['stations'],
                          cross_report_rms_m=result['cross_report_rms_m']), indent=2))


if __name__ == '__main__':
    main()
