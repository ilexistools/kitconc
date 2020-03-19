# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import pandas as pd
from io import StringIO
import xlsxwriter 
from kitconc.kit_plots import CollDist
from kitconc.kit_plots import CollGraph

class xStyles():
    
    def xls_columns_resize(self,worksheet,sizes):
        for k in sizes:
            worksheet.set_column(k+':'+k,sizes[k])
    
    def xls_header(self,workbook,font_name='Calibri',font_color='#003366',font_size=12,bold=True,align='center'):
        header_style = workbook.add_format({'bold': bold, 'font_color': font_color})
        header_style.set_font(font_name)
        header_style.set_font_size(font_size)
        header_style.set_align(align)
        return header_style 
    
    def xls_column_cells(self,workbook,font_name,font_color,font_size,bold,align):
        cell_style = workbook.add_format({'bold': bold, 'font_color': font_color})
        cell_style.set_font(font_name)
        cell_style.set_font_size(font_size)
        cell_style.set_align(align)
        return cell_style 

class Wordlist(object):
    
    def __init__(self,**kwargs):
        self.df = None
        self.tokens = kwargs.get('tokens',0)
        self.types = kwargs.get('types',0)
        self.typetoken=kwargs.get('typetoken',0)
        self.hapax=kwargs.get('hapax',0)
        self.encoding = kwargs.get('encoding','utf-8')
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
        return True 
     
    def save_excel(self,filename):
        # create Excel
        style = xStyles() # style object
        workbook = xlsxwriter.Workbook(filename,{'constant_memory': True})
        worksheet = workbook.add_worksheet()
        worksheet.name = 'Wordlist'
        # resize columns
        column_sizes = {'A':10, 'B':20,'C':15,'D':10,'E':3,'F':3,'G':3,'H':3,'I':3,'J':20,'K':20,'L':25,'M':20}
        style.xls_columns_resize(worksheet, column_sizes)
        # styles
        header_style = style.xls_header(workbook)
        n_style = style.xls_column_cells(workbook,'Tahoma','#404040',11,False,'center')
        word_style = style.xls_column_cells(workbook,'Tahoma','#b30000',11,False,'right')
        freq_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        p_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        info_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        # set headers
        worksheet.write('A1', 'N',header_style)
        worksheet.write('B1', 'WORD',header_style)
        worksheet.write('C1', 'FREQUENCY',header_style)
        worksheet.write('D1', '%',header_style)
        worksheet.write('J1', 'TOKENS',header_style)
        worksheet.write('K1', 'TYPES',header_style)
        worksheet.write('L1', 'TYPE-TOKEN RATIO',header_style)
        worksheet.write('M1', 'HAPAX',header_style)
        # set contents
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(row[0]),n_style)       # N
            worksheet.write(i,1, str(row[1]),word_style)    # WORD 
            worksheet.write(i,2, int(row[2]),freq_style)    # FREQ
            worksheet.write(i,3, float(row[3]),p_style)     # %
            if i == 1:
                # corpus info
                worksheet.write('J2', self.tokens ,info_style)
                worksheet.write('K2', self.types,info_style)
                worksheet.write('L2', self.typetoken,info_style)
                worksheet.write('M2', self.hapax,info_style)
        # close
        workbook.close()
        return True
    

class Keywords(object):

    def __init__(self,**kwargs):
        self.df = None
        self.encoding = kwargs.get('encoding','utf-8')
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
     
    def save_excel(self,filename):
        # create Excel
        style = xStyles() # style object
        workbook = xlsxwriter.Workbook(filename,{'constant_memory': True})
        worksheet = workbook.add_worksheet()
        worksheet.name = 'Keywords'
        # resize columns
        column_sizes = {'A':10, 'B':20,'C':15,'D':15}
        style.xls_columns_resize(worksheet, column_sizes)
        # styles
        header_style = style.xls_header(workbook)
        n_style = style.xls_column_cells(workbook,'Tahoma','#404040',11,False,'center')
        word_style = style.xls_column_cells(workbook,'Tahoma','#b30000',11,False,'right')
        freq_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        keyness_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        # set headers
        worksheet.write('A1', 'N',header_style)
        worksheet.write('B1', 'WORD',header_style)
        worksheet.write('C1', 'FREQUENCY',header_style)
        worksheet.write('D1', 'KEYNESS',header_style)
        # set contents
        i = 0
        for kv in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(i),n_style)
            worksheet.write(i,1, str(kv[1]),word_style)
            worksheet.write(i,2, int(kv[2]),freq_style)
            worksheet.write(i,3, float(kv[3]),keyness_style)
        # close
        workbook.close()
        return True 

class WTfreq(object):
    
    def __init__(self,**kwargs):
        self.df = None
        self.encoding = kwargs.get('encoding','utf-8')
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
    
    def save_excel(self,filename):
        # create Excel
        style = xStyles() # style object
        workbook = xlsxwriter.Workbook(filename,{'constant_memory': True})
        worksheet = workbook.add_worksheet()
        worksheet.name = 'WTfreq'
        # resize columns
        column_sizes = {'A':10, 'B':20,'C':20,'D':20,'E':10}
        style.xls_columns_resize(worksheet, column_sizes)
        # styles
        header_style = style.xls_header(workbook)
        n_style = style.xls_column_cells(workbook,'Tahoma','#404040',11,False,'center')
        word_style = style.xls_column_cells(workbook,'Tahoma','#b30000',11,False,'right')
        tag_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        freq_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        p_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        # set headers
        worksheet.write('A1', 'N',header_style)
        worksheet.write('B1', 'WORD',header_style)
        worksheet.write('C1', 'TAG',header_style)
        worksheet.write('D1', 'FREQUENCY',header_style)
        worksheet.write('E1', '%',header_style)
        # set contents
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(row[0]),n_style) # N
            worksheet.write(i,1, str(row[1]),word_style) # WORD
            worksheet.write(i,2, str(row[2]),tag_style) # TAG 
            worksheet.write(i,3, int(row[3]),freq_style) # FREQ
            worksheet.write(i,4, float(row[4]),p_style) # %
        # close    
        workbook.close()
        return True

