# -*- coding: utf-8 -*-
# Author: jlopes@alumni.usp.br
import os 
import numpy as np



class HeatMap():
    
    def __init__(self,**kwargs):
        self.__path = os.path.dirname(os.path.abspath(__file__))
        self.title = kwargs.get('title','Heat Map')
        self.annotation = kwargs.get('annotation',True)
        self.annotation_color = kwargs.get('annotation_color','k')
        self.fontsize = kwargs.get('fontsize',9)
        self.xrotation = kwargs.get('xrotation',45)
        self.cmap = kwargs.get('cmap','YlOrBr')
        
    
    def plot(self, x_labels,y_labels,values):
        """Shows a heat map plot from lists of values.
        :param  x_labels: A list of string labels for the x axis.
        :type   x_labels: list
        :param  y_labels: A list of string labels for the y axis.
        :type   y_labels: list
        :param  values: A list of int or float values.
        :type   values: list
        """
        import matplotlib
        values = np.array(values)
        fig, ax= matplotlib.pyplot.subplots()
        ax.set_title(self.title)
        ax.set_xticks(np.arange(len(x_labels)))
        ax.set_yticks(np.arange(len(y_labels)))
        ax.set_xticklabels(x_labels,fontsize=self.fontsize)
        ax.set_yticklabels(y_labels,fontsize=self.fontsize)
        matplotlib.pyplot.setp(ax.get_xticklabels(), rotation=self.xrotation, ha="right", rotation_mode="anchor")
        if self.annotation == True:
            for i in range(len(y_labels)):
                for j in range(len(x_labels)):
                    t = ax.text(j, i, values[i, j], ha="center", va="center", color=self.annotation_color)
        matplotlib.pyplot.imshow(values,norm=matplotlib.colors.LogNorm(),interpolation='nearest',cmap=self.cmap)
        matplotlib.pyplot.show()
            
        
class CollDist(object):
    
    def __init__(self):
        self.__path = os.path.dirname(os.path.abspath(__file__))
    
    def plot_colldist(self,left_freq,right_freq,**kwargs):
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
        import matplotlib.pyplot
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
        fig, ax = matplotlib.pyplot.subplots()
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
        matplotlib.pyplot.show()
        return matplotlib.pyplot
    

