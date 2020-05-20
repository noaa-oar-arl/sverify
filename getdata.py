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
        "--aqs",
        action="store_true",
        dest="aqs",
        default=False,
        help="Retrieve AQS data",
    )
    parser.add_option(
        "--cems",
        action="store_true",
        dest="cems",
        default=False,
        help="Retrieve CEMS data",
    )
    parser.add_option(
        "--ish",
        action="store_true",
        dest="ish",
        default=False,
        help="Retrieve ISH data. Not currently working",
    )
    parser.add_option(
        "--datem",
        action="store_true",
        dest="datem",
        default=False,
        help="Write datem files in the subdirectories",
    )
    parser.add_option(
        "--efiles",
        action="store_true",
        dest="efiles",
        default=False,
        help="Write EMIT TIMES files in subdiretories",
    )
    parser.add_option(
        "--nei",
        action="store_true",
        dest="nei",
        default=False,
        help="Retrieve NEI data.",
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
    if not opts.aqs and not opts.cems and not opts.ish and not opts.nei:
        opts.aqs = True
        opts.cems = True

    options = svconfig.ConfigFile(opts.configfile)
    if opts.print_help:
        print("-------------------------------------------------------------")
        print("Configuration file options (key words are not case sensitive)")
        print("-------------------------------------------------------------")
        print(options.print_help(order=options.lorder))
        sys.exit()


    opts.ish = 0
    if opts.ish: options.ish = 1
    else: options.ish = 0

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


    if opts.aqs: options.obs=True

    ##------------------------------------------------------##
    # Run a test
    ##------------------------------------------------------##

    runtest = False
    if runtest:
        options_obs.test(
            options,
            d1,
            d2,
            area,
            source_chunks,
            run_duration,
            logfile,
            rfignum,
            svp.ensemble,
        )
        sys.exit()

    ##------------------------------------------------------##
    ## Get the CEMS data.
    ##------------------------------------------------------##
    if opts.cems:
        # OUTPUTS
        # ef SEmissions object
        # rfignum integer
        # FILES CREATED
        # source_summary.csv
        from sverify import options_cems
        ef, rfignum = options_cems.options_cems_main(
            options, d1, d2, area, source_chunks, 
            svp.ensemble, opts.efiles, verbose=opts.debug
        )
    ##------------------------------------------------------##
    ## Get ISH data
    ##------------------------------------------------------##
    if opts.ish:
       options_obs.get_ish(options,d1,d2,area)

    if opts.nei:
       nei = options_obs.get_nei(options,d1,d2,area)
    ##------------------------------------------------------##
    ## Get observational data
    ##------------------------------------------------------##
    if opts.aqs:
        # OUTPUTS
        # meto - MetObs object with met observations.
        # obs  - SObs object
        # FILES CREATED
        # datem files in subdirectories
        # geometry.csv file
        # PLOTS CREATED
        # time series of observations
        # map with obs, cems, ish
        # 2d distributions of so2 conc and wdir for sites with met data.
        meto, obs = options_obs.options_obs_main(
            options,
            d1,
            d2,
            area,
            source_chunks,
            run_duration,
            rfignum,
            svp.ensemble,
            datem = opts.datem
            
        )



if __name__ == "__main__":
   if sys.argv.count("--debug") > 0:
       log_level = logging.DEBUG
   elif sys.argv.count("--verbose") > 0:
       log_level = logging.INFO
   else:
       log_level = logging.WARNING
   sverify.run(main, 'getdata.py', log_level = log_level)