class Wfreqinfiles(object):
    
    def __init__(self,**kwargs):
        self.df = None
        self.encoding = kwargs.get('encoding','utf-8')
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
    
    def save_excel(self,filename):
        # create Excel
        style = xStyles() # style object
        workbook = xlsxwriter.Workbook(filename,{'constant_memory': True})
        worksheet = workbook.add_worksheet()
        worksheet.name='Range'
        # resize columns
        column_sizes = {'A':10, 'B':20,'C':15,'D':10}
        style.xls_columns_resize(worksheet, column_sizes)
        # styles
        header_style = style.xls_header(workbook)
        n_style = style.xls_column_cells(workbook,'Tahoma','#404040',11,False,'center')
        word_style = style.xls_column_cells(workbook,'Tahoma','#b30000',11,False,'right')
        range_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        p_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        # set headers
        worksheet.write('A1', 'N',header_style)
        worksheet.write('B1', 'WORD',header_style)
        worksheet.write('C1', 'RANGE',header_style)
        worksheet.write('D1', '%',header_style)
        # set contents
        i = 0
        types = 0
        tokens=0
        for row in self.df.itertuples(index=False):
            i+=1
            types+=1
            tokens += int(row[2])
            worksheet.write(i,0, int(row[0]),n_style) # N
            worksheet.write(i,1, str(row[1]),word_style) # WORD 
            worksheet.write(i,2, int(row[2]),range_style) # RANGE
            worksheet.write(i,3, float(row[3]),p_style) # %
        # close
        workbook.close()
        return True  

