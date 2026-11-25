# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
from scipy.io import netcdf_file

from lll.ilvis0_ncar_rf04 import inspect_recording, sampled_rotation


def fixture(path, *, flight=b'rf04'):
    with netcdf_file(path, 'w') as data:
        data.Platform = b'N677F'
        data.ProjectName = b'ICEBRIDGE'
        data.FlightNumber = flight
        data.FlightDate = b'10/12/2011'
        data.createDimension('Time', 5)
        clock = data.createVariable('Time', 'i', ('Time',))
        clock.units = b'seconds since 2011-10-12 12:05:39 +0000'
        clock[:] = [0, 1, 2, 4, 5]
        for name, units, values in (
            ('ROLL', b'degree', [0, 0, 0, 0, -32767]),
            ('PITCH', b'degree', [0, 0, 0, 0, 0]),
            ('THDG', b'degree_T', [359, 359, 1, 30, 30]),
            ('GGLAT', b'degree_N', [-72]*5),
            ('GGLON', b'degree_E', [-70]*5),
            ('GGALT', b'm', [5000]*5),
            ('GGNSAT', b'number', [10, 10, 0, 11, 11]),
            ('GGQUAL', b'none', [5, 5, 0, 5, 5]),
            ('GGSTATUS', b'none', [1, 1, 0, 1, 1]),
            ('GGVNS', b'm/s', [10, 20, 30, 40, -32767]),
            ('GGVEW', b'm/s', [-5]*5),
            ('PSXC', b'hPa', [500]*5),
            ('PSFC', b'hPa', [500]*5),
            ('PS_A', b'hPa', [501, 501, -32767, 501, 501]),
            ('ATX', b'deg_C', [-30]*5),
        ):
            variable = data.createVariable(name, 'f', ('Time',))
            variable.units = units
            variable._FillValue = -32767.
            variable[:] = values
            if name in ('PITCH', 'ROLL', 'THDG'):
                variable.TimeLag = -80
                variable.TimeLagUnits = b'milliseconds'
            if name == 'PSXC':
                variable.Dependencies = b'1 PSFC'


def test_rf04_intake_preserves_utc_gaps_fill_values_and_lag_metadata(tmp_path):
    path = tmp_path/'rf04.nc'
    fixture(path)
    result = inspect_recording(path)
    assert result['matching_seconds'] == 4
    assert result['independent_peak_rate_upper_bound_established'] is False
    assert result['attitude_epochs'] == 3
    assert result['one_second_attitude_pairs'] == 1
    assert result['maximum_endpoint_rate_deg_s'] == pytest.approx(2.)
    assert result['variables']['PITCH']['TimeLag'] == -80
    assert result['rows'][-1]['ROLL'] is None
    assert result['rows'][0]['utc'] == '2011-10-12T12:05:40Z'


def test_rf04_intake_refuses_the_other_flight(tmp_path):
    path = tmp_path/'rf01.nc'
    fixture(path, flight=b'rf01')
    with pytest.raises(ValueError, match='RF04'):
        inspect_recording(path)


def test_rf04_intake_retains_distinct_pressure_channels_and_receiver_status(tmp_path):
    path = tmp_path/'rf04.nc'
    fixture(path)
    result = inspect_recording(path)
    first, second = result['rows'][:2]
    assert first['PSXC'] == first['PSFC'] == 500
    assert result['variables']['PSXC']['Dependencies'] == '1 PSFC'
    assert first['PS_A'] == 501
    assert second['PS_A'] is None
    assert first['ATX'] == -30
    assert (second['GGNSAT'], second['GGQUAL'], second['GGSTATUS']) == (0, 0, 0)
    assert result['used_for_earth_model_scoring'] is False


def test_attitude_endpoint_rotation_combines_axes_and_wraps_heading():
    assert sampled_rotation((0, 0, 359), (0, 0, 1)) == pytest.approx(2.)
    assert sampled_rotation((0, 0, 0), (12, 0, 0)) == pytest.approx(12.)
    assert sampled_rotation((0, 0, 0), (90, 90, 0)) == pytest.approx(120.)


def test_rf04_reference_velocity_intake_preserves_old_output_and_signed_valid_samples(tmp_path):
    path = tmp_path/'rf04.nc'
    fixture(path)
    original = inspect_recording(path)
    assert 'GGVNS' not in original['variables']
    report = inspect_recording(path, include_reference_velocity=True)
    assert report['rows'][0]['GGVNS'] == 20.
    assert report['rows'][0]['GGVEW'] == -5.
    assert report['rows'][-1]['GGVNS'] is None
