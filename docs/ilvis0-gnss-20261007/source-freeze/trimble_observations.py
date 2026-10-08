# SPDX-License-Identifier: AGPL-3.0-or-later
"""Strict receiver-observation decoding, separate from Applanix fused navigation.

Structural references are Trimble's RT17 concise/expanded, RT27 and GPS ephemeris
tables. Raw flags and encoded values remain available: decoding is not calibration.
No IMU, Earth-model decision, range repair, ambiguity resolution or interpolation.
"""
import math
import struct

import numpy as np

REFERENCES = {
    'rt17_concise': 'https://receiverhelp.trimble.com/oem-gnss/icd-subtype0-realtime-survey-data-17-concise.html',
    'rt17_expanded': 'https://receiverhelp.trimble.com/oem-gnss/icd-subtype0-realtime-survey-data-17-expanded.html',
    'rt27': 'https://receiverhelp.trimble.com/oem-gnss/icd-subtype6-realtime-gnss-survey-data-27.html',
    'gps_ephemeris': 'https://receiverhelp.trimble.com/oem-gnss/icd-pkt-response55h-gps-eph.html',
    'rtklib_unit_crosscheck': 'https://raw.githubusercontent.com/tomojitakasu/RTKLIB/master/src/rcv/rt17.c',
    'gps_orbit_equations': 'https://www.navcen.uscg.gov/sites/default/files/pdf/gps/IS-GPS-200N.pdf',
}


class Cursor:
    def __init__(self, data):
        self.data = bytes(data)
        self.offset = 0

    def take(self, size):
        if size < 0 or self.offset + size > len(self.data):
            raise ValueError('truncated receiver field; no repair')
        start = self.offset
        self.offset += size
        return self.data[start:self.offset]

    def integer(self, size, signed=False):
        return int.from_bytes(self.take(size), 'big', signed=signed)

    def number(self, code):
        value = struct.unpack('>'+code, self.take(struct.calcsize('>'+code)))[0]
        if not math.isfinite(value):
            raise ValueError('nonfinite receiver measurement')
        return value

    def flags(self, maximum=4):
        values = []
        while True:
            if len(values) == maximum:
                raise ValueError('unsupported receiver flag extension')
            value = self.integer(1)
            values.append(value)
            if not value & 128:
                return values

    def block(self):
        size = self.integer(1)
        if size < 2:
            raise ValueError('invalid receiver block length')
        return Cursor(self.take(size-1))

    def finish(self):
        if self.offset != len(self.data):
            raise ValueError('unexpected trailing receiver fields; no ignored bytes')


def epoch(seconds, week):
    if not math.isfinite(seconds) or not 0 <= seconds < 604800:
        raise ValueError('receiver epoch outside GPS week')
    if week is None or not isinstance(week, int) or not 0 <= week <= 65535:
        raise ValueError('recorded GPS week required; no current-date guessing')
    return dict(gps_week=week, gps_week_seconds=seconds)


