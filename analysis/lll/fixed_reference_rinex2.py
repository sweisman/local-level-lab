# SPDX-License-Identifier: AGPL-3.0-or-later
"""Stream legacy RINEX GPS coverage while keeping its native signal labels."""
import math

from .esa_rinex_window import gps_seconds


def _line(stream):
    raw = stream.readline(128)
    if raw and not raw.endswith(b'\n'):
        raise ValueError('truncated or overlong RINEX record')
    return raw.decode('ascii')


def _finite(text):
    value = float(text)
    if not math.isfinite(value):
        raise ValueError('nonfinite RINEX field')
    return value


def read_header(stream):
    first = _line(stream)
    version, system = first[:9].strip(), first[40:41].strip() or 'G'
    if (version not in {'2.10', '2.11'} or first[20:21] != 'O' or system not in {'G', 'M'}
            or first[60:].strip() != 'RINEX VERSION / TYPE'):
        raise ValueError('GPS or mixed RINEX 2.10/2.11 observations required')
    layout = dict(version=version, system=system, observation_types=[], time_scale='GPS')
    count = None
    for _ in range(256):
        line = _line(stream)
        if not line:
            break
        label = line[60:].strip()
        if label == '# / TYPES OF OBSERV':
            prefix = line[:6].strip()
            if prefix:
                if count is not None:
                    raise ValueError('repeated RINEX observation declaration')
                count = int(prefix)
            layout['observation_types'].extend(line[6:60].split())
        elif label == 'WAVELENGTH FACT L1/2':
            if [int(line[i:i+6]) for i in (0, 6)] != [1, 1]:
                raise ValueError('only full-cycle GPS wavelength factors are supported')
        elif label == 'MARKER NAME':
            layout['marker'] = line[:60].strip()
        elif label == 'INTERVAL':
            layout['interval_s'] = _finite(line[:60])
        elif label in ('APPROX POSITION XYZ', 'ANTENNA: DELTA H/E/N'):
            values = tuple(_finite(line[i:i+14]) for i in (0, 14, 28))
            key = 'approx_xyz_m' if label == 'APPROX POSITION XYZ' else 'antenna_delta_hen_m'
            layout[key] = values
        elif label == 'RCV CLOCK OFFS APPL':
            applied = int(line[:6])
            if applied not in (0, 1):
                raise ValueError('invalid legacy receiver clock declaration')
            layout['receiver_clock_applied'] = bool(applied)
        elif label == 'TIME OF FIRST OBS':
            fields = line[:60].split()
            if fields[6:] != ['GPS'] and (fields[6:] or system != 'G'):
                raise ValueError('legacy GPS time scale required')
            layout['first'] = gps_seconds(fields[:6])
            layout['century'] = int(fields[0])//100*100
        elif label == 'END OF HEADER':
            declared = layout['observation_types']
            if count != len(declared) or len(set(declared)) != count or not 2 <= count <= 32:
                raise ValueError('complete legacy observation types required')
            if not layout.get('marker') or 'first' not in layout or not {'L1', 'L2'} <= set(declared):
                raise ValueError('marker, GPS epoch and both carrier bands required')
            return layout
    raise ValueError('truncated RINEX observation header')


def _satellites(stream, header, count):
    names = header[32:68]
    for _ in range((count-1)//12):
        continuation = _line(stream)
        if not continuation or continuation[:32].strip():
            raise ValueError('truncated or invalid satellite continuation')
        names = names.rstrip('\r\n')+continuation[32:68]
    if len(names.rstrip('\r\n')) < 3*count:
        raise ValueError('truncated legacy satellite list')
    normalized = []
    for pos in range(0, 3*count, 3):
        token = names[pos:pos+3]
        system, number = token[0].strip() or 'G', token[1:].strip()
        if system not in 'GRESJC' or not number.isdigit() or not 1 <= int(number) <= (32 if system == 'G' else 99):
            raise ValueError('invalid legacy satellite identifier')
        normalized.append(f'{system}{int(number):02}')
    if len(set(normalized)) != count:
        raise ValueError('duplicate satellite identifier')
    return normalized


def _fields(stream, count):
    values = []
    for start in range(0, count, 5):
        line = _line(stream)
        if not line:
            raise ValueError('truncated wrapped RINEX observations')
        size = min(count-start, 5)*16
        fields = line.rstrip('\r\n').ljust(size)
        if fields[size:].strip():
            raise ValueError('legacy observation record exceeds declared fields')
        values.extend(fields[k:k+16] for k in range(0, size, 16))
    return values


def _signal_status(values):
    def present(*codes):
        return any(value and value[:14].strip() and _finite(value[:14]) != 0
                   for code in codes if (value := values.get(code)) is not None)

    if not (present('C1', 'P1') and present('P2', 'C2') and present('L1') and present('L2')):
        return None
    digits = [values[signal][14:15].strip() or '0' for signal in ('L1', 'L2')]
    if any(digit not in '01234567' for digit in digits):
        raise ValueError('invalid legacy carrier lock indicator')
    return tuple(map(int, digits))


def lock_screen(satellites):
    """Exclude variable wavelength epochs and isolate the actual loss-of-lock bit."""
    return {name: tuple(flag & 1 for flag in flags) for name, flags in satellites.items()
            if all(not flag & 2 for flag in flags)}


def observation_epochs(stream, layout, *, retain_measurements=False):
    """Read complete epochs, preserving native observations when requested."""
    previous = None
    codes = layout['observation_types']
    while line := _line(stream):
        fields = line[:26].split()
        if len(fields) != 6 or len(fields[0]) != 2:
            raise ValueError('timed legacy epoch required')
        fields[0] = str(layout['century']+int(fields[0]))
        time = gps_seconds(fields)
        if previous is not None and time <= previous:
            raise ValueError('legacy observation times must be strictly increasing')
        previous = time
        flag, count = int(line[28:29]), int(line[29:32])
        if flag not in (0, 1, 5, 6) or not 0 <= count <= 128:
            raise ValueError('unsupported legacy station event or satellite count')
        satellites, measurements = {}, {}
        if flag == 5:
            for _ in range(count):
                if not _line(stream):
                    raise ValueError('truncated legacy event')
        elif count:
            for name in _satellites(stream, line, count):
                values = _fields(stream, len(codes))
                if flag == 0 and name.startswith('G'):
                    fields = dict(zip(codes, values, strict=True))
                    status = _signal_status(fields)
                    if status is not None:
                        satellites[name] = status
                        if retain_measurements:
                            measurements[name] = {code: _finite(value[:14]) for code, value in fields.items()
                                                  if code in ('C1', 'P1', 'P2', 'C2', 'L1', 'L2') and value[:14].strip()}
        row = dict(week=time[0], seconds=time[1], flag=flag, satellites=satellites)
        if retain_measurements:
            row.update(measurements=measurements,
                       receiver_offset_s=_finite(line[68:80]) if line[68:80].strip() else None)
        yield row