class CollGraph(object):
    
    def __init__(self,**kwargs):
        self.title = kwargs.get('title','Collocations')
        self.xlabel = kwargs.get('xlabel','position of the collocate')
        self.ylabel = kwargs.get('ylabel','strength of association')
        self.node = kwargs.get('node','node')
        self.cutoff = kwargs.get('cutoff',0.5)
        self.limit = kwargs.get('limit',20)
        self.stoplist = kwargs.get('stoplist',[])
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
        

    def __color(self,p):
        p = 100-p
        arr = np.array([c for c in self.__colors])
        idx = (np.abs(arr-p)).argmin()
        return self.__colors[arr[idx]] 
    
    def __normalize(self,value, max_value,min_value):
        norm = ((value-min_value) / (max_value-min_value)) * 100
        return norm
    
    def __distance(self,norm_stat):
        d = 50 - ( (norm_stat * 50) / 100)
        return d  
    
    def plot_graphcoll(self,collocates):
        data = []
        max_freq = collocates.df['FREQUENCY'].max()
        min_freq = collocates.df['FREQUENCY'].min()
        max_stat = collocates.df['ASSOCIATION'].max()  
        min_stat = collocates.df['ASSOCIATION'].min()
   
        for row in collocates.df.itertuples(index=False):
            if row[5] >= self.cutoff:
                if row[1] not in self.stoplist:
                    if len(row[1]) == 1 and str(row[1]).isalpha()== False:
                        pass 
                    else:
                        word = row[1]
                        norm_freq = self.__normalize(row[2], max_freq, min_freq)
                        norm_stat = self.__normalize(row[5], max_stat, min_stat)
                        distance = self.__distance(norm_stat)
                        if row[3] > row[4]:
                            side = 1
                        elif row[3] < row[4]:
                            side = 2
                        else:
                            side = 0
                        data.append((word,norm_freq,norm_stat,distance,side))
            
            if len(data) >= self.limit:
                break 
        self.plot(data)
                    
    
    def plot(self,data):
        import matplotlib.pyplot
        # set plot title
        matplotlib.pyplot.title(self.title)
        # set limits
        ax = matplotlib.pyplot.gca()
        ax.set_ylim([0,100])
        ax.set_xlim([0,100])
        # define x,y labels
        matplotlib.pyplot.xlabel(self.xlabel)
        matplotlib.pyplot.ylabel(self.ylabel)
        # place node line at the center
        matplotlib.pyplot.plot([50,50],[1,95],color='#9999ff', marker=',',linewidth=1)
        matplotlib.pyplot.plot([50], [95],color='#9999ff',marker=',', markersize=10, label=self.node)
        # set font
        font = {'family': 'Courier New',
        'color':  'black',
        'weight': 'normal',
        'size': 10,
        }
        # set position
        offset = 5
        xr = 100
        xl = 100
        y=100
        i = 0
        for d in data:
            i+=1
            # draw left 
            if d[4] == 1:
                y-= offset
                xl = 49 - d[3]
                matplotlib.pyplot.plot([xl,50],[y,y],color='#999999', marker='.',linewidth=0.1)
                matplotlib.pyplot.plot(xl, y,color=self.__color(d[1]),marker='o', markersize=10)
                matplotlib.pyplot.text((xl-3) - (len(d[0])*1.5),y-1,d[0],fontdict=font)
            # draw right    
            if d[4] == 2:
                y-= offset
                xr = 51 + d[3]
                matplotlib.pyplot.plot([50,xr],[y,y],color='#999999', marker='.',linewidth=0.1)
                matplotlib.pyplot.plot(xr, y,color=self.__color(d[1]),marker='o', markersize=10)
                matplotlib.pyplot.text(xr+2,y-1,d[0],fontdict=font)
            
        # show legend
        matplotlib.pyplot.legend(loc='best')
        matplotlib.pyplot.gca().axes.get_xaxis().set_visible(False)
        matplotlib.pyplot.gca().axes.get_yaxis().set_visible(False)
        # hide frame
        matplotlib.pyplot.box(False)
        # show plot
        matplotlib.pyplot.show()
        


_WORD_COLUMNS = ('WORD', 'N-GRAM', 'CLUSTER', 'LEMMA', 'P-FRAME', 'TYPE')
_VALUE_COLUMNS = ('FREQUENCY', 'KEYNESS', 'ASSOCIATION', 'RANGE', 'TOTAL')


def _wordcloud_items(data, word_column=None, value_column=None):
    """Normalises the input of wordcloud() into a list of (word, value)."""
    import re
    if isinstance(data, str):
        counts = {}
        for w in re.findall(r'\w+', data.lower()):
            counts[w] = counts.get(w, 0) + 1
        return list(counts.items())
    if isinstance(data, dict):
        return [(str(k), float(v)) for k, v in data.items()]
    df = getattr(data, 'df', data)
    columns = list(df.columns)
    if word_column is None:
        word_column = next((c for c in _WORD_COLUMNS if c in columns), None)
        if word_column is None:
            word_column = next(c for c in columns if df[c].dtype == object)
    if value_column is None:
        value_column = next((c for c in _VALUE_COLUMNS if c in columns), None)
        if value_column is None:
            value_column = next(c for c in columns if c != 'N' and df[c].dtype != object)
    return [(str(w), float(v)) for w, v in zip(df[word_column], df[value_column])]