def decode_rt17(record, recorded_week):
    if record['subtype'] != 0 or record['flags'] & ~3:
        raise ValueError('unsupported RT17 subtype/interpretation flags')
    concise, enhanced = bool(record['flags'] & 1), bool(record['flags'] & 2)
    cursor = Cursor(record['payload'])
    out = epoch(cursor.number('d')/1000, recorded_week)
    clock = cursor.number('d')/1000
    count = cursor.integer(1)
    if count > 32:
        raise ValueError('invalid RT17 satellite count')
    satellites = []
    identities = set()
    for _ in range(count):
        prn, flags1, flags2 = (cursor.integer(1) for _ in range(3))
        if not 1 <= prn <= 32 or prn in identities:
            raise ValueError('invalid/duplicate RT17 satellite')
        identities.add(prn)
        status = 1 if concise else cursor.integer(1)
        # Expanded flag-status controls whether loading flags have defined meaning.
        if not status & 1:
            raise ValueError('undefined expanded RT17 loading flags')
        elevation = cursor.integer(1 if concise else 2, signed=True)
        azimuth = cursor.integer(2, signed=True)
        satellite = dict(system=0, antenna=0, sv_id=prn, flags=[flags1, flags2],
            flag_status=status, elevation_deg=elevation, azimuth_deg=azimuth,
            code_smoothed=bool(flags2 & 8), signals=[])
        l1 = None
        if flags1 & 64:
            snr = cursor.integer(1)/4 if concise else cursor.number('d')
            pseudorange, phase = cursor.number('d'), cursor.number('d')
            doppler = cursor.number('f' if concise else 'd')
            if not concise:
                satellite['l1_reserved'] = cursor.number('d')
            l1 = dict(band=0, track_type=flags2 & 1, snr_dbhz=snr,
                pseudorange_m=pseudorange, phase_cycles=phase, doppler_hz=doppler,
                range_loaded=True, phase_loaded=bool(flags1 & 16),
                cycle_slip=bool(flags1 & 2), raw_flags=flags1)
            satellite['signals'].append(l1)
        if flags1 & 1:
            snr = cursor.integer(1)/4 if concise else cursor.number('d')
            phase = cursor.number('d')
            difference = cursor.number('f' if concise else 'd')
            satellite['signals'].append(dict(band=1, track_type=(flags2 >> 1) & 1,
                snr_dbhz=snr, phase_cycles=phase, phase_loaded=True,
                phase_units='L2 cycles' if flags1 & 32 else 'squared-L2 phase; not ordinary cycles',
                pseudorange_difference_m=difference,
                pseudorange_m=l1['pseudorange_m']+difference if l1 and flags1 & 32 else None,
                range_loaded=bool(flags1 & 32), cycle_slip=bool(flags1 & 4), raw_flags=flags1))
        if enhanced:
            satellite.update(iode=cursor.integer(1), l1_slip_counter=cursor.integer(1),
                             l2_slip_counter=cursor.integer(1))
            if not concise:
                satellite['enhanced_reserved'] = cursor.integer(1)
                satellite['enhanced_l2_doppler_hz'] = cursor.number('d')
        satellites.append(satellite)
    cursor.finish()
    out.update(format='RT17', receiver_clock_offset_s=clock,
        receiver_clock_offset_known=clock != 0, satellites=satellites,
        encoded_payload_hex=record['payload'].hex(),
        phase_sign_convention='receiver phase decreases for increasing range; not RINEX converted',
        interpretation_flags=record['flags'])
    return out


def decode_rt27(record):
    if record['subtype'] != 6 or record['flags'] != 0:
        raise ValueError('unsupported RT27 subtype/interpretation flags')
    cursor = Cursor(record['payload'])
    header = cursor.block()
    week, ms, clock = header.integer(2), header.integer(4), header.integer(3, signed=True)
    out = epoch(ms/1000, week)
    count, flags = header.integer(1), header.flags()
    epoch_flags = list(flags)
    if len(flags) != 1 or flags[0] & ~0x32:
        raise ValueError('unsupported RT27 epoch flag semantics')
    if flags[0] & 2:
        out['gps_glonass_offset_ms'] = header.integer(3, signed=True)/2**22
    if flags[0] & 16:
        out['raim_info'] = header.integer(1)
    header.finish()
    if flags[0] & 32:
        # Inter-system clock offsets are variable-width blocks, not observations.
        block = cursor.block()
        out['inter_system_clock_offsets_opaque_hex'] = block.data.hex()
        block.offset = len(block.data)
    satellites = []
    identities = set()
    for _ in range(count):
        block = cursor.block()
        sv, system_antenna = block.integer(1), block.integer(1)
        channel, signals = block.integer(1, signed=True), block.integer(1)
        elevation, azimuth = block.integer(1), block.integer(1)*2
        flags = block.flags()
        if len(flags) > 2:
            raise ValueError('unsupported RT27 SV flag extension semantics')
        satellite = dict(system=system_antenna & 63, antenna=system_antenna >> 6,
            sv_id=sv, channel=channel, elevation_deg=elevation, azimuth_deg=azimuth,
            flags=flags, code_smoothed=bool(flags[0] & 4),
            phase_smoothed=bool(flags[0] & 8), unhealthy=bool(flags[0] & 16),
            raim_fault=bool(flags[0] & 32), signals=[])
        identity = (satellite['system'], satellite['antenna'], sv)
        if sv == 0 or identity in identities or signals == 0:
            raise ValueError('invalid/duplicate RT27 SV identity or no signal blocks')
        identities.add(identity)
        if flags[0] & 64:
            satellite['pseudo_iode'] = block.integer(4)
        block.finish()
        base_range = None
        for index in range(signals):
            block = cursor.block()
            band, track = block.integer(1), block.integer(1)
            snr = block.integer(2)
            range_bytes = block.take(4 if index == 0 else 2)
            raw_phase, slips = block.integer(6, signed=True), block.integer(1)
            mf = block.flags()
            if len(mf) > 4:
                raise ValueError('unsupported RT27 measurement flags')
            mf2 = mf[1] if len(mf) > 1 else 0
            raw_doppler = block.integer(3, signed=True) if mf[0] & 4 else None
            overflow = block.take(1) if mf2 & 1 else b''
            if index == 0 and overflow:
                raise ValueError('differential range overflow on absolute first range')
            block.finish()
            raw_range = int.from_bytes(overflow+range_bytes, 'big', signed=index != 0)
            if index == 0:
                base_range = raw_range/(2**6 if satellite['system'] in (1, 4) else 2**7)
                if mf2 & 2:
                    base_range += 33554431.0
                pseudorange = base_range
            else:
                if mf2 & 2:
                    raise ValueError('absolute-range overflow on differential range unsupported')
                pseudorange = base_range+raw_range/2**8
            satellite['signals'].append(dict(band=band, track_type=track, raw_snr=snr,
                snr_dbhz=snr/10, raw_range=raw_range, raw_phase=raw_phase,
                raw_doppler=raw_doppler, pseudorange_m=pseudorange,
                pseudorange_difference_m=raw_range/2**8 if index else None,
                phase_cycles=raw_phase/2**15,
                doppler_hz=raw_doppler/2**8 if raw_doppler is not None else None,
                slip_counter=slips, measurement_flags=mf,
                phase_loaded=bool(mf[0] & 1), range_loaded=bool(mf[0] & 2),
                cycle_slip=bool(mf[0] & 8), half_cycle=bool(mf[0] & 16),
                unhealthy=bool(len(mf) > 2 and mf[2] & 4)))
        satellites.append(satellite)
    cursor.finish()
    out.update(format='RT27', receiver_clock_offset_s=clock/2**19/1000,
        raw_clock_offset=clock, epoch_flags=epoch_flags,
        satellites=satellites, encoded_payload_hex=record['payload'].hex())
    return out


