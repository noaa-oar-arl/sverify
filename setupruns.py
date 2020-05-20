import sys
import os
import logging
from optparse import OptionParser
import sverify
from sverify import options_process
#from sverify import options_vmix
#from sverify import options_obs  
from sverify import svconfig
from sverify.options_run import options_run_main

# import cartopy.crs as ccrs
# import cartopy.feature as cfeature

"""
Functions
-----------
INPUTS: 
inputs are detailed in the attributes of the ConfigFile class.

STEPS

"""
logger = logging.getLogger(__name__)


def main():
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
    parser.add_option(
    "--defaults",
    action="store_true",
    dest="defaults",
    default=False,
    help="Write CONTROL.0 and SETUP.0 files in top level directory",
    )

    parser.add_option(
    "--vmix",
    action="store_true",
    dest="vmix",
    default=False,
    help="Write CONTROL and SETUP files for vmixing, \
          Locations are where there are AQS stations. \
          CONTROL.suffix, suffix is V+AQS station id.",
    )

    parser.add_option(
    "--nei",
    action="store_true",
    dest="nei",
    default=False,
    help="Write CONTROL and SETUP files for sources found in \
          the CONFIG.nei file.",
    )

    parser.add_option(
    "--debug",
    action="store_true",
    dest="debug",
    default=False,
    help="Print messages for debugging",
    )

    parser.add_option(
    "--verbose",
    action="store_true",
    dest="verbose",
    default=False,
    help="Print messages" 
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
    source_chunks = svp.source_chunks
    datem_chunks = svp.datem_chunks
    tcmrun = svp.tcmrun
    run_duration = svp.run_duration
    rfignum = 1

    # create an instance of the MetObs class.
    # vmet = MetObs()

    ##------------------------------------------------------##
    # Run a test
    ##------------------------------------------------------##
    runtest=False
    if runtest:
        print('No test available')
        rval = 1
    ##------------------------------------------------------##
    # Create default CONTROL.0 and SETUP.0 files
    ##------------------------------------------------------##
    elif opts.defaults and not svp.ensemble:
        #with open(logfile, 'a') as fid:
        #    fid.write('Running  defaults\n')
        from sverify.svhy import default_setup
        from sverify.svhy import default_control
        logger.info("writing CONTROL.0 and SETUP.0")
        # if units='ppb' then ichem=6 is set to output mixing ratios.
        default_setup("SETUP.0", options.tdir, units=options.cunits)
        default_control("CONTROL.0", options.tdir, run_duration, d1, area=area)
        # if ensemble then copy CONTROL.0 and SETUP.0 to ensemble directories
    elif opts.defaults and svp.ensemble:
        from sverify.svens import ensemble_defaults
        ensemble_defaults(options.tdir)

    ##------------------------------------------------------##
    # Create CONTROL and SETUP files in subdirectories.
    ##------------------------------------------------------##
    # FILES created
    # CONTROL and SETUP and ASCDATA.CFG files in each subdirectory.
    # CONTROL files for vmixing. 
    elif not opts.defaults:
       tcmrun=False
       main = False
       vmix = opts.vmix
       neibool = opts.nei
       if not vmix and not neibool: main = True
       #logger.info('writing control files')
       options_run_main(options, d1, d2, source_chunks, 
                        tcmrun, main, vmix, neibool)
    return 1


if __name__ == "__main__":
   if sys.argv.count("--debug") > 0:
       log_level = logging.DEBUG
   elif sys.argv.count("--verbose") > 0:
       log_level = logging.INFO
   else:
       log_level = logging.WARNING
   sverify.run(main, 'setupruns.py', log_level = log_level)
