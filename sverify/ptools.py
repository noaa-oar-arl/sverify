# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import matplotlib.dates as mdates
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.ticker import MultipleLocator
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import datetime

"""
NAME: plotall.py
UID: p102
PGRMMR: Alice Crawford ORG: ARL
This code written at the NOAA Air Resources Laboratory
ABSTRACT: This code contains functions and classes to create concentrations as a function of time at a location from database
CTYPE: source code

-----------------------------------------------------------------------------------------------------
"""

def mod_map(gl, lonlist, latlist):
    if lonlist:
        gl.xlocator = mticker.FixedLocator([lonlist])
        gl.ylocator = mticker.FixedLocator([latlist])
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    #gl.xlabel_style('size': 15, 'color': 'gray'}
    #gl.ylabel_style('size': 15, 'color': 'gray', 'weight': 'bold'}

def create_map(fignum, lonlist=None):
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
   
    fig = plt.figure(fignum)
    proj = ccrs.PlateCarree()
    ax = plt.axes(projection=proj)
    gl = ax.gridlines(draw_labels=True, linewidth=2, color="gray")
    gl.xlabel_style={'size': 15, 'color': 'gray', 'weight': 'bold'}
    gl.ylabel_style={'size': 15, 'color': 'gray', 'weight': 'bold'}
    gl.ylabels_right = False
    gl.xlabels_top = False
    gl.xlocator = mticker.MaxNLocator(nbins=4, steps=[1,2,5,10,20,25],
                                      min_n_tickes=3)
    gl.ylocator = mticker.MaxNLocator(nbins=6, steps=[1,2,5,10,20,25],
                                      min_n_tickes=3)
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    states = cfeature.NaturalEarthFeature(
        category="cultural",
        name="admin_1_states_provinces_lines",
        scale="50m",
        facecolor="none",
    )
    ax.add_feature(states, edgecolor="gray")
    ax.add_feature(cfeature.BORDERS)
    ax.add_feature(cfeature.LAKES)
    ax.add_feature(cfeature.RIVERS)
    ax.add_feature(cfeature.COASTLINE)
    return fig, ax, gl


def set_date_ticksC(ax):
    mloc=mdates.MonthLocator()
    #minloc=mdates.WeekdayLocator()
    minloc=mdates.DayLocator(bymonthday=None, interval=2)
    #minloc=mdates.DayLocator(bymonthday=[1,5,10,15,20,25,30])
    #minloc=mdates.DayLocator(byweekday=M)
    mloc=mdates.DayLocator(bymonthday=[1,5,10,15,20,25])
    ax.xaxis.set_major_locator(mloc)
    ax.xaxis.set_minor_locator(minloc)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    start, end = ax.get_ylim()
    ax.tick_params(axis='both', which='major', labelsize=20)
    

# specifically for BAMS paper.
def set_date_ticksD(ax):
    mloc=mdates.MonthLocator()
    #minloc=mdates.WeekdayLocator()
    minloc=mdates.DayLocator(bymonthday=None, interval=1)
    #minloc=mdates.DayLocator(bymonthday=[1,5,10,15,20,25,30])
    #minloc=mdates.DayLocator(byweekday=M)
    mloc=mdates.DayLocator(bymonthday=[6,8])
    ax.xaxis.set_major_locator(mloc)
    ax.xaxis.set_minor_locator(minloc)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    start, end = ax.get_ylim()
    rdate = datetime.datetime(2018,6,8,0)
    ldate = datetime.datetime(2018,6,6,0)
    ax.set_xlim(left = ldate, right=rdate)
    start, end = ax.get_xlim()
    ax.tick_params(axis='both', which='major', labelsize=20)
    print('START END', start, end)

def set_date_ticksB(ax):
    mloc=mdates.MonthLocator()
    #minloc=mdates.WeekdayLocator()
    #minloc=mdates.WeekdayLocator(byweekday=MO, interval=1)
    minloc=mdates.DayLocator(bymonthday=[1,5,10,15,20,25,30])
    #mloc=mdates.DayLocator(bymonthday=[1,10,20,30])
    ax.xaxis.set_major_locator(mloc)
    ax.xaxis.set_minor_locator(minloc)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%y'))
    start, end = ax.get_ylim()


def set_date_ticks(ax):
    mloc=mdates.MonthLocator()
    minloc=mdates.WeekdayLocator()
    ax.xaxis.set_major_locator(mloc)
    ax.xaxis.set_minor_locator(minloc)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%y'))
    start, end = ax.get_ylim()
    #ax.yaxis.set_ticks(np.arange(start, end+ny, ny))


