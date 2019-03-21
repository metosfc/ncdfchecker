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

import argparse
import json
import logging
import re
import sys

import netCDF4

import numpy as np


class LevelFilter(logging.Filter):
    """
    Set up a filter for a logging class. The class is initialised with the
    start and end of logging levels to accept. If the logging level is
    outside the defined range, it is rejected by the related handler and
    not logged.

    The comparison between levels is done on a "greater/less than or equal to"
    basis so the start and end values will be included by the filter.

    """
    def __init__(self, start=logging.DEBUG, end=logging.CRITICAL):
        self.reject_start = start
        self.reject_end = end

    def filter(self, record):
        return (record.levelno >= self.reject_start and
                record.levelno <= self.reject_end)


def initialise_logger(name=sys.argv[0], verbosity=logging.INFO):
    """
    Initialise the logger.
    """
    # Create the logging object and set it's logging level to default.
    # We will rely on the filters to stop DEBUG messages getting to the
    # output.
    logger = logging.getLogger(name)
    logger.setLevel(verbosity)

    formatter = logging.Formatter("[%(levelname)s] - %(message)s")

    # Set up the stdout handler, with filter.
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_filter = LevelFilter(end=logging.WARNING)

    stdout_handler.addFilter(stdout_filter)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    # Set up the stderr handler with filter, much the same as above but
    # different fitler ranges.
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_filter = LevelFilter(start=logging.ERROR)

    stderr_handler.addFilter(stderr_filter)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    return logger


def load_constraints(config_file_path):
    """
    Handle loading in of config file.
    """
    with open(config_file_path) as config_file:
        config_str = config_file.read()
    constraints = json.loads(config_str)
    return constraints


def load_input(input_file_path):
    """
    Handle loading in of file to validate.
    """
    nc_file = netCDF4.Dataset(input_file_path, 'r')
    return nc_file


def match_pattern(pattern, value):
    """
    Helper function to carry out pattern matching
    """
    patt = re.compile(pattern)
    match = patt.match(value)
    return match is not None


def check_globals(product, constraints, skip=["short_name"], strict=False,
                  logger=None):
    """
    Check any global attributes are valid possible entries based on any
    constraints provided. N.B. If a particular product has a specific value
    specified in its config e.g. frequency must be "day", then the match for
    that value is checked in the simple_variable_checks routine.
    """
    errcount = 0
    warncount = 0

    if not logger:
        logger = initialise_logger(verbosity=logging.CRITICAL)

    for key in constraints['required_global_attributes']:
        if key not in skip:
            # Check if a known required_global_attribute is present in a
            # product and determine if there are any constraints on it.
            # N.B. Constraints on globals are top-level entries in the config
            # file, hence the check for both.
            if key in product.ncattrs() and key in constraints:
                # Checks for when a global is present and has some constraints
                # specified.
                if isinstance(constraints[key], list):
                    # Checking against a list of specified values
                    if product.getncattr(key) in constraints[key]:
                        logger.info("OK - Global %s" % key)
                    else:
                        logger.error("Global %s not in allowed values" % key)
                        errcount += 1
                elif isinstance(constraints[key], dict):
                    # Checking against entries in a dict
                    for conkey in constraints[key]:
                        if conkey == "pattern":
                            if match_pattern(constraints[key]['pattern'],
                                             product.getncattr(key)):
                                logger.info("OK - %s matches pattern" % key)
                            else:
                                logger.error(
                                    "%s does not match required pattern" %
                                    key)
                                errcount += 1
                        else:
                            logger.error(
                                "Check for %s, %s not implemented" %
                                (key, confkey))
                            errcount += 1
                else:
                    logger.warn("Constraint on %s is not defined" % key)
                    warncount += 1
            # Checks for when a required_global_attribute is present but there
            # are no constraints specified
            elif key in product.ncattrs() and key not in constraints:
                logger.info("OK - Global %s" % key)
            # If a required global is not present in the file then an error
            # needs recording
            elif key not in product.ncattrs():
                logger.error("required global %s not defined" % key)
                errcount += 1

    if strict:
        for key in product.ncattrs():
            if key not in constraints['required_global_attributes']:
                errcount += 1
                logger.error('Unrequested global variable %s present' % key)

    return errcount, warncount