class Kwic(object):
    
    class __KwicColors(object):
        def __init__(self):
            self.black = '#000000'
            self.blue = '#000099'
            self.brown = '#604020'
            self.green = '#008000'
            self.orange = '#cc5200'
            self.pink = '#ff0080'
            self.purple = '#990099'
            self.red = '#cc2900'
            self.white = '#ffffff'
            self.yellow='#e6e600' 
        
    def __init__(self,**kwargs):
        self.colors = self.__KwicColors()
        self.df = None
        self.encoding = kwargs.get('encoding','utf-8')
        self.node_length = kwargs.get('node_length',1)
        self.HIGHLIGHT_L1 = ['L1']
        self.HIGHLIGHT_L2 = ['L2']
        self.HIGHLIGHT_L3 = ['L3']
        self.HIGHLIGHT_R1 = ['R1']
        self.HIGHLIGHT_R2 = ['R2']
        self.HIGHLIGHT_R3 = ['R3']
        self.HIGHLIGHT_LEFT = 'L1 L2 L3'
        self.HIGHLIGHT_RIGHT = 'R1 R2 R3'
        
        
        """
        self.color_blue = '#000099'
        self.color_orange = '#cc5200'
        self.color_green = '#008000'
        self.color_brown = '#604020'
        self.color_red = '#cc2900'
        self.color_yellow='#e6e600'
        self.color_purple = '#990099'
        self.color_pink = '#ff0080'
        self.color_black = '#000000'
        self.color_white = '#ffffff'
        """
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
    
    def sort(self,first='R1',second='R2',third='R3'):
        horizon = ['L1','L2','L3','L4','L5','R1','R2','R3','R4','R5']
        # first
        if first == 'N':
            df1 = self.__get_node_column('Col1')
        elif first in horizon:
            df1= self.__get_column(first,'Col1')
        else:
            df1 = self.__get_node_column('Col1')
        # second
        if second != None:
            if second == 'N':
                df2 = self.__get_node_column('Col2')
            elif second in horizon:
                df2= self.__get_column(second,'Col2')
            else:
                df2= None
        else: 
            df2 = None
        # third
        if third != None:
            if third == 'N':
                df3 = self.__get_node_column('Col3')
            elif third in horizon:
                df3= self.__get_column(third,'Col3')
            else:
                df3= None
        else: 
            df3 = None 
        # add columns
        if df2 is not None and df3 is not None:
            self.df['Sort'] = df1['Col1'] +  df2['Col2'] + df3['Col3']
        elif df2 is None and df3 is not None:
            self.df['Sort'] = df1['Col1'] +  df3['Col3']
        elif df2 is not None and df3 is None:
            self.df['Sort'] = df1['Col1'] +  df2['Col2']
        elif df2 is None and df3 is None:
            self.df['Sort'] = df1['Col1'] 
        # sort
        self.df.sort_values(['Sort'], ascending=[True],inplace=True)
        
        self.df = self.df.drop('Sort',1)
        
        
    def __get_node_column(self,column_name):    
        data = []
        for row in self.df.itertuples():
            data.append((int(row[0]), str(row[3])))
        # create DataFrame
        df = pd.DataFrame(data, columns=['Idx',column_name])
        data = None
        return df
         
    def __get_column(self,col,column_name):
        # parse col
        h = str(col[0:1]).upper()
        p = int(col[-1:])
        # avoid p out of range
        if p > 5:
            p = 5
        elif p < 1:
            p = 1
        # adjust index 
        if h == 'L':
            idx = 5 - p
        elif h == 'R':
            idx = p-1  
        # get values
        data =[]
        i = 0
        for row in self.df.itertuples():
            i+=1
            # get horizon
            if h == 'L':
                hs = str(row[2]).split(' ')[-5:]
            elif h == 'R':
                hs = str(row[4]).split(' ')[0:5]
            else:
                hs = str(row[4]).split(' ')[0:5]
            if len(hs) < 5:
                for i in range(5-len(hs)):
                    hs.append(' ')
            # get column
            data.append((int(row[0]), hs[idx]))
        # create DataFrame
        df = pd.DataFrame(data, columns=['Idx',column_name])
        data = None
        
        
        return df 
    
    def __cleft(self,left,p1,p2,p3,h1,h2,h3,n_format,c):
        left = str(left)
        t = len(left)
        if t < c:
            left = ' ' * (c-t) + left 
        if t > c:
            left = left[(t-c):]
         
        arr = str(left).split(' ')
        new_arr = []
        for item in arr:
            new_arr.append([' ' + item,n_format])
            
        arr = None
        total = len(new_arr)
        
        if p1 is not None:
            new_arr[total - p1][1] = h1
        if p2 is not None:
            new_arr[total - p2][1] = h2
        if p3 is not None:
            new_arr[total - p3][1] = h3
        
        arr = []
        for item in new_arr:
            arr.append(item[1])
            arr.append(item[0])
        return arr 

    def __cright(self,right,p1,p2,p3,h1,h2,h3,n_format,c):
        right = str(right)
        t = len(right)
        if t > c:
            right = right[:c]
        
        arr = str(right).split(' ')
        new_arr = []
        for item in arr:
            new_arr.append([item + ' ',n_format])
            
        arr = None
        total = len(new_arr)
        
        
        if p1 is not None:
            if total > p1:
                new_arr[p1-1][1] = h1
                
        if p2 is not None:
            if total > p2:
                new_arr[p2-1][1] = h2
                
        if p3 is not None:
            if total > p3:
                new_arr[p3-1][1] = h3
        
        arr = []
        for item in new_arr:
            arr.append(item[1])
            arr.append(item[0])
        return arr
            
    def __norm(self,s):
        for r in [(' ,', ','), (' .', '.'),(' ;', ';'), (' ?', '?'),(' !', '!'),(' :', ':'), (' %', '%'),
                  (' )', ')'), ('( ', '('), (' ]', ']'), ('[ ', '['),(' }', '}'), ('{ ', '{')]:
            s = str(s).replace(r[0],r[1])
        return s
    
    def __nleft(self,s,c):
        s = self.__norm(s)
        t = len(s)
        if t < c:
            s = ' ' * (c-t) + s
        if t > c:
            s = s[(t-c):]
        return s
    
    def __nright(self,s,c):
        s = self.__norm(s)
        t = len(s)
        if t > c:
            s = s[:c]
        return s 

    def save_excel(self,filename,**kwargs):
        # args
        width = kwargs.get('width',50)
        cols = kwargs.get('highlight',None)
        left_colors = kwargs.get('left_colors',[self.colors.blue,self.colors.green, self.colors.orange])
        right_colors = kwargs.get('right_colors',[self.colors.blue,self.colors.green, self.colors.orange])
        
        if len (left_colors) < 3:
            while len(left_colors) < 3:
                left_colors.append(self.colors.blue)
        if len (right_colors) < 3:
            while len(right_colors) < 3:
                right_colors.append(self.colors.blue)
        if cols == None:
            lc = [None,None,None]
            rc = [None,None,None]
        else:
            lc = []
            rc = []
            if type(cols) != list:
                cols = cols.strip().split(' ')
            for item in cols:
                if item.startswith('L'):
                    lc.append(int(item[-1:]))
                if item.startswith('R'):
                    rc.append(int(item[-1:]))
            while len(lc) < 3:
                lc.append(None)
            while len(rc) < 3:
                rc.append(None)
        if lc == [None,None,None] and rc == [None,None,None]:
            kcolor = False
        else:
            kcolor = True
        # create Excel
        style = xStyles()
        workbook = xlsxwriter.Workbook(filename,{'constant_memory': True})
        worksheet = workbook.add_worksheet()
        worksheet.name = "KWIC"
        # resize columns
        column_sizes = {'A':10, 'B':150,'C':15,'D':10,'E':10,'F':10}
        style.xls_columns_resize(worksheet, column_sizes)
        # styles
        header_style = style.xls_header(workbook)
        n_style = style.xls_column_cells(workbook,'Tahoma','#404040',11,False,'center')
        node_style = style.xls_column_cells(workbook,'Courier New','#cc0066',10,True,'center')
        node_style.set_border(0)
        node_style.set_bottom_color('white')
        node_style.set_bg_color("white") 
        left_hf1_style = style.xls_column_cells(workbook,'Courier New',left_colors[0],10,True,'center')
        left_hf2_style = style.xls_column_cells(workbook,'Courier New',left_colors[1],10,True,'center')
        left_hf3_style = style.xls_column_cells(workbook,'Courier New',left_colors[2],10,True,'center')
        right_hf1_style = style.xls_column_cells(workbook,'Courier New',right_colors[0],10,True,'center')
        right_hf2_style = style.xls_column_cells(workbook,'Courier New',right_colors[1],10,True,'center')
        right_hf3_style = style.xls_column_cells(workbook,'Courier New',right_colors[2],10,True,'center')
        hor_style = style.xls_column_cells(workbook,'Courier New','#000000',10,False,'center')
        hor_style.set_border(0)
        hor_style.set_bottom_color('white')
        hor_style.set_bg_color("white")
        filename_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        token_id_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        sent_id_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        file_id_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        # set headers
        worksheet.write('A1', 'N',header_style)
        worksheet.write('B1', 'CONCORDANCE',header_style)
        worksheet.write('C1', 'FILENAME',header_style)
        worksheet.write('D1', 'TOKEN_ID',header_style)
        worksheet.write('E1', 'SENT_ID',header_style)
        worksheet.write('F1', 'FILE_ID',header_style)
        # set contents
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(row[0]),n_style) # N
            if kcolor == True:
                left = self.__cleft(row[1], lc[0], lc[1], lc[2], left_hf1_style,left_hf2_style,left_hf3_style, hor_style,width)
                right = self.__cright(row[3], rc[0], rc[1], rc[2], right_hf1_style,right_hf2_style,right_hf3_style, hor_style,width)
                whole = left + [node_style, ' ' + row[2] + ' '] + right
            else:
                whole = [hor_style, self.__nleft(row[1],width), node_style, ' ' + row[2] + ' ', hor_style, self.__nright(row[3],width)]
                worksheet.write_rich_string(i,1, *whole)   # CONCORDANCE
            worksheet.write_rich_string(i,1, *whole)       # CONCORDANCE
            worksheet.write(i,2, str(row[4]),filename_style) # FILENAME
            worksheet.write(i,3, int(row[5]),token_id_style) # TOKEN_ID
            worksheet.write(i,4, int(row[6]),sent_id_style) # SENT_ID
            worksheet.write(i,5, int(row[7]),file_id_style) # FILE_ID
        # close    
        workbook.close()
        return True
    

