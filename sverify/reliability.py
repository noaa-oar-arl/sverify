import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
           
class ReliabilityCurve:

    def __init__(self, thresh, num):
        """
        thresh : float
        num : int or list of floats.

        Attributes
        self.binlist : list of floats from 0 to 1.
        self.yeshash : dictionary
                       key is bin number, value is number of times agreement
        self.nohash  : dictionary
                       key is bin number, value is number of times disagreement
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
        print('BINLIST ', self.binlist)
     
        self.yeshash = {}
        self.nohash = {}
        for binval in self.binlist:
            self.yeshash[binval] = 0
            self.nohash[binval] = 0
  
        self.thresh = thresh
 
    def reliability_add(self, obs, prob):
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

    def reliability_plot(self):
        xxx = []
        yyy = []
        nnn = []
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
        fig = plt.figure(1)
        ax1 = fig.add_subplot(2,1,1)
        ax2 = fig.add_subplot(2,1,2)   
        ax1.plot(xxx,yyy, '-g.')
        ax1.plot([0,1], [0,1], '-k')
        ax2.plot(xxx, nnn)
        ax2.set_yscale('log')
        plt.savefig('reliability.png')
        fig2 = plt.figure(2)
        ax3 = fig2.add_subplot(1,1,1)
        #with open('reliability.txt', 'w') as fid:
        #    fid.write(yesval)
        #    print(noval)
        print('meas > thresh', yesval)
        print('meas < thresh', noval)
        plt.plot(xxx, yesval, '-g.')
        plt.plot(xxx, noval, '-r.')
        plt.show()
        plt.show()
