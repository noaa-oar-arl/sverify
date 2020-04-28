#import datetime
import matplotlib.pyplot as plt
import os
import sys
from optparse import OptionParser
#import pandas as pd
#import numpy as np
import sverify as sv

"""
FUNCTIONS

options_obs_main

create_obs
create_metobs
make_geometry
make_map
make_hexbin

"""
def autocorr(options, d1, d2, area, source_chunks, 
                     run_duration, logfile, rfignum):
    obs = create_obs(options, d1, d2, area, rfignum)
    obs.autocorr()

def create_obs(options, d1, d2, area, rfignum):
    # create the SObs object to get AQS data.    
    obs = sv.svobs.SObs([d1, d2], area, tdir=options.tdir)
    obs.fignum = rfignum
    obs.find(tdir=options.tdir, test=options.runtest, units=options.cunits)
    return obs

def create_metobs(obs, options, met=True):
    #meto = sv.svmet.obs2metobs(obs, met=met)
    meto = sv.svmet.obs2metobs(obs)
    meto.to_csv(options.tdir, csvfile = obs.csvfile)
    meto.set_geoname(options.tag + '.geometry.csv')
    return meto

def make_geometry(options, obsfile, logfile):
    # output geometry.csv file with distances and directons from power plants to aqs sites.
    sumfile = options.tag + ".source_summary.csv"
    cemsfile = options.tag + ".cems.csv"
    if options.neiconfig: 
       neifile = options.tdir + 'neifiles/' + options.neiconfig
       if not os.path.isfile(neifile):
           neifile=None 
    else:
       neifile=None 
    t1 = os.path.isfile(obsfile)
    t2 = os.path.isfile(sumfile)
    t3 = os.path.isfile(cemsfile)
    #t4 = os.path.isfile(neifile)
    #if not t4: neifile=None 
    if t1 and t2 and t3:
        from sverify.svan1 import CemsObs
        from sverify.svan1 import gpd2csv
        cando = CemsObs(obsfile, cemsfile, sumfile, neifile)
        osum, gsum = cando.make_sumdf()
        with open(logfile, 'a') as fid:
             fid.write('Creating geometry.csv file\n')
        gpd2csv(osum, options.tag + ".geometry.csv")
    else:
        with open(logfile, 'a') as fid:
             fid.write('geometry.csv not created\n')
             fid.write('obsfile ' + obsfile + str(t1))
             fid.write('sumfile ' + sumfile + str(t2))
             fid.write('cemsfile ' + cemsfile + str(t3))

def options_obs_main(options, d1, d2, area, source_chunks, 
                     run_duration, logfile, rfignum, svensemble, met=True):
    #INPUTS 
    # options
    # source_chunks
    # run duration
    # d1, d2
    # logfile
    # area
    #OUTPUTS
    # meto - MetObs object with met observations.
    # obs  - SObs object
    # FILES CREATED
    # datem files in subdirectories
    # geometry.csv file
    # PLOTS CREATED
    # time series of observations
    # map with obs, cems, ish 
    # 2d distributions of so2 conc and wdir for sites with met data.

    with open(logfile, 'a') as fid:
        fid.write('Running obs=True options\n')

    # create the SObs object to get AQS data.    
    obs = create_obs(options, d1, d2, area, rfignum)


    # exerperiment with fitting an AR or ARMA model to obs data.
    # then generate artificial time series for reference forecast.
    #obs.try_ar()

    # make the geometry.csv file 
    with open(logfile, 'a') as fid:
        fid.write('Creating geometry.csv file\n')
    make_geometry(options, obs.csvfile, logfile)

    # create the datem files in each subdirectory.
    if svensemble:
        # if ensemble runs create dfiles in each subdirectory.
        sv.svens.create_ens_dfile(obs, d1, source_chunks, run_duration,
                                options.tdir)
    else:
        obs.obs2datem(d1, ochunks=(source_chunks, run_duration), tdir=options.tdir)

    # create a MetObs object which specifically has the met data from the obs.
    meto = create_metobs(obs, options, met=met)
    #meto.clustering_csv(options.tdir)

    # plot histogram of wind speeds at two sites. 
    #meto.plot_all_winds()
    #sys.exit()

    # create map with obs and power plants (if source_summary file available)
    make_map(options, obs, d1, d2, area)
    meto.fignum = obs.fignum+1

    # create 2d distributions of wind direction and so2 measurements.
    if options.neiconfig:
         nei = sv.nei.NeiSummary()
         nei.load(options.tdir + 'neifiles/' + options.neiconfig)
         meto.add_nei_data(nei.df)

    # plot 2d histograms of SO2 measurements and measured wind speeds. 
    make_hexbin(options, meto)
    plt.show()

    # PLOT time series of observations
    print('Plotting obs time series')
    obs.plot(save=True, quiet=options.quiet)
    return meto, obs


#def make_map_nice(options, obs, d1, d2, area):
    
    
def make_map(options, obs, d1, d2, area):
    ################################################################################ 
    # Now create a geographic map.
    txt=True
    fignum = obs.fignum
    if options.quiet == 1:
        plt.close("all")
        fignum = 1
    figmap, axmap, gl = sv.ptools.create_map(fignum)
    figmap.set_size_inches(15,15)
    # put the obs data on the map
    obs.map(axmap, txt=txt)
    print("map fig number  " + str(fignum))
    # put the cems data on the map if the source_summary file exists..
    if os.path.isfile(options.tdir + options.tag + ".source_summary.csv"):
        cemsum = sv.svcems.SourceSummary(options.tdir, options.tag + ".source_summary.csv")
        #if not cemsum.sumdf.empty:
        cemsum.map(axmap, txt=txt)
    # put the ISH sites on the map. 
    if options.ish > 0:
        #with open(logfile, 'a') as fid:
        #     fid.write('running ish options\n')
        print('FINDING ISH DATA')
        ishdata = sv.svish.Mverify([d1, d2], area)
        test = ishdata.from_csv(options.tdir)
        if not test: ishdata.find_obs()
        if not test: ishdata.save(options.tdir)
        ishdata.map(axmap)
        ishdata.print_summary('ISH_SUMMARY.csv')

    # Add NEI data
    if options.neiconfig:
        nei = NeiSummary(options.tdir + 'neifiles/' + options.neiconfig)
    else:
        nei = sv.nei.NeiData(options.ndir)
    nei.load()
    if not options.neiconfig:
        nei.filter(area)
        nei.write_summary(options.tdir, options.tag + '.nei.csv')
    nei.map(axmap)
    plt.sca(axmap)
    plt.savefig(options.tdir + "map.png")
    if options.quiet < 2:
        plt.show()
    else:
       plt.close('all')

def make_hexbin(options, meto):
    # create 2d distributions of so2 conc and wdir for sites with met data.
    plt.close('all')
    sites = meto.get_sites()
    pstr=''
    for sss in sites:
        pstr += str(sss) + ' ' 
    print('Plotting met data for sites ' + pstr)
    if options.quiet < 2:
        meto.nowarning_plothexbin(quiet=False, save=True)
    else:
        meto.nowarning_plothexbin(quiet=True, save=True)
    plt.close('all')
    
