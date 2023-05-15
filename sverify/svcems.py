import os
import sys
import subprocess
import logging
import pandas as pd
import numpy as np
import matplotlib
#matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import datetime
import seaborn as sns
from timezonefinder import TimezoneFinder
#from shapely.geometry import Point
#import geopandas as gpd
import pandas as pd
pd.options.mode.chained_assignment = None
import warnings

# SO2 modules
from sverify.svdir import date2dir

# MONETIO MODULES
import monetio.obs
#from  monetio.obs import cems_api
import monetio.obs.cems_api as cems_api
from monetio.obs import cems_mod
import monetio.obs.obs_util as obs_util

from utilhysplit import emitimes


logger = logging.getLogger(__name__)
# from monet.obs.epa_util import convert_epa_unit


#2021 Jan 29 (amc) added make_csv method to SEmissions class.

"""
SEmissions class

methods:
  __init__
  find
  get_so2_sources
  get_heat
  get_sources
  create_emitimes
  emit_subroutine
  plot
  map

# in script
  A. ef.find
  B  ef.plot
  C  ef.create_emitimes
  D  er.map

SourceSummary class
"""


def determine_color(mass, unit='lbs'):
    if unit=='lbs':
        kg = mass/2.2
    else:
        kg = mass 
    if kg  < 0.05: ms = 'g'
    elif kg  < 1: ms = 'g'
    elif kg  < 10: ms= 'r'
    else: ms = 'r'
    return ms

def determine_size(mass, unit='lbs'):
    # set marker size based on emissions.
    if unit=='lbs':
        kg = mass/2.2
    else:
        kg = mass 
    if kg  < 0.05: ms=0
    elif kg  < 1: ms=1
    elif kg  < 10: ms=3
    elif kg < 50: ms = 5
    elif kg < 100: ms = 7
    elif kg < 500: ms = 9
    elif kg < 1000: ms = 11
    elif kg < 5000: ms = 13
    elif kg < 10000: ms = 15
    else: ms = 17
    return ms 


def remove_strings(df, stype):
    def remove_str(x):
        if isinstance(x, str):
           try:
               x = float(x)
           except:
               print('string value found ', x)
               return 0
        elif isinstance(x, float):
           return x 
        elif isinstance(x, int):
           return x 
        else:
           print('unexpected type found ', type(x), x)
           return x 

    df[stype] = df.apply(lambda row: remove_str(row[stype]), axis=1)
    return df


def remove_negs(df, stype):
    def remove_negs(x):
        if isinstance(x, str):
           try:
               x = float(x)
           except:
               print('string value found ', x)
               return 0
        if x < 0:
            return 0
        else:
            return x
    df[stype] = df.apply(lambda row: remove_negs(row[stype]), axis=1)
    return df


def get_stackheight_hash(df):
    """
    creates dictionary with key is oris code.
    value is maximum stack height for that oris.
    """

    dftemp = df[["oris", "stackht"]]
    dftemp = dftemp.drop_duplicates()
    orislist = dftemp["oris"].unique()

    shash = {}
    for oris in orislist:
        df2 = dftemp[dftemp["oris"] == oris]
        stackhts = df2["stackht"].unique()
        sh = np.max(stackhts)
        shash[oris] = sh
    return shash


def get_timezone(lat, lon):
    """ returns time difference in hours"""
    tf = TimezoneFinder()
    tz = tf.closest_timezone_at(lng=lon, lat=lat)
    #print("TZ-------------", tz, lat, lon)
    dtest = datetime.datetime(2010, 2, 1, 0)
    t1 = pd.Timestamp(dtest).tz_localize(tz)  # local time
    t2 = t1.tz_convert("utc")  # utc time

    t1 = t1.tz_localize(None)
    t2 = t2.tz_localize(None)
    # returns hours. must add this to local time to get utc.
    return (t2 - t1).seconds / 3600.0

