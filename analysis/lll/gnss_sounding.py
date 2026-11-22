# SPDX-License-Identifier: AGPL-3.0-or-later
"""Use observed IGRA pressure, temperature and dew point in a GNSS delay model."""

from bisect import bisect_right
from dataclasses import dataclass
import math


def _interpolate(rows, point):
    index = bisect_right(rows, point, key=lambda row: row[0])
    if index == len(rows) and point == rows[-1][0]:
        return rows[-1][1:]
    if not 0 < index < len(rows):
        raise ValueError('query outside measured profile')
    low, high = rows[index - 1:index + 1]
    fraction = (point - low[0]) / (high[0] - low[0])
    return tuple(a + fraction * (b - a) for a, b in zip(low[1:], high[1:], strict=True))


@dataclass(frozen=True)
class Sounding:
    station_id: str
    latitude_deg: float
    longitude_deg: float
    heights: tuple[tuple[float, float], ...]
    weather: tuple[tuple[float, float, float], ...]

    def weather_at(self, height_m):
        pressure_log, = _interpolate(self.heights, height_m)
        temperature, dewpoint = _interpolate(self.weather, pressure_log)
        return math.exp(pressure_log), temperature, dewpoint


def read_sounding(text, surface_height_m):
    header, *levels = text.splitlines()
    if not header.startswith('#') or len(header) < 71:
        raise ValueError('IGRA sounding header required')
    if len(levels) != int(header[32:36]):
        raise ValueError('IGRA level count mismatch')
    heights, weather = {}, {}
    for level in levels:
        if len(level) < 51:
            raise ValueError('truncated IGRA level')
        pressure_pa = int(level[9:15])
        if pressure_pa <= 0:
            continue
        pressure_log = math.log(pressure_pa / 100.)
        height = int(level[16:21])
        if height in (-9999, -8888) and level[1] == '1':
            height = surface_height_m
        if height not in (-9999, -8888):
            if height in heights and heights[height] != pressure_log:
                raise ValueError('contradictory pressures at one height')
            heights[height] = pressure_log
        temperature = int(level[22:27])
        depression = int(level[34:39])
        if temperature not in (-9999, -8888) and depression >= 0:
            values = (273.15 + temperature / 10., 273.15 + (temperature - depression) / 10.)
            if pressure_log in weather and weather[pressure_log] != values:
                raise ValueError('contradictory temperature or dew point at one pressure')
            weather[pressure_log] = values
    heights = tuple(sorted(heights.items()))
    if len(heights) < 2 or len(weather) < 2 or any(
            b[1] >= a[1] for a, b in zip(heights, heights[1:])):
        raise ValueError('incomplete or non-monotonic sounding')
    return Sounding(header[1:12], int(header[55:62]) / 1e4, int(header[63:71]) / 1e4,
                    heights, tuple((p, *values) for p, values in sorted(weather.items())))


def vapour_at_dewpoint(dewpoint_kelvin):
    return 6.108 * math.exp((17.15 * dewpoint_kelvin - 4684.) / (dewpoint_kelvin - 38.45))


def zenith_delay(latitude_rad, height_m, pressure_hpa, temperature_kelvin, vapour_hpa):
    dry = .0022768 * pressure_hpa / (1 - .00266 * math.cos(2 * latitude_rad) - .00028 * height_m / 1000)
    wet = .002277 * (1255. / temperature_kelvin + .05) * vapour_hpa
    return dry + wet
