# -*- coding: utf-8 -*-
import pandas as pd
from io import StringIO
import xlsxwriter 


class ComparedCollocates(object):
    
    def __init__(self,**kwargs):
        self.df = None
        self.encoding = kwargs.get('encoding','utf-8')
        
    def read_str(self,str_table):
        """Reads data table from string"""
        self.df = pd.read_csv(StringIO(str_table),sep='\t')
    
    def save_tab(self,filename):
        self.df.to_csv(filename,sep='\t',index=False)
     
    def save_xls(self,filename):
        # create Excel
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        worksheet.name = 'Comparison'
        # resize columns
        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 10)
        worksheet.set_column('D:D', 10)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 12)
        # formats
        headers_format = workbook.add_format({'bold': True, 'font_color': '#003366'})
        headers_format.set_font("Calibri")
        headers_format.set_font_size(12)
        headers_format.set_align('center')
        # rows
        col_N_format = workbook.add_format({'bold': False, 'font_color': '#404040'})
        col_N_format.set_font("Tahoma")
        col_N_format.set_font_size(11)
        col_N_format.set_align('center')
        
        col_WORD_format = workbook.add_format({'bold': False, 'font_color': '#b30000'})
        col_WORD_format.set_font("Tahoma")
        col_WORD_format.set_font_size(11)
        col_WORD_format.set_align('right')
        
        col_C_format = workbook.add_format({'bold': False, 'font_color': '#000000'})
        col_C_format.set_font("Tahoma")
        col_C_format.set_font_size(11)
        col_C_format.set_align('center')
        
        col_RL_format = workbook.add_format({'bold': False, 'font_color': '#000000'})
        col_RL_format.set_font("Tahoma")
        col_RL_format.set_font_size(11)
        col_RL_format.set_align('center')
        
        # format headers
        worksheet.write('A1', 'N',headers_format)
        worksheet.write('B1', 'WORD',headers_format)
        worksheet.write('C1', 'FREQ1',headers_format)
        worksheet.write('D1', 'FREQ2',headers_format)
        worksheet.write('E1', 'ASSOCIATION1',headers_format)
        worksheet.write('F1', 'ASSOCIATION2',headers_format)
        worksheet.write('G1', 'DIFFERENCE',headers_format)
        
        # add data
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(row[0]),col_N_format) # N
            worksheet.write(i,1, str(row[1]),col_WORD_format) # WORD 
            worksheet.write(i,2, int(row[2]),col_RL_format) # FREQ1
            worksheet.write(i,3, int(row[3]),col_RL_format) # FREQ2
            worksheet.write(i,4, float(row[4]),col_RL_format) # AM1
            worksheet.write(i,5, float(row[5]),col_RL_format) # AM2
            worksheet.write(i,6, float(row[6]),col_RL_format) # PD
            
        # close
        workbook.close()    
        
    
        
    
        
        
    
    
    
    
        
        
        
        