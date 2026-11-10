# SPDX-License-Identifier: AGPL-3.0-or-later
"""Checked enhanced-position decoding kept separate from the frozen TSIP parser."""
import hashlib


def decode_enhanced_position(record):
    """Decode checked RT27 subtype 7 fields, retaining every original integer.

    The reported sigmas are receiver output, not an independently calibrated
    covariance. Optional variable blocks are retained by hash, not guessed.
    """
    if record['subtype'] != 7 or record['flags'] != 0:
        raise ValueError('unsupported enhanced-position subtype or flags')
    data = record['payload']
    if len(data) < 68 or data[0] != 15 or data[15] != 53:
        raise ValueError('unsupported enhanced-position block lengths')

    def integer(start, size, *, signed=False):
        return int.from_bytes(data[start:start+size], 'big', signed=signed)

    week, milliseconds = integer(1, 2), integer(3, 4)
    if milliseconds >= 604800000:
        raise ValueError('enhanced-position time outside GPS week')
    raw = dict(latitude_counts=integer(16, 6, signed=True),
               longitude_counts=integer(22, 6, signed=True),
               height_counts=integer(28, 4, signed=True),
               velocity_north_counts=integer(32, 4, signed=True),
               velocity_east_counts=integer(36, 4, signed=True),
               velocity_up_counts=integer(40, 4, signed=True),
               receiver_clock_offset_counts=integer(44, 4, signed=True),
               receiver_clock_drift_counts=integer(48, 4, signed=True),
               hdop_counts=integer(52, 2), vdop_counts=integer(54, 2),
               tdop_counts=integer(56, 2),
               sigma_north_counts=integer(58, 2),
               sigma_east_counts=integer(60, 2),
               sigma_up_counts=integer(62, 2),
               rms_counts=integer(64, 2), unit_std_counts=integer(66, 2))
    latitude = raw['latitude_counts']/2**40
    longitude = raw['longitude_counts']/2**39
    if abs(latitude) > 90 or abs(longitude) > 180:
        raise ValueError('invalid enhanced-position coordinates')
    optional = []
    offset = 68
    while offset < len(data):
        size = data[offset]
        if size < 1 or offset+size > len(data):
            raise ValueError('truncated enhanced-position optional block')
        block = data[offset:offset+size]
        optional.append(dict(size=size, sha256=hashlib.sha256(block).hexdigest()))
        offset += size
    return dict(subtype=7, first_stream_offset=record['first_stream_offset'],
        last_stream_offset=record['last_stream_offset'], pages=record['pages'],
        payload_sha256=record['payload_sha256'], gps_week=week,
        gps_milliseconds=milliseconds, gps_week_seconds=milliseconds/1000,
        receiver_motion_state=data[7], satellites_tracked=data[8],
        satellites_used=data[9], raim_info=data[10],
        position_system_flags=data[11], position_solution_mode=data[12],
        position_augmentation_type=data[13], position_processing_type=data[14],
        latitude_deg=latitude, longitude_deg=longitude,
        ellipsoid_height_m=raw['height_counts']/2**12,
        velocity_north_mps=raw['velocity_north_counts']/2**21,
        velocity_east_mps=raw['velocity_east_counts']/2**21,
        velocity_up_mps=raw['velocity_up_counts']/2**21,
        hdop=raw['hdop_counts']/16, vdop=raw['vdop_counts']/16,
        tdop=raw['tdop_counts']/16,
        reported_sigma_north_m=raw['sigma_north_counts']/2**11,
        reported_sigma_east_m=raw['sigma_east_counts']/2**11,
        reported_sigma_up_m=raw['sigma_up_counts']/2**11,
        reported_rms_m=raw['rms_counts']/2**14,
        reported_unit_std=raw['unit_std_counts']/2**11,
        raw=raw, optional_blocks=optional,
        source_kind='primary GNSS receiver enhanced position, not Applanix fused navigation',
        receiver_covariance_established=False)
