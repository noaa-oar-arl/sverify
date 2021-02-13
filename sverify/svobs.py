import os
#import subprocess
import pandas as pd
import numpy as np
import pickle as pickle
import matplotlib
#matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import datetime
import sys
import seaborn as sns
import warnings
import logging

#MONETIO modules
from monetio.obs import aqs as aqs_mod
from monetio.obs import airnow
from monetio.obs import obs_util
from utilhysplit.evaluation import datem

#MONET MODULES in UTILHYSPLIT
from utilhysplit.evaluation import statmain

#MONET MODULES THAT should be SO2 modules
from sverify.svdir import date2dir

logger = logging.getLogger(__name__)

"""
FUNCTIONS

find_obs_files
print_info 
read_csv
generate_obs
get_tseries

CLASSES
SObs

"""
def obs_pivot(df):
    """
    df: pandas dataframe
    Returns:
    wpivot :   dataframe 
    Similar to long_to_wide.
    """
    import pandas as pd
    wpivot = pd.pivot_table(df,
        values=['obs'], index=['time', 'siteid', 'latitude','longitude'],
        columns=['variable','units']).reset_index()
    return wpivot

def rename_columns(df=pd.DataFrame()):
    """
    To be used with output of obs_pivot to make
    more manageable column names.
    """
    newc = []
    for col in self.df.columns.values:
        if isinstance(col, tuple):
           if 'obs' not in col[0]:
               val = col[0].strip()
           else:
               val = col[1].strip()
        else:
           val = col
        newc.append(self.rename_sub(val))
    return newc

def print_info(df, cname):
    """
    creates the info_obs files.
    """
    rdf = df.drop(['obs','time','variable','units','time_local'],axis=1)
    rdf.drop_duplicates(inplace=True)
    rdf.to_csv(cname, float_format="%g")
    #print('HEADER------')
    #print(rdf.columns.values)
    return 1 

def find_obs_files(tdirpath, sdate, edate, ftype='obs', tag=None):
    fnamelist = []
    if tag:
       fname = 'tag' + '.' + ftype +  '.csv'
       if os.path.isfile(os.path.join(tdirpath,fname)):
          fnamelist = [fname]
    else:    
        file_start = None
        file_end = None
        for item in os.listdir(tdirpath):
            #if os.path.isfile(os.path.join(tdirpath,item)):
               if item[0:3] == ftype:
                  
                  temp = item.split('.')
                  try:
                      file_start = datetime.datetime.strptime(temp[0],ftype+"%Y%m%d")
                  except:
                      continue
                  file_end = datetime.datetime.strptime(temp[1],"%Y%m%d")
                  file_end += datetime.timedelta(hours=23)
                  if sdate >=file_start and edate <=file_end:
                     fnamelist.append(item)
    return fnamelist

def read_csv(name, hdrs=[0]):
    # print('in subroutine read_csv', name)
    def to_datetime(d):
        return datetime.datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
    obs = pd.read_csv(name, sep=",", header=hdrs, converters={"time": to_datetime})
    return obs

def generate_obs(siteidlist, obsfile):
    """
    yields a time series of measurements for each site in the siteidlist.
    similar to the generate_ts method in SObs class.
    """
    #obsfile = self.obsfile.replace('info_','')
    str1 = obsfile.split('.')
    dt1 = datetime.datetime.strptime(str1[0], "obs%Y%m%d") 
    dt2 = datetime.datetime.strptime(str1[1], "%Y%m%d") 
    area=''
    obs = SObs([dt1, dt2], area)
    if not os.path.isfile(obsfile):
       logger.warning(obsfile + ' does not exist')
    odf = read_csv(obsfile, hdrs=[0])
    #print('HERE', odf[0:1])
    #print(odf.columns)
    odf = odf[odf["variable"] == "SO2"]
    for sid in siteidlist:
        # gets a time series of observations at sid.
        ts = get_tseries(odf, sid, var='obs', svar='siteid', convert=False) 
        yield ts

