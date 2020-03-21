#import svhy
import svhy
#from svhy import create_controls
#from svhy import create_vmix_controls
#from svhy import RunScript
#from svhy import VmixScript
#from svhy import DatemScript
from svcems import SourceSummary
from svens import create_ensemble_controls

def options_run_main(options, d1,d2, source_chunks, tcmrun):
    #if 'ENS' in options.metfmt:
    #    options_deterministic(options, d1, d2, source_chunks, tcmrun)
    #else:
    if 'ENS' in options.metfmt:
        metfmt = options.metfmt.replace('ENS', '')
        runlist = create_ensemble_controls(options.tdir, options.hdir,  d1, d2, source_chunks, metfmt,
                    units = options.cunits, tcm=tcmrun, orislist=None)
    else:
        runlist = options_deterministic(options, d1, d2, source_chunks, tcmrun) 

def options_deterministic(options, d1, d2, source_chunks, tcmrun=False,
                          main=True, vmix=True):
    runlist = []
    #with open(logfile, 'a') as fid:
    #     fid.write('creating CONTROL files\n')

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
       #if not nei_runlist:
       #   print('NO CONTROL files for NEI sources ')
       #   #sys.exit()
       #else:
       #   print('Making script for NEI sources ')
       #   print(len(nei_runlist))
       #   rs = RunScript(options.tag + "_nei.sh", nei_runlist, options.tdir)
       #   print('Making DATEM script for NEI sources ')
       #   rs = svhy.DatemScript(
       #   options.tag + "_nei_datem.sh", nei_runlist, options.tdir, options.cunits, poll=1
       #   )

    if main:
        print('Creating CONTROL files')
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
            print('No  CONTROL files created') 
            print('Check if EMITIMES files have been created')
    #else:
    #    print('Creating batch script for HYSPLIT runs')
    #    rs = RunScript(options.tag + ".sh", runlist, options.tdir)
    #sys.exit()
    if vmix:
        print('Creating CONTROL files for vmixing')
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
