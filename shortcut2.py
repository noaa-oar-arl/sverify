import sys
import os
import logging
from optparse import OptionParser
from sverify import options_process
from sverify import options_obs
from sverify import svconfig
import sverify
# import cartopy.crs as ccrs
# import cartopy.feature as cfeature

"""
shortcut1.py should be run first.
Use %run -i shortcut2.py 
The -i option gives shortcut2.py access to variables
that were loaded into the interactive namespace with shortcut1.py
-----------
This shortcut explores the AQS data.
"""
obs = sverify.svobs.SObs([d1,d2],area,options.tdir,tag=options.tag)
obs.find()

# This is a pandas dataframe with all the AQS information.
# A pandas DataFrame is similar to an excel spreadsheet.
# the obs dataframe contains just the SO2 data.
df = obs.obs

# The dfall DataFrame contains all variables not just SO2
dfall = obs.dfall
print(obs.dfall.variable.unique())

# print the column headers of the dataframe.
print(df.columns.values)

# you can use the help command to see what methods are available for
# a class instance.
# help(obs)

# plot time series. 
#obs.nowarningplot(quiet=False) 

# obs class generate_ts method will 
# return time series of so2 and minimum detectable level.
fignum=0
for sid, ts, ms in obs.generate_ts(sidlist=None):
    print(str(fignum))
    fig = plt.figure(fignum)
    plt.plot(ts, '-b')
    plt.plot(ms, '-r')
    plt.title(str(sid))
    plt.show()
    fignum += 1

# The following will take the dfall dataframe from
# the obs instance and create a pivot table which
# takes the different variables in 'variables' and
# create a column for each of them.
# it will also rename the columns and drop
# rows which have NO met data associated with them.

metobs = sverify.svmet.obs2metobs(obs)
print(metobs.df[0:10])

# to get just the pivot table part you can use.
pivotdf = sverify.svobs.obs_pivot(obs.dfall)




