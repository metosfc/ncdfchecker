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
import os
import json
import unittest
import tempfile
import time
import numpy
import netCDF4

from ncdfchecker import *

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


if __name__ == '__main__':
    unittest.main()
