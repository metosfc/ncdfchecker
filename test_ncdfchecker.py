#!/usr/bin/env python

# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2018-2019 Met Office.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import copy
import datetime
import os
import json
import unittest
import tempfile
import time
import numpy
import netCDF4
import logging

from ncdfchecker import *

import numpy as np

TEMPDIR = tempfile.mkdtemp()
datapath = os.path.join(TEMPDIR, "test.nc")
jsonpath = os.path.join(TEMPDIR, "test.json")

# Basic set of constraints to test against
test_constraints = {
    "lat": {
        "axis": "Y",
        "dimensions": [
            "lat"
        ],
        "long_name": "latitude",
        "required_attributes": [
            "long_name",
            "standard_name"
        ],
        "required_intervals": 10.0,
        "required_min_max": [
            -90.0,
            90.0
        ],
        "required_range": [
            -90.0,
            90.0
        ],
        "required_values": numpy.arange(-90.0, 100.0, 10.0).tolist(),
        "standard_name": "latitude"
    },
    "lon": {
        "axis": "X",
        "dimensions": [
            "lon"
        ],
        "long_name": "longitude",
        "required_attributes": [
            "long_name",
            "standard_name"
        ],
        "required_intervals": 10.0,
        "required_min_max": [
            0.0,
            360.0
        ],
        "required_range": [
            0.0,
            360.0
        ],
        "required_values": numpy.arange(0.0, 370.0, 10.0).tolist(),
        "standard_name": "longitude"
    },
    "testfield": {
        "cell_methods": "time: point",
        "dimensions": [
            "time",
            "lat",
            "lon"
        ],
        "frequency": "6hr",
        "long_name": "Test Field",
        "required_intervals": {
            "time": 6
        },
        "required_range": [
            0,
            1
        ],
        "modeling_realm": "atmos",
        "standard_name": "test_field",
        "units": "1"
    },
    "required_global_attributes": [
        "title",
        "source",
        "creation_date",
        "frequency",
        "short_name"
    ],
    "creation_date": {
        "pattern": "\\d\\d\\d\\d-\\d\\d-\\d\\d \\d\\d:\\d\\d"
    },
}

monthly_field = {"testfield_monthly": {
    "cell_methods": "leadtime: point",
    "dimensions": [
        "leadtime",
        "lat",
        "lon"
    ],
    "frequency": "mon",
    "long_name": "Monthly Test Field",
    "required_intervals": {
        "leadtime": "mon"
    },
    "required_range": [
        0,
        1
    ],
    "modeling_realm": "ocean",
    "standard_name": "test_field_monthly",
    "units": "1"
    }
}

monthly_test_constraints = copy.deepcopy(test_constraints)

# Substitute the 6-hourly field for the monthly field
monthly_test_constraints.pop('testfield')
monthly_test_constraints.update(monthly_field)


class StubLogger(logging.Logger):
    """
    Override reporting methods of logger
    to make testing easier.
    """

    def __init__(self):
        self.errors = []
        self.infos = []
        self.warns = []

    def error(self, msg):
        self.errors.append(msg)

    def info(self, msg):
        self.infos.append(msg)

    def warn(self, msg):
        self.warns.append(msg)


