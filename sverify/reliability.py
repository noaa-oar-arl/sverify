import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns        
 
def plot_freq(obs,prob):
    sns.set()
    sns.set_style('whitegrid')
    obscolor = '-k'
    probcolor = '-b'

    fig = plt.figure(10)
    ax1 = fig.add_subplot(1,1,1)
    ax2 = ax1.twinx()
    ax2.plot(prob, probcolor  ,linewidth=2, alpha=0.7) 
    ax2.set_yticks([0,0.2,0.4,0.6,0.8,1.0])
    #ax2.set_yticklabels(['0','1','2','3','4','5'])
    ax2.tick_params(axis='y', which='major', labelsize=20)
    ax2.grid(b=None, which='major', axis='y')
 
    ax1.plot(obs, obscolor, label='obs')  


def process_data(df, resample_time, resample_type):
    if resample_type == 'max':
       df = df.resample(resample_time).max()  
    elif resample_type == 'mean':
       df = df.resample(resample_time).mean()  
    elif resample_type == 'sum':
       df = df.resample(resample_time).sum()  
    else:
       print('Warning: resample_type not recognized', resample_type)
    return df


def make_talagrand(dflist,thresh,bnum,
                     resample_time=None,
                     resample_type='max',
                     rname='talagrand'):
    tal = Talagrand(thresh,bnum)
    for df in dflist:
        if resample_time:
           df = process_data(df,resample_time,resample_type)
        tal.add_data(df)
    #tal.plotrank(nbins=bnum)
    return tal

def make_reliability(dflist,thresh,bnum,
                     resample_time=None,
                     resample_type='max',
                     rname='reliability'):
    # seperate the observation column out.
    # bnum is number of bins in the reliability curve.
    
    # initialize reliability curve obejct.
    # num is number of bins to use.
    # here use one bin per simulation.
    rc = ReliabilityCurve(thresh, num=bnum)
    for df in dflist:
        if resample_time:
           df = process_data(df,resample_time,resample_type)

        obs_col = [x for x in df.columns if 'obs' in x]
        obs_col = obs_col[0]
        print(obs_col)
        obsdf = df[obs_col]
        df2 = df.drop([obs_col],axis=1)
        # not sure why take the transpose?
        num = len(df2.columns)
        df2 = df2.T
        # num is number of simulations.
         
        # gives percentage of simulations above threshold.
        prob = (df2[df2 > thresh].count())/num 
        plot_freq(obsdf, prob)
        plt.show()

        # add data to curve
        rc.reliability_add(obsdf, prob)
    # plot curve
    rc.reliability_plot(rname=rname) 
    return rc

class Talagrand:
    # get list of forecasts and order them.
    # find where in the list the observation would go.
    # p372 Wilks
    # if obs smaller than all forecasts then rank is 1
    # if obs is larger than all forecasts then rank is n_ens+1
    # calculate rank for each observation
    # create histogram.

    # simple way when there are not duplicat values of forecasts
    # is to just sort the list and find index of observation.

    # However when there are a lot of duplicate values then must
    # create the bins first and fill them as you go along. 

    # do we only look at observations above threshold?
    # What if multiple forecasts are the same? What rank is obs given?
    # This would occur in case of 0's usually. What if 10 forecasts are 0 and
    # observation is 0 and 5 forecasts are above 0? 
    # ANSWER: create the bins first - one for each forecast.
    # 

    def __init__(self, thresh,nbins):
        self.thresh = thresh
        self.ranklist = [] 
        self.obsvals = []
        # create bins for histogram.
        self.binra = np.zeros(nbins)
        # when obs are 0, count how many forecasts are 0.
        self.zeronum = []
        # when rank is 27, count how many forecasts 
        # are non-zero.
        # number which are 0 shows how many are completely missed.
        self.nonzero = []
        self.nonzerorow = []
        # value of obs which is higher than all forecasts
        self.obsmax = []
        # consider values with difference less than this the same.
        self.tolerance = 1e-2

    def plotrank(self, fname=None):
        sns.set_style('whitegrid')
        nbins = self.binra.shape[0] + 1
        xval = np.arange(1,nbins)
        plt.bar(xval,self.binra,alpha=0.5)
        plt.xlabel('Rank')
        plt.ylabel('Counts')
        plt.tight_layout() 
        if fname:
           plt.savefig('{}.png'.format(fname))
       
        

    def plotrank_old(self,nbins):
        sns.set()
        plt.hist(self.ranklist,bins=nbins,histtype='bar',
                 color='b',rwidth=0.9,density=True,align='mid')
        #plt.show()
        #plt.hist(self.obsvals,bins=nbins,histtype='bar',
        #         color='g',rwidth=0.9,density=True,align='mid')

    def add_data_temp(self,df):
        obs_col = [x for x in df.columns if 'obs' in x]
        obs_col = obs_col[0]
        # this keeps rows which have at least one value above threshold.
        df2 = df[(df>self.thresh).any(1)]
        for iii in np.arange(0,len(df2)):
            # selects row
            row = df2.iloc[iii]
            # sorts values
            row = row.sort_values()
            # creates dataframe with columns of index, name, value
            temp = pd.DataFrame(row).reset_index().reset_index()
            temp.columns = ['iii','name','val']
            # gets index of the observation
            # add one since index starts at 0.
            print(temp)
             
            rank = float(temp[temp.name==obs_col].iii) 
            obsval = float(temp[temp.name==obs_col].val)


 
    def add_data(self,df):
        # Assumes no duplicate values in forecast.
        # ToDO - should be able to apply to row so that the rank becomes
        # another column in the dataframe.
        obs_col = [x for x in df.columns if 'obs' in x]
        obs_col = obs_col[0]
        # this keeps rows which have at least one value above threshold.
        df2 = df[(df>self.thresh).any(1)]
        for iii in np.arange(0,len(df2)):
            # selects row
            row = df2.iloc[iii]
            # sorts values
            row = row.sort_values()
            # creates dataframe with columns of index, name, value
            temp = pd.DataFrame(row).reset_index().reset_index()
            temp.columns = ['iii','name','val']
            # gets index of the observation
            # add one since index starts at 0.
            
            # do not add +1 because now using it as index of self.binra.
            # which starts at 0. 
            rank = int(float(temp[temp.name==obs_col].iii))
            obsval = float(temp[temp.name==obs_col].val)


            temp['zval'] = np.abs(obsval - temp['val'])
            # should be one zero value where obs matches itself.
            # if multiple forecasts are within the tolerance then
            # point is split among them evenly.
            if len(temp[temp.zval <= self.tolerance]) > 1:
                val2add = 1.0 / len(temp[temp.zval<=tolerance]) 
                # indices of where forecasts match obs.
                rankvals = np.where(temp.zval<=self.tolerance)
                # add value to binra.
                #print(rankvals[0], type(rankvals))
                for rrr in rankvals[0]:
                    rrr = int(rrr)
                    #print('Adding to binra', rank, self.binra)
                    self.binra[rrr] += val2add

            # else just add one to position of obs value.
            else:
                #print('Adding to binra', rank)
                self.binra[rank] += 1

            # This is incorrect way. Making rank middle
            # of multiple 0 values. 
            if obsval < zero:
               rowz = row[row<zero]
               rank = int(len(rowz)/2.0)
               self.zeronum.append(len(rowz)-1)
      
            if rank == len(self.binra)-1:
               print('high val', row)
               rowz = row[row>zero]
               self.nonzero.append(len(rowz)-1)
               self.nonzerorow.append(row)
               self.obsmax.append(obsval)
 
            #print(rank)
            self.ranklist.append(rank)                
            self.obsvals.append(obsval)          

 
