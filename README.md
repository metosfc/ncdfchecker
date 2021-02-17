#ncdfchecker.py

ncdfchecker.py is a config driven utility that will allow you to check that a
NetCDF4 file is compliant with a standard specified in a particular config, as
provided in a json file.

usage: ncdfchecker.py [-h] [--quiet] [--strict] [--initdate INITDATE] [--runlength RUNLENGTH] input_file config_path

positional arguments:
  input_file   Path to file input netCDF file to be validated.
  config_path  Path to json config file containing details to validate input
               against.

optional arguments:
  -h, --help   show this help message and exit
  --quiet, -q  Only display error messages
  --strict     If an unknown variable is encountered or fill values specified
               but not used then it should be considered an error.
  --initdate   Model initialisation date
  --runlength  Model run length in days