def check_stepsize(data, stepsize):
    """
    Helper routine to check that the stepsize in some given data is equal to
    a given value
    """
    steparr = data[1:len(data)] - data[0:len(data)-1]
    return np.all(steparr == stepsize)


def simple_variable_checks(product, constaints, strict=False, logger=None):
    """
    Carry out simple checks based on variables present in product
    """

    errcount = 0
    warncount = 0

    if not logger:
        logger = initialise_logger(verbosity=logging.CRITICAL)

    for variable in product.variables:
        logger.info("Checking %s" % variable)
        # If running in strict mode _FillValue should only be present if used
        if strict:
            if "_FillValue" in product[variable].ncattrs():
                if not np.ma.is_masked(product[variable][:]):
                    errcount += 1
                    logger.error("%s : _FillValue present but unused" %
                                 variable)

        # Catch completely unknown variables - those not in either the
        # constraints or list of allowed dimensions
        if variable not in constraints:
            # If variable is an allowed dimension then no error to raise.
            if 'allowed_dimensions' in constraints and \
                    variable in constraints['allowed_dimensions']:
                continue
            if strict:
                logger.error("Unknown variable %s" % variable)
                errcount += 1
            else:
                logger.warn("Unknown Variable %s" % variable)
                warncount += 1
        elif variable in constraints:
            for key in constraints[variable]:
                if key == "required_values":
                    if np.all(product[variable][:] ==
                              constraints[variable][key]):
                        logger.info("OK: %s : %s" % (variable, key))
                    else:
                        logger.error("%s : %s" % (variable, key))
                        errcount += 1
                elif key == "required_range":
                    datrange = constraints[variable][key]
                    if np.any(product[variable][:] < datrange[0]) or \
                            np.any(product[variable][:] > datrange[1]):
                        logger.error("%s : %s - outside allowed range" %
                                     (variable, key))
                        errcount += 1
                    else:
                        logger.info("OK: %s : %s" % (variable, key))
                elif key == "required_min_max":
                    minmax = constraints[variable][key]
                    if np.amin(product[variable][:]) != minmax[0] or \
                            np.amax(product[variable][:]) != minmax[1]:
                        logger.error(
                            ("%s : %s - min_max values don't align with "
                             "specification") %
                            (variable, key))
                        errcount += 1
                    else:
                        logger.info("OK: %s : %s" % (variable, key))
                elif key == "required_attributes":
                    for attname in constraints[variable][key]:
                        if attname not in product[variable].ncattrs():
                            logger.error(
                                "%s : required attribute missing : %s"
                                % (variable, attname))
                            errcount += 1
                        else:
                            logger.info("OK: %s attribute present for %s" %
                                        (attname, variable))
                elif key == "required_intervals":
                    # required intervals may be specified for a related
                    # variables in dictionary format or directly on the
                    # variable itself
                    if isinstance(constraints[variable][key], dict):
                        for intervalkey in constraints[variable][key]:
                            if intervalkey in product.variables:
                                arr = product[intervalkey][:]
                                step = constraints[variable][key][intervalkey]
                                if not check_stepsize(arr, step):
                                    logger.error(
                                        "%s: %s not matched" % (variable, key))
                                    errcount += 1
                                else:
                                    logger.info("OK: %s : %s - %s" %
                                                (variable, key, intervalkey))
                            else:
                                logger.error("%s not in file" % intervalkey)
                    else:
                        arr = product[variable][:]
                        step = constraints[variable][key]
                        if not check_stepsize(arr, step):
                            logger.error(
                                "%s: %s not matched" % (variable, key))
                            errcount += 1
                        else:
                            logger.info("OK: %s : %s" % (variable, key))
                elif key.startswith("required"):
                    logger.error("required check %s Not implemented" % key)
                elif key == "bounds":
                    # Check for presence of expected bounds
                    # - any checking of bounds themselves is done as if it were
                    #   a normal variable
                    for bound in constraints[variable][key]:
                        if bound not in product.variables:
                            logger.error("%s not found" % bound)
                            errcount += 1
                        else:
                            logger.info("OK: %s : %s" % (variable, bound))
                elif key == "cell_methods":
                    # Cell methods can be a pattern so just match outright
                    if match_pattern(constraints[variable][key],
                                     product[variable].getncattr(key)):
                        logger.info("OK: %s : %s" % (variable, key))
                    else:
                        logger.error("%s : %s mismatch" % (variable, key))
                        errcount += 1
                elif key == "dimensions":
                    if list(product[variable].dimensions) != \
                            constraints[variable][key]:
                        logger.error(
                            "Dimensions mismatch got: %s should have: %s" %
                            (str(list(product[variable].dimensions)),
                             str(constraints[variable][key])))
                        errcount += 1
                    else:
                        logger.info("OK: %s : %s" % (variable, key))
                elif "required_global_attributes" in constraints and \
                        key in constraints['required_global_attributes']:
                    # Checking global attribute values are correct for this
                    # variable if explicitly specified e.g. frequency is the
                    # expected value of "day" rather than just a valid possible
                    # entry as specified in the global details.
                    if key in product.ncattrs():
                        if product.getncattr(key) == \
                                constraints[variable][key]:
                            logger.info("OK: %s : %s" % (variable, key))
                        else:
                            logger.error("%s:%s mismatch" % (variable, key))
                            errcount += 1
                    else:
                        logger.error("%s:%s global missing" % (variable, key))
                        errcount += 1
                else:
                    if key in product[variable].ncattrs():
                        if product[variable].getncattr(key) != \
                                constraints[variable][key]:
                            logger.error(
                                "Mismatch for %s %s" % (variable, key))
                            errcount += 1
                        else:
                            logger.info("OK: %s : %s" % (variable, key))
                    else:
                        logger.error("%s : %s missing" % (variable, key))
                        errcount += 1

    return errcount, warncount


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',
                        help=('Path to file input netCDF file to be '
                              'validated.'))
    parser.add_argument('config_path',
                        help=('Path to json config file containing details to '
                              'validate input against.'))
    parser.add_argument('--quiet', '-q', action="store_const",
                        const=logging.WARN, default=logging.INFO,
                        help="Only display error messages"
                        )
    parser.add_argument('--strict', action="store_true",
                        help="If an unknown variable is encountered or fill "
                        "values specified but not used then it should be "
                        "considered an error.")
    args = parser.parse_args()

    logger = initialise_logger(verbosity=args.quiet)

    try:
        product = load_input(args.input_file)
    except IOError as err:
        logger.critical("Unable to load: %s" % args.input_file)
        sys.exit(1)

    try:
        constraints = load_constraints(args.config_path)
    except IOError as err:
        logger.critical("Unable to load: %s" % args.config_path)
        sys.exit(1)

    # Keep a running total of number of errors found
    errcount = 0
    warncount = 0

    # Global variable checks
    if "required_global_attributes" in constraints:
        logger.info("Found some global attributes")
        errs, warns = check_globals(product, constraints, strict=args.strict,
                                    logger=logger)
        errcount += errs
        warncount += warns

    # Variable Checks
    errs, warns = simple_variable_checks(product, constraints, args.strict,
                                         logger=logger)
    errcount += errs
    warncount += warns

    if errcount > 0:
        logger.critical("%s errors found" % errcount)
    if warncount > 0:
        logger.warn("%s warnings raised" % warncount)

    if errcount > 0:
        sys.exit(1)