class Concordance(object):
    
    def __init__(self,**kwargs):
        self.df = None
        self.encoding = kwargs.get('encoding','utf-8')
        self.node_length = kwargs.get('node_length',1)
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
    
    def __norm(self,s):
        for r in [(' ,', ','), (' .', '.'),(' ;', ';'), (' ?', '?'),(' !', '!'),(' :', ':'), (' %', '%'),
                  (' )', ')'), ('( ', '('), (' ]', ']'), ('[ ', '['),(' }', '}'), ('{ ', '{')]:
            s = str(s).replace(r[0],r[1])
        return s

    def save_excel(self,filename,**kwargs):
        node_color = kwargs.get('node_color','#cc0066')
        # create Excel
        style = xStyles()
        workbook = xlsxwriter.Workbook(filename,{'constant_memory': True})
        worksheet = workbook.add_worksheet()
        worksheet.name = "CONCORDANCE"
        # resize columns
        column_sizes = {'A':10, 'B':150,'C':15,'D':10,'E':10,'F':10}
        style.xls_columns_resize(worksheet, column_sizes)
        # styles
        header_style = style.xls_header(workbook)
        n_style = style.xls_column_cells(workbook,'Tahoma','#404040',11,False,'center')
        node_style = style.xls_column_cells(workbook,'Courier New',node_color,10,True,'left')
        node_style.set_border(0)
        node_style.set_bottom_color('white')
        node_style.set_bg_color("white")
        hor_style = style.xls_column_cells(workbook,'Courier New','#000000',10,False,'left')
        hor_style.set_border(0)
        hor_style.set_bottom_color('white')
        hor_style.set_bg_color("white")
        filename_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        token_id_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        sent_id_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        file_id_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        # set headers
        worksheet.write('A1', 'N',header_style)
        worksheet.write('B1', 'CONCORDANCE',header_style)
        worksheet.write('C1', 'FILENAME',header_style)
        worksheet.write('D1', 'TOKEN_ID',header_style)
        worksheet.write('E1', 'SENT_ID',header_style)
        worksheet.write('F1', 'FILE_ID',header_style)
        # set contents
        def highlight(sentence,position,ns,hs):
            tokens = sentence.strip().split(' ')
            tokens_length = len(tokens)
            position = position - 1
            s = []
            # in the beginning
            if position == 0 :
                s = [ns,tokens[0] + ' '] + [hs,self.__norm(' '.join(tokens[1:]))]
            # in the end
            elif (position+1) == tokens_length:
                s = [hs,self.__norm(' '.join(tokens[:-1])) + ' '] + [ns,tokens[position]] 
            # in the middle
            else:
                s = [hs,self.__norm(' '.join(tokens[:position])) + ' '] + [ns,tokens[position]] +  [hs,' ' + self.__norm(' '.join(tokens[position+1:]))]
            return s 
        
        def highlight_multi(sentence,position,ns,hs):
            tokens = sentence.strip().split(' ')
            tokens_length = len(tokens)
            position = position - 1
            s = []
            # in the beginning
            if position == 0:
                s=[ns,self.__norm(' '.join(tokens[0:self.node_length]))] + [hs, ' ' + self.__norm(' '.join(tokens[self.node_length:]))]
            # in the end
            elif (position+self.node_length) == tokens_length:
                s = [hs,self.__norm(' '.join(tokens[:position])) + ' '] + [ns,self.__norm(' '.join(tokens[position:]))]
            # in the middle
            else:
                s = [hs,self.__norm(' '.join(tokens[:position])) + ' '] + [ns,self.__norm(' '.join(tokens[position:position + self.node_length]))] +  [hs,' ' + self.__norm(' '.join(tokens[position+self.node_length:]))]
            return s  
            
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            if self.node_length == 1:
                whole = highlight(row[1], row[3], node_style,hor_style)
            else:
                whole = highlight_multi(row[1], row[3], node_style,hor_style)
            worksheet.write(i,0, int(row[0]),n_style) # N
            worksheet.write_rich_string(i,1, *whole) # CONCORDANCE
            worksheet.write(i,2, str(row[2]),filename_style) # FILENAME
            worksheet.write(i,3, int(row[3]),token_id_style) # TOKEN_ID
            worksheet.write(i,4, int(row[4]),sent_id_style) # SENT_ID
            worksheet.write(i,5, int(row[5]),file_id_style) # FILE_ID
        # close
        workbook.close()
        return True 

