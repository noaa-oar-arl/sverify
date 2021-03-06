from optparse import OptionParser
#import datetime
import sys
#import pandas as pd
#import numpy as np
#import matplotlib.pyplot as plt
#import os
from sverify import options_process
from sverify import svconfig
from sverify.svhy import VmixScript
from sverify.svhy import DatemScript
from sverify.svhy import RunScript
from sverify.svhy import create_nei_runlist
from sverify.svhy import create_runlist

# import cartopy.crs as ccrs
# import cartopy.feature as cfeature

"""
Functions
-----------

INPUTS: 
inputs are detailed in the attributes of the ConfigFile class.

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
    "-c",
    action="store_true",
    dest="check_cdump",
    default=False,
    help="Only write command to run HYSPLIT if the cdump file does not exist.",
)
parser.add_option(
    "-p",
    action="store_true",
    dest="print_help",
    default=False,
    help="Print help for configuration file",
)
parser.add_option(
    "--datem",
    action="store_true",
    dest="datem",
    default=False,
    help="create bash scripts to run datem",
)
parser.add_option(
    "--vmix",
    action="store_true",
    dest="vmix",
    default=False,
    help="create bash scripts to run vmixing",
)
parser.add_option(
    "--run",
    action="store_true",
    dest="run",
    default=False,
    help="create bash scripts to run HYSPLIT",
)
parser.add_option(
    "--nei",
    action="store_true",
    dest="nei",
    default=False,
    help="create bash scripts to run datem or HYSPLIT for the data\
          found in the confignei file",
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

# FILES created
# bash scripts to run c2datem on the results.

if opts.nei:
    from monet.util import nei
    ns = nei.NeiSummary()
    print(options.tdir, options.neiconfig)
    neidf = ns.load(fname = options.tdir + '/neifiles/' + options.neiconfig) 
    #ns.remove_cems(sss.sumdf)
    #ns.print(fname = options.tdir + '/neifiles/CONFIG.NEWNEI')
    neidf = ns.df
    nei_runlist = create_nei_runlist(options.tdir, options.hdir, neidf,d1, d2,
    if opts.run:
        print('Making bash script for NEI HYSPLIT runs ')
        rs = RunScript(options.tag + "_nei.sh", nei_runlist, options.tdir,
                        check=check_cdump)
    if opts.datem:
        print('Making DATEM script for NEI sources ')
        rs = DatemScript(
              options.tag + "_nei_datem.sh", nei_runlist, options.tdir, options.cunits, poll=1
              )

if opts.vmix:
    print('writing vmix script')
    rs = VmixScript(options.tag + '.vmix.sh', runlist, options.tdir)

if opts.run and not opts.nei:
    runlist = create_runlist(options.tdir, options.hdir, d1, d2, source_chunks)
    print('writing hysplit run script')
    rs = RunScript(options.tag + ".sh", runlist, options.tdir, check=check_cdump)

if opts.datem and not opts.nei:
    runlist = create_runlist(options.tdir, options.hdir, d1, d2, source_chunks)
    print('writing datem scripts')
    rs = DatemScript(
        "p1datem_" + options.tag + ".sh", runlist, options.tdir, options.cunits, poll=1
    )
    rs = DatemScript(
        "p2datem_" + options.tag + ".sh", runlist, options.tdir, options.cunits, poll=2
    )
    rs = DatemScript(
        "p3datem_" + options.tag + ".sh", runlist, options.tdir, options.cunits, poll=3
    )

