import os
import logging
import matplotlib.pyplot as plt
from sverify.svcems import SEmissions
from sverify.ptools import create_map
from sverify.svens import ensemble_emitimes

#changes
#2021 Jan 29 (amc) write csv file for cems even if emit-times files not created.


#def emit_ens(options, tdir):
#
#    ef.create_emitimes(
#        ef.d1,
#        schunks=source_chunks,
#        tdir=options.tdir,
#        unit=options.byunit,
#        heat=options.heat,
#        emit_area=options.emit_area,
#    )

logger = logging.getLogger(__name__)

def check_apifiles_dir(tdir):
    dname = os.path.join(tdir, 'apifiles')
    if not os.path.isdir(dname):
       logger.warning('Please create the following directory ' + dname)
       wstr = 'Files related to CEMS data will be placed in this directory'
       logger.warning(wstr)
       return False
    else:
       return True

def get_ef(options, d1, d2, area, source_chunks, verbose=False):
    #with open(logfile, 'a') as fid:
    logger.info('Getting CEMS data')
    #print(options.orislist[0])
    if options.orislist[0] != "None":
        alist = options.orislist
        byarea = False
    else:
        alist = area
        byarea = True
    # instantiate object
    ef = SEmissions(
        [d1, d2],
        alist,
        area=byarea,
        tdir=options.tdir,
        spnum=options.spnum,
        tag=options.tag,
        )
     # get emissions data
     # create source_summary.csv file.
    ef.find(verbose=verbose)
    return ef


def options_cems_main(options, d1, d2, area, source_chunks,
                      ensemble=False, efiles=False, verbose=False,
                      create_plots=False):
    # returns ef : SEmissions object
    #         rfit : int
    if not check_apifiles_dir(options.tdir):
       logger.warning('Cannot get CEMS data without apifiles directory')
       return None , None
      

    ef = get_ef(options, d1, d2, area, source_chunks, verbose=verbose)

    rfignum = ef.fignum
    if ensemble and efiles:
        ensemble_emitimes(options, options.metfmt, ef, source_chunks)
    elif efiles: 
        # create emittimes files
        logger.info('Creating emit times files')
        ef.create_emitimes(
            ef.d1,
            schunks=source_chunks,
            tdir=options.tdir,
            unit=options.byunit,
            heat=options.heat,
            emit_area=options.emit_area,
        )
        #return ef, rfignum
    # create plots of emissions
    else:
       ef.write_csv(unit=False)
    if create_plots:
       make_plots(options,ef,rfignum)
    return ef, rfignum

def make_plots(options, ef, rfignum):
    logger.info('Creating plots of emissions')
    if options.quiet == 0:
        ef.nowarning_plot(save=True, quiet=False)
    else:
        ef.nowarning_plot(save=True, quiet=True)

    rfignum = ef.fignum
    # make map
    if options.quiet == 1:
        plt.close("all")
        rfignum = 1
    #if not options.obs:
    #    #logger.debug("map fig number  " + str(rfignum))
    #    mapfig = plt.figure(rfignum)
    #    figmap, axmap, gl = create_map(rfignum)
    #    ef.map(axmap)
    #    plt.savefig(options.tdir + "map.jpg")
    #    if options.quiet < 2:
    #        plt.show()