def get_tseries(df, siteid, var="obs", svar="siteid", convert=False):
    """
    df : pandas DataFrame
    siteid : integer
    var : str
    svar : str
    Returns 
    series : pandsa time series
    """

    #qqq = df["siteid"].unique()
    df = df[df[svar] == siteid]
    df.set_index("time", inplace=True)
    mult = 1
    #if convert:
    #    mult = 1 / 2.6178
    series = df[var] * mult
    return series


class SObs(object):
    """This class for running the SO2 HYSPLIT verification.
    

       methods
       -------
       find
       plot
       save (saves to a csv file)
       check
    """
    def __init__(self, dates, area, tdir="./", tag=None):
        """
        area is a tuple or list of four floats
        states : list of strings
                 Currently not used
        tdir : string : top level directory
        TODO - currently state codes are not used.
        """
        # dates to consider.
        self.d1 = dates[0]
        self.d2 = dates[1]
        # not used
        #self.states = states

        # top level directory for outputs
        self.tdir = tdir

        # area to consider
        self.area = area

        # name of csv file to save data to.
        self.csvfile = None
        self.pload = True
        self.find_csv()
        
        # keeps track of current figure number for plotting
        self.fignum = 1

        # self obs is a Dataframe returned by either the aqs or airnow MONET
        # class.
        self.obs = pd.DataFrame()
        self.dfall = pd.DataFrame()
        # siteidlist is list of siteid's of measurement stations that we want to look at.
        # if emptly will look at all stations in the dataframe.
        self.siteidlist = []

    def find_csv(self):
         """
          checks to see if a downloaded csv file in the correct date range
          exists.
         """
         names = []
         names =  find_obs_files(self.tdir, self.d1, self.d2, tag=None)
         # if it exists then
         if len(names) > 0:
            self.csvfile = (names[0])
            self.pload = True
         else: 
            self.csvfile = ("obs" + self.d1.strftime("%Y%m%d.") +
                             self.d2.strftime("%Y%m%d.") + "csv")
            self.pload = False

    def plumeplot(self):
        """
        Not working?
        To plot with the plume want list for each time of
        location and value
        """
        phash = {}
        temp = obs_util.timefilter(self.obs, [d1, d1])
        sra = self.obs["siteid"].unique()
        # for sid in sra:
        #    phash[d1] = (sid, self.obs
        #     df = df[df[svar] == siteid]
        #     val = df['obs']

    def generate_ts(self, sidlist=None):
        """
        Input
        list of site ids (optional).
        If None will loop through all.
        Returns
        siteid (int), pandas time series of obs, pandas time series of mdl.
        """
        # get list of siteids.
        if not sidlist:
            sra = self.obs["siteid"].unique()
        else:
            sratest = self.obs["siteid"].unique()
            sra = []
            # test to make sure 
            for sid in sidlist:
                if sid in sratest: sra.append(sid) 
                else: print('WARNING siteid not found ', str(sid), type(sid)) 
        for sid in sra:
            ts = get_tseries(self.obs, sid, var="obs", svar="siteid", convert=False)
            ms = get_tseries(self.obs, sid, var="mdl", svar="siteid")
            yield sid, ts, ms

    def calc_autocorr(self):
        for sid, ts, ms in self.generate_ts(sidlist=None):
            alist = []
            nlist = np.arange(0,48)
            for nnn in nlist:
                alist.append(ts.autocorr(lag=nnn))
            yield sid, nlist, alist

    def autocorr(self):
        """
        autocorrelation of measurements
        """
        fignum=0
        for sid, nlist, alist in self.calc_autocorr():
        #for sid, ts, ms in self.generate_ts(sidlist=None):
        #    alist = []
        #    nlist = np.arange(0,48)
        #    for nnn in nlist:
        #        alist.append(ts.autocorr(lag=nnn))
            fig = plt.figure(fignum)
            plt.plot(nlist, alist, 'k.')
            plt.title(str(sid))
            plt.savefig(str(sid) + 'obs.autocorr.png')
            fignum +=1
        plt.show()    


    def get_peaks(self, sidlist=None, pval=[0.95,1], plotfigs=True):
        """
        for each obs data series creates a CDF of values which are above mdl.
        Finds values which have prob between pval[0] and pval[1] and returns
        series of just those values.

        Can be used to identify peaks or valleys.
        """
      
        for sid, ts, ms in self.generate_ts(sidlist=sidlist):
            # get minimum detectable level
            mdl = np.max(ms.values)
            # create copy of series
            tso = ts.copy()
            # include only values above mdl
            ts = ts[ts > mdl]
            # find value in which prob(data < val) == pval 
            valA = statmain.probof(ts.values, pval[0])
            valB = statmain.probof(ts.values, pval[1])
            # data in which values are >= val.
            tsp = ts[ts >= valA]
            tsp = tsp[tsp <= valB]
            # plot peaks as well as CDF's.
            sns.set()
            if plotfigs:
                fig = plt.figure(1)
                ax1 = fig.add_subplot(1,1,1)
                ax1.plot(tso.index.tolist(), tso.values, '-k', linewidth=0.5)
                ax1.plot(tsp.index.tolist(), tsp.values, 'r.', linewidth=0.5)
                ax1.plot(ms.index.tolist(), ms, '-b')
                plt.title(str(sid))
                fig = plt.figure(2)
                ax = fig.add_subplot(1,1,1)
                cx, cy = statmain.cdf(ts.values)
                statmain.plot_cdf(cx, cy, ax) 
                cx, cy = statmain.cdf(tso.values)
                statmain.plot_cdf(cx, cy, ax) 
                ax.plot(valA, pval[0], 'b.')
                ax.plot(valB, pval[1], 'b.')
                plt.tight_layout()
                plt.show()
            # sid is site number
            # tsp is a time series of peaks
            yield sid, tsp 

    #def show_peaksA(self):
        # investigated using scipy signal peak finders.
        # not very satisfactory.
    #    for sid, ts, ms in self.generate_ts():
    #        tso = ts.copy()
    #        mdl = np.max(ms.values)
    #        print('MDL', mdl)
    #        zeros = ts <= mdl 
    #        ts[zeros] = 0
            
    #        fts = pd.Series(sigprocess.filter(ts), ts.index.tolist())

    #        peaks = sigprocess.findpeak_cwt(fts)
    #        peaks = sigprocess.findpeak_simple(tso) 
    #        tsp = tso.iloc[peaks] 
            
    #        plt.plot(tso.index.tolist(), tso.values, '-k', linewidth=0.5)
            #plt.plot(fts.index.tolist(), fts.values, '--g')
    #        plt.plot(tsp.index.tolist(), tsp.values, 'r.')
    #        plt.plot(ms.index.tolist(), ms, '-b')
    #        plt.title(sid)
    #        plt.show() 
    def nowarningplot(self, save=True, quiet=True,sra=None, maxfig=10 ):
        #logger.info('plotting with suppressed warnings')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.plot(save=save, quiet=quiet,sra=sra, maxfig=maxfig )

    def plot(self, save=True, quiet=True,sra=None, maxfig=10 ):
        """plot time series of observations"""
        if not sra:
            sra = self.obs["siteid"].unique()
 
        # catch if 
        if not isinstance(self.fignum, int): 
           wstr = 'Invalide type for self.fignum ' + type(self.fignum)
           logger.warning(wstr)
           self.fignum=1
        if not isinstance(maxfig, int): 
           logger.warning('Invalide type for maxfig ' + type(maxfig))
           maxfig=10
        #print("PLOT OBSERVATION SITES")
        #print(sra)
        sns.set()
        sns.set_style('whitegrid')
        dist = []
        if len(sra) > 20:
            if not quiet:
                print("Too many sites to pop up all plots")
            quiet = True
        for sid in sra:
            ts = get_tseries(self.obs, sid, var="obs", svar="siteid", convert=False)
            ms = get_tseries(self.obs, sid, var="mdl", svar="siteid")
            dist.extend(ts.tolist())
            fig = plt.figure(self.fignum)
            # nickname = nickmapping(sid)
            ax = fig.add_subplot(1, 1, 1)
            # plt.title(str(sid) + '  (' + str(nickname) + ')' )
            plt.title(str(sid))
            ax.set_xlim(self.d1, self.d2)
            ts2 = ts.sort_index()
            ts2 = ts2.resample("H").asfreq(fill_value=-9)
            ax.plot(ts2.index.tolist(), ts2.values, '-b.')
            ax.plot(ms.index.tolist(), ms.values, '-r')
            if save:
                figname = self.tdir + "/so2." + str(sid) + ".png"
                plt.savefig(figname)
            if self.fignum > maxfig:
                if not quiet:
                    plt.show()
                plt.close("all")
                self.fignum = 0
            else:
                if not quiet:
                    plt.show()
                #plt.close("all")
                #self.fignum = 0
            # if quiet: plt.close('all')
            logger.info("plotting obs figure " + str(sid) + ' ' + str(self.fignum))
            self.fignum += 1


    def save(self, tdir="./", name="obs.csv"):
        fname = tdir + name
        self.obs.to_csv(fname)

    def read_met(self):
        tdir='./'
        mname=tdir + "met" + self.csvfile
        if(os.path.isfile(mname)):
            met = pd.read_csv(mname, parse_dates=True)
        else:
            met = pd.DataFrame()
        return(met)

    def runtest(self):
        aqs = aqs_mod.AQS()
        basedir = os.path.abspath(os.path.dirname(__file__))[:-4]
        fn = "testaqs.csv"
        fname = os.path.join(basedir, "data", fn)
        df = aqs_mod.load_aqs_file(fname, None)
        self.obs = aqs_mod.add_data2(df) 
        print("--------------TEST1--------------------------------") 
        print(self.obs[0:10])
        rt = datetime.timedelta(hours=72)
        self.obs = obs_util.timefilter(self.obs, [self.d1, self.d2 + rt])
        print("--------------TEST2--------------------------------")
        print(self.obs[0:10])
        self.save(tdir, "testobs.csv")

    def find(
        self,
        verbose=False,
        getairnow=False,
        tdir="./",
        test=False,
        units="UG/M3",
    ):
        """
        Find observations from AQS within the
        specified date range and area.
        Parameters
        -----------
        verbose   : boolean
        getairnow : boolean
        tdir      : string
        test      : boolean
        """
        area = self.area
        mload = False
        if test:
           runtest
        elif self.pload:
            self.obs = read_csv(os.path.join(tdir,self.csvfile), hdrs=[0])
            logger.info("Loaded csv file file " + tdir + self.csvfile)
            mload = True
            try:
                met_obs = read_csv(os.path.join(tdir, "met" + self.csvfile), hdrs=[0, 1])
            except BaseException:
                logger.info("did not load metobs from file")
        if mload: logger.info("loaded csv file metobs")
        elif not self.pload:
            logger.info("LOADING from EPA site. Please wait\n")
            if getairnow:
                #aq = airnow.AirNow()
                logger.info('AIRNOW')
                self.obs = airnow.add_data([self.d1, self.d2], download=True)
            else:
                logger.info('AQS')
                aq = aqs_mod.AQS()
                self.obs = aq.add_data(
                    [self.d1, self.d2],
                    param=["SO2", "WIND", "TEMP", "RHDP"],
                    download=False,
                )
            # aq.add_data([self.d1, self.d2], param=['SO2','WIND','TEMP'], download=False)
            #self.obs = aq.df.copy()
        #logger.debug("HEADERS in OBS: ", self.obs.columns.values)
        if self.obs.empty: 
           logger.warning('Obs empty')
        # filter by area.
        if area:
            self.obs = obs_util.latlonfilter(
                self.obs, (area[0], area[1]), (area[2], area[3])
            )
        if self.obs.empty: logger.warning('Obs empty after latlon filter')
        # filter by time
        rt = datetime.timedelta(hours=72)
        self.obs = obs_util.timefilter(self.obs, [self.d1, self.d2 + rt])
        if self.obs.empty: 
           logger.warning('Obs empty after time filter')
           logger.warning(self.d1.strftime("%Y %m %d"))
           logger.warning((self.d2+rt).strftime("%Y %m %d"))
        else:
           logger.warning('obs loaded successfully')
           logger.warning(self.d1.strftime("%Y %m %d"))
           logger.warning((self.d2+rt).strftime("%Y %m %d"))

        # if the data was not loaded from a file then save all the data here.
        if not self.pload:
            self.save(tdir, self.csvfile)
            logger.info("saving to file " + tdir + "met" + self.csvfile)

        # create dataframe with all the data
        self.dfall = self.obs.copy()

        # now create a dataframe with data for each site.
        # get rid of the meteorological (and other) variables in the file.
        self.obs = self.obs[self.obs["variable"] == "SO2"]
        if self.obs.empty: print('No So2 in Obs')

        # added back in 8/12/2019
        # print summary csv file
        print_info(self.obs, tdir+ "/info_" + self.csvfile)
        if verbose:
            obs_util.summarize(self.obs)

        # No longer convert but keep in ppm.
        # convert units of SO2
        #units = units.upper()
        #if units == "UG/M3":
        #    self.obs = convert_epa_unit(self.obs, obscolumn="obs", unit=units)


    def bysiteid(self, siteidlist):
        obs = self.obs[self.obs["siteid"].isin(siteidlist)]
        return obs         

    def obs2datem(self, edate, ochunks=(1000, 1000), tdir="./"):
        """
        ##https://aqsdr1.epa.gov/aqsweb/aqstmp/airdata/FileFormats.html
        ##Time GMT is time of dat that sampling began.
        edate: datetime object
        ochunks: tuple (integer, integer)
                 Each represents hours

        tdir: string
              top level directory for output.
        """
        logger.info("WRITING Datem FILE " + edate.strftime("%Y-%m-%d"))
        #print(self.obs["units"].unique())
        d1 = edate
        done = False
        iii = 0
        maxiii = 1000
        oe = ochunks[1]
        oc = ochunks[0]
        while not done:
            d2 = d1 + datetime.timedelta(hours=oc - 1)
            d3 = d1 + datetime.timedelta(hours=oe - 1)
            odir = date2dir(tdir, d1, dhour=oc, chkdir=True)
            dname = odir + "datem.txt"
            logger.info('writing to '+ dname)
            logger.info(d1.strftime("%Y-%m-%d"))
            logger.info(d3.strftime("%Y-%m-%d"))
            logger.info(d2.strftime("%Y-%m-%d"))
            logger.info('-----------------------')
            datem.write_datem(
                self.obs, sitename="siteid", drange=[d1, d3], dname=dname,
                fillhours=1, verbose=False
            )
            d1 = d2 + datetime.timedelta(hours=1)
            iii += 1
            if d1 > self.d2:
                done = True
            if iii > maxiii:
                done = True
                logger.warning("WARNING: obs2datem, loop exceeded maxiii")

    #def old_obs2datem(self):
    #    """
    #    write datemfile.txt. observations in datem format
    #    """
    #    sdate = self.d1
    #    edate = self.d2
    #    obs_util.write_datem(self.obs, sitename="siteid", drange=[sdate, edate])

    def get_map_info(self):
        ohash = obs_util.get_lhash(self.obs, "siteid")
        return ohash

    #def try_ar(self):
    #    from util.armodels import ARtest
    #    for sid, ts, ms in self.generate_ts():
    #        nnn= int(len(ts)/2.0)
    #        ts1 = ts[0:nnn]
    #        ts2 = ts[nnn:]
    #        print('SITE', sid)
    #        ar = ARtest(ts1, ts2)
             

    def map(self, ax, txt=True):
        """
        ax : map axes object?
        """
        ohash = obs_util.get_lhash(self.obs, "siteid")
        plt.sca(ax)
        clr = sns.xkcd_rgb["cerulean"]
        # sns.set()
        latmin = 90
        lonmin = 180
        latmax = 0
        lonmax = 0
        for key in ohash:
            latlon = ohash[key]
            if latlon[1] < lonmin: lonmin = latlon[1]
            if latlon[1] > lonmax: lonmax = latlon[1]
            if latlon[0] < latmin: latmin = latlon[0]
            if latlon[0] > latmax: latmax = latlon[0]
            if txt: plt.text(latlon[1], latlon[0], str(key), fontsize=7, color="red")
            plt.plot(latlon[1], latlon[0], color=clr, marker="*")
            with open('obs.csv', 'a') as fid:
                 rstr = str(key) + ','
                 rstr += str(latlon[1]) + ',' + str(latlon[0]) 
                 rstr += '\n'
                 fid.write(rstr)
        return [latmin, latmax, lonmin, lonmax]