def decode_gps_ephemeris(packet):
    payload = packet['payload']
    if packet['kind'] != 'binary' or packet['packet_type'] != 0x55 or len(payload) != 176 or payload[0] != 1:
        raise ValueError('unsupported GPS ephemeris subtype/length')
    cursor = Cursor(payload)
    subtype, prn, week, iodc = cursor.integer(1), cursor.integer(1), cursor.integer(2), cursor.integer(2)
    reserved, iode = cursor.integer(1), cursor.integer(1)
    tow, toc, toe = (cursor.integer(4) for _ in range(3))
    names = ('tgd_s','af2','af1','af0','crs_m','delta_n_semicircles_s','m0_semicircles',
             'cuc_semicircles','eccentricity','cus_semicircles','sqrt_a_m',
             'cic_semicircles','omega0_semicircles','cis_semicircles','i0_semicircles',
             'crc_m','argument_perigee_semicircles','omega_dot_semicircles_s','i_dot_semicircles_s')
    values = {name:cursor.number('d') for name in names}
    flags = cursor.integer(4)
    cursor.finish()
    if not 1 <= prn <= 32 or any(t >= 604800 for t in (tow, toc, toe)) or not (
            0 <= values['eccentricity'] < 1 and 4000 < values['sqrt_a_m'] < 6000):
        raise ValueError('invalid GPS ephemeris engineering values')
    out = dict(subtype=subtype, sv_id=prn, gps_week=week, iodc=iodc, iode=iode,
        reserved=reserved, tow_s=tow, toc_s=toc, toe_s=toe, flags=flags,
        health=(flags >> 4) & 63, ura_index=(flags >> 11) & 15,
        fit_interval_flag=bool(flags & 1024), raw_payload_hex=payload.hex(), **values)
    # All angular elements arrive in semicircles; retain the original fields too.
    for name in names:
        if 'semicircles' in name:
            out[name.replace('semicircles', 'rad')] = values[name]*math.pi
    return out