class Collocates(object):
    
    def __init__(self,**kwargs):
        self.df = None
        self.encoding = kwargs.get('encoding','utf-8')
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
     
    def save_excel(self,filename):
        # create Excel
        style = xStyles()
        workbook = xlsxwriter.Workbook(filename,{'constant_memory': True})
        worksheet = workbook.add_worksheet()
        worksheet.name = 'Collocates'
        # resize columns
        column_sizes = {'A':10, 'B':20,'C':15,'D':15,'E':15,'F':15}
        style.xls_columns_resize(worksheet, column_sizes)
        # styles
        header_style = style.xls_header(workbook)
        n_style = style.xls_column_cells(workbook,'Tahoma','#404040',11,False,'center')
        word_style = style.xls_column_cells(workbook,'Tahoma','#b30000',11,False,'right')
        freq_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        left_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        right_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        association_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        # set headers
        worksheet.write('A1', 'N',header_style)
        worksheet.write('B1', 'WORD',header_style)
        worksheet.write('C1', 'FREQUENCY',header_style)
        worksheet.write('D1', 'LEFT',header_style)
        worksheet.write('E1', 'RIGHT',header_style)
        worksheet.write('F1', 'ASSOCIATION',header_style)
        # set contents
        # load wordlist
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(row[0]),n_style) # N
            worksheet.write(i,1, str(row[1]),word_style) # WORD 
            worksheet.write(i,2, int(row[2]),freq_style) # FREQ
            worksheet.write(i,3, float(row[3]),left_style) # LEFT
            worksheet.write(i,4, float(row[4]),right_style) # RIGHT
            worksheet.write(i,5, float(row[5]),association_style) # FORCE
        # close
        workbook.close()
        return True 
    
    def plot_collgraph(self,**kwargs):
        args_title = kwargs.get('title','Collocations')
        args_xlabel = kwargs.get('xlabel','position of the collocate')
        args_ylabel = kwargs.get('ylabel','strength of association')
        args_node = kwargs.get('node','node')
        args_cutoff = kwargs.get('cutoff',0.5)
        args_limit = kwargs.get('limit',20)
        args_stoplist = kwargs.get('stoplist',[])
        collgraph = CollGraph(title=args_title,xlabel=args_xlabel,ylabel=args_ylabel,node=args_node,
                                 cutoff=args_cutoff,limit=args_limit,stoplist=args_stoplist)
        collgraph.plot_graphcoll(self)


class Ngrams(object):
    
    def __init__(self,**kwargs):
        self.df = None
        self.encoding = kwargs.get('encoding','utf-8')
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
     
    def save_excel(self,filename):
        # create Excel
        style = xStyles()
        workbook = xlsxwriter.Workbook(filename,{'constant_memory': True})
        worksheet = workbook.add_worksheet()
        worksheet.name = 'N-grams'
        # resize columns
        column_sizes = {'A':10, 'B':35,'C':15,'D':15,'E':15}
        style.xls_columns_resize(worksheet, column_sizes)
        # styles
        header_style = style.xls_header(workbook)
        n_style = style.xls_column_cells(workbook,'Tahoma','#404040',11,False,'center')
        ngram_style = style.xls_column_cells(workbook,'Tahoma','#b30000',11,False,'right')
        freq_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        range_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        p_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        # set headers
        worksheet.write('A1', 'N',header_style)
        worksheet.write('B1', 'N-GRAM',header_style)
        worksheet.write('C1', 'FREQUENCY',header_style)
        worksheet.write('D1', 'RANGE',header_style)
        worksheet.write('E1', '%',header_style)
        # set contents
        # load wordlist
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(row[0]),n_style) # N
            worksheet.write(i,1, str(row[1]),ngram_style) # N-GRAM 
            worksheet.write(i,2, int(row[2]),freq_style) # FREQ
            worksheet.write(i,3, float(row[3]),range_style) # RANGE
            worksheet.write(i,4, float(row[4]),p_style) # %
        # close
        workbook.close()
        return True 

class Clusters(object):
    
    def __init__(self,**kwargs):
        self.df = None
        self.encoding = kwargs.get('encoding','utf-8')
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
     
    def save_excel(self,filename):
        # create Excel
        style = xStyles()
        workbook = xlsxwriter.Workbook(filename,{'constant_memory': True})
        worksheet = workbook.add_worksheet()
        worksheet.name = 'Clusters'
        # resize columns
        column_sizes = {'A':10, 'B':35,'C':15,'D':15,'E':15}
        style.xls_columns_resize(worksheet, column_sizes)
        # styles
        header_style = style.xls_header(workbook)
        n_style = style.xls_column_cells(workbook,'Tahoma','#404040',11,False,'center')
        cluster_style = style.xls_column_cells(workbook,'Tahoma','#b30000',11,False,'right')
        freq_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        range_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        p_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        # set headers
        worksheet.write('A1', 'N',header_style)
        worksheet.write('B1', 'CLUSTER',header_style)
        worksheet.write('C1', 'FREQUENCY',header_style)
        worksheet.write('D1', 'RANGE',header_style)
        worksheet.write('E1', '%',header_style)
        # set contents
        # load wordlist
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(row[0]),n_style) # N
            worksheet.write(i,1, str(row[1]),cluster_style) # CLUSTER 
            worksheet.write(i,2, int(row[2]),freq_style) # FREQ
            worksheet.write(i,3, float(row[3]),range_style) # RANGE
            worksheet.write(i,4, float(row[4]),p_style) # %
        # close
        workbook.close()
        return True 
    
