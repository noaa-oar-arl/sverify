from optparse import OptionParser
import datetime
import sys
import pandas as pd
import os
from sverify import options_process
from sverify import svconfig

# import cartopy.crs as ccrs
# import cartopy.feature as cfeature

"""
Functions
-----------

INPUTS: 
inputs are detailed in the attributes of the ConfigFile class.

STEPS
A. Preliminary.
1. Find Emission sources.
2. Find measurement stations in area
3. Produce map of sources and measurements.
4. Create plots of emissions vs. time
5. Create plots of measurements vs. time
-----------------------------------------------
7 Main parts currently.

options.defaults - 
   import svhy
   create CONTROL.0 and SETUP.0 files

options.results -
   import svresults2
   svcems
   Uses the SourceSummary file.
   read dataA files in subdirectories
   write datem files
   plot obs and measurements

options.vmix -
   svhy
   svobs
   svmet

options.cems
   svcems

options.obs
   svobs
   svmet
   svish

options.create_runs
   svhy

options.write_scripts
   svhy

"""


parser = OptionParser()
# parser.add_option(
#    "-a", type="string", dest="state", default="ND", help="two letter state code (ND)"
# )
parser.add_option(
    "-i",
    type="string",
    dest="configfile",
    default="CONFIG.S",
    help="Name of configuration file",
)
parser.add_option(
    "-p",
    action="store_true",
    dest="print_help",
    default=False,
    help="Print help for configuration file",
)

(opts, args) = parser.parse_args()

options = svconfig.ConfigFile(opts.configfile)
if opts.print_help:
    print("-------------------------------------------------------------")
    print("Configuration file options (key words are not case sensitive)")
    print("-------------------------------------------------------------")
    print(options.print_help(order=options.lorder))
    sys.exit()

#options = svconfig.ConfigFile(opts.configfile)
# options.fileread is a boolean attribute of ConfigFile class.
if not options.fileread:
    print("configuration file " + opts.configfile + " not found.\ngoodbye")
    sys.exit()

svp=options_process.main(options)
d1 = svp.d1
d2 = svp.d2
area = svp.area
#if no dtlist then will plot all dates in the cdump file
datelist=None
##------------------------------------------------------##
##------------------------------------------------------##
# Process some of the options to create new parameters.
##------------------------------------------------------##
##------------------------------------------------------##
level=100
fname='/pub/ECMWF/SO2/stilwell/area3/F2hrrr/y2018/m02/d05/cdump.2103'
temp = conprob.ConProb(level=level)
temp.plot(fname, bounds=area,
           sos=False, oname=options.tag, dtlist=datelist)

