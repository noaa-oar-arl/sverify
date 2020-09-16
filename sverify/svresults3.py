# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import numpy as np
import datetime
import time
import os
from os import path, chdir
from subprocess import call
import pandas as pd
import matplotlib.pyplot as plt
from utilhysplit.evaluation.statmain import MatchedData
from sverify.svcems import SourceSummary
from sverify.svcems import df2hash
from sverify.svobs import SObs
import sverify.svobs as svo
from sverify.svobs import get_tseries
import seaborn as sns
from shapely.geometry import Point
from shapely.geometry import LineString
import geopandas as gpd
import sys

from utilhysplit.evaluation.datem import read_dataA
from sverify.ptools import set_date_ticks
from sverify.ptools import generate_colors
from sverify.ptools import set_legend
from utilhysplit.evaluation.datem import frame2datem
from utilhysplit.evaluation.datem import frame2datem2

"""
DatemOutput class 
reads all c2datem output into a dataframe.
Creates plots of obs and model forecast.

"""
def dirpath2date(dirpath):
    """
    converts directory path to a date.
    """
    temp = dirpath.split('/')
    year = None
    month = None
    day = None
    for val in temp:
        if not val:
           pass 
        elif val[0] == 'y':
           try:
               year = int(val.replace('y',''))
           except:
               pass
        elif val[0] == 'm':
           try:
               month = int(val.replace('m',''))
           except:
               pass
        elif val[0] == 'd':
           try:
               day = int(val.replace('d',''))
           except:
               pass
    if year and month and day:
       rval =  datetime.datetime(year, month, day)
    else:
       rval = None
    return rval