def wordcloud(data, filename=None, **kwargs):
    """Draws a word cloud and returns it as a PIL image (saved as PNG when ``filename`` is given).

    data: a kitconc result object (wordlist, keywords, collocates, n-grams...), a DataFrame,
          a dict {word: value} or plain text.

    Keyword Arguments:
      word_column / value_column (str): Columns used for labels and sizes (detected automatically).
      max_words (int): Default is 150.
      width / height (int): Image size in pixels. Defaults are 1200 x 800.
      background (str): Background colour (default 'white').
      colormap (str): Matplotlib colormap name (default 'viridis').
      font_path (str): TrueType font (default: the bundled Ubuntu font).
      min_font_size / max_font_size (int): Defaults are 10 and height / 6.
      scale (str): 'sqrt' (default), 'linear' or 'log' mapping of values to font sizes.
      stoplist (iterable): Words to ignore.
      margin (int): Space around each word in pixels (default 2).
      seed (int): Random seed for colours (default 0).
    """
    from PIL import Image, ImageDraw, ImageFont
    import math
    import random

    max_words = kwargs.get('max_words', 150)
    width = int(kwargs.get('width', 1200))
    height = int(kwargs.get('height', 800))
    background = kwargs.get('background', 'white')
    colormap = kwargs.get('colormap', 'viridis')
    font_path = kwargs.get('font_path', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ubuntu.ttf'))
    min_font = int(kwargs.get('min_font_size', 10))
    max_font = int(kwargs.get('max_font_size', height // 6))
    scale = kwargs.get('scale', 'sqrt')
    margin = int(kwargs.get('margin', 2))
    stop = {str(w).lower() for w in (kwargs.get('stoplist') or [])}
    rng = random.Random(kwargs.get('seed', 0))

    items = _wordcloud_items(data, kwargs.get('word_column'), kwargs.get('value_column'))
    items = [(w, v) for w, v in items if v > 0 and w.strip() and w.lower() not in stop]
    items.sort(key=lambda x: x[1], reverse=True)
    items = items[:max_words]

    image = Image.new('RGB', (width, height), background)
    if not items:
        if filename:
            image.save(filename)
        return image

    def transform(v):
        if scale == 'log':
            return math.log1p(v)
        if scale == 'sqrt':
            return math.sqrt(v)
        return v

    vmax = transform(items[0][1])
    vmin = transform(items[-1][1])
    try:
        import matplotlib
        cmap = matplotlib.colormaps.get_cmap(colormap) if hasattr(matplotlib, 'colormaps') else matplotlib.cm.get_cmap(colormap)
    except Exception:
        cmap = None

    draw = ImageDraw.Draw(image)
    occupied = np.zeros((height, width), dtype=bool)
    cx, cy = width / 2.0, height / 2.0
    fonts = {}

    for word, value in items:
        rel = 1.0 if vmax == vmin else (transform(value) - vmin) / (vmax - vmin)
        size = int(min_font + rel * (max_font - min_font))
        placed = False
        while size >= min_font and not placed:
            font = fonts.get(size)
            if font is None:
                font = fonts[size] = ImageFont.truetype(font_path, size)
            left, top, right, bottom = draw.textbbox((0, 0), word, font=font)
            w, h = right - left + 2 * margin, bottom - top + 2 * margin
            if w < width and h < height:
                t = 0.0
                step = max(2.0, size / 6.0)
                while True:
                    r = 2.0 * t
                    if r > math.hypot(width, height) / 2:
                        break
                    x = int(cx + r * math.cos(t) * (width / height) - w / 2)
                    y = int(cy + r * math.sin(t) - h / 2)
                    t += step / max(r, step)
                    if x < 0 or y < 0 or x + w > width or y + h > height:
                        continue
                    if not occupied[y:y + h, x:x + w].any():
                        occupied[y:y + h, x:x + w] = True
                        if cmap is not None:
                            rgba = cmap(0.8 * rng.random())
                            color = tuple(int(255 * c) for c in rgba[:3])
                        else:
                            color = (0, 0, 0)
                        draw.text((x + margin - left, y + margin - top), word, font=font, fill=color)
                        placed = True
                        break
            if not placed:
                size = int(size * 0.85) if size > min_font else min_font - 1
    if filename:
        image.save(filename)
    return image
