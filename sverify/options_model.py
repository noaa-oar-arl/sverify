from os import path
import sys
import matplotlib.pyplot as plt
import pandas as pd
from sverify.svresults3 import DatemOutput
from sverify.svcems import SourceSummary
from sverify.svcems import CEMScsv
from sverify.svens import create_member_list_srefA
##------------------------------------------------------##
#vmet is a MetObs object.
#vmetdf is the dataframe associated with that.
#vmetdf = pd.DataFrame()

# Step1: vmet needs to already exist.

# Step2: create DatemOuptut object.  

# Step3: add this object to the svmet object.


def options_model_main(options, d1, d2, vmet,
                      logfile, model_list=['sref']):

    print('IN OPTIONS MODEL MAIN', model_list)
    #vmet.plot_all_winds()
    #sys.exit()
    #if options.model_list == ['sref']:
    #    model_list = create_member_list_srefA()
    #elif not model_list:
    #    model_list = get_model_list(5)
    print(options.tag + '.source_summary.csv')
    sss = SourceSummary(fname = options.tag + '.source_summary.csv')

    orislist = sss.check_oris(10)
    #orislist=[2103]
    for model in model_list:
        print(model)
        tdir = path.join(options.tdir + model)
        print('TDIR', tdir)
        # this adds the model data into a dictionary in vmet.
        vmet = options_model_sub(vmet, tdir, orislist, [d1,d2], model)
    # used for plotting the time series.
    #if options.time_series:
    #    options_model_ts(options, d1, d2, vmet, logfile, model_list=model_list)
    #if options.prob_plots:
    #    options_model_prob(options, d1, d2, vmet, logfile, model_list=model_list)
    return vmet


def options_model_ts(options, d1, d2, vmet, logfile, model_list=None):
    print('MODEL TS')
    #model_list  = get_model_list(1)
    #model_list = ['F2hrrr', 'B4nam12', 'B4wrf','B17nam12', 'Bnam12']
    #model_list=['F2hrrr'] 
    #model_list=['B4wrf'] 
    levlist = [[1,2]]
    levlist = [[1]]
    #levlist = [[4,5]]
    sss = SourceSummary(fname = options.tag + '.source_summary.csv')
    orislist = sss.check_oris(10)
    for model in model_list:
        tdir = path.join(options.tdir + model)
        print('TDIR', tdir)
        options_model_sub(vmet, tdir, orislist, [d1,d2], model)
    #vmet.plot_ts(levlist=levlist) 
    #vmet.plot_autocorr(levlist=levlist) 
    #vmet.plot_spag(levlist=levlist) 
    #vmet.plot_model_hexbin(levlist=levlist, tag=model_list[0]) 
    #vmet.plot_cdf(levlist=levlist) 
    #plt.show()

def get_model_list(number):
    model_list = ['']
    if number == 1: 
        model_list = ['B4nam12', 'B17nam12','Bnam12','F2hrrr','B4wrf']
    elif number == 2: 
        # uses Beljaar holstead for the low plume rise nam
        model_list = ['B17nam12', 'B4nam12','Enam12','F2hrrr','B4wrf']
    else:
        model_list = ['']
    return model_list


def options_model_prob(options, d1, d2, vmet,
                      logfile, model_list=None):
   """
   code for 
   """
   #levlist = [[4,5]]
   levlist = [[1]]
   with open(logfile, 'a') as fid:
     fid.write('Running options.datem\n')
   sss = SourceSummary(fname = options.tag + '.source_summary.csv')
   orislist = sss.check_oris(10)
   for model in model_list:
       tdir = path.join(options.tdir + model)
       options_model_sub(vmet, tdir, orislist, [d1,d2], model)
   #vmet.plot_ts(levlist=levlist) 
   vmet.plot_prob(levlist=levlist) 
   plt.show()

def options_model_sub(vmet, tdir, orislist, daterange, name):
   """
   Add model objects to the vmet class.
   INPUTS
   vmet : MetObs object
   tdir : string. Directory where datem output is.
   orislist : list of ints
   daterange :
   name : name to write file to.
   OUTPUTS
   vmet
   """

   print('ADDING model ', name)
   svr = DatemOutput(tdir, orislist=orislist, daterange=daterange)
   flist = svr.find_files()
   svr.create_df(flist)
   svr.writedatemall(name + '.datem.txt')
   #svr.plotall()
   if not vmet.isempty():
       #datemdf = svr.get_pivot()
       vmet.add_model_object(name=name, model=svr)
       #vmet.add_model_all(datemdf)
       #vmet.conditional_model(varlist=['SO2', 'model'])
       #vmet.add_model(datemdf, verbose=True)
       #vmet.plot_ts() 
       #plt.show() 
   else:
       print('VMET IS EMPTY')
   return vmet