class CEMScsv:
    """
    csv file with Emissions data. Created from SEmissions object dataframe.
    """
    def __init__(self, tdir="./", cname="cems.csv"):
                 #data=pd.DataFrame()):
        if '/' != tdir[-1]: tdir += '/'
        self.tdir = tdir
        self.cname = cname
        self.cems = pd.DataFrame()
        self.melted = pd.DataFrame()
        self.timecol = ('time','time','time')
        #self.df = data

    def read_csv(self, cname=None):
        if not cname: cname = self.cname
        dtp = {self.timecol: 'datetime64[ns]'}
        if os.path.isfile(self.tdir + cname):
            cems = pd.read_csv(self.tdir + cname, sep=",", header=[0,1,2], dtype=dtp
                              ) 
            self.cems = cems
        #print('READ CEMS', self.tdir, cname, self.cems[0:10])
        self.cems[self.timecol] = self.cems[self.timecol].astype('datetime64[ns]')
        #print(self.cems.dtypes)
        #print('READ CEMS', self.cems[0:10])
        return self.cems

    def melt(self):
        vals = list(self.cems.columns.values[1:])
        #print('VALS', vals, type(vals), type(vals[0]))
       
        self.melted = pd.melt(self.cems,
                id_vars=[self.timecol],
                value_vars = vals)
        new = ['time','oris','pollnum','unit','SO2']
        self.melted.columns = new
        return self.melted

    def get_cems(self):
        if self.melted.empty and not self.cems.empty:
           self.melt()
        if not self.melted.empty:
            #df = self.melted[self.melted['oris'].isin(orislist)]
            #if not df.empty:
            sources = pd.pivot_table(self.melted, index="time", columns='oris', values='SO2',aggfunc=np.sum)
            sources.reset_index(inplace=True)
            #else:
            #    sources = pd.DataFrame()
        else:
            sources = pd.DataFrame()
        return sources 

    def make_csv(self, df):
        logger.info("CREATE CSV FILE " +  self.tdir +  self.cname)
        new = [self.timecol]
        df.fillna(0, inplace=True)
        for hd in df.columns:
            val1 = hd[0]
            # particle type
            try:
                val2 = " P" + str(hd[4])
            except:
                val2 = ' Pall'
            # unit
            try:
                val3 = " U" + str(hd[5])
            except:
                val3 = ' Uall'
            try:
                cstr = hd[0] + " P" + str(hd[4])
            except:
                cstr = hd
            try:
                cstr += " U" + str(hd[5])
            except:
                pass
            #new.append(cstr)
            new.append((val1,val2,val3))
        #df.columns = new
        df.reset_index(inplace=True)
        df.columns=pd.MultiIndex.from_tuples(new)
        df.to_csv(self.tdir + self.cname, float_format="%.1f", index=False)

    def generate_cems(self,orislist, spnum='P1'):
        """
        return time series of measurements.
        """
        cemsfile = self.tdir + self.cname
        cems = pd.read_csv(cemsfile,sep=",", index_col=[0],parse_dates=True)
        new=[]   
        for hd in cems.columns:
            temp = hd.split(',')
            temp = temp[0].replace('(','')
            try:
                new.append(int(float(temp)))
            except:
                new.append(temp)
        cems.columns = new
        for col in cems.columns:
            for oris in orislist:
                if str(oris) in col and  spnum in col:
                   yield cems[col]