class DatemOutput:

    """
    ATTRIBUTES:
    tdirpath : str : top level directory for results.
    df       : pandas DataFrame
    orislist : list of oris numbers in the area
    sidlist  : list of station id's in the area
    dhash    : dictionary  
               key is oris code and value is DataFrame with
               model and observation data from the dataA output
               from statmain.
             
 
    METHODDS:
    __init__
    fill_hash
    find_files
    writedatem


    Caveats - there should be no extra dataA files in the directories.
    
    """
    def __init__(self, tdirpath, orislist=None, daterange=None): 
        print('INIT')
        ## inputs
        self.tdirpath = tdirpath 
        self.orislist = orislist 
        self.daterange = daterange
        #self.orislist=[None]

        ## outputs
        self.df = pd.DataFrame() 
        self.sidlist = [] 

        ## internal use
        #self.plist = ['p1','p2','p3']
        self.zlist = ['z1','z2','z3','z4']
        self.plist = [None]
        
        #self.chash = {}  #dict. key is oris code. value is a color.
        #self.set_colors()
 
    def datetest(self, dirpath):
        """
        decides from directory path whether files are in the specified date
        range.
        """
        if not self.daterange:
           rval = True
        else:
           date = dirpath2date(dirpath)
           if not date:
              rval = False
           else:
               #print('DATE ', date)
               if date >= self.daterange[0] and date <= self.daterange[1]:
                  rval = True
               else:
                  rval = False
        return rval




    def find_files(self, oris=None, 
                         filetag=None,
                         dirtaglist = ['None'], 
                         poll='p1', 
                         lev=None, 
                         verbose=True): 
        """ oris should be oris number or None
            poll should indicate species (p1, p2, p3) or be None.

        if both are None then will return all files with dataA in the name.
        if oris indicated will return only dataA files with indicated oris code.
        if poll indicated will return only dataA files with indicated species.
        only finds files in directories with date between dates in daterange
        """
        dataA_files = []
        for (dirpath, dirnames, filenames) in os.walk(self.tdirpath):
            if verbose: print('CHECKING ', dirpath, filetag)
            if not self.datetest(dirpath): continue 
            # this is to limit directory search.
            if dirtaglist[0] != 'None':
                if not any(word in dirpath for word in dirtaglist): continue
            #if verbose: print('Passed ', dirpath, filetag)
            for fl in filenames:
                test1 = 'dataA' in fl
                if not filetag: test2 = True
                else:  test2 = str(filetag) in fl
            
                # test for species
                if not poll: test3 = True
                else:  test3 = poll in fl
            
                # test for level 
                if not lev: test4 = True
                else: test4 = lev in fl
 
                if test1 and test2 and test3 and test4: 
                    if verbose: print('Passed ', dirpath, fl)
                    print('Passed ', dirpath, fl)
                    #print('found', fl)
                    dataA_files.append(dirpath + '/' + fl)
                    if verbose: print('found', dirpath + '/' + fl)
        return dataA_files 

    # instead of this will add this dataframe to metobs.
    def add_metobs(self, metobsdf, orislist=None):
        # merge in the met data based on time and site id.
        print('metdf**', metobsdf.columns.values)
        keep = ['siteid','WDIR','WS','time','PSQ']
        if orislist: keep.extend(list(map(str,orislist)))
        self.orislist = list(map(str,orislist))
        metobsdf = metobsdf[keep] 
        print('sdf**', self.df.columns.values) 
        mla = ['date','sid']
        mra = ['time','siteid']
        newdf = pd.merge(self.df, 
                 metobsdf, 
                 how='left',
                 left_on= mla,
                 right_on=mra
                 )
        # drop the duplicated columns
        #newdf = newdf.drop(['date','siteid'])
        print(newdf[0:10])
        self.df = newdf
        return -1 

    def writedatem_enhanced(self, dfile):
           cnames=['date','duration','lat', 'lon',
                   'obs','model','sid','altitude',
                   'WDIR', 'WS']
           cnames.extend(self.orislist) 
           self.writedatem(dfile, bymonth=True, poll=None, cnames=cnames)

    #def readc2datem(self, poll=None, frq = 'H'):
    #    flist = self.find_files(oris=None, poll=poll)
    #    df = self.fromdataA(flist)
    #    self.df = df

    def writedatemall(self, dfile, bymonth=True, poll=None,
                   cnames = None):
        if not cnames:
           cnames=['date','duration','lat', 'lon',
                           'obs','model','sid','altitude'] 
           df = self.df.copy()
           df['duration'] = '0100' 
           df['altitude'] =  10
           print(df.columns.values)
           df = df[df['obs']!=-9]
           frame2datem2(dfile, df,cnames=cnames) 
           

    def writedatem(self, dfile, bymonth=True, poll=None,
                   cnames = None):
        """
        1. find datem files in the subdirectories
        2. read them into a dataframe
        """
        if not cnames:
           cnames=['date','duration','lat', 'lon',
                           'obs','model','sid','altitude'] 
        bymonth=True
        if self.df.empty:
           self.readc2datem(poll=poll)
        df = self.df.copy()
        #flist = self.find_files(oris=None, poll=poll)
        #print('FLIST', flist)
        #df = self.fromdataA(flist)
        #df.set_index('date', inplace=True)
        if df.empty: return
        #df = self.massage_df(df)
        #df = df.resample("H").asfreq()
        #df = df.reset_index()
        #df.drop('Num', axis=1, inplace=True)
        #print('WRITING--------------------------')
        #print(df[0:10])
        sidlist = df['sid'].unique()
        print('SID', sidlist)
        for sid in sidlist:
            print('SID', str(sid))
            dftemp = df[df['sid'] == sid] 
            dftemp.set_index('date', inplace=True)
            # loooking at autocorrelation functions of data.
            md = MatchedData(dftemp['obs'], dftemp['model'])
            sns.set()
            fig = plt.figure(1)
            ax = fig.add_subplot(1,1,1) 
            md.autocorr(ax)
            plt.title(str(sid))
            plt.savefig(str(sid) + 'autocorr.jpg') 

            sns.set()
            fig2 = plt.figure(2)
            ax2 = fig2.add_subplot(1,1,1) 
            md.plotseries(ax2,clrs=['-k','-b'], lbl='Model')
            plt.title(str(sid)) 
            plt.show()
            #dftemp = dftemp.resample("H").asfreq()
            try:
                dftemp = self.massage_df(dftemp)
            except:
                print('Problem with ' + str(sid))
                print(dftemp[0:10])
                continue
            dftemp.reset_index(inplace=True)
            dfile2 = str(sid) + '.' + dfile
            frame2datem(dfile2, dftemp,cnames=cnames) 
            if bymonth:
                dftemp["month"] = dftemp["date"].map(lambda x: x.month)
                mnths = dftemp['month'].unique()
                #print('MONTHS', mnths)
            else:
                mnths = []
            for mmm in mnths:
                dfile2 = str(sid) + ".month" + str(mmm) + "." + dfile
                print('DATEMFILE', dfile2)  
               #dftemp["month"] = dftemp["date"].map(lambda x: x.month)
                dfmonth= dftemp[dftemp["month"] == mmm]
                dfmonth.set_index('date', inplace=True)
                dfmonth = dfmonth.resample("H").asfreq()
                dfmonth.reset_index(inplace=True)
                dfmonth.fillna(0, inplace=True)
                frame2datem(dfile2, dfmonth, cnames=cnames)


    def parse_dataA_name(self, dname):
        temp = dname.split('.')
        source = temp[0].replace('dataA_', '')
        pollnum = temp[1].replace('p','')
        try: 
           pollnum = int(pollnum)
        except:
           pollnum = 0
        if 'z' in temp[2]:
            lev = temp[2].replace('z','')
            lev = int(lev)
        else:
            lev = 1
        return source, pollnum, lev 

    def save_dataset(self,cname):
        df.to_csv(cname, float_format="%0.1f")
        
    def open_dataset(self,verbose=False,dirtaglist=['None'],cname=None):
        """
        dirtaglist : list of strings.
        This can be used to use the file path to tag the data as beloning
        to a particular run. e.g. for the SREF data use dirtaglist
        =['nmb','arw'].
        """
        if cname:
            # reader has not been tested.
            # may need to tweak how time column etc is read in.
            #cname = os.path.join(cname)
            def to_datetime(d):
                return datetime.datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
            df = pd.read_csv(cname,sep=",",
                             header=[0],
                             index_col=[0],
                             converters={"date":to_datetime})  
            self.df = df
            return df
        else:
            flist = self.find_files(verbose=verbose,
                                dirtaglist=dirtaglist)
            return self.create_df(flist,dirtaglist=dirtaglist)

    def create_df(self, filelist,dirtaglist=['None']):
        df = pd.DataFrame()
        nnn = 0
        mcols = ['sid', 'date', 'lat','lon','obs', 'source', 'pollnum',\
                 'stype', 'lev','nwp']
        for fname  in filelist:
            temp = fname.split('/')
            dname, pollnum, lev = self.parse_dataA_name(temp[-1])
            # find name of simulation
            # if the tag (x) is part of the name (temp) then 
            # use the whole string as the identifier in the nwp column.
            nwp = [y for x in dirtaglist for y in temp if x in y]
            if not nwp: nwp = ['other']
            if nnn%50 == 0:
               print('Working on ', fname)
               print('tagging as', nwp)
            if 'EIS' in fname: stype = 'NEI'
            else: stype = 'ORIS'
            tempdf = read_dataA(fname)
            if  tempdf.empty: continue
            tempdf.drop(['Num'], inplace=True, axis=1)
            tempdf['source'] = dname
            tempdf['pollnum'] = pollnum
            tempdf['stype'] = stype
            tempdf['lev'] = lev
            tempdf['nwp'] = nwp[0]
            dropra = ['day', 'hour', 'month', 'year']
            for dr in dropra:
                if dr in tempdf.columns.values:
                   tempdf.drop(dr, axis=1, inplace=True)
            if nnn==0:
               df = tempdf
            else:
               df = pd.concat([df, tempdf], sort=True)
            #print('CREATE DF', df.columns.values)
            df = df.groupby(mcols).sum().reset_index()
            nnn+=1
        #df = df.set_index(mcols)
        #df.set_index('date', inplace=True)
        #df  = df.resample("H").asfreq(fill_value=0)
        #df.as_freq('H")
      
        self.df = df
        #print(self.df[0:10])
        #print(self.df.sum(level='

        print('get_pivot input', self.df[0:10])
        #plt.plot(self.df['model'])
        #plt.show()
        df2 = self.get_pivot()
        print(df2[0:10])
        print('---------------------------')
        #sys.exit()
        return df 

    def get_pivot(self, vals='model',  pollagg=True):
        # time is now the index
        # a separate column is generated for each model at each sid at each
        # source.
        #if pollagg:
        #   mcols = ['sid', 'date', 'lat','lon','obs','source','stype']

        if vals not in ['model', 'obs']:
           vals = 'model'

        df = pd.pivot_table(self.df, values=vals,
                            index = ['date', 'sid'],
                            columns = ['source','pollnum','stype'],
                            aggfunc=np.sum)
        df = df.reset_index()
        #newcols = []
        #for val in df.columns.values: 
        #    if 'date' in val: newcols.append('time')
        #    elif 'sid' in val: newcols.append('siteid')
        #    else: newcols.append(val)
        #df.columns = newcols
        #print('COLUMN VALUE', df.columns.values)
        #print(df[0:10])
        return df


    def group(self, sid=None, sourcelist=None, pollnumlist=None, stypelist=None,
               levlist=None,nwplist=None):
        mcols = ['sid', 'date','nwp','lat','lon','obs']
        tempdf = self.df.copy()
        # default is to only use the first level.
        # keep only levels in the list
        # should only adding levels with the same thickness. 
        # otherwise will need to add information about level thicknesses.
        if not levlist:
           levlist = [1]
        nlev = len(levlist)    
        tempdf = tempdf[tempdf['lev'].isin(levlist)]
        if nlev > 1:
           print('WARNING multiple levels being added.\n')
           print('This will only be correct if levels are the same\
                   thickness')
        #print('GROUP A', tempdf[0:5])
        # keep only sources in the sourcelist
        if sid:
            tempdf = tempdf[tempdf['sid'].isin([sid])]
        if sourcelist:
            tempdf = tempdf[tempdf['source'].isin(sourcelist)]
        # keep only sources types in the list
        if stypelist:
            tempdf = tempdf[tempdf['stype'].isin(stypelist)]
        # keep only polluntant species in the list
        if pollnumlist:
            tempdf = tempdf[tempdf['pollnum'].isin(pollnumlist)]
        # keep nwp models in the list
        if isinstance(nwplist,list) or isinstance(nwplist,np.ndarray):
            tempdf = tempdf[tempdf.nwp.isin(nwplist)]


        tempdf = tempdf.groupby(mcols).sum().reset_index()
        # divide by nlev when adding levels of same thickness.
        tempdf['model'] = tempdf['model'] / nlev

        #print('GROUP B', sourcelist, tempdf[0:5])
        return tempdf



    def generate_plot_ts(self,levlist=[1]):
        for df in self.generate_model_ts(levlist=levlist):
            df.plot()
            plt.show()

    def generate_model_ts(self,levlist=[1]):
        """
        can be used to create the reliability curves.
        
        Return:
        rlist : list of pandas DataFrames
        one DtaFrame per observation site is returned.
        index is date.
        columns are model forecasts from different ensemble members.

        """
        # concatenates the observed data as another column.
        sidlist = self.get_sidlist()
        def subfunc(sid):
            simulated =  self.get_ts(sid, levlist) 
            obs =self.get_ts(sid,levlist,vals='obs')
            # an observed row is created for each nwp model.
            # they should all be the same.
            # just use the first one.
            obs = obs[self.df.nwp.unique()[0]]
            obs.name = 'obs_' + str(sid)
            return pd.concat([simulated, obs], axis=1)  
        rlist = [subfunc(x) for x in sidlist]
        return rlist
          
    def get_ts(self, sid, levlist=[1],vals='model'):
        if vals == 'model': aggfunc=np.sum
        elif vals == 'obs' : aggfunc=np.max

        sourcelist = self.df.source.unique()
        nlist = self.df.nwp.unique()
        # this will add multiple levels if necessary.
        sdf2 = self.group(sid=sid,
                          levlist = levlist,
                          sourcelist=sourcelist,
                          stypelist=['ORIS'],
                          nwplist=nlist)
        # creates one column of values per model. 
        df = pd.pivot_table(sdf2, 
                            values=vals,
                            index=['date'],
                            columns=['nwp'],
                            aggfunc=aggfunc)
        # dataA does not print out 0,0 pairs. Add them in here.
        dftemp = df.resample("H").asfreq()
        for nval in self.df.nwp.unique():
            dftemp[nval].fillna(0, inplace=True)
        return dftemp

    def pivot_sub(self, sid=None, 
                  vals='model', 
                  nwplist=None, 
                  sourcelist=None, 
                  pollnumlist=None, 
                  stypelist=None):
        # can be fed into reliability curve class.

        if vals not in ['model', 'obs']:
           vals = 'model'
        tempdf = self.df.copy()
        #if sid: tempdf = tempdf['sid'] = sid
        if sourcelist:
            tempdf = tempdf[tempdf['source'].isin(sourcelist)]
        if stypelist:
            tempdf = tempdf[tempdf['stype'].isin(stypelist)]
        if pollnumlist:
            tempdf = tempdf[tempdf['pollnum'].isin(pollnumlist)]
        if nwplist:
            tempdf = tempdf[tempdf['nwp'].isin(nwplist)]
        df = pd.pivot_table(tempdf, values=vals,
                            index = ['date'],
                            columns = 'sid', aggfunc=np.sum)
        return df 

    def sourcelist(self):
        df = self.df.copy()
        tempdf = df[df['stype'] == 'NEI']
        elist = tempdf['source'].unique()
        df = self.df.copy()
        tempdf = df[df['stype'] != 'NEI']
        slist = tempdf['source'].unique()
        return list(elist), list(slist)

    def nwplist(self):
        return list(self.df.nwp.unique())

    def get_sidlist(self):
        return self.df['sid'].unique()

    #df = pd.concat([df, tempdf], sort=True).groupby(mcols).sum().reset_index()

    def colorhash(self, slist):
        """
        Assign a specific color to each ORIS code.
        """
        clr = generate_colors()       
        chash = {}
        print(slist)
        for oris in slist:
            print(oris)
            chash[str(oris)] = next(clr)
        return chash

    def set_colors(self, chash=None):
        if not chash: chash = self.colorhash()
        self.chash = chash       
        return chash 

    def plotall(self):
        print('Plotting all in svresults3')
        sns.set()

        # elist list of EIS sources
        # slist list of ORIS sources
        elist, slist = self.sourcelist()
        print(elist)
        print(slist)
        chash1 = self.colorhash(slist)
        chash2 = self.colorhash(elist)
        print(elist)
        print(slist)
        # for each site.
        for sid in self.get_sidlist():
            figa = plt.figure(1)
            ax1a = figa.add_subplot(1,1,1)
            figa.set_size_inches(10,5)
            figb = plt.figure(2)
            ax1b = figb.add_subplot(1,1,1)
            figb.set_size_inches(10,5)
            figc = plt.figure(3)
            ax1c = figc.add_subplot(1,1,1)
            figc.set_size_inches(10,5)

            iii=0
            iii2=0
            self.plot_loop(ax1a, chash1, slist, sid)
            self.plot_loop(ax1b, chash2, elist, sid, legend=True)
            self.plot_loop(ax1c, chash2, [slist, elist], sid, clrs=['g', 'b'],
                           lbls = ['ORIS', 'NEI'])           
  
            plt.show()

    def plot_loop(self, ax, chash, slist, sid, 
                  clrs=None,
                  lbls=None,
                  legend=True):
            iii=0 
            for oris in slist:
                if not isinstance(oris, list): 
                    #df = self.pivot_sub(sid, sourcelist=[oris])
                    #df2 = self.pivot_sub(vals='obs', sourcelist=[oris])
                    df = self.group(sid, sourcelist=[oris])
                else:
                    #df = self.pivot_sub(sid, sourcelist=oris)
                    #df2 = self.pivot_sub(vals='obs', sourcelist=oris)
                    df = self.group(sid, sourcelist=oris)
                #dftemp = df[df["sid"] == sid]
                print('GROUPED', df[0:10])
                #model = df[sid]
                #obs = df2[sid]
                df.set_index('date', inplace=True)
                model = df['model']
                #obs = df['obs'].fillna(0, inplace=True)
                obs = df['obs']
                #dftemp.set_index('date', inplace=True)
                #dftemp = self.massage_df(dftemp)
                #obs = dftemp["obs"]
                #model = df["model"]
                #obs = df2["obs"]
                if iii==0: 
                    ax.plot(obs.index.tolist(), obs.values, '-k.')
                    #ax2.plot(obs.index.tolist(), obs.values, '-k',label='Obs')
                if model.values.any(): 
                    if clrs: clr = clrs[iii]
                    else: clr = chash[str(oris)]
                    if lbls:
                       label = lbls[iii]
                    else:
                       label = str(oris) 

                    #if np.max(model.values) > 0:
                    ax.plot(model.index.tolist(), model.values,
                                     clr,
                                     label=label)
                iii+=1
                set_date_ticks(ax)
                if legend: set_legend(ax, bw=0.95)
                ax.set_title(str(sid))

    def massage_df(self, df):
            dftemp = df.copy()
            #dftemp = df[df["sid"] == site]
            dftemp = dftemp.resample("H").asfreq()
            dftemp["obs"].fillna(0, inplace=True)
            dftemp["model"].fillna(0, inplace=True)
            dftemp["duration"].fillna(method="bfill", inplace=True)
            dftemp["lat"].fillna(method="bfill", inplace=True)
            dftemp["lon"].fillna(method="bfill", inplace=True)
            dftemp["sid"].fillna(method="bfill", inplace=True)
            dftemp["altitude"].fillna(method="bfill", inplace=True)
            return dftemp
            #msitedata = MatchedData(obs, model)



def get_model_ts(sdf, site,levlist):
    model_ts = sdf.group(sid, stypelist=['ORIS'], levelist=levlist)
    
#Create the reliability curve
# 1. Get hourly time series of model data.
# 2. calculate percent


def plot1(sdf):
    cols = sdf.columns.values
    arw = [x for x in cols if 'arw' in x]





 

