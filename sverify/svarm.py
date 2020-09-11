import os
from utilhysplit.evaluation import armdata
import datetime
from sverify.svdir import dirtree

def writedatem(tdir, sdate,edate,timechunks):
    """
    writes a fake datem file with locations of arm sites
    """
    arm = armdata.ARMdata()
    arm.stations = ['C1']
    sample = datetime.datetime(2019,2,1)
    lochash = arm.get_locations(sample)
    dtree = dirtree(tdir, sdate,edate,chkdir=True,dhour=timechunks)
    for dirpath in dtree:
        with open(os.path.join(dirpath, 'datem.txt'),'w') as fid:
             fid.write('dummy info for arm locations\n')
             fid.write('dummy info for arm locations\n')
             fid.write('dummy info for arm locations\n')
             for key in lochash.keys():
                 latstr = str(lochash[key][0])
                 lonstr = str(lochash[key][1])
                 sid = str(key)
                 fstr = ['1999 02 01 2200 0100',latstr,lonstr,'0.1',sid,'10\n']
                 rstr = str.join(' ',fstr)
                 fid.write(rstr)
     