class SourceSummary:

    def __init__(self, tdir="./", fname="source_summary.csv",
                 data=pd.DataFrame()):
        if tdir[-1] != '/': tdir += '/'
        self.commentchar = "#"
        if not data.empty:
            self.sumdf = self.create(data)
        else:
            if os.path.isfile(tdir + fname):
                self.sumdf = self.load(tdir, fname)
            else:
                self.sumdf = pd.DataFrame()
        self.tdir = tdir
        self.fname = fname

    def map(self, ax, txt=True):
        """plot location of emission sources"""
        # if self.cems.df.empty:
        #    self.find()
        sumdf = self.sumdf
        plt.sca(ax)
        oris = sumdf["ORIS"].unique()
        keep = [
            "ORIS",
            "lat",
            "lon",
            "Max(lbs)",
        ]
        grouplist = [
            "ORIS",
            "lat",
            "lon"]

        sumdf = sumdf[keep]
        sumdf = sumdf.groupby(grouplist).sum()
        if isinstance(oris, str):
            oris = [oris]
        sumdf = sumdf.reset_index()
        lathash = df2hash(sumdf, "ORIS", "lat")
        lonhash = df2hash(sumdf, "ORIS", "lon")
        tothash = df2hash(sumdf, "ORIS", "Max(lbs)")
        # fig = plt.figure(self.fignum)
        for loc in oris:
            try:
                lat = lathash[loc]
            except:
                loc = None
            if loc:
                lat = lathash[loc]
                lon = lonhash[loc]
                ms = determine_size(tothash[loc])
                #if loc in self.goodoris:
                print('pl ' + str(loc) + ' ' + str(tothash[loc]) + ' ' + str(ms))
                ax.plot(lon, lat, "ko", markersize=ms, linewidth=2, mew=1)
                if txt:
                    plt.text(lon+0.05, lat-0.05, (str(loc)), fontsize=15, color="b")
                #else:
                #    ax.text(lon, lat, str(int(loc)), fontsize=8, color="k")

    def check_oris(self, threshold):
        """
        return list of oris codes for which the max emission was above
        threshold.
        """
        h1 = "Max(lbs)"
        try:
            tempdf = self.sumdf[["ORIS", "Max(lbs)"]]
        except:
            tempdf = self.sumdf[["ORIS", "Max(kg)"]]
            h1 = "Max(kg)"
        tempdf.groupby("ORIS").max()
        df = tempdf[tempdf[h1] >= threshold]
        bad = tempdf[tempdf[h1] < threshold]
        print("ORIS below threshold ", bad["ORIS"].unique())
        print("ORIS above threshold ", df["ORIS"].unique())
        goodoris = df["ORIS"].unique()
        return goodoris

    def operatingtime(self, data1):
        grouplist = ["oris", "unit"]
        keep = grouplist.copy()
        keep.append("OperatingTime")
        data1 = cems_api.keepcols(data1, keep)
        optime = data1.groupby(grouplist).sum()
        optime = optime.reset_index()
        return optime

    def create(self, data1):
        """
        creates a dataframe with columns 
        oris
        unit (id of monitoring location)
        Name (facilities name)
        lat
        lon
        Stack Height (m)
        Mean(lbs)  (mean 1 hour emission over the time period) 
        Max(lbs)  (Max 1 hour emission over the time period) 
        """
        columns = [
            "ORIS",
            "unit",
            "Name",
            "lat",
            "lon",
            "Stack height (m)",
            "Mean(lbs)",
            "Max(lbs)",
            "Total(lbs)",
            "OperatingTime",
        ]
        # print(data1.columns)
        optime = self.operatingtime(data1)
        # only average when plant was operating.
        # data0 = data1.copy()
        # only average when plant was operating.
        data1 = data1[data1["OperatingTime"] > 0]
        #
        grouplist = [
            "oris",
            "unit",
            "facility_name",
            "latitude",
            "longitude",
            "stackht",
        ]
        keep = grouplist.copy()
        keep.append("so2_lbs")
        # drop columns not in the keep list.
        data1 = data1[keep]
        # data1 = cems_api.keepcols(data1, keep)
        # data1.fillna({'stackht':0}, inplace=True)
        data1 = data1.fillna(0)
        if data1.empty: 
           return pd.DataFrame()
        remove_negs(data1, "so2_lbs")
        # data1.dropna(axis=0, inplace=True, subset=["so2_lbs"])
        # data1.dropna(inplace=True)
        # data1.fillna(0, inplace=True, subset=["so2_lbs"])
        # get the mean of so2_lbs
        meandf = data1.groupby(grouplist).mean()
        # get the max of so2_lbs
        maxdf = data1.groupby(grouplist).max()
        totaldf = data1.groupby(grouplist).sum()
        meandf.reset_index(inplace=True)
        maxdf.reset_index(inplace=True)
        totaldf.reset_index(inplace=True)
        # merge so mean and max in same DataFrame
        sumdf = pd.merge(
            meandf, maxdf, how="left", left_on=grouplist, right_on=grouplist
        )
        # print('SOURCE summary sumdf')
        # print(sumdf)
        # print(sumdf.columns.values)
        sumdf = pd.merge(
            sumdf, totaldf, how="left", left_on=grouplist, right_on=grouplist
        )
        sumdf = pd.merge(
            sumdf,
            optime,
            how="left",
            left_on=["oris", "unit"],
            right_on=["oris", "unit"],
        )
        sumdf.columns = columns
        return sumdf

    def __str__(self):
        print("Placeholder for Source Summary String")

    def load(self, tdir=None, name=None):
        if not name:
            name = self.fname
        if not tdir:
            tdir = self.tdir
        if os.path.isfile(tdir + name):
            # df = pd.read_csv(tdir + name, header=None)
            df = pd.read_csv(tdir + name, comment=self.commentchar)
        else:
            df = pd.DataFrame()
        # get rid of spaces in column values
        cols = df.columns.values
        newc = []
        for val in cols:
            newc.append(val.strip())
        df.columns = newc
        return df

    def print(self, tdir="./", fname="source_summary.csv"):
        if self.sumdf.empty:
           print('No Source Summary Data')
        else:
            name = tdir + fname
            cols = self.sumdf.columns.values.copy()
            cols[8] = cols[8].replace("lbs", "tons")
            orislist = self.sumdf["ORIS"].unique()
            with open(name, "w") as fid:
                rstr = ""
                for val in cols:
                    rstr += str(val) + " ,    "
                rstr += "\n"
                fid.write(rstr)
                for oris in orislist:
                    tempdf = self.sumdf[self.sumdf["ORIS"] == oris]
                    rstr = self.create_string(tempdf)
                    fid.write(rstr)

    def create_string(self, sumdf):
        total = 0
        rstr = ""
        for index, row in sumdf.iterrows():
            rstr += str(row["ORIS"]) + " "
            rstr += ","
            rstr += "{0:>10.11s}".format(str(row["unit"]))
            rstr += ","
            rstr += "{0:>12.11s}".format(str(row["Name"]))
            rstr += ","
            rstr += " "
            rstr += "{:10.4f}".format(row["lat"])
            rstr += ","
            rstr += "{:10.4f}".format(row["lon"])
            rstr += ","
            rstr += "{:10.1f}".format(row["Stack height (m)"])
            rstr += ","
            rstr += "{:10.1f}".format(row["Mean(lbs)"])
            rstr += ","
            rstr += "{:10.1f}".format(row["Max(lbs)"])
            rstr += "," + "  "
            rstr += "{:10.1f}".format(row["Total(lbs)"] * 0.0005)
            rstr += "," + "  "
            rstr += "{:10.3f}".format(row["OperatingTime"])
            rstr += "\n"
            total += row["Total(lbs)"]
            # fid.write(rstr)
        # rstr += 'Total '  + "{:10.4e}".format(total)   + ' lbs \n'
        rstr += (
            self.commentchar
            + "Total "
            + "{:10.1f}".format(total * 0.0005)
            + " Tons\n\n"
        )
        return rstr
        # fid.write(rstr)

    # self.sumdf.to_csv(fname)


