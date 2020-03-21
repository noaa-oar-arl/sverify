from optparse import OptionParser
import sys
#import pandas as pd
#import numpy as np
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

if opts.print_help:
    print("-------------------------------------------------------------")
    print("Configuration file options (key words are not case sensitive)")
    print("-------------------------------------------------------------")
    print(options.print_help(order=options.lorder))
    sys.exit()

options = svconfig.ConfigFile(opts.configfile)
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
logfile = svp.logfile
source_chunks = svp.source_chunks
datem_chunks = svp.datem_chunks
tcmrun = svp.tcmrun
run_duration = svp.run_duration
rfignum = 1

runlist = []
if options.create_runs:
    from monet.util.svhy import create_controls
    from monet.util.svhy import create_vmix_controls
    from monet.util.svhy import RunScript
    from monet.util.svhy import VmixScript
    from monet.util.svhy import DatemScript
    from monet.util.svcems import SourceSummary
    with open(logfile, 'a') as fid:
         fid.write('creating CONTROL files\n')

    if options.neiconfig:
       from monet.util import nei
       from monet.util.svhy import nei_controls
       ns = nei.NeiSummary()
       print('WRITING EIS CONTROLS')
       sss = SourceSummary(fname = options.tag + '.source_summary.csv')
       
       neidf = ns.load(fname = options.tdir + '/neifiles/' + options.neiconfig) 
       ns.remove_cems(sss.sumdf)
       ns.print(fname = options.tdir + '/neifiles/CONFIG.NEWNEI')
       neidf = ns.df
       nei_runlist = nei_controls(options.tdir, options.hdir, neidf, d1, d2, source_chunks, options.metfmt,
                    units = options.cunits, tcm=tcmrun)
       if not nei_runlist:
          print('NO CONTROL files for NEI sources ')
          #sys.exit()
       else:
          print('Making script for NEI sources ')
          print(len(nei_runlist))
          rs = RunScript(options.tag + "_nei.sh", nei_runlist, options.tdir)
          print('Making DATEM script for NEI sources ')
          rs = DatemScript(
          options.tag + "_nei_datem.sh", nei_runlist, options.tdir, options.cunits, poll=1
          )

    sys.exit()
