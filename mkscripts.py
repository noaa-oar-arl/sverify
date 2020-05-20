from optparse import OptionParser
#import datetime
import sys
import logging
#import pandas as pd
#import numpy as np
#import matplotlib.pyplot as plt
#import os
import sverify
from sverify import svens
from sverify import options_process
from sverify import svconfig
from sverify.svhy import VmixScript
from sverify.svhy import DatemScript
from sverify.svhy import RunScript
from sverify.svhy import create_nei_runlist
from sverify.svhy import create_vmix_controls
from sverify.svhy import create_runlist

"""
Functions
-----------

INPUTS: 
inputs are detailed in the attributes of the ConfigFile class.

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
    parser.add_option(
        "--ens",
        action="store_true",
        dest="ens",
        default=False,
        help="create bash scripts to ensemble. not completely working."
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
    if opts.check_cdump:
       wstr = '-c option set ' + str(opts.check_cdump)
       wstr += 'lines to run HYSPLIT when cdump files exist will be'
       wstr += 'commented out'

    if not opts.check_cdump:
       wstr = '-c option not set ' + str(opts.check_cdump)
       wstr += 'cdump files may be overwritten if script is run'

    logger.warning(wstr)

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
    source_chunks = svp.source_chunks
    datem_chunks = svp.datem_chunks
    tcmrun = svp.tcmrun
    run_duration = svp.run_duration
    rfignum = 1

    # FILES created
    # bash scripts to run c2datem on the results.

    if opts.nei:
        from sverify import nei
        ns = nei.NeiSummary()
        #print(options.tdir, options.neiconfig)
        neidf = ns.load(fname = options.tdir + '/neifiles/' + options.neiconfig) 
        #ns.remove_cems(sss.sumdf)
        #ns.print(fname = options.tdir + '/neifiles/CONFIG.NEWNEI')
        neidf = ns.df
        nei_runlist = create_nei_runlist(options.tdir, options.hdir, neidf,d1, d2,
                                         source_chunks)
        if opts.run:
            fname = options.tag + "nei.sh"
            logger.info('Making bash script for NEI HYSPLIT runs ' + fname)
            rs = RunScript(fname, nei_runlist, options.tdir,
                            check=opts.check_cdump)
        if opts.datem:
            fname = options.tag + "_nei_datem.sh"
            logger.info('Making DATEM script for NEI sources :' + fname)
            rs = DatemScript(
                  fname , nei_runlist, options.tdir, options.cunits, poll=1
                  )

    if opts.vmix and not opts.ens:
        runlist = create_vmix_controls(options.vdir, options.hdir, d1, d2,
                                       source_chunks, metfmt='None', write=False)
        fname = options.tag + '.vmix.sh'
        logger.info('writing script to run vmix ' + fname)
        rs = VmixScript(fname, runlist, options.tdir)
    elif opts.vmix and opts.ens:
        logger.warning('Ensemble option set ')
        logger.info('writing script to run ensemble vmix ')
        runlist = create_ensemble_vmix_controls(options.tdir, options.hdir, d1, d2,
                                       source_chunks, options.metfmt)
        svens.create_ensemble_vmix(options, d1, d2, source_chunks)

    # create ensemble scripts for running.
    if opts.run and not opts.nei and opts.ens:
        logger.warning('Ensemble option set ')
        svens.create_ensemble_scripts(options, d1, d2, source_chunks,
                                       opts.check_cdump)

    if opts.datem and not opts.nei and opts.ens:
        logger.warning('Ensemble option set ')
        svens.create_ensemble_datem_scripts(options, d1, d2, source_chunks)

    if opts.run and not opts.nei and not opts.ens:
        runlist = create_runlist(options.tdir, options.hdir, d1, d2, source_chunks)
        fname = options.tag + ".sh"
        logger.info('writing script to run HYSPLIT for CEMS sources: ' + fname)
        rs = RunScript(fname, runlist, options.tdir, check=opts.check_cdump)


    if opts.datem and not opts.nei and not opts.ens:
        runlist = create_runlist(options.tdir, options.hdir, d1, d2, source_chunks)
        logger.info('writing scripts to create datemfiles for CEMS hysplit runs')
        logger.info('p1datem_' + options.tag + ".sh")
        logger.info('p2datem_' + options.tag + ".sh")
        logger.info('p3datem_' + options.tag + ".sh")
        rs = DatemScript(
            "p1datem_" + options.tag + ".sh", runlist, options.tdir, options.cunits, poll=1
        )
        rs = DatemScript(
            "p2datem_" + options.tag + ".sh", runlist, options.tdir, options.cunits, poll=2
        )
        rs = DatemScript(
            "p3datem_" + options.tag + ".sh", runlist, options.tdir, options.cunits, poll=3
        )



if __name__ == "__main__":
   if sys.argv.count("--debug") > 0:
       log_level = logging.DEBUG
   elif sys.argv.count("--quiet") == 0:
       log_level = logging.INFO
   else:
       log_level = logging.WARNING
   sverify.run(main, 'mkscripts.py', log_level = log_level)