def df2hash(df, key, value):
    """ create a dictionary from two columns
        in a pandas dataframe. 
    """
    if key not in df.columns:
        return None
    if value not in df.columns:
        return None
    dseries = df.set_index(key)
    dseries = dseries[value]
    return dseries.to_dict()


class SEmissions(object):
    """This class for running the SO2 HYSPLIT verification.
       self.cems is a CEMS object

       methods
       find_emissions
       get_sources
       plot - plots time series of emissions
       map  - plots locations of power plants on map
    """

    def __init__(
        self,
        dates,
        alist,
        area=True,
        tdir="./",
        source_thresh=50,
        spnum=False,
        tag=None,
        cemsource="api",
    ):
        """
        self.sources: pandas dataframe
            sources are created from a CEMSEmissions class object in the get_sources method.

        area: list or tuple of four floats
             (lat, lon, lat, lon) describing lower left and upper right corner
              of area to consider. Note that the user is responsible for
              requestiong all states that may lie within this area.
        states: list of strings
              list of two letter state abbreviations. Data for all states listed
              will be downloaded and then stations outside of the area requested
              will be pruned.

        source_thresh : float
              sources which do not have a maximum value above this in the time
              period specifed by dateswill not be
              considered.

        spnum : boolean
              True - sort emissions onto different species depending on MODC
              flag value. (see modc2spnum method)
              False - ignore MODC flag value.
        """
        self.tag = tag
        self.df = pd.DataFrame()
        self.dfu = pd.DataFrame()
        # data frame for uncertain emissions.
        # MODC >= 8
        self.dfu = pd.DataFrame()
        self.sources = pd.DataFrame()

        # dates to consider.
        self.d1 = dates[0]
        self.d2 = dates[1]
        # area to consider
        if area:
            self.area = alist
        else:
            self.goodoris = alist
            self.area = None
        self.byarea = area
        self.tdir = tdir
        self.fignum = 1
        # self.sources is a DataFrame returned by the CEMS class.
        if cemsource == "api":
            self.cems = cems_api.CEMS()
        else:
            self.cems = cems_mod.CEMSftp()

        self.ethresh = source_thresh  # lbs emittimes only created if max emission over

        self.lbs2kg = 0.453592
        self.logfile = "svcems.log.txt"
        self.meanhash = {}
        # CONTROLS whether emissions are put on different species
        # according to SO2MODC flag.
        self.use_spnum = spnum

    def find(self, testcase=False, verbose=False):
        """find emissions using the CEMS class

           prints out list of emissions soures with information about them.

        """
        # figure out whether finding by area or predefined orislist.
        if self.byarea:
            alist = self.area
        else:
            alist = self.goodoris

        if testcase:
            efile = "emission_02-28-2018_103721604.csv"
            self.cems.load(efile, verbose=verbose)
        else:
            data = self.cems.add_data(
                [self.d1, self.d2], alist, area=self.byarea, verbose=verbose
            )
        if data.empty:
            print("NO SO2 data found. Exiting program")
            sys.exit()

        tag = self.tag
        if not tag: tag = '' 
        source_summary = SourceSummary(fname = tag + '.source_summary.csv', data=data)
        self.meanhash = df2hash(source_summary.sumdf, "ORIS", "Max(lbs)")

        # remove sources which do not have high enough emissions.
        self.goodoris = source_summary.check_oris(self.ethresh)
        self.df = data[data["oris"].isin(self.goodoris)].copy()

        lathash = df2hash(self.df, "oris", "latitude")
        lonhash = df2hash(self.df, "oris", "longitude")

        # convert time to utc
        tzhash = {}
        for oris in self.df["oris"].unique():
            # tz = cems_api.get_timezone_offset(lathash[oris], lonhash[oris])
            tz = get_timezone(lathash[oris], lonhash[oris])
            tzhash[oris] = datetime.timedelta(hours=tz)

        def loc2utc(local, oris, tzhash):
            if isinstance(local, str):
                #logger.debug("NOT DATE " + local)
                utc = local
            else:
                try:
                    utc = local + tzhash[oris]
                except:
                    # print('LOCAL', local)
                    # print('oris', oris)
                    # print('tzhash', tzhash)
                    utc = "None"
            return utc

        # all these copy statements are to avoid the warning - a value is trying
        # to be set ona copy of a dataframe.
        #logger.debug("DATA CHECK")
        #logger.debug(self.df[0:10])
        self.df["time"] = self.df.apply(
            lambda row: loc2utc(row["time local"], row["oris"], tzhash), axis=1
        )
        print(self.df.columns.values)
        temp = self.df[self.df.time == "None"]
        if not temp.empty:
            #logger.debug("TEMP with None time\n", temp[0:20])
            self.df = self.df[self.df.time != "None"]

        # get the source summary for the dates of interest
        df = obs_util.timefilter(self.df, [self.d1, self.d2])
        source_summary2 = SourceSummary(data=df)
        source_summary2.print(fname= tag + '.source_summary.csv')

    def get_so2_sources(self, unit=True):
        sources = self.get_sources(stype="so2_lbs", unit=unit)
        sources = sources * self.lbs2kg  # convert from lbs to kg.
        return sources

    def get_heat(self, unit=False):
        """
        return dataframe with heat from the CEMS file
        """
        sources = self.get_sources(stype="heat_input (mmbtu)", unit=unit)
        mult = 1.055e9 / 3600.0  # mmbtu to watts
        mult = 0  # the heat input from the CEMS files is not the correct value to
        # use.
        sources = sources * mult
        return sources

    #def get_stackvalues(self, unit=False):
    #    """
    #    return dataframe with string which has stack diamter, temperature
    #    velocity  obtained from the ptinv file.
    #    """
    #    sources = self.get_sources(stype="stack values", unit=unit)
    #    # mult = 1.055e9 / 3600.0  #mmbtu to watts
    #    # mult=0  ##the heat input from the CEMS files is not the correct value to
        # use.
        # sources = sources * mult
    #    return sources

    #def check_oris(self, series, oris):
    #    """
    #    Only model sources for which maxval is above the set threshold.
    #    """
    #    print(oris, "CHECK COLUMN---------------------------")
    #    nanum = series.isna().sum()
    #    series.dropna(inplace=True)
    #    maxval = np.max(series)
    #    print("Number of Nans", nanum)
    #    print("Max value", maxval)
    #    rval = False
    #    if maxval > self.ethresh:
    #        rval = True
    #    else:
    #        print("DROPPING")
    #    return rval
