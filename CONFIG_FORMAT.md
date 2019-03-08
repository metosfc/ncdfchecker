# Guide to config file format

The ncdfchecker tool is driven by a json file containing details of expected
metadata entries and data values.

An example json file is supplied with the tool as "example.json" this can be
a useful starting point for developing your own driving file and is the easiest
way to learn about the structure of the driving file. It is recommended you
take a look at that first and then use this guide to understand what it is
doing and how you could extend/alter it. It is assumed you are familiar with
json files.

For the most part, the structure of the driving file is freeform using the json
dictionary format to define variables, their entries and the values associated
with them. Loosely:

```
{
  "some_fields_shortname" : {
    "an_entry" : "a_value",
    "another_entry" : "another_value"
  }
}
```

There are, however some restricted names and functionalities you can exploit as
part of your checking.


# Entries starting with "required_"

Entries starting with "required_" must always be present in your ncdf file
where applicable, for example a particular entry may have required values if
present in the file.

Here, the "required_" config entries are listed:

## required_global_attributes

Use this entry to list the set of global attributes you always want to be
present in your netcdf file.

Location: Top level entry in the dictionary
Format: List of names of required attributes
Example: "required_global_attributes" : ["title", "short_name"]

## required_attributes

Use this within the definition of a variable to define its required attributes.
A good example for this would be for use in a dimension's entry to define what
units etc. you want it to have. This helps you ensure that any attributes you
want to be present for your variable are always present.

Location: Within a variable's definition
Format: List of names of required attributes.
Example: "lon" : { "required_attributes" : ["axis", "units"] }

## required_intervals

Use this to specify the expected interval between entries in the data. This can
be used in one of two ways.

1) In the variable itself to define the interval between its entries

This is the simplest usage, for example specifying the number of degrees apart
entries for lattitude may be.

Location: Within a variable's definition
Format: Numeric value of expected difference
Example: "lat" : { "required_intervals" : 10.0 }

2) Using within a variable to specify the expected interval of an associated
variable

Location: Within a variable's definition
Format: Dictionary specifying an associated variable and its required interval
Example: "tas" : { "required_intervals" : { "leadtime" : 6.0 } }

This is useful when you want to have more than one variable within a file that
have the same named associated variables but which may be different for each.

For example you may have be outputting various variables at different timesteps
depending on what that variable is e.g. tas with a leadtime of 6.0 while tauv
has a leadtime of 24.

## required_min_max

Use this to specify the expected minimum and maximum values. This is an
*inclusive* setting so these values must be present. If you want values to fall
within a specific range then use the "required_range" entry instead.

Location: Within a variable's definition
Format: Two item list as [min, max]
Example: "lon" : { "required_min_max": [0.5, 359.5] }

## required_range

Use this to specify the (inclusive) range within which values must be. If you
want the minimum and maximum values to be specific values, then use the
"required_min_max" entry instead.

Location: Within a variable's definition
Format: Two item list as [min, max]
Example: "lon" : { "required_range": [0.0, 360.0] }

## required_values

Use this to specify the values which the varible must have. This is an exact
matching so, when inspecting the variable, even if all values are present the
check will still fail if they are not in the expected order.

Location: Within a variable's definition
Format: List of items in the order you expect them as [item1, item2, ... itemN]
Example: "lon" : { "required_values": [0.0, 180.0, 360.0] }

# Other reserved config items

## pattern

Use this to specify the pattern you expect an entry to follow.

Location: Within an attribute's definition
Format: Python regular expression to match
Example: "creation_date": { "pattern": "\\d\\d\\d\\d-\\d\\d-\\d\\d }

## bounds

Use this to specify any associated bounds variables you want to have present in
your file.

Location: Within a variable's definition
Format: List of associated bounds names
Example: "lon" : ["lon_bnds"]

## cell_methods

Use this to specify an expected cell_method associated with a variable.

N.B. this can be a pattern where multiple possible cell methods are acceptable
for a given entry.

Location: Within a variable's definition
Format: String or pattern for matching agains
Example 1: "lwee" : { "cell_methods": "leadtime: sum" }
Example 2: "rls" : { "cell_methods": "(leadtime: mean$|(leadtime: mean \\(interval: ?[0-9]*?.?[0-9]?[0-9] ?[a-z]*?\\)))" }

## dimensions

Use this to ensure a variable has a particular set of dimensions associated
with it and that they are in an expected order.

Location: Within a variable's definition
Format: List of expected dimenstions
Example: "tas" : { "dimensions" : ["time", "lat", "lon"] }
