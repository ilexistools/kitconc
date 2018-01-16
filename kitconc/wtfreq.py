import pandas as pd
from io import StringIO
import xlsxwriter 


class WTfreq(object):
    
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
        worksheet.name = 'WTfreq'
        
        # resize columns
        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 10)
        
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
        
        col_E_format = workbook.add_format({'bold': False, 'font_color': '#000000'})
        col_E_format.set_font("Tahoma")
        col_E_format.set_font_size(11)
        col_E_format.set_align('center')
        
        worksheet.write('A1', 'N',headers_format)
        worksheet.write('B1', 'WORD',headers_format)
        worksheet.write('C1', 'TAG',headers_format)
        worksheet.write('D1', 'FREQUENCY',headers_format)
        worksheet.write('E1', '%',headers_format)
        
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(row[0]),col_A_format) # N
            worksheet.write(i,1, str(row[1]),col_B_format) # WORD
            worksheet.write(i,2, str(row[2]),col_C_format) # TAG 
            worksheet.write(i,3, int(row[3]),col_D_format) # FREQ
            worksheet.write(i,4, float(row[4]),col_E_format) # %
            
        workbook.close() 