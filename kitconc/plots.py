# -*- coding: utf-8 -*-
import os 
import numpy as np
import matplotlib.pyplot as plt

class Plots(object):
    
    def __init__(self):
        self.__path = os.path.dirname(os.path.abspath(__file__))
    
    
    def collocates_distribution(self,left_freq,right_freq,**kwargs):
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
    
    
        
