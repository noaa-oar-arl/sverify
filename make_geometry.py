import sys
import os
import logging
from optparse import OptionParser
from sverify import options_process
from sverify import options_obs
from sverify import svconfig
import sverify

# import cartopy.crs as ccrs
# import cartopy.feature as cfeature

"""
SCRIPT to obtain CEMS and AQS data
-----------

INPUTS: 
inputs are detailed in the attributes of the ConfigFile class.

-----------------------------------------------

options.cems
   svcems

options.obs
   svobs
   svmet
   svish


"""

logger = logging.getLogger(__name__)

def main():
    parser = OptionParser()

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
    parser.add_option(
    "--debug",
    action="store_true",
    dest="debug",
    default=False,
    help="Print messages for debugging",
    )

    parser.add_option(
    "--quiet",
    action="store_false",
    dest="verbose",
    default=True,
    help="Don't print  messages" 
    )

    (opts, args) = parser.parse_args()

    logger.info('Creates file with distance and direction from')
    logger.info('AQS measurement sites to CEMS and NEI sources.')
    options = svconfig.ConfigFile(opts.configfile)
    if opts.print_help:
        print("-------------------------------------------------------------")
        print("Configuration file options (key words are not case sensitive)")
        print("-------------------------------------------------------------")
        print(options.print_help(order=options.lorder))
        sys.exit()



    # options = svconfig.ConfigFile(opts.configfile)
    # options.fileread is a boolean attribute of ConfigFile class.
    if not options.fileread:
        print("configuration file " + opts.configfile + " not found.\ngoodbye")
        sys.exit()

    ##------------------------------------------------------##
    ##------------------------------------------------------##
    # Process some of the options to create new parameters.
    ##------------------------------------------------------##
    ##------------------------------------------------------##

    svp = options_process.main(options)
    # TO DO - may pass svp rather than individual attributes to functions.
    d1 = svp.d1
    d2 = svp.d2
    area = svp.area
    #logfile = svp.logfile
    logfile = "None"
    source_chunks = svp.source_chunks
    datem_chunks = svp.datem_chunks
    tcmrun = svp.tcmrun
    run_duration = svp.run_duration
    rfignum = 1
    options_obs.options_geometry(options,d1,d2,area)



if __name__ == "__main__":
   if sys.argv.count("--debug") > 0:
       log_level = logging.DEBUG
   elif sys.argv.count("--quiet") == 0:
       log_level = logging.INFO
   else:
       log_level = logging.WARNING
   sverify.run(main, 'make_geometry.py', log_level = log_level)



