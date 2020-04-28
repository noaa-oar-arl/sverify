import sys
import matplotlib.pyplot as plt
import pandas as pd
from sverify.svhy import read_vmix
from sverify.svobs import SObs
from sverify.svmet import vmixing2metobs
from sverify.svmet import metobs2matched
from sverify.svcems import CEMScsv
##------------------------------------------------------##
#vmet is a MetObs object.
#vmetdf is the dataframe associated with that.
#vmetdf = pd.DataFrame()

def flowchart():
   # functions contained in this file.
   functions = ['get_obs_vmet']
   functions.append('get_vmet')
   functions.append('options_vmix_main')
   functions.append('options_vmix_cems')
   functions.append('options_vmix_met')

   # classes contained in this file.
   classes = []

   # connections between functions in this file
   edges = [('options_vmis_main','options_vmix_cems')]
   edges.append(('options_vmis_main','options_vmix_cems'))

   # connections with other functions 
   edges2 = ['options_vmix_cems','CEMScsv']
   edges2.append(('options_vmix_main','vmixing2metobs'))
   edges2.append(('options_vmix_main','read_vmix'))
   edges2.append(('options_vmix_main','SObs'))
   edges2.append(('options_vmix_main','NeiSummary'))
   edges2.append(('options_vmix_main','options_vmix_cems'))

   edges2.append(('get_vmet','NeiSummary'))
   edges2.append(('get_vmet','vmixing2metobs'))
   edges2.append(('get_vmet','SObs'))
   edges2.append(('get_vmet','read_vmix'))

   edges2.append(('get_obs_vmet','SObs'))
   edges2.append(('get_obs_vmet','obs2metobs'))
   return functions, classes, edges, edges2

def get_obs_vmet(options, d1, d2, area, source_chunks,
                      logfile):
   from sverify.svmet import obs2metobs
   obs = SObs([d1, d2], area, tdir=options.vdir)
   vmet = obs2metobs(obs.obs, met=False)
   return vmet


def get_vmet(options, d1, d2, area, source_chunks,
                      logfile):
   from sverify.nei import NeiSummary
   print('GET VMET')
   # get vmixing data.
   df = read_vmix(options.vdir, d1, d2, source_chunks, sid=None)
   #vmet = vmixing2metobs(df,obs.obs)
   if not df.empty:
      # start getting obs data to compare with.
      obs = SObs([d1, d2], area, tdir=options.tdir)
      obs.find(tdir=options.tdir, test=options.runtest, units=options.cunits)
      # outputs a MetObs object. 
      vmet = vmixing2metobs(df,obs.obs)
   else:
      print('No vmixing data available')
      #sys.exit()
      vmet = vmixing2metobs(df, pd.DataFrame())
   return vmet


def options_vmix_main(options, d1, d2, area, source_chunks,
                      logfile):

   """
   d1 : datetime.datetime object
   d2 : datetime.datetime object
    
   """
   print('OPTIONS VMIX MAIN')
   with open(logfile, 'a') as fid:
     fid.write('Running vmix=1 options\n')
   from sverify.nei import NeiSummary

   df = read_vmix(options.vdir, d1, d2, source_chunks, sid=None)
   #vmet = vmixing2metobs(df,obs.obs)
   if not df.empty:
      # start getting obs data to compare with.
      obs = SObs([d1, d2], area, tdir=options.vdir)
      obs.find(tdir=options.vdir, test=options.runtest, units=options.cunits)
      # outputs a MetObs object. 
      vmet = vmixing2metobs(df,obs.obs)
      vmet.set_geoname(options.tag + '.geometry.csv')
      sites = vmet.get_sites()
      pstr=''
      for sss in sites:
           pstr += str(sss) + ' ' 
      print('Plotting met data for sites ' + pstr)
      quiet=True
      if options.quiet < 2:
          quiet=False
      #vmet.plot_ts(quiet=quiet, save=True) 
      vmet.nowarning_plothexbin(quiet=quiet, save=True) 
      if options.neiconfig:
          nei = NeiSummary()
          nei.load(options.tdir + 'neifiles/' + options.neiconfig)
          vmet.add_nei_data(nei.df)

      cemstest, cemsdf = options_vmix_cems(options.tag)
      if cemstest: 
         vmet.add_cems(cemsdf)
         #vmet.conditionalA()         
      #sys.exit()
      vmet.conditional(quiet=quiet, save=True, varlist=['SO2']) 
      vmet.conditionalB(quiet=quiet, save=True) 
      vmet.to_csv(options.vdir, csvfile = options.tag + '.vmixing.'  + '.csv')
      #vmetdf = vmet.df
   else:
      print('No vmixing data available')
      vmet = vmixing2metobs(df, pd.DataFrame())
   return vmet

def options_vmix_cems(tag):
    print('OPTIONS VMIX CEMS')
    cems = CEMScsv()
    cems.read_csv(tag + '.cems.csv')
    #sss = SourceSummary(fname = tag + '.source_summary.csv')
    #orislist = sss.check_oris(10)
    sdf = cems.get_cems()
    if not sdf.empty: rval = True
    else: rval = False
    return rval, sdf 

def options_vmix_met(options, vmet, meto, logfile):
   print('OPTIONS VMIX MET')
   # compare vmixing output with met data from AQS. 
   if not vmet.df.empty and not meto.df.empty:
       with open(logfile, 'a') as fid:
             fid.write('comparing met and vmixing data\n')
       mdlist = metobs2matched(vmet.df, meto.df)
       fignum=10
       for md in mdlist:
           #print('MATCHED DATA CHECK')
           #print(md.stn)
           #print(md.obsra[0:10])
           #print('---------------------')
           
           fig = plt.figure(fignum)
           ax = fig.add_subplot(1,1,1)
           md.plotscatter(ax)
           save_str = str(md.stn[0]) + '_' + str(md.stn[1])
           plt.title(save_str)
           plt.savefig(save_str + '.jpg')
           fignum+=1
           if str(md.stn[1])=='WDIR' or str(md.stn[1])=='WS':
              fig = plt.figure(fignum)
              ax = fig.add_subplot(1,1,1)
              wdir=False
              if md.stn[1] == 'WDIR': wdir=True
              md.plotdiff(ax, wdir=wdir)
              save_str = 'TS_' + str(md.stn[0]) + '_' + str(md.stn[1])
              plt.savefig(save_str + '.jpg')
              fignum+=1
       if options.quiet < 2: 
          plt.show()
       else:
          plt.close()