class Dispersion(object):
    
    def __init__(self,**kwargs):
        self.df = None
        self.dpts = {}
        self.total_s1 = 0
        self.total_s2 = 0
        self.total_s3 = 0
        self.total_s4 = 0
        self.total_s5 = 0
        self.encoding = kwargs.get('encoding','utf-8')
        self.output_path = kwargs.get('output_path',None)
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
        
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
     
    def save_excel(self,filename):
        import os 
        import shutil 
        import PIL
        from PIL import ImageDraw
        # function
        def create_temp_folder(path):
            flag = True 
            try:
                if not os.path.exists(path):
                    if not os.path.isfile(path):
                        os.mkdir(path)
                flag = True 
            except:
                flag = False 
            return flag 
        # function
        def remove_temp_folder(path):
            flag = True 
            try:
                if os.path.exists(path):
                    if not os.path.isfile(path):
                        shutil.rmtree(path)
                        
                flag = True 
            except:
                flag = False 
            return flag
        # function
        def draw_barcode(points):
            # create rectangle
            im = PIL.Image.new('RGB', (201,19), (255,255,255))
            dr = PIL.ImageDraw.Draw(im)
            dr.rectangle(((0,0),(200,18)), fill="white", outline="blue")
            # draw lines
            for point in points:
                p = (point * 200)/100
                dr.line(((p,0),(p,18)), fill="black", width=1)
            # save file
            return im
        # create Excel
        style = xStyles()
        workbook = xlsxwriter.Workbook(filename,{'constant_memory': True})
        worksheet = workbook.add_worksheet()
        worksheet.name = 'Dispersion'
        # resize columns
        column_sizes = {'A':10, 'B':25,'C':10,'D':10,'E':8,'F':8,'G':8,'H':8,'I':8,'J':28,'K':1,'L':10,'M':10,'N':10}
        style.xls_columns_resize(worksheet, column_sizes)
        # styles
        header_style = style.xls_header(workbook)
        n_style = style.xls_column_cells(workbook,'Tahoma','#404040',11,False,'center')
        filename_style = style.xls_column_cells(workbook,'Tahoma','#b30000',11,False,'center')
        freq_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        zero_style = style.xls_column_cells(workbook,'Tahoma','#cccccc',11,False,'center')
        # set headers
        worksheet.write('A1', 'N',header_style)
        worksheet.write('B1', 'FILENAME',header_style)
        worksheet.write('C1', 'TOTAL',header_style)
        worksheet.write('D1', 'HITS',header_style)
        worksheet.write('E1', 'S1',header_style)
        worksheet.write('F1', 'S2',header_style)
        worksheet.write('G1', 'S3',header_style)
        worksheet.write('H1', 'S4',header_style)
        worksheet.write('I1', 'S5',header_style)
        worksheet.write('J1', 'PLOT',header_style)
        #worksheet.write('L1', 'SECTION',header_style)
        #worksheet.write('M1', 'HITS',header_style)
        #worksheet.write('N1', '%',header_style)
       
        total = float(self.total_s1 + self.total_s2 + self.total_s3 + self.total_s4 + self.total_s5)
        create_temp_folder(self.output_path + 'temp')
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(row[0]),n_style) # N
            worksheet.write(i,1, str(row[1]),filename_style) # FILENAME 
            worksheet.write(i,2, int(row[2]),freq_style) # TOTAL
            if row[3] == 0:
                worksheet.write(i,3, float(row[3]),zero_style) # HITS
            else:
                worksheet.write(i,3, float(row[3]),freq_style) # HITS
            
            if row[4] == 0:
                worksheet.write(i,4, float(row[4]),zero_style) # S1
            else:
                worksheet.write(i,4, float(row[4]),freq_style) # S1
            
            if row[5] == 0:
                worksheet.write(i,5, float(row[5]),zero_style) # S2
            else:
                worksheet.write(i,5, float(row[5]),freq_style) # S2
            
            if row[6] == 0:
                worksheet.write(i,6, float(row[6]),zero_style) # S3
            else:
                worksheet.write(i,6, float(row[6]),freq_style) # S3
                
            if row[7] == 0:
                worksheet.write(i,7, float(row[7]),zero_style) # S4
            else:
                worksheet.write(i,7, float(row[7]),freq_style) # S4
            
            if row[8] == 0:
                worksheet.write(i,8, float(row[8]),zero_style) # S5
            else:
                worksheet.write(i,8, float(row[8]),freq_style) # S5
            
            """
            # set section total contents
            if i == 2:
                #worksheet.write('L2', 'S1',header_style)
                worksheet.write('M2', int(self.total_s1),freq_style)
                worksheet.write('N2', round((self.total_s1 / total) * 100,2),freq_style)
            elif i == 3:
                #worksheet.write('L3', 'S2',header_style)
                worksheet.write('M3', int(self.total_s2),freq_style)
                worksheet.write('N3', round((self.total_s2 / total) * 100,2),freq_style)
            elif i == 4:
                #worksheet.write('L4', 'S3',header_style)
                worksheet.write('M4', int(self.total_s3),freq_style)
                worksheet.write('N4', round((self.total_s3 / total) * 100,2),freq_style)
            elif i == 5:
                #worksheet.write('L5', 'S4',header_style)
                worksheet.write('M5', int(self.total_s4),freq_style)
                worksheet.write('N5', round((self.total_s4 / total) * 100,2),freq_style)
            elif i == 6:
                #worksheet.write('L6', 'S5',header_style)
                worksheet.write('M6', int(self.total_s5),freq_style)
                worksheet.write('N6', round((self.total_s5 / total) * 100,2),freq_style)
            """
            
            img = draw_barcode(self.dpts[row[1]])
            img.save(self.output_path + 'temp/' + str(i) + '.jpg')
            worksheet.insert_image('J' + str(i+1), self.output_path + 'temp/' + str(i) + '.jpg')
            
            
            
            
            
            
            
             
                
            
        # close
        workbook.close()
        remove_temp_folder(self.output_path + 'temp')
        return True 
        