def geometry_diagnostic(satellites):
    """Equal-weight local geometry only; not measured errors or a covariance model."""
    rows = []
    systems = []
    for satellite in satellites:
        usable = any(signal['range_loaded'] and not signal.get('unhealthy') for signal in satellite['signals'])
        if (not usable or satellite['antenna'] != 0 or satellite.get('unhealthy') or
                satellite.get('raim_fault') or not 0 <= satellite['elevation_deg'] <= 90):
            continue
        az, el = math.radians(satellite['azimuth_deg']), math.radians(satellite['elevation_deg'])
        rows.append([-math.cos(el)*math.cos(az), -math.cos(el)*math.sin(az), -math.sin(el)])
        systems.append(satellite['system'])
    if not rows:
        return dict(satellites=0, rank=0, full_rank=False, covariance_established=False)
    distinct = sorted(set(systems))
    # One independent clock per GNSS system; never treat a mixed constellation as
    # sharing an independently known receiver/inter-system clock.
    design = np.column_stack([np.array(rows), np.array([[int(s==c) for c in distinct] for s in systems])])
    singular = np.linalg.svd(design, compute_uv=False)
    rank = int(np.linalg.matrix_rank(design))
    out = dict(satellites=len(rows), systems=distinct, parameters=design.shape[1], rank=rank,
        full_rank=rank == design.shape[1], singular_values=singular.tolist(),
        covariance_established=False, assumption='unit independent range variance; geometry diagnostic only')
    if out['full_rank']:
        inverse = np.linalg.pinv(design) @ np.linalg.pinv(design).T
        out.update(hdop=float(np.sqrt(inverse[0,0]+inverse[1,1])),
            vdop=float(np.sqrt(inverse[2,2])), pdop=float(np.sqrt(np.trace(inverse[:3,:3]))))
    return out


def gps_position(ephemeris, week, seconds):
    """Broadcast GPS ECEF geometry, conditional on the standard GNSS model.

    Used solely for decoder/sky-angle checks. No range positioning, atmosphere,
    satellite-clock correction, transmit-time or Earth-model conclusion here.
    Reject stale and unhealthy ephemerides; don't wrap a wrong week into agreement.
    """
    dt = (week-ephemeris['gps_week'])*604800+seconds-ephemeris['toe_s']
    if ephemeris['health'] or abs(dt)>7200:
        raise ValueError('unhealthy or stale GPS ephemeris')
    a = ephemeris['sqrt_a_m']**2
    mean = ephemeris['m0_rad']+(math.sqrt(3.986005e14/a**3)+ephemeris['delta_n_rad_s'])*dt
    eccentricity = ephemeris['eccentricity']
    eccentric = mean
    for _ in range(20):
        change = (eccentric-eccentricity*math.sin(eccentric)-mean)/(1-eccentricity*math.cos(eccentric))
        eccentric -= change
        if abs(change)<1e-13:
            break
    else:
        raise ValueError('GPS Kepler solve did not converge')
    true = math.atan2(math.sqrt(1-eccentricity**2)*math.sin(eccentric), math.cos(eccentric)-eccentricity)
    argument = true+ephemeris['argument_perigee_rad']
    c2, s2 = math.cos(2*argument), math.sin(2*argument)
    latitude = argument+ephemeris['cus_rad']*s2+ephemeris['cuc_rad']*c2
    radius = a*(1-eccentricity*math.cos(eccentric))+ephemeris['crs_m']*s2+ephemeris['crc_m']*c2
    inclination = ephemeris['i0_rad']+ephemeris['i_dot_rad_s']*dt+ephemeris['cis_rad']*s2+ephemeris['cic_rad']*c2
    rotation = 7.2921151467e-5
    node = ephemeris['omega0_rad']+(ephemeris['omega_dot_rad_s']-rotation)*dt-rotation*ephemeris['toe_s']
    x, y = radius*math.cos(latitude), radius*math.sin(latitude)
    return np.array([x*math.cos(node)-y*math.cos(inclination)*math.sin(node),
        x*math.sin(node)+y*math.cos(inclination)*math.cos(node),y*math.sin(inclination)])


def sky_angles(position, receiver):
    """WGS84 receiver coordinate context; no IMU orientation is supplied."""
    latitude, longitude = receiver['latitude_rad'], receiver['longitude_rad']
    s, c = math.sin(latitude), math.cos(latitude)
    sl, cl = math.sin(longitude), math.cos(longitude)
    e2 = (1/298.257223563)*(2-1/298.257223563)
    n = 6378137/math.sqrt(1-e2*s*s)
    h = receiver['ellipsoid_height_m']
    difference = position-np.array([(n+h)*c*cl,(n+h)*c*sl,(n*(1-e2)+h)*s])
    east = -sl*difference[0]+cl*difference[1]
    north = -s*cl*difference[0]-s*sl*difference[1]+c*difference[2]
    up = c*cl*difference[0]+c*sl*difference[1]+s*difference[2]
    return math.degrees(math.atan2(east,north))%360, math.degrees(math.atan2(up,math.hypot(north,east)))
