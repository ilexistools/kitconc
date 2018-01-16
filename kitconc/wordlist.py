# -*- coding: utf-8 -*-
import pandas as pd
from io import StringIO
import xlsxwriter 


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
     
    def save_xls(self,filename):
        # create Excel
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        worksheet.name = 'Wordlist'
        # resize columns
        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 10)
        worksheet.set_column('E:E', 3)
        worksheet.set_column('F:F', 3)
        worksheet.set_column('G:G', 3)
        worksheet.set_column('H:H', 3)
        worksheet.set_column('I:I', 3)
        worksheet.set_column('J:J', 20)
        worksheet.set_column('K:K', 20)
        worksheet.set_column('L:L', 25)
        worksheet.set_column('M:M', 20)
        # formats
        headers_format = workbook.add_format({'bold': True, 'font_color': '#003366'})
        headers_format.set_font("Calibri")
        headers_format.set_font_size(12)
        headers_format.set_align('center')
        col_A_format = workbook.add_format({'bold': False, 'font_color': '#404040'})
        col_A_format.set_font("Tahoma")
        col_A_format.set_font_size(11)
        col_A_format.set_align('center')
        col_B_format = workbook.add_format({'bold': False, 'font_color': '#b30000'})
        col_B_format.set_font("Tahoma")
        col_B_format.set_font_size(11)
        col_B_format.set_align('right')
        col_C_format = workbook.add_format({'bold': False, 'font_color': '#000000'})
        col_C_format.set_font("Tahoma")
        col_C_format.set_font_size(11)
        col_C_format.set_align('center')
        col_D_format = workbook.add_format({'bold': False, 'font_color': '#000000'})
        col_D_format.set_font("Tahoma")
        col_D_format.set_font_size(11)
        col_D_format.set_align('center')
        col_J_format = workbook.add_format({'bold': False, 'font_color': '#000000'})
        col_J_format.set_font("Tahoma")
        col_J_format.set_font_size(11)
        col_J_format.set_align('center')
        col_K_format = workbook.add_format({'bold': False, 'font_color': '#000000'})
        col_K_format.set_font("Tahoma")
        col_K_format.set_font_size(11)
        col_K_format.set_align('center')
        col_L_format = workbook.add_format({'bold': False, 'font_color': '#000000'})
        col_L_format.set_font("Tahoma")
        col_L_format.set_font_size(11)
        col_L_format.set_align('center')
        col_M_format = workbook.add_format({'bold': False, 'font_color': '#000000'})
        col_M_format.set_font("Tahoma")
        col_M_format.set_font_size(11)
        col_M_format.set_align('center')
        worksheet.write('A1', 'N',headers_format)
        worksheet.write('B1', 'WORD',headers_format)
        worksheet.write('C1', 'FREQUENCY',headers_format)
        worksheet.write('D1', '%',headers_format)
        worksheet.write('J1', 'TOKENS',headers_format)
        worksheet.write('K1', 'TYPES',headers_format)
        worksheet.write('L1', 'TYPE-TOKEN RATIO',headers_format)
        worksheet.write('M1', 'HAPAX',headers_format)
        # load wordlist
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(row[0]),col_A_format) # N
            worksheet.write(i,1, str(row[1]),col_B_format) # WORD 
            worksheet.write(i,2, int(row[2]),col_C_format) # FREQ
            worksheet.write(i,3, float(row[3]),col_D_format) # %
        # corpus info
        worksheet.write('J2', self.tokens ,col_J_format)
        worksheet.write('K2', self.types,col_K_format)
        worksheet.write('L2', self.typetoken,col_L_format)
        worksheet.write('M2', self.hapax,col_L_format)
        # close
        workbook.close()
        
        
    
        
    
        
        
    
    
    
    
        
        
        
        