#
    def get_sources(self, stype="so2_lbs", unit=True, verbose=False):
        """
        Returns a dataframe with rows indexed by date.
        column has info about lat, lon,
        stackheight in meters,
        orisp code
        values are
        if stype=='so2_lbs'  so2 emissions
        if stype='

        """
        # print("GET SOURCES")
        if self.df.empty:
            print("SOURCES EMPTY")
            self.find()
        ut = unit
        df = obs_util.timefilter(self.df, [self.d1, self.d2])
        df = self.modc2spnum(df)
        # set negative values to 0.
        df = remove_negs(df, stype)

        # dftemp = df[df["spnum"] == 1]
        # dftemp = df[df["spnum"] == 2]
        # dftemp = df[df["spnum"] == 3]
        # print("SP 3", dftemp.SO2MODC.unique())
        # print("OP TIME", dftemp.OperatingTime.unique())

        if not self.use_spnum:
            # set all species numbers to 1
            df["spnum"] = 1

        if not unit:
            # need to find stack heights to use.
            stackht = get_stackheight_hash(df)

        cols = ["oris"]
        cols.append("spnum")
        if unit:
            cols.append("stackht")
        if unit:
            cols.append("unit")

        sources = pd.pivot_table(
            df, index=["time"], values=stype, columns=cols, aggfunc=np.sum
        )

        #######################################################################
        #######################################################################
        # original column header contains either just ORIS code or
        # (ORIS,UNITID)
        # This block adds additional information into the COLUMN HEADER.
        # lat lon information is added here because they are floats.
        # when creating the pivot table, do not want to have extra columns if
        # floats are slightly different.
        lathash = df2hash(self.df, "oris", "latitude")
        lonhash = df2hash(self.df, "oris", "longitude")
        newcolumn = []
        cols = sources.columns
        if isinstance(cols, str):
            cols = [cols]
        for val in cols:
            lat = lathash[val[0]]
            lon = lonhash[val[0]]
            spnum = val[1]
            if not unit:
                height = stackht[val[0]]
            else:
                height = val[2]
            # val[0] is the oris code
            # val[3] is the unit number
            tp = (val[0], height, lat, lon, spnum)
            if unit:
                tp = (val[0], height, lat, lon, spnum, val[3])
            newcolumn.append(tp)
            # tuple  oris, stackheight, lat, lon, spnum, unit
        sources.columns = newcolumn
        #######################################################################
        #######################################################################
        # print("SOURCES ", sources.columns)
        return sources


    def read_csv(self, name="cems.csv"):
        cems = pd.read_csv(name, sep=",")
        return cems

    def write_csv(self,unit=False):
        df = self.get_so2_sources(unit=unit)
        self.make_csv(df.copy())

    def make_csv(self,df, cname="cems.csv"):
        if self.tag:
            cname = str(self.tag) + ".cems.csv"
        csvfile = CEMScsv(tdir=self.tdir,cname=cname)
        csvfile.make_csv(df)

    def make_csv_direct(self, df, cname="cems.csv"):
        new = []
        df.fillna(0, inplace=True)
        for hd in df.columns:
            try:
                cstr = hd[0] + " P" + str(hd[4])
            except:
                cstr = hd
            try:
                cstr += " U" + str(hd[5])
            except:
                pass
            new.append(cstr)
        df.columns = new
        if self.tag:
            cname = str(self.tag) + ".cems.csv"
        df.to_csv(cname, float_format="%.1f")

    def create_emitimes(
        self, edate, schunks=1000, tdir="./", unit=True, heat=0, emit_area=0
    ):
        """
        One of the main methods. 
        create emitimes file for CEMS emissions.
        edate: datetime : the date to start the file on.
        Currently, 24 hour cycles are hard-wired.


        self.get_so2_sources
        """
        # lbs is converted to kg in get_so2_sources
        df = self.get_so2_sources(unit=unit)
        # unit in csv file is kg
        #print("CREATE CSV FILE ")
        self.make_csv(df.copy())
        logger.info("CREATE EMITIMES in SVCEMS " +  tdir + ' Use day chunks ' +  str(schunks/24))
        # placeholder. Will later add routine to get heat for plume rise
        # calculation.
        dfheat = df.copy() * 0 + heat
        # dfheat = self.get_heat(unit=unit)

        done = False
        iii = 0
        d1 = edate
        # loop to create each emittimes file.
        while not done:
            d2 = d1 + datetime.timedelta(hours=schunks - 1)
            dftemp = df.loc[d1:d2]
            hdf = dfheat.loc[d1:d2]
            # if unit:
            #    sdf = dfstack[d1:d2]
            # if no emissions during time period then break.
            if dftemp.empty:
                print("---------------------------------------")
                print("-------create emitimes method ---------")
                print("---------------------------------------")
                print("NO EMISSIONS FOR TIME PERIOD")
                print(d1.strftime("%Y %m/%d %Hz"), " to ")
                print(d2.strftime("%Y %m/%d %Hz"))
                print(self.d2.strftime("%Y %m/%d %Hz"))
                print(str(schunks))
                print("---------------------------------------")
                continue
            self.emit_subroutine(
                dftemp, hdf, d1, schunks, tdir, unit=unit, emit_area=emit_area
            )
            # create separate EMIT TIMES file for each unit.
            # these are named STACKFILE rather than EMIT
            # if unit:
            #    self.emit_subroutine(
            #        dftemp, sdf, d1, schunks, tdir, unit=unit, bname="STACKFILE"
            #    )
            d1 = d2 + datetime.timedelta(hours=1)
            # just a fail-safe loop.
            iii += 1
            if iii > 500:
                print('Hit loop limit in create_emittimes method')
                print('Exiting program')
                print(d1, d2, self.d2)
                done = True
                sys.exit()
            if d1 > self.d2:
                done = True
 
    def emit_subroutine(
        self,
        df,
        dfheat,
        edate,
        schunks,
        tdir="./",
        unit=True,
        bname="EMIT",
        emit_area=0,
    ):
        """
        create emitimes file for CEMS emissions.
        edate is the date to start the file on.
        Currently, 24 hour cycles are hard-wired.
        """
        # df = self.get_so2()
        # dfheat = self.get_heat()
        locs = df.columns.values
        prev_oris = "none"
        ehash = {}

        # get list of oris numbers
        orislist = []
        unithash = {}
        for hdr in locs:
            oris = hdr[0]
            orislist.append(oris)
            unithash[oris] = []

        for hdr in locs:
            oris = hdr[0]
            # print(hdr)
            if unit:
                mid = hdr[5]
            else:
                mid = "None"
            unithash[oris].append(mid)

        orislist = list(set(orislist))
        sphash = {1: "MEAS", 2: "EST1", 3: "EST2"}

        # create a dictionary with key oris number and value and EmiTimes
        # object.
        for oris in orislist:
            for mid in unithash[oris]:
                # output directory is determined by tdir and starting date.
                # chkdir=True means date2dir will create the directory if
                # it does not exist already.
                ename = bname + str(oris)
                if unit:
                    ename = ename + "_" + str(mid)
                odir = date2dir(tdir, edate, dhour=schunks, chkdir=True)
                ename = odir + ename + ".txt"
                if unit:
                    key = str(oris) + str(mid)
                else:
                    key = oris
                ehash[key] = emitimes.EmiTimes(filename=ename,species=sphash)
                # TODO need to check this update. sphash now set in __init__.
                #ehash[key].set_species(sphash)

        # now this loop fills the EmitTimes objects
        for hdr in locs:
            oris = hdr[0]
            d1 = edate  # date to start emitimes file.
            dftemp = df[hdr]
            dfh = dfheat[hdr]
            dftemp.fillna(0, inplace=True)
            dftemp = dftemp[dftemp != 0]
            # ename = bname + str(oris)
            # if unit:
            #    sid = hdr[4]
            #   ename += "." + str(sid)
            height = hdr[1]
            lat = hdr[2]
            lon = hdr[3]
            spnum = hdr[4]
            key = oris
            if unit:
                mid = hdr[5]
                key += str(mid)
            # hardwire 1 hr duraton of emissions.
            record_duration = "0100"
            # pick which EmitTimes object we are working with.
            efile = ehash[key]
            # output directory is determined by tdir and starting date.
            # chkdir=True means date2dir will create the directory if
            # it does not exist already.
            # odir = date2dir(tdir, edate, dhour=schunks, chkdir=True)
            # ename = odir + ename + ".txt"
            # efile = emitimes.EmiTimes(filename=ename)
            # this was creating a special file for a pre-processing program
            # that would take diameter, temp and velocity to compute plume rise.
            if "STACK" in bname:
                hstring = efile.header.replace(
                    "HEAT(w)", "DIAMETER(m) TEMP(K) VELOCITY(m/s)"
                )
                efile.modify_header(hstring)
            # hardwire 24 hour cycle length
            dt = datetime.timedelta(hours=24)
            #efile.add_cycle(d1, "0024")
            efile.add_cycle(d1, 24)
            for date, rate in dftemp.iteritems():
                # if spnum!=1: print(date, rate, spnum)
                if date >= edate:
                    heat = dfh[date]
                    check = efile.add_record(
                        date,
                        record_duration,
                        lat,
                        lon,
                        height,
                        rate,
                        emit_area,
                        heat,
                        spnum,
                    )
                    nnn = 0

                    while not check:
                        d1 = d1 + dt
                        efile.add_cycle(d1, 24)
                        check = efile.add_record(
                            date,
                            record_duration,
                            lat,
                            lon,
                            height,
                            rate,
                            emit_area,
                            heat,
                            spnum,
                        )
                        nnn += 1
                        if nnn > 20:
                            break
                        # if not check2:
                        #    print("sverify WARNING: record not added to EmiTimes")
                        #    print(date.strftime("%Y %m %d %H:%M"))
                        #    print(str(lat), str(lon), str(rate), str(heat))
                        #    break
        # here we write the EmitTimes files
        for ef in ehash.values():
            ef.write_new(ef.filename)

    def modc2spnum(self, dfin):
        """
        The modc is a flag which give information about if the
        value was measured or estimated.
        Estimated values will be carried by different particles.
        spnum will indicate what species the emission will go on. 

        # According to lookups MODC values
        # 01 primary monitoring system
        # 02 backup monitoring system
        # 03 alternative monitoring system
        # 04 backup monitoring system

        # 06 average hour before/hour after
        # 07 average hourly

        # 21 negative value replaced with 0.
        # 08 90th percentile value in Lookback Period
        # 09 95th precentile value in Lookback Period
        # etc.

        # values between 1-4  - Species 1 (high certainty)
        # 6-7  - Species 2  (medium certainty)
        # higher values - Species 3 (high uncertainty)

        # when operatingTime is 0, the modc is Nan
        # these are set as Species 1 since 0 emissions is certain.

        # sometimes negative emissions are associated with higher MODC
        # not sure why this is.

        # in cems_api
        # When emissions are retrieved from hourlyfuel (methodCode=AD), set the MODC=-8
        # When emissions are retrieved with LME method, set the MODC=-9
        # When MODC value not defined and formula code is F-23 set MODC=-7
        # both of these are considered reliable estimates
        """
        df = dfin.copy()

        def sort_modc(x):
            try:
                val = int(x["SO2MODC"])
            except:
                val = 99

            try:
                optime = float(x["OperatingTime"])
            except:
                optime = 99

            if val in [1, 2, 3, 4, -9, -8, -7]:
                return 1
            if val in [6, 7]:
                return 2
            else:
                if optime <= 0.00001:
                    return 1
                else:
                    return 3

        # print('USE SPNUM', self.use_spnum)
        # if self.use_spnum:
        df = remove_strings(df, 'SO2MODC') 
        df["spnum"] = df.apply(sort_modc, axis=1)
        # else:
        #    df["spnum"] = 1
        # print(df.columns)
        # temp = df[df['so2_lbs']>0]
        # print(temp[['time','SO2MODC','spnum','so2_lbs']][0:10])
        return df

    def nowarning_plot(self, save=True, quiet=True, maxfig=10):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.plot(save, quiet, maxfig)


    def plotA(self, data, sdate, edate, clr, namehash, save, quiet):
        for ky in data.keys():
            oris = ky
            fig = plt.figure(self.fignum)
            fig.set_size_inches(9,5)
            ax = fig.add_subplot(1, 1, 1)
            data2 = data[ky] * self.lbs2kg
            ax.plot(data2, clr)
            ax.set_ylabel("SO2 mass kg")
            ax.set_xlim(sdate, edate)
            plt.setp(ax.get_xticklabels(), rotation=30, ha='right')  
            self.fignum +=1
 
            yearstr=sdate.strftime("%Y ")
            #plt.title(yearstr + 'Total for ' + str(oris) + " " + namehash[oris])
            plt.tight_layout()
            if save:
                figname = self.tdir + "/cems." + str(oris) + ".png"
                plt.savefig(figname)
            if quiet==0:
                plt.show()

    def plot(self, save=True, quiet=True, maxfig=10, byunit=True):
        """plot time series of emissions"""
        if self.df.empty:
            print("PLOT EMPTY")
            self.find()
        sns.set()
        namehash = df2hash(self.df, "oris", "facility_name")
        # ---------------
        df = obs_util.timefilter(self.df, [self.d1, self.d2])
        df = self.modc2spnum(df)
        cols = ["oris", "spnum"]
        if byunit:
            cols.insert(1, "unit")
        data1 = pd.pivot_table(
            df, index=["time"], values="so2_lbs", columns=cols, aggfunc=np.sum
        )
        try:
            data2 = pd.pivot_table(
                df, index=["time"], values="SO2MODC", columns=cols, aggfunc=np.max
            )
        except:
            print('Problem with creating pivot table for SO2MODC')
            data2 = pd.DataFrame()

        sdate, edate = self.plotB(data1, data2, byunit, namehash, save, quiet)
 
        alldata = pd.pivot_table(df, index=["time"], values="so2_lbs",
                                  columns=["oris"], aggfunc=np.sum)
        self.plotA(alldata, sdate, edate, '.k', namehash, save, quiet)




    def plotB(self, data1, data2, byunit, namehash, save, quiet):
        maxfig=10
        clrs = ["b.", "g.", "r."]
        jjj = 0
        ploc = 0
        unit = 0
        punit = 0

        for ky in data1.keys():
            loc = ky[0]
            spnum = ky[1]
            if byunit:
                unit = ky[1]
                spnum = ky[2]
            if spnum == 1:
                clr = "b."
            elif spnum == 2:
                clr = "g."
            elif spnum == 3:
                clr = "r."
            else:
                clr = "k."
            if loc != ploc or punit != unit:
                self.fignum += 1
                jjj = 0
            fig = plt.figure(self.fignum)
            sns.set()
            sns.set_style('whitegrid')
            fig.set_size_inches(9,5)
            ax = fig.add_subplot(2, 1, 1)
            ax2 = fig.add_subplot(2, 1, 2)
            data = data1[ky] * self.lbs2kg
            #data = data1[ky] * 1
            ax.plot(data, clr)
            md2 = True
            try:
                ax2.plot(data2[ky], clr)
            except:
                print('Problem with plotting so2modc: ', ky)
                md2 = False
 
            ax.set_ylabel("SO2 mass released in one hour (kg)")
            ax2.set_ylabel("SO2 MODC value")
            plt.sca(ax)
            d1 = data.index.tolist()

            if md2:
                d2 = data2[ky].index.tolist()
                if d1[0] < d2[0]:
                   sdate = d1[0]
                else:
                   sdate = d1[0]
                if d1[-1] < d2[-1]:
                   edate = d2[-1]
                else:
                   edate = d1[-1]
            else:
                sdate = d1[0]
                edate = d1[-1]

            ax.set_xlim(sdate, edate)
            ax2.set_xlim(sdate, edate)
            ax.xaxis.set_major_formatter(plt.NullFormatter())
            plt.setp(ax2.get_xticklabels(), rotation=30, ha='right')  
            yearstr=sdate.strftime("%Y ")
            if byunit:
                locstr = str(loc) + "." + str(unit).strip()
            else:
                locstr = str(loc)
            #plt.title(yearstr + locstr + " " + namehash[loc])
             
            if save:
                locstr = locstr.replace('*','a')
                figname = self.tdir + "/cems." + locstr + ".png"
                plt.savefig(figname)
            if self.fignum > maxfig:
                if not quiet:
                    plt.show()
                plt.close("all")
                self.fignum = 0
            ploc = loc
            punit = unit
            jjj += 1
        self.fignum+=1
        return sdate, edate




    def map(self, ax, txt=True):
        """plot location of emission sources"""
        # if self.cems.df.empty:
        #    self.find()
        plt.sca(ax)
        oris = self.df["oris"].unique()
        if isinstance(oris, str):
            oris = [oris]
        lathash = df2hash(self.df, "oris", "latitude")
        lonhash = df2hash(self.df, "oris", "longitude")
        # fig = plt.figure(self.fignum)
        for loc in oris:
            try:
                lat = lathash[loc]
            except:
                loc = None
            if loc:
                lat = lathash[loc]
                lon = lonhash[loc]
                # print('PLOT', str(lat), str(lon))
                # plt.text(lon, lat, (str(loc) + ' ' + str(self.meanhash[loc])), fontsize=12, color='red')
                # pstr = str(loc) + " \n" + str(int(self.meanhash[loc])) + "kg"
                # if self.meanhash[loc] > self.ethresh:
                if loc in self.goodoris:
                    # ax.text(lon, lat, pstr, fontsize=12, color="red")
                    ax.plot(lon, lat, "ko")
                    plt.text(lon, lat, (str(loc)), fontsize=12, color="red")
                else:
                    ax.text(lon, lat, str(int(loc)), fontsize=8, color="k")
                    ax.plot(lon, lat, "k.")