class TestProductValidator(unittest.TestCase):
    def setUp(self):
        self.create_example_files()
        self.data = load_input(datapath)

    def create_example_files(self):
        """
        Create a basic netcdf file that can be used for testing against and
        dump an example json file for testing reading routine.
        """

        data = netCDF4.Dataset(datapath, 'w', format='NETCDF4')
        lats = numpy.arange(-90.0, 100.0, 10.0)
        lons = numpy.arange(0.0, 370.0, 10.0)

        # Create Dimensions
        data.createDimension('time', None)
        data.createDimension('lat', len(lats))
        data.createDimension('lon', len(lons))

        # variables
        time_var = data.createVariable('time', 'f8', ('time',))
        time_var[:] = numpy.arange(0, 24, 6)
        lat = data.createVariable('lat', 'f4', ('lat',))
        lat[:] = lats
        lon = data.createVariable('lon', 'f4', ('lon',))
        lon[:] = lons
        testfield = \
            data.createVariable('testfield', 'f8', ('time', 'lat', 'lon',))
        for t_val in range(len(time_var)):
            testfield[t_val, :, :] = \
                numpy.random.uniform(size=(len(lat), len(lon)))

        # Metadata
        lat.axis = "Y"
        lat.long_name = "latitude"
        lat.standard_name = "latitude"

        lon.axis = "X"
        lon.long_name = "longitude"
        lon.standard_name = "longitude"

        testfield.cell_methods = "time: point"
        testfield.frequency = "6hr"
        testfield.long_name = "Test Field"
        testfield.modeling_realm = "atmos"
        testfield.standard_name = "test_field"
        testfield.units = "1"

        data.title = "Nosetest exemplar dataset"
        data.source = "Generated by test_product_validator.py"
        data.creation_date = time.strftime("%Y-%m-%d %H:%M")
        data.frequency = "6hr"
        data.short_name = "testfield"

        data.close()

        with open(jsonpath, 'w') as outfile:
            json.dump(test_constraints, outfile, sort_keys=True, indent=4,
                      ensure_ascii=False)
        return

    def tearDown(self):
        """
        Cleanup temporary files
        """
        try:
            os.remove(datapath)
        except OSError:
            pass
        return

    def test_load_constraints_ok(self):
        """
        Test constraint loading from json routine
        """
        cons = load_constraints(jsonpath)
        assert cons == test_constraints

    def test_load_input_ok(self):
        """
        Test routine for loading of input from netcdf file

        A quick check of data title is carried out to make sure correct data is
        returned. Anything more in depth would basically involve writing a
        version of the checker here.
        """
        data = load_input(datapath)
        assert data is not None and data.title == "Nosetest exemplar dataset"

    def test_match_pattern_ok(self):
        """
        Test correct pattern matching
        """
        assert match_pattern(test_constraints['creation_date']['pattern'],
                             self.data.creation_date)

    def test_match_pattern_fail(self):
        """
        Test pattern matching will fail on mismatch
        """
        assert not match_pattern(
            test_constraints['creation_date']['pattern']+"Z",
            self.data.creation_date)

    def test_check_stepsize_ok(self):
        """
        Test check correct stepsize matching
        """
        step = test_constraints['testfield']['required_intervals']['time']
        assert check_stepsize(self.data['time'][:], step)

    def test_check_stepsize_fail(self):
        """
        Test check stepsize fails on mismatch
        """
        step = test_constraints['testfield']['required_intervals']['time'] + 1
        assert not (check_stepsize(self.data['time'][:], step))

    def test_check_irregular_stepsize_fail(self):
        """
        Test check stepsize fails on mismatch when presented with irregular
        steps
        """
        step = 6
        irregset = numpy.array([0, 8, 12, 18])
        assert not check_stepsize(irregset, step)

    def test_check_globals_ok(self):
        """
        Test check_globals matching
        """
        res = check_globals(self.data, test_constraints)
        assert (check_globals(self.data, test_constraints) == (0, 0))

    def test_check_globals_fail(self):
        """
        Test check_globals expected failure
        """
        bad_constraints = copy.deepcopy(test_constraints)
        bad_constraints['creation_date']['pattern'] = "\\d\\d\\d\\dZ"
        assert (check_globals(self.data, bad_constraints) == (1, 0))

    def test_check_globals_strict_ok(self):
        """
        Test check_globals strict mode
        """
        assert (check_globals(
            self.data, test_constraints, strict=True) == (0, 0))

    def test_check_globals_strict_fail(self):
        """
        Test check_globals strict mode expected failure
        """
        unmet_constraints = copy.deepcopy(test_constraints)
        unmet_constraints['required_global_attributes'] = ["title", "source"]
        assert (check_globals(
            self.data, unmet_constraints, strict=True) == (3, 0))

    def test_check_logger_creation(self):
        """
        Check the automatic creation of the logger object. The test will
        fail if the logging object is not correctly defined.
        """
        try:
            check_globals(self.data, test_constraints, logger="a")
        except:
            self.fail("Unexpected exception.")

    def test_simple_variable_checks(self):
        """
        Check simple_variable_checks runs and finds a warning
        because the constraint does not define time tests.
        """
        alogger = StubLogger()
        result = simple_variable_checks(self.data, test_constraints,
                                        logger=alogger)
        assert result == (0, 1)
        assert alogger.errors == []
        assert alogger.infos[0] == 'Checking time'
        assert alogger.warns == ['Unknown Variable time']

    def test_variable_below_range(self):
        """
        Check an error is logged if the data values of a variable
        go below the required range.

        The test data is random from 0-1. There is a chance that
        this test will fail if the random distribution samples only values
        bigger than 0.5.  This is very small (I think
        0.5**(nlon*nlat*ntimes)).
        """

        alogger = StubLogger()
        unmet_constraints = copy.deepcopy(test_constraints)
        unmet_constraints['testfield']['required_range'] = [0.5, 1.5]
        result = simple_variable_checks(self.data, unmet_constraints,
                                        logger=alogger)
        assert result == (1, 1)
        assert (alogger.errors[0] ==
                'testfield : required_range - outside allowed range')