def generate_colors():
    clrs = ['-b','-g','-c','-r','-m','-y']
    clrs.append(sns.xkcd_rgb['royal blue'])
    clrs.append(sns.xkcd_rgb['pink'])
    clrs.append(sns.xkcd_rgb['beige'])
    clrs.append(sns.xkcd_rgb['seafoam'])
    clrs.append(sns.xkcd_rgb['kelly green'])
    iii=0
    maxi=0
    done=False
    while not done:
        clr = clrs[iii]
        iii+=1
        maxi+=1
        if iii > len(clrs)-1: iii=0
        if maxi>100: done=True
        yield clr


def set_legend(ax, bw=0.8):
    # puts legend outside of plot to the right hand side.
    handles, labels = ax.get_legend_handles_labels()
    # shrink width of plot by bw%
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * bw, box.height], which='both')
    ax.legend(handles, labels, loc='center left', bbox_to_anchor=(1, 0.5),
             bbox_transform=ax.transAxes)
             #bbox_transform=plt.gcf().transFigure)

def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)


def setuphexbin(setup='individual'):
     axhash={}
     szhash={}
     namehash={}
     fnum=1

     if setup=='individual':
        sz=(6,5)
        sns.set()
        sns.set_style('whitegrid')
        sns.set_context('talk', font_scale=1.2)

        fig1 = plt.figure(fnum) 
        ax1 = fig1.add_subplot(1,1,1)
        axhash['wind speed']=ax1
        szhash['wind speed']=[10,10]
        fig1.set_size_inches(sz[0],sz[1])

        fnum+=1 
        fig2 = plt.figure(fnum) 
        ax2 = fig2.add_subplot(1,1,1)
        axhash['wdir']=ax2
        szhash['wdir']=[45,10]
        fig2.set_size_inches(sz[0],sz[1])

        fnum+=1 
        fig3 = plt.figure(fnum) 
        ax3 = fig3.add_subplot(1,1,1)
        axhash['hour']=ax3
        fig3.set_size_inches(sz[0],sz[1])
        szhash['hour']=[15,10]

     if setup=='basic':
        sz=(20,5)
        sz1=(10,15)
        nnn=3
        aaa=1

     elif setup=='psqplot':
        sz=(15,10)
        sz1=(10,15)
        nnn=2
        aaa=3
        bbb=1
     return axhash, szhash

def set_hexbin(key, ax, ymax, tag=''):
    sety='Talk'
    fs=20
    if key=='wdir':
        ax.set_xticks([0,45,90,135, 180,225,270,315])
        ax.set_xticklabels(['0','','90','', '180','','270',''],fontsize=fs)
    elif key=='wind speed':
        ax.set_xticks([0,2.5,5,7.5,10])
        ax.set_xticklabels(['0','','5','', '10'],fontsize=fs)
        ax.set_xlim(0,15)  
    elif key=='hour':
        ax.set_xticks([0,3,6,9,12,15,18,21])
        ax.set_xticklabels(['0','','6','', '12','','18',''],fontsize=fs)
    if sety=='Talk': 
        ax.yaxis.set_major_locator(MultipleLocator(10))
        ax.yaxis.set_minor_locator(MultipleLocator(5))
        ax.set_ylim(0,ymax+2)  
        ax.tick_params(labelsize=fs, which='both')
        ax.set_ylim(0,ymax+2)  

        psqplot=False
        if psqplot:
           ax7.set_xlabel('PSQ')
           ax7.set_ylabel('SO2 (ppb)')
           ax7.set_xticks([1,2,3,4,5,6,7])
           ax7.set_xticklabels(['A','B','C','D','E','F','G'])

           ax4.set_xlabel('time')
           ax4.set_ylabel('PSQ')
           ax4.set_yticks([1,2,3,4,5,6,7])
           ax4.set_yticklabels(['A','B','C','D','E','F','G'])
           ax5.set_xlabel('PBL height (m) ')
           ax6.set_ylabel('PBL height ')
           ax6.set_xlabel('Stability')
           ax6.set_xticks([1,2,3,4,5,6,7])
           ax6.set_xticklabels(['A','B','C','D','E','F','G'])
        #ax1.set_title(str(site))
        plt.tight_layout() 
        save=True
        if save:
            if not tag: tag = ''
            plt.sca(ax)
            key2 = key.replace(' ','')
            plt.savefig(key2 + tag +  '.modeldistB.jpg')
        #plt.show()
            #if psqplot:
            #   plt.sca(ax4)
            #   plt.savefig(tag + str(site) + '.met_distB.jpg')

