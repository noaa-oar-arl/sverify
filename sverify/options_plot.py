import matplotlib.pyplot as plt
import pandas as pd
from svresults3 import DatemOutput
from svcems import SourceSummary
from svcems import CEMScsv

##------------------------------------------------------##
#vmet is a MetObs object.
#vmetdf is the dataframe associated with that.
#vmetdf = pd.DataFrame()

def time_series(options, d1, d2, vmet,
                      logfile):
   with open(logfile, 'a') as fid:
     fid.write('Running options.datem\n')
   sss = SourceSummary(fname = options.tag + '.source_summary.csv')
   orislist = sss.check_oris(10)
   svr = DatemOutput(options.tdir, orislist=orislist, daterange=[d1,d2])
   flist = svr.find_files()
   svr.create_df(flist)
   #svr.plotall()
   if not vmet.empty:
       datemdf = svr.get_pivot()
       vmet.add_model(datemdf, verbose=True)
       vmet.plot_ts() 

   tsplot = svTimeSeries()
  
    
   ob1 = PTimeSeries(ts, 
                     plotnum=1,
                     position='left',
                     ylabel='ppb',
                     ylimit=None,
                     color = 'k ',
                     linestyle = '-',
                     which='both')


    tsplot.add_time_series(ob1)
