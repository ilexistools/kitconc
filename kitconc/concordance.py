# -*- coding: utf-8 -*-
import pandas as pd
from io import StringIO
import xlsxwriter 

class Concordance(object):
    
    def __init__(self,**kwargs):
        self.df = None
        self.encoding = kwargs.get('encoding','utf-8')
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
    
    def save_xls(self,filename,**kwargs):
        node_color = kwargs.get('node_color','#cc0066')
            
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
        
        node_format = workbook.add_format({'bold': True, 'font_color': node_color})
        node_format.set_font("Courier New")
        node_format.set_font_size(10)
        node_format.set_align('center')
        node_format.set_border(0)
        node_format.set_bottom_color('white')
        node_format.set_bg_color("white")
        
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
            tokens = str(row[1]).split(' ')
            
            # node is in the beggining
            if int(row[3]) == 1:
                node = tokens[0] + ' '
                context = self.norm( ' '.join(tokens[1:]))
                whole = [node_format,node,hor_format,context]
            # node is in the final
            elif (int(row[3])-1) == len(tokens):
                node = ' ' + tokens[-1:]
                context = self.norm( ' '.join(tokens[:-1]))
                whole = [hor_format,context,node_format,node] 
            # node is in the middle
            else:
                idx = int(row[3])-1
                total = len(tokens)
                node = ' ' + tokens[idx] + ' '
                left  = self.norm( ' '.join(tokens[0:idx]))
                right = self.norm( ' '.join(tokens[idx+1:total]))
                whole = [hor_format,left,node_format,node,hor_format,right]
            
            tokens = None 

            worksheet.write_rich_string(i,1, *whole)       # CONCORDANCE
            worksheet.write(i,2, str(row[2]),col_C_format) # FILENAME
            worksheet.write(i,3, int(row[3]),col_D_format) # TOKEN_ID
            worksheet.write(i,4, int(row[4]),col_D_format) # SENT_ID
            worksheet.write(i,5, int(row[5]),col_D_format) # FILE_ID
        workbook.close()
    
        
    def norm(self,s):
        for r in [(' ,', ','), (' .', '.'),(' ;', ';'), (' ?', '?'),(' !', '!'),(' :', ':'), (' %', '%'),
                  (' )', ')'), ('( ', '('), (' ]', ']'), ('[ ', '['),(' }', '}'), ('{ ', '{')]:
            s = str(s).replace(r[0],r[1])
        return s
    