class ReliabilityCurve:

    def __init__(self, thresh, num):
        """
        thresh : float
        num : int or list of floats.

        Attributes
        self.binlist : list of floats from 0 to 1.

        self.yeshash : dictionary
                       key is bin number, value is number of times
                       obs above threshold for this bin.

        self.nohash  : dictionary
                       key is bin number, value is number of times obs
                       below threshold for this bin.
                   
        self.thresh  : float
 

        """
        # use num to define the bins
        if isinstance(num, int):
            self.binlist = list(np.arange(0,1, 1.0/num) + 1.0/(num*10))
            self.binlist.append(1)
        elif isinstance(num, list):
            self.binlist = num
        else: 
            self.binlist = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
     
        self.yeshash = {}
        self.nohash = {}
        for binval in self.binlist:
            self.yeshash[binval] = 0
            self.nohash[binval] = 0
  
        self.thresh = thresh
 
    def reliability_add(self, obs, prob):
        """

        """
        df = pd.concat([obs, prob], axis=1)
        df.dropna(axis=0, inplace=True)
        cols = ['obs','prob']
        df.columns = cols
        #print(type(df))
        #print(df[0:10])
        for index, row in df.iterrows():
            prob = row['prob'] 
            for pbin in self.binlist:
                if prob <= pbin: 
                   binval = pbin
                   #print('break', binval)
                   break 
            if row['obs'] >= self.thresh:
               self.yeshash[binval] += 1
            else:
               self.nohash[binval] += 1

    def reliability_plot(self,rname='reliability'):
        sns.set()
        sns.set_style("whitegrid")
        xxx = [] # the bin values for x axis
        yyy = [] # total number abo
        nnn = [] # total number
        yesval = []
        noval = []
        for binval in self.binlist:
            x = binval
            
            n = self.yeshash[binval] + self.nohash[binval]
            if n != 0:
                noval.append(self.nohash[binval])
                yesval.append(self.yeshash[binval])
                y = self.yeshash[binval] / n
                xxx.append(x)
                yyy.append(y)
                nnn.append(n)
            else:
                yesval.append(0)
                noval.append(0) 
                xxx.append(x)
                yyy.append(-0.1) 
                nnn.append(0)
        fig = plt.figure(1,figsize=(6,12))

        ax1 = fig.add_subplot(2,1,1)
        ax2 = fig.add_subplot(2,1,2)   
        ax1.plot(xxx,yyy, '-g.')
        ax1.plot([0,1], [0,1], '-k')
        ax2.plot(xxx, nnn)
        ax2.set_yscale('log')
        ax2.set_xlabel('Fraction model runs')
        ax1.set_ylabel('Fraction observations')
        ax2.set_ylabel('Number of points')
       
        plt.tight_layout()
        plt.savefig('{}.png'.format(rname))


        fig2 = plt.figure(2)
        ax3 = fig2.add_subplot(1,1,1)
        #with open('reliability.txt', 'w') as fid:
        #    fid.write(yesval)
        #    print(noval)
        #print('meas > thresh', yesval)
        #print('meas < thresh', noval)
        plt.plot(xxx, yesval, '-g.',label='Obs above')
        plt.plot(xxx, noval, '-r.',label='Obs below')
        plt.show()
