# -*- coding: utf-8 -*-
import pandas as pd
from io import StringIO
import xlsxwriter 


class KwicColors(object):
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


class Kwic(object):
    
    def __init__(self,**kwargs):
        self.colors = KwicColors()
        self.df = None
        self.encoding = kwargs.get('encoding','utf-8')
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
         
    
    def save_xls(self,filename,**kwargs):
        width = kwargs.get('width',65)
        cols = kwargs.get('cols',None)
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
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        worksheet.name = "Page 01"
        
        # resize columns
        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 150)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 10)
        worksheet.set_column('E:E', 10)
        worksheet.set_column('F:F', 10)
        
        # formats
        headers_format = workbook.add_format({'bold': True, 'font_color': '#003366'})
        headers_format.set_font("Calibri")
        headers_format.set_font_size(12)
        headers_format.set_align('center')
        
        node_format = workbook.add_format({'bold': True, 'font_color': '#cc0066'})
        node_format.set_font("Courier New")
        node_format.set_font_size(10)
        node_format.set_align('center')
        node_format.set_border(0)
        node_format.set_bottom_color('white')
        node_format.set_bg_color("white")
        
        left_hf1 = workbook.add_format({'bold': False, 'font_color': left_colors[0] })
        left_hf1.set_font("Courier New")
        left_hf1.set_font_size(10)
        left_hf1.set_align('center')
        
        
        left_hf2 = workbook.add_format({'bold': False, 'font_color': left_colors[1]})
        left_hf2.set_font("Courier New")
        left_hf2.set_font_size(10)
        left_hf2.set_align('center')
        
        left_hf3 = workbook.add_format({'bold': False, 'font_color': left_colors[2]})
        left_hf3.set_font("Courier New")
        left_hf3.set_font_size(10)
        left_hf3.set_align('center')
        
        
        right_hf1 = workbook.add_format({'bold': False, 'font_color': right_colors[0]})
        right_hf1.set_font("Courier New")
        right_hf1.set_font_size(10)
        right_hf1.set_align('center')
        
        
        right_hf2 = workbook.add_format({'bold': False, 'font_color': right_colors[1]})
        right_hf2.set_font("Courier New")
        right_hf2.set_font_size(10)
        right_hf2.set_align('center')
        
        right_hf3 = workbook.add_format({'bold': False, 'font_color': right_colors[2]})
        right_hf3.set_font("Courier New")
        right_hf3.set_font_size(10)
        right_hf3.set_align('center')
        
        
        hor_format = workbook.add_format({'bold': False, 'font_color': '#000000'})
        hor_format.set_font("Courier New")
        hor_format.set_font_size(10)
        hor_format.set_align('center')
        hor_format.set_border(0)
        hor_format.set_bottom_color('white')
        hor_format.set_bg_color("white")
        
        
        col_A_format = workbook.add_format({'bold': False, 'font_color': '#404040'})
        col_A_format.set_font("Tahoma")
        col_A_format.set_font_size(11)
        col_A_format.set_align('center')
        
        col_B_format = workbook.add_format({'bold': False, 'font_color': '#000000'})
        col_B_format.set_font("Tahoma")
        col_B_format.set_font_size(11)
        col_B_format.set_align('center')
        col_B_format.set_bottom_color('white')
        col_B_format.set_bg_color('white')
        
        
        col_C_format = workbook.add_format({'bold': False, 'font_color': '#000000'})
        col_C_format.set_font("Tahoma")
        col_C_format.set_font_size(11)
        col_C_format.set_align('center')
        
        col_D_format = workbook.add_format({'bold': False, 'font_color': '#000000'})
        col_D_format.set_font("Tahoma")
        col_D_format.set_font_size(11)
        col_D_format.set_align('center')
        
        col_E_format = workbook.add_format({'bold': False, 'font_color': '#000000'})
        col_E_format.set_font("Tahoma")
        col_E_format.set_font_size(11)
        col_E_format.set_align('center')
        
        col_F_format = workbook.add_format({'bold': False, 'font_color': '#000000'})
        col_F_format.set_font("Tahoma")
        col_F_format.set_font_size(11)
        col_F_format.set_align('center')
        
        
        worksheet.write('A1', 'N',headers_format)
        worksheet.write('B1', 'CONCORDANCE',headers_format)
        worksheet.write('C1', 'FILENAME',headers_format)
        worksheet.write('D1', 'TOKEN_ID',headers_format)
        worksheet.write('E1', 'SENT_ID',headers_format)
        worksheet.write('F1', 'FILE_ID',headers_format)
        
        
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            
            worksheet.write(i,0, int(row[0]),col_A_format) # N
            
            if kcolor == True:
                left = self.__cleft(row[1], lc[0], lc[1], lc[2], left_hf1,left_hf2,left_hf3, hor_format,width)
                right = self.__cright(row[3], rc[0], rc[1], rc[2], right_hf1,right_hf2,right_hf3, hor_format,width)
                whole = left + [node_format, ' ' + row[2] + ' '] + right
            else:
                whole = [hor_format, self.nleft(row[1],width), node_format, ' ' + row[2] + ' ', hor_format, self.nright(row[3],width)]
                worksheet.write_rich_string(i,1, *whole)       # CONCORDANCE
            
            worksheet.write_rich_string(i,1, *whole)       # CONCORDANCE
            worksheet.write(i,2, str(row[4]),col_C_format) # FILENAME
            worksheet.write(i,3, int(row[5]),col_D_format) # TOKEN_ID
            worksheet.write(i,4, int(row[6]),col_D_format) # SENT_ID
            worksheet.write(i,5, int(row[7]),col_D_format) # FILE_ID
            
        workbook.close()
    
    
    
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
            
        
        
    def norm(self,s):
        for r in [(' ,', ','), (' .', '.'),(' ;', ';'), (' ?', '?'),(' !', '!'),(' :', ':'), (' %', '%'),
                  (' )', ')'), ('( ', '('), (' ]', ']'), ('[ ', '['),(' }', '}'), ('{ ', '{')]:
            s = str(s).replace(r[0],r[1])
        return s
    
    def nleft(self,s,c):
        s = self.norm(s)
        t = len(s)
        if t < c:
            s = ' ' * (c-t) + s
        if t > c:
            s = s[(t-c):]
        return s
    
    def nright(self,s,c):
        s = self.norm(s)
        t = len(s)
        if t > c:
            s = s[:c]
        return s 
    
