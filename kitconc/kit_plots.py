# -*- coding: utf-8 -*-
import os 
import numpy as np
import matplotlib.pyplot as plt
import math 



class CollocatesDistribution(object):
    
    def __init__(self):
        self.__path = os.path.dirname(os.path.abspath(__file__))
    
    def plot_collocates_distribution(self,left_freq,right_freq,**kwargs):
        """
        Returns a plot to show the distribution of a collocate.
        Ex.:
        plt = distribution_of_collocate([10,15,30],[20,5,35]) 
        args:
        - left_freq: list of left frequencies
        - right_freq: list of right frequencies 
        kwargs:
        title, label,xlabel, ylabel, left_labels, right_labels
        bar_line_color,bar_fill_color, opacity
        show_values, values_color 
        """
        # kwargs - colors
        opacity = kwargs.get('opacity',1)
        bar_line_color = kwargs.get('bar_line_color','black')
        bar_fill_color = kwargs.get('bar_fill_color','white')
        # kwargs - labels
        title = kwargs.get('title','Distribution')
        label = kwargs.get('label','...')
        xlabel = kwargs.get('xlabel','Horizon')
        ylabel = kwargs.get('ylabel','Frequency')
        left_labels = kwargs.get('left_labels',['L1','L2','L3','L4','L5'])
        right_labels = kwargs.get('right_labels',['R1','R2','R3','R4','R5'])
        # kwargs - values
        show_values = kwargs.get('show_values',False)
        values_color = kwargs.get('values_color','black')
        # arrange data
        total_left = 5
        total_right = 5
        n_groups = total_left + total_right + 1
        hlabels = []
        hfreqs = []
        i=0
        for freq in left_freq:
            hfreqs.append(freq)
            hlabels.append(left_labels[i])
            i+=1
        if len(left_freq) < 5:
            while len(hfreqs) < 5:
                hfreqs.append(0)
                hlabels.append('-')
        hfreqs = list(reversed(hfreqs))
        hlabels = list(reversed(hlabels))
        hfreqs.append(0)
        hlabels.append('N')
        i=0
        for freq in right_freq:
            hfreqs.append(freq)
            hlabels.append(right_labels[i])
            i+=1
        if len(right_freq) <5:
            while len(hfreqs) < 11:
                hfreqs.append(0)
                hlabels.append('-')
        # make bars
        std_hor = (0,0,0,0,0,0,0,0,0,0,0)
        fig, ax = plt.subplots()
        index = np.arange(n_groups)
        bar_width = 0.55
        error_config = {'ecolor': '0.4'}
        ax.bar(index, hfreqs, bar_width,
                        alpha=opacity, edgecolor=bar_line_color,color=bar_fill_color,
                        yerr=std_hor,error_kw=error_config,label=label)
        # format
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xticks(index + 0.01)
        ax.set_xticklabels(hlabels)
        ax.legend()
        # check show values
        if show_values == True:
            j = 0
            for i, v in enumerate(hfreqs):
                j+=1
                if v !=0:
                    if j == 6:
                        ax.text((i + (bar_width/2) ) - bar_width, v + 0.3, ' ', color=values_color)
                    else:
                        ax.text((i + (bar_width/2) ) - bar_width, v + 0.3, str(v), color=values_color)
        # show plot
        fig.tight_layout()
        plt.show()
        return plt
    