class KeywordsDispersion(object):
    
    def __init__(self,**kwargs):
        self.df = None
        self.dpts = {}
        self.total_s1 = 0
        self.total_s2 = 0
        self.total_s3 = 0
        self.total_s4 = 0
        self.total_s5 = 0
        self.encoding = kwargs.get('encoding','utf-8')
        self.output_path = kwargs.get('output_path',None)
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
        
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
     
    def save_excel(self,filename):
        import os 
        import shutil 
        import PIL
        from PIL import ImageDraw
        # function
        def create_temp_folder(path):
            flag = True 
            try:
                if not os.path.exists(path):
                    if not os.path.isfile(path):
                        os.mkdir(path)
                flag = True 
            except:
                flag = False 
            return flag 
        # function
        def remove_temp_folder(path):
            flag = True 
            try:
                if os.path.exists(path):
                    if not os.path.isfile(path):
                        shutil.rmtree(path)
                flag = True 
            except:
                flag = False 
            return flag
        # function
        def draw_barcode(points):
            # create rectangle
            im = PIL.Image.new('RGB', (201,19), (255,255,255))
            dr = PIL.ImageDraw.Draw(im)
            dr.rectangle(((0,0),(200,18)), fill="white", outline="blue")
            # draw lines
            for point in points:
                p = (point * 200)/100
                dr.line(((p,0),(p,18)), fill="black", width=1)
            # save file
            return im
        # create Excel
        style = xStyles()
        workbook = xlsxwriter.Workbook(filename,{'constant_memory': True})
        worksheet = workbook.add_worksheet()
        worksheet.name = 'Keywords Dispersion'
        # resize columns
        column_sizes = {'A':10, 'B':25,'C':10,'D':10,'E':8,'F':8,'G':8,'H':8,'I':8,'J':28,'K':7,'L':7,'M':7,'N':7,'O':7}
        style.xls_columns_resize(worksheet, column_sizes)
        # formats
        header_style = style.xls_header(workbook)
        n_style = style.xls_column_cells(workbook,'Tahoma','#404040',11,False,'center')
        word_style = style.xls_column_cells(workbook,'Tahoma','#b30000',11,False,'center')
        freq_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        zero_style = style.xls_column_cells(workbook,'Tahoma','#cccccc',11,False,'center')
        # set headers
        worksheet.write('A1', 'N',header_style)
        worksheet.write('B1', 'WORD',header_style)
        worksheet.write('C1', 'KEYNESS',header_style)
        worksheet.write('D1', 'HITS',header_style)
        worksheet.write('E1', 'S1',header_style)
        worksheet.write('F1', 'S2',header_style)
        worksheet.write('G1', 'S3',header_style)
        worksheet.write('H1', 'S4',header_style)
        worksheet.write('I1', 'S5',header_style)
        worksheet.write('J1', 'PLOT',header_style)
        worksheet.write('K1', 'S1%',header_style)
        worksheet.write('L1', 'S2%',header_style)
        worksheet.write('M1', 'S3%',header_style)
        worksheet.write('N1', 'S4%',header_style)
        worksheet.write('O1', 'S5%',header_style)
        # set contents
        create_temp_folder(self.output_path + 'temp')
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(row[0]),n_style) # N
            worksheet.write(i,1, str(row[1]),word_style) # WORD 
            worksheet.write(i,2, float(row[2]),freq_style) # KEYNESS
            if row[3] == 0:
                worksheet.write(i,3, float(row[3]),zero_style) # HITS
            else:
                worksheet.write(i,3, float(row[3]),freq_style) # HITS
            if row[4] == 0:
                worksheet.write(i,4, float(row[4]),zero_style) # S1
            else:
                worksheet.write(i,4, float(row[4]),freq_style) # S1
            if row[5] == 0:
                worksheet.write(i,5, float(row[5]),zero_style) # S2
            else:
                worksheet.write(i,5, float(row[5]),freq_style) # S2
            if row[6] == 0:
                worksheet.write(i,6, float(row[6]),zero_style) # S3
            else:
                worksheet.write(i,6, float(row[6]),freq_style) # S3
            if row[7] == 0:
                worksheet.write(i,7, float(row[7]),zero_style) # S4
            else:
                worksheet.write(i,7, float(row[7]),freq_style) # S4
            if row[8] == 0:
                worksheet.write(i,8, float(row[8]),zero_style) # S5
            else:
                worksheet.write(i,8, float(row[8]),freq_style) # S5
            img = draw_barcode(self.dpts[row[1]])
            img.save(self.output_path + 'temp/' + str(i) + '.jpg')
            worksheet.insert_image('J' + str(i+1), self.output_path + 'temp/' + str(i) + '.jpg')
            s1 = round((row[4]/row[3])*100,2)
            s2 = round((row[5]/row[3])*100,2)
            s3 = round((row[6]/row[3])*100,2)
            s4 = round((row[7]/row[3])*100,2)
            s5 = round((row[8]/row[3])*100,2)
            
            if s1 <=0:
                worksheet.write(i,10, s1,zero_style) # S1%
            else:
                worksheet.write(i,10, s1,freq_style) # S1%
            
            if s2 <=0:
                worksheet.write(i,11, s2,zero_style) # S2%
            else:
                worksheet.write(i,11, s2,freq_style) # S2%
            
            if s3 <=0:
                worksheet.write(i,12, s3,zero_style) # S3%
            else:
                worksheet.write(i,12, s3,freq_style) # S3%
            
            if s4 <=0:
                worksheet.write(i,13, s4,zero_style) # S4%
            else:
                worksheet.write(i,13, s4,freq_style) # S4%
            
            if s5 <=0:
                worksheet.write(i,14, s5,zero_style) # S5%
            else:
                worksheet.write(i,14, s5,freq_style) # S5%
            
            
        # close
        workbook.close()
        remove_temp_folder(self.output_path + 'temp')
        return True
    
class Keynessxrange(object):
    
    def __init__(self,**kwargs):
        self.df = None
        self.encoding = kwargs.get('encoding','utf-8')
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
     
    def save_excel(self,filename):
        # create Excel
        style = xStyles()
        workbook = xlsxwriter.Workbook(filename,{'constant_memory': True})
        worksheet = workbook.add_worksheet()
        worksheet.name = 'KeywordsxRange'
        # resize columns
        column_sizes = {'A':10, 'B':20,'C':15,'D':15}
        style.xls_columns_resize(worksheet, column_sizes)
        # styles
        header_style = style.xls_header(workbook)
        n_style = style.xls_column_cells(workbook,'Tahoma','#404040',11,False,'center')
        word_style = style.xls_column_cells(workbook,'Tahoma','#b30000',11,False,'right')
        freq_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        key_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        # set headers
        worksheet.write('A1', 'N',header_style)
        worksheet.write('B1', 'WORD',header_style)
        worksheet.write('C1', 'FREQUENCY',header_style)
        worksheet.write('D1', 'KEYNESS',header_style)
        # set contents
        i = 0
        for kv in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(i),n_style)
            worksheet.write(i,1, kv[1],word_style)
            worksheet.write(i,2, kv[2],freq_style)
            worksheet.write(i,3, kv[3],key_style)
        # close
        workbook.close()
        return True