class TestMonthlyProductValidator(unittest.TestCase):
    def setUp(self):
        self.create_example_files()
        self.data = load_input(datapath)
        self.initdate = '19940409'
        self.runlength = 216
        self.expected_stepsize_arr = get_expected_monthly_stepsize(
            self.initdate, self.runlength)

    def tearDown(self):
        """
        Cleanup temporary files
        """
        try:
            os.remove(datapath)
        except OSError:
            pass
        return

    def create_example_files(self):
        """
        Create a basic netcdf file containing a monthly field that can be
        used for testing against and dump an example json file for
        testing reading routine.

        """

        data = netCDF4.Dataset(datapath, 'w', format='NETCDF4')
        lats = numpy.arange(-90.0, 100.0, 10.0)
        lons = numpy.arange(0.0, 370.0, 10.0)

        # Create Dimensions
        data.createDimension('leadtime', None)
        data.createDimension('lat', len(lats))
        data.createDimension('lon', len(lons))

        # variables
        leadtime_var = data.createVariable('leadtime', 'f8', ('leadtime',))
        leadtime_var[:] = numpy.array([900, 1632, 2364, 3108, 3840, 4572])

        lat = data.createVariable('lat', 'f4', ('lat',))
        lat[:] = lats
        lon = data.createVariable('lon', 'f4', ('lon',))
        lon[:] = lons
        testfield_monthly = \
            data.createVariable('testfield_monthly', 'f8',
                                ('leadtime', 'lat', 'lon',))

        for t_val in range(len(leadtime_var)):
            testfield_monthly[t_val, :, :] = \
                numpy.random.uniform(size=(len(lat), len(lon)))

        # Metadata
        lat.axis = "Y"
        lat.long_name = "latitude"
        lat.standard_name = "latitude"

        lon.axis = "X"
        lon.long_name = "longitude"
        lon.standard_name = "longitude"

        testfield_monthly.cell_methods = "leadtime: point"
        testfield_monthly.frequency = "mon"
        testfield_monthly.long_name = "Monthly Test Field"
        testfield_monthly.modeling_realm = "ocean"
        testfield_monthly.standard_name = "test_field_monthly"
        testfield_monthly.units = "1"

        data.title = "Nosetest exemplar dataset"
        data.source = "Generated by test_ncdfchecker.py"
        data.creation_date = time.strftime("%Y-%m-%d %H:%M")
        data.frequency = "mon"
        data.short_name = "testfield_monthly"

        data.close()

        with open(jsonpath, 'w') as outfile:
            json.dump(monthly_test_constraints, outfile, sort_keys=True,
                      indent=4, ensure_ascii=False)
        return

    def test_load_constraints_ok(self):
        """
        Check constraints load ok for monthly meta-data.
        """
        cons = load_constraints(jsonpath)
        assert cons == monthly_test_constraints

    def test_check_stepsize_ok(self):
        """
        Test check correct monthly stepsize matching.
        """
        assert check_stepsize(
            self.data['leadtime'][:], self.expected_stepsize_arr)

    def test_check_stepsize_fail(self):
        """
        Check failure upon monthly stepsize mismatch.
        """
        wrong_stepsizes = numpy.array([732., 732., 732., 744., 732.])

        assert not check_stepsize(
            wrong_stepsizes, self.expected_stepsize_arr)

    def test_check_stepsize_bad_size_fail(self):
        """
        Check failure upon mismatch due to incorrect length of stepsize array.
        """
        assert not check_stepsize(
            self.data['leadtime'][:], self.expected_stepsize_arr[1:])

    def test_simple_variable_checks(self):
        """
        Check simple_variable_checks runs and finds a warning
        because the constraint does not define time tests.
        """
        alogger = StubLogger()
        result = simple_variable_checks(self.data, monthly_test_constraints,
                                        logger=alogger, initdate=self.initdate,
                                        runlength=self.runlength)

        assert result == (0, 1)
        assert alogger.errors == []
        assert alogger.infos[0] == 'Checking leadtime'
        assert alogger.warns == ['Unknown Variable leadtime']


