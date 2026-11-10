# SPDX-License-Identifier: AGPL-3.0-or-later
"""Strict streaming reader for the documented GNSS-only PPP export layout.

GNSS-only provenance comes from the survey report, not its generic software
label. Preserve receiver coordinates, velocity, covariance and reported UTC.
"""
import math
import re

VERSION='esa-inertial-explorer-ppp-thirty-columns-v1'
COLUMNS=tuple('SeqNum Latitude Longitude H-Ell CxNN CxEE CxHH CxEN CxNH CxEH VNorth VEast VUp CxVNN CxVEE CxVHH CxVEN CxVNH CxVEH SDHeight PDOP GPS GLN GAL BDS QZS CorrTime Week UTCDate UTCTime'.split())


def records(lines):
    datum=False;columns=False;previous=None;count=0
    for number,line in enumerate(lines,1):
        try:text=line.decode('ascii') if isinstance(line,bytes) else line
        except UnicodeError as error:raise ValueError('ASCII receiver export required') from error
        parts=text.split()
        if not parts:continue
        numeric=bool(re.fullmatch(r'\d{8}',parts[0]))
        if not numeric:
            if count:raise ValueError(f'unexpected content after receiver records at line {number}')
            if text.strip().startswith('Datum:'):datum=bool(re.match(r'^\s*Datum:\s+WGS84(?:\s|$)',text))
            if parts[0]=='SeqNum':
                if tuple(parts)!=COLUMNS:raise ValueError('unsupported receiver columns')
                columns=True
            continue
        if not datum or not columns:raise ValueError('documented WGS84 receiver layout required')
        if len(parts)!=30:raise ValueError(f'thirty receiver fields required at line {number}')
        try:values=list(map(float,parts[:28]))
        except ValueError as error:raise ValueError(f'invalid receiver number at line {number}') from error
        if not all(math.isfinite(v) for v in values):raise ValueError('finite receiver measurements required')
        for i in (0,21,22,23,24,25,27):
            if values[i]<0 or not values[i].is_integer():raise ValueError('nonnegative integer sequence, week and satellite counts required')
        if not -90<=values[1]<=90 or not -180<=values[2]<=180 or not 0<=values[26]<604800:
            raise ValueError('unsupported receiver coordinate/time range')
        if not re.fullmatch(r'\d{1,2}/\d{2}/\d{4}',parts[28]) or not re.fullmatch(r'\d{2}:\d{2}:\d{2}(?:\.\d+)?',parts[29]):
            raise ValueError('documented receiver UTC text required')
        if previous is not None and (values[0]<=previous[0] or values[26]<=previous[26] or values[27]!=previous[27]):
            raise ValueError('ordered single-week receiver sequence and time required')
        yield dict(line_number=number,sequence=int(values[0]),latitude_deg=values[1],longitude_deg=values[2],height_m=values[3],
            position_variance_m2=values[4:7],position_cross_covariance_m2=values[7:10],north_mps=values[10],east_mps=values[11],
            up_mps=values[12],reported_height_sd_m=values[19],pdop=values[20],satellites=int(sum(values[21:26])),
            constellation_satellites=[int(v) for v in values[21:26]],time_s=values[26],gps_week=int(values[27]),
            utc_date=parts[28],utc_time=parts[29])
        previous=values;count+=1
    if not count:raise ValueError('receiver observations missing')