class ComparedCollocates(object):
    
    def __init__(self,**kwargs):
        self.df = None
        self.encoding = kwargs.get('encoding','utf-8')
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
     
    def save_excel(self,filename):
        # create Excel
        style = xStyles()
        workbook = xlsxwriter.Workbook(filename,{'constant_memory': True})
        worksheet = workbook.add_worksheet()
        worksheet.name = 'Comparison'
        # resize columns
        column_sizes = {'A':10, 'B':20,'C':10,'D':10,'E':15,'F':15,'G':12}
        style.xls_columns_resize(worksheet, column_sizes)
        # styles
        header_style = style.xls_header(workbook)
        n_style = style.xls_column_cells(workbook,'Tahoma','#404040',11,False,'center')
        word_style = style.xls_column_cells(workbook,'Tahoma','#b30000',11,False,'right')
        freq_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        # set headers
        worksheet.write('A1', 'N',header_style)
        worksheet.write('B1', 'WORD',header_style)
        worksheet.write('C1', 'FREQ1',header_style)
        worksheet.write('D1', 'FREQ2',header_style)
        worksheet.write('E1', 'ASSOCIATION1',header_style)
        worksheet.write('F1', 'ASSOCIATION2',header_style)
        worksheet.write('G1', 'DIFFERENCE',header_style)
        # set contents
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(row[0]),n_style) # N
            worksheet.write(i,1, str(row[1]),word_style) # WORD 
            worksheet.write(i,2, int(row[2]),freq_style) # FREQ1
            worksheet.write(i,3, int(row[3]),freq_style) # FREQ2
            worksheet.write(i,4, float(row[4]),freq_style) # AM1
            worksheet.write(i,5, float(row[5]),freq_style) # AM2
            worksheet.write(i,6, float(row[6]),freq_style) # PD
        # close
        workbook.close()
        return True

class Collocations(object):
    
    def __init__(self,**kwargs):
        self.df = None
        self.encoding = kwargs.get('encoding','utf-8')
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
     
    def save_excel(self,filename):
        # create Excel
        style = xStyles()
        workbook = xlsxwriter.Workbook(filename,{'constant_memory': True})
        worksheet = workbook.add_worksheet()
        worksheet.name = 'Collocations'
        # resize columns
        column_sizes = {'A':10, 'B':20,'C':7,'D':7,'E':7,'F':7,'G':7,'H':4,'I':7,'J':7,
                        'K':7,'L':7,'M':7,'N':8,'O':8,'P':8,'Q':15}
        style.xls_columns_resize(worksheet, column_sizes)
        # formats
        header_style = style.xls_header(workbook)
        n_style = style.xls_column_cells(workbook,'Tahoma','#404040',11,False,'center')
        word_style = style.xls_column_cells(workbook,'Tahoma','#b30000',11,False,'right')
        freq_style = style.xls_column_cells(workbook,'Tahoma','#000000',11,False,'center')
        # set headers
        worksheet.write('A1', 'N',header_style)
        worksheet.write('B1', 'WORD',header_style)
        worksheet.write('C1', 'L5',header_style)
        worksheet.write('D1', 'L4',header_style)
        worksheet.write('E1', 'L3',header_style)
        worksheet.write('F1', 'L2',header_style)
        worksheet.write('G1', 'L1',header_style)
        worksheet.write('H1', 'N',header_style)
        worksheet.write('I1', 'R1',header_style)
        worksheet.write('J1', 'R2',header_style)
        worksheet.write('K1', 'R3',header_style)
        worksheet.write('L1', 'R4',header_style)
        worksheet.write('M1', 'R5',header_style)
        worksheet.write('N1', 'LEFT',header_style)
        worksheet.write('O1', 'RIGHT',header_style)
        worksheet.write('P1', 'TOTAL',header_style)
        worksheet.write('Q1', 'ASSOCIATION',header_style)
        # set contents
        # add data
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(row[0]),n_style) # N
            worksheet.write(i,1, str(row[1]),word_style) # WORD 
            worksheet.write(i,2, int(row[2]),freq_style) # L5
            worksheet.write(i,3, int(row[3]),freq_style) # L4
            worksheet.write(i,4, int(row[4]),freq_style) # L3
            worksheet.write(i,5, int(row[5]),freq_style) # L2
            worksheet.write(i,6, int(row[6]),freq_style) # L1
            worksheet.write(i,7,  '*' ,freq_style) # N
            worksheet.write(i,8, int(row[7]),freq_style) # R1
            worksheet.write(i,9, int(row[8]),freq_style) # R2
            worksheet.write(i,10, int(row[9]),freq_style) # R3
            worksheet.write(i,11, int(row[10]),freq_style) # R4
            worksheet.write(i,12, int(row[11]),freq_style) # R5
            worksheet.write(i,13, int(row[12]),freq_style) # LEFT
            worksheet.write(i,14, int(row[13]),freq_style) # RIGHT
            worksheet.write(i,15, int(row[14]),freq_style) # TOTAL
            worksheet.write(i,16, float(row[15]),freq_style) # ASSOCIATION
        # close
        workbook.close()
        return True 
    
    def plot_colldist(self,word,**kwargs):
        results = self.df.loc[self.df['WORD'] == word].values.tolist()[0]
        if len(results) != 0:
            title = kwargs.get('title','Distribution of "' + word + '"')
            show_values = kwargs.get('show_values',False)
            xlabel = kwargs.get('xlabel','Horizon')
            ylabel = kwargs.get('ylabel','Frequency')
            colldist = CollDist()
            left = list(reversed(results[2:7]))
            right = results[7:12]
            colldist.plot_colldist(left,right,title=title,show_values=show_values,xlabel=xlabel,ylabel=ylabel)
            
        
        
        
      
    
        
        
    
        
    
        
        
    
    
    
    
        
        
        
        