class TestGetMonthMidpoints(unittest.TestCase):

    def test_get_month_midpoints__non_leap(self):
        """
        Check the correct dates corresponding to the middle of the
        month are returned for a non-leap year.
        """
        dates = [datetime.datetime(1993, 1, 1),
                 datetime.datetime(1993, 2, 1),
                 datetime.datetime(1993, 3, 1),
                 datetime.datetime(1993, 4, 1)]

        expected_midpoints = [
            datetime.datetime(1993, 1, 16, 12, 0, 0),
            datetime.datetime(1993, 2, 15, 0, 0, 0),
            datetime.datetime(1993, 3, 16, 12, 0, 0)]

        self.assertEqual(
            expected_midpoints, get_month_midpoints(dates))

    def test_get_month_midpoints__leap(self):
        """
        Check the correct dates corresponding to the middle of the
        month are returned for a leap year.
        """
        dates = [datetime.datetime(2020, 1, 1),
                 datetime.datetime(2020, 2, 1),
                 datetime.datetime(2020, 3, 1),
                 datetime.datetime(2020, 4, 1)]

        expected_midpoints = [
            datetime.datetime(2020, 1, 16, 12, 0, 0),
            datetime.datetime(2020, 2, 15, 12, 0, 0),
            datetime.datetime(2020, 3, 16, 12, 0, 0)]

        self.assertEqual(
            expected_midpoints, get_month_midpoints(dates))

    def test_get_month_midpoints__edge(self):
        """
        Check the correct dates corresponding to the middle of the
        month are returned when crossing into a New Year.
        """
        dates = [datetime.datetime(2020, 11, 1),
                 datetime.datetime(2020, 12, 1),
                 datetime.datetime(2021, 1, 1),
                 datetime.datetime(2021, 2, 1)]

        expected_midpoints = [
            datetime.datetime(2020, 11, 16, 0, 0, 0),
            datetime.datetime(2020, 12, 16, 12, 0, 0),
            datetime.datetime(2021, 1, 16, 12, 0, 0)]

        self.assertEqual(
            expected_midpoints, get_month_midpoints(dates))


class TestGetExpectedMonthlyStepsize(unittest.TestCase):

    def setUp(self):
        self.runlength = 216

    def test_get_expected_monthly_stepsize__month_start(self):
        """
        Check the correct step size array is returned when the
        model initialisation date is at the start of the month.
        """
        initdate = '19950401'
        expected_stepsizes = np.array([
            732., 732., 732., 744., 732., 732.])

        stepsizes = get_expected_monthly_stepsize(
            initdate, self.runlength)

        self.assertTrue(np.array_equal(expected_stepsizes, stepsizes))

    def test_get_expected_monthly_stepsize__mid_month(self):
        """
        Check the correct step size array is returned when the model
        initialisation date is not at the start of the month.

        """
        initdate = '19940409'
        expected_stepsizes = np.array([
            732., 732., 744., 732., 732.])

        stepsizes = get_expected_monthly_stepsize(
            initdate, self.runlength)

        self.assertTrue(np.array_equal(expected_stepsizes, stepsizes))


if __name__ == '__main__':
    unittest.main()