class CollocationGraph(object):
    
    def __init__(self,**kwargs):
        self.title = kwargs.get('title','Collocations')
        self.xlabel = kwargs.get('xlabel','position of the collocate')
        self.ylabel = kwargs.get('ylabel','strength of association')
        self.node = kwargs.get('node','node')
        self.cutoff = kwargs.get('cutoff',3)
        self.limit = kwargs.get('limit',25)
        self.__load_colors()
        
    
    def __load_colors(self):
        self.__colors = {
            0 : '#000000', 5:  '#0d0d0d', 10: '#1a1a1a', 15: '#262626',
            20: '#333333', 25: '#404040', 30: '#4d4d4d', 35: '#595959',
            40: '#666666', 45: '#737373', 50: '#808080', 55: '#8c8c8c',
            60: '#999999', 65: '#a6a6a6', 70: '#b3b3b3', 75: '#bfbfbf',
            80: '#cccccc', 85: '#d9d9d9', 90: '#e6e6e6', 95: '#f2f2f2', 
            100: '#ffffff', 
            }
        
    
    def __get_position(self,distance,angle):
        radians = angle * math.pi / 180.0
        x = (distance * math.cos(radians)) + 50
        y = (distance * math.sin(radians)) + 50
        return (x,y)

    def __pick_color(self,p):
        arr = np.array([c for c in self.__colors])
        p = 100-p
        arr = np.array([c for c in self.__colors])
        idx = (np.abs(arr-p)).argmin()
        return self.__colors[arr[idx]] 
    

    def __normalize_freq(self,x_freq,max_freq,min_freq):
        norm  = (x_freq - min_freq) / (max_freq-min_freq)
        norm = norm * 100
        return norm 

    def __normalize_stat(self,x_stat,max_stat,min_stat):
        max_stat += 2.5
        norm  = (x_stat - min_stat) / (max_stat-min_stat)
        norm = norm * 100
        return norm
    
    def __get_distance(self,norm_stat):
        distance = 50
        if (norm_stat/2) > 50:
            distance = (norm_stat/2)-50
        else:
            distance = 50 - (norm_stat/2)
        return distance
    
    def __get_angle(self,right_norm_freq):
        angle = (100 - right_norm_freq) * 1.8
        return angle 
    
    def __get_angle2(self,x1,x2,y1,y2):
        deltaX = x2-x1 
        deltaY = y2-y1
        radians = math.atan2(deltaY, deltaX)
        angle = radians * (180 /math.pi)
        return angle

    def plot_graphcoll(self,collocates):
        max_freq = collocates.df['FREQUENCY'].max()
        min_freq = collocates.df['FREQUENCY'].min()
        max_stat = collocates.df['ASSOCIATION'].max()  
        min_stat = collocates.df['ASSOCIATION'].min()
        
        pos = []
        for i in range (0,105,10):
            pos.append(105-i)
        
        #print(pos)
        
        data = []
        i = 0
        for row in collocates.df.itertuples(index=False):
            
            if row[5] >= self.cutoff:
                i+=1    
                word = row[1]
                norm_freq = self.__normalize_freq(row[2], max_freq, min_freq) 
                norm_stat = self.__normalize_stat(row[5]  ,max_stat,min_stat) 
                norm_right_freq = (row[4] / (row[4]+row[3]))*100
                angle = self.__get_angle2(50,norm_right_freq, 50, pos[i])
                distance = self.__get_distance(norm_stat)
                position = self.__get_position(distance, angle)
                d = (word,norm_freq,position[0],position[1])
                data.append(d)
                #print(d)
                
                if i == self.limit:
                    break 
            
        self.plot(data)
    
        
    
    def plot(self,data):
        # set plot title
        plt.title(self.title)
        # set limits
        ax = plt.gca()
        ax.set_ylim([0,100])
        ax.set_xlim([0,100])
        # define x,y labels
        plt.xlabel(self.xlabel)
        plt.ylabel(self.ylabel)
        
        # add collocates here:
        for d in data:
            plt.plot([50,d[2]],[50,d[3]],color='#999999', marker='.',linewidth=0.5)
            plt.plot(d[2], d[3],color=self.__pick_color(d[1]),marker='o', markersize=10)
            plt.annotate(d[0],xy=(d[2]+2,d[3]-1))
        # place node at the center
        plt.plot([50], [50],color='#9999ff',marker='o', markersize=10, label=self.node)
        # show legend
        plt.legend(loc='best')
        #plt.xticks([])
        #plt.yticks([])
        plt.gca().axes.get_xaxis().set_visible(False)
        plt.gca().axes.get_yaxis().set_visible(False)

        # show plot
        plt.show() 
    
        
