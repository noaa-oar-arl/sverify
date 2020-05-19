import logging
import sverify.nei as nei
import sverify.svhy as svhy
#from svhy import create_controls
#from svhy import create_vmix_controls
#from svhy import RunScript
#from svhy import VmixScript
#from svhy import DatemScript
from sverify.svcems import SourceSummary
from sverify.svens import create_ensemble_controls

logger = logging.getLogger(__name__)

def options_run_main(options, d1,d2, source_chunks, tcmrun, main, vmix,nei):
    #if 'ENS' in options.metfmt:
    #    options_deterministic(options, d1, d2, source_chunks, tcmrun)
    #else:
    if 'ENS' in options.metfmt:
        logger.info('Ensemble meteorological data detected')
        metfmt = options.metfmt.replace('ENS', '')
        runlist = create_ensemble_controls(options.tdir, options.hdir,  d1, d2, source_chunks, metfmt,
                    units = options.cunits, tcm=tcmrun, orislist=None)
    else:
        runlist = options_deterministic(options, d1, d2, source_chunks, tcmrun,
                                        main, vmix, nei) 


def options_nei(options, d1, d2, source_chunks, tcmrun=False):
   ns = nei.NeiSummary()
   logger.info('writing EIS control and setup files for NEI data')
   sss = SourceSummary(fname = options.tag + '.source_summary.csv')
   
   neidf = ns.load(fname = options.tdir + '/neifiles/' + options.neiconfig) 
   ns.remove_cems(sss.sumdf)
   ns.print(fname = options.tdir + '/neifiles/CONFIG.NEWNEI')
   neidf = ns.df
   nei_runlist = svhy.nei_controls(options.tdir, options.hdir, neidf, d1, d2, source_chunks, options.metfmt,
                units = options.cunits, tcm=tcmrun)

def options_deterministic(options, d1, d2, source_chunks, tcmrun=False,
                          main=True, vmix=True, nei=False):
    runlist = []
    #with open(logfile, 'a') as fid:
    #     fid.write('creating CONTROL files\n')
    if nei:
       options_nei(options,d1,d2,source_chunks,tcmrun)
 
    if main:
        logger.info('Creating CONTROL files for CEMS data')
        runlist = svhy.create_controls(
            options.tdir,
            options.hdir,
            d1,
            d2,
            source_chunks,
            options.metfmt,
            units = options.cunits,
            tcm = tcmrun
        )
        if not runlist: 
            logger.warning('No  CONTROL files created') 
            logger.warning('Check if EMITIMES files have been created')
    #else:
    #    print('Creating batch script for HYSPLIT runs')
    #    rs = RunScript(options.tag + ".sh", runlist, options.tdir)
    #sys.exit()
    if vmix:
        logger.info('Creating CONTROL files for vmixing')
        runlist = svhy.create_vmix_controls(
            options.tdir,
            options.hdir,
                d1,
                d2,
                source_chunks,
                options.metfmt,
            )
        if not runlist: 
                print('No vmixing CONTROL files created. Check if datem.txt files exist')
    return runlist
