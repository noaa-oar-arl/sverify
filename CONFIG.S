# getdata.py  to retrieve CEMS and/or AQS  data.
#       --aqs    to get just aqs data.
#       --datem  This creates datem files in the subdirectories                
#       --cems   to get just cems data. 
#       --efiles This creates emitimes files in the subdirectories.
#       --nei    Gets data from National Emissions Inventory for the area

# setupruns.py to create CONTROL and SETUP files for hysplit and vmixing runs.
        --
# 
# mkscript.py to make the bash scripts to run HYSPLIT and/or vmixing.

# Tag which will be used for naming output files.
tag=run1a

# area defines box to search for cems / aqs data
# latmin: lonmin: latmax: lonmax
area=38.3:-77.0:38.4:-76.95

# drange defines date range for search
# YYYY:M:D:YYYY:M:D
drange=2009:1:1:2009:1:31
# directory where files will be written.
outdir=/outputdir/subdir/
# directory where hysplit executable is found.
# do not include 'exec'
hysplitdir='/hysplitdir/'
# determines whether graphs 'pop up'
quiet=2
# write separate emitimes / control files
# for different units at the same plant.
# may be useful if different units have different stack heights
byUnit=true
# if ppb then will run HYSPLIT with ichem=6
unit=ppb
# use different species for different codes.
# not currently recommended.
species=false
# Duration of HYSPLIT runs.
emitdays=5
# Used for plume rise calculation 
heat=50e6

# File with information on nei sources which could
# be used to create CONTROL files for HYSPLIT
# the neiconfig file MUST be found in the $outdir/neifiles/
neiconfig= 'CONFIG.nei'

