# for running a test
if options.runtest:
   # this is finding peaks in the obs data.
   from monet.util.svobs import SObs
   from monet.util.svmet import obs2metobs
   from monet.util.svmet import vmixing2metobs
   from monet.util.svhy import read_vmix
   from monet.util.svcems import CEMScsv
   from monet.util.svan1 import geometry2hash
   from monet.utilhysplit.statmain import degdiff
   from monet.util.svmet import hexbin
   import sys
   with open(logfile, 'a') as fid:
     fid.write('Running a test')
   cems = CEMScsv(tdir='./', cname='2017.cems.csv')
   obs = SObs([d1,d2], area, tdir=options.tdir)
   obs.find(tdir=options.tdir,  units=options.cunits)
   meto = obs2metobs(obs)
   meto.set_geoname(options.tag + '.geometry.csv')
   df = read_vmix(options.tdir, d1, d2, source_chunks, sid=None)
   vmet = vmixing2metobs(df,obs.obs)
   for sid, pkts in obs.get_peaks():
       pkdf = pkts.to_frame()
       pkdf['siteid'] = int(sid)
       pkdf.reset_index(inplace=True)
       #mdf = meto.df[meto.df['siteid'] == int(sid)]
       mdf = vmet.df.copy()
       # now have dataframe with met data for peaks.
       mdf = pd.merge(pkdf, mdf, how='left')
       # now find power plants in direction of wind.
       disthash, dirhash = geometry2hash(sid, fname=options.tag +\
                                         '.geometry.csv')
       orislist = list(dirhash.keys())
       iii=0
   
       for edata in cems.generate_cems(orislist, spnum='P1'):
           oris = orislist[iii]
           iii+=1 
           edata = edata.to_frame()
           edata.reset_index(inplace=True)
           edata.columns = ['time', oris]
           print('SITE ', sid, ' ORIS ', oris)
           print('DISTANCE ', disthash[oris]) 
           print('DIRECTION ', dirhash[oris])
           print('-----------------------')
           if disthash[oris] < 150:
               mdf = pd.merge(mdf, edata, how='left')
               direction = dirhash[oris]
               mdf[oris+'dir'] = mdf.apply(lambda row: degdiff(row['WDIR'], \
                                          direction), axis=1)
               #print(mdf[0:20])
               fig = plt.figure(1)
               ax = fig.add_subplot(1,1,1)
               mt = mdf[mdf[oris + 'dir'] <= 25]  
               mt = mt[mt[oris + 'dir'] >= -25]  
               xx = mt['SO2']
               yy = mt[oris]
               hexbin(xx,yy, ax, cbar=True)
               tx = np.min(xx) + 0.3(np.max(xx) - np.min(xx))
               yx = np.max(yy) *0.80 
               sp = (np.max(yy) - np.min(yy))/10
               print(tx, ty, sp)
               ax.text(tx,yx, str(oris), fontsize=12)
               ax.text(tx,yx-sp, str(disthash[oris]), fontsize=12)
               ax.text(tx,yx-2*sp, str(dirhash[oris]), fontsize=12)
               plt.show() 

       #for oris in dirhash.keys():
       #    #cemsdata = cems.
       #    print(oris, 'Distance', disthash[oris], '---', type(disthash[oris]))
       #    if disthash[oris] < 150:
       #        direction = dirhash[oris]
       #        mdf[oris] = mdf.apply(lambda row: degdiff(row['WDIR'], \
       #                                   direction), axis=1)
       #print(mdf[0:20])


