# -*- coding: utf-8 -*-
import pandas as pd
from io import StringIO
import xlsxwriter 


class Collocations(object):
    
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
        worksheet.name = 'Collocations'
        # resize columns
        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 7)
        worksheet.set_column('D:D', 7)
        worksheet.set_column('E:E', 7)
        worksheet.set_column('F:F', 7)
        worksheet.set_column('G:G', 7)
        worksheet.set_column('H:H', 4)
        worksheet.set_column('I:I', 7)
        worksheet.set_column('J:J', 7)
        worksheet.set_column('K:K', 7)
        worksheet.set_column('L:L', 7)
        worksheet.set_column('M:M', 7)
        worksheet.set_column('N:N', 8)
        worksheet.set_column('O:O', 8)
        worksheet.set_column('P:P', 8)
        worksheet.set_column('Q:Q', 15)
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
        worksheet.write('C1', 'L5',headers_format)
        worksheet.write('D1', 'L4',headers_format)
        worksheet.write('E1', 'L3',headers_format)
        worksheet.write('F1', 'L2',headers_format)
        worksheet.write('G1', 'L1',headers_format)
        worksheet.write('H1', 'N',headers_format)
        worksheet.write('I1', 'R1',headers_format)
        worksheet.write('J1', 'R2',headers_format)
        worksheet.write('K1', 'R3',headers_format)
        worksheet.write('L1', 'R4',headers_format)
        worksheet.write('M1', 'R5',headers_format)
        worksheet.write('N1', 'LEFT',headers_format)
        worksheet.write('O1', 'RIGHT',headers_format)
        worksheet.write('P1', 'TOTAL',headers_format)
        worksheet.write('Q1', 'ASSOCIATION',headers_format)

        # add data
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(row[0]),col_N_format) # N
            worksheet.write(i,1, str(row[1]),col_WORD_format) # WORD 
            worksheet.write(i,2, int(row[2]),col_RL_format) # L5
            worksheet.write(i,3, int(row[3]),col_RL_format) # L4
            worksheet.write(i,4, int(row[4]),col_RL_format) # L3
            worksheet.write(i,5, int(row[5]),col_RL_format) # L2
            worksheet.write(i,6, int(row[6]),col_RL_format) # L1
            worksheet.write(i,7,  '*' ,col_RL_format) # N
            worksheet.write(i,8, int(row[7]),col_RL_format) # R1
            worksheet.write(i,9, int(row[8]),col_RL_format) # R2
            worksheet.write(i,10, int(row[9]),col_RL_format) # R3
            worksheet.write(i,11, int(row[10]),col_RL_format) # R4
            worksheet.write(i,12, int(row[11]),col_RL_format) # R5
            worksheet.write(i,13, int(row[12]),col_RL_format) # LEFT
            worksheet.write(i,14, int(row[13]),col_RL_format) # RIGHT
            worksheet.write(i,15, int(row[14]),col_RL_format) # TOTAL
            worksheet.write(i,16, float(row[15]),col_RL_format) # ASSOCIATION
            
        # close
        workbook.close()
    
