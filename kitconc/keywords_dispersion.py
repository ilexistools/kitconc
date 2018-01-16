# -*- coding: utf-8 -*-
import pandas as pd
from io import StringIO
import xlsxwriter
from kitconc import utils  


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
     
    def save_xls(self,filename):
        # create Excel
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        worksheet.name = 'Keywords Dispersion'
        # resize columns
        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 10)
        worksheet.set_column('D:D', 10)
        worksheet.set_column('E:E', 8)
        worksheet.set_column('F:F', 8)
        worksheet.set_column('G:G', 8)
        worksheet.set_column('H:H', 8)
        worksheet.set_column('I:I', 8)
        worksheet.set_column('J:J', 28)
        worksheet.set_column('L:L', 10)
        worksheet.set_column('M:M', 10)
        worksheet.set_column('N:N', 10)
        
        
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
        col_B_format.set_align('center')
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
        zero_format = workbook.add_format({'bold': False, 'font_color': '#cccccc'})
        zero_format.set_font("Tahoma")
        zero_format.set_font_size(11)
        zero_format.set_align('center')
        
        worksheet.write('A1', 'N',headers_format)
        worksheet.write('B1', 'WORD',headers_format)
        worksheet.write('C1', 'KEYNESS',headers_format)
        worksheet.write('D1', 'HITS',headers_format)
        worksheet.write('E1', 'S1',headers_format)
        worksheet.write('F1', 'S2',headers_format)
        worksheet.write('G1', 'S3',headers_format)
        worksheet.write('H1', 'S4',headers_format)
        worksheet.write('I1', 'S5',headers_format)
        worksheet.write('J1', 'PLOT',headers_format)
        
        
        utils.create_temp_folder(self.output_path + 'temp')
        
        i = 0
        for row in self.df.itertuples(index=False):
            i+=1
            worksheet.write(i,0, int(row[0]),col_A_format) # N
            worksheet.write(i,1, str(row[1]),col_B_format) # WORD 
            worksheet.write(i,2, int(row[2]),col_C_format) # KEYNESS
            if row[3] == 0:
                worksheet.write(i,3, float(row[3]),zero_format) # HITS
            else:
                worksheet.write(i,3, float(row[3]),col_D_format) # HITS
            
            if row[4] == 0:
                worksheet.write(i,4, float(row[4]),zero_format) # S1
            else:
                worksheet.write(i,4, float(row[4]),col_E_format) # S1
            
            if row[5] == 0:
                worksheet.write(i,5, float(row[5]),zero_format) # S2
            else:
                worksheet.write(i,5, float(row[5]),col_E_format) # S2
            
            if row[6] == 0:
                worksheet.write(i,6, float(row[6]),zero_format) # S3
            else:
                worksheet.write(i,6, float(row[6]),col_E_format) # S3
                
            if row[7] == 0:
                worksheet.write(i,7, float(row[7]),zero_format) # S4
            else:
                worksheet.write(i,7, float(row[7]),col_E_format) # S4
            
            if row[8] == 0:
                worksheet.write(i,8, float(row[8]),zero_format) # S5
            else:
                worksheet.write(i,8, float(row[8]),col_E_format) # S5
            
            img = utils.draw_barcode(self.dpts[row[1]])
            img.save(self.output_path + 'temp/' + str(i) + '.jpg')
            worksheet.insert_image('J' + str(i+1), self.output_path + 'temp/' + str(i) + '.jpg')
        
            
        # close
        workbook.close()
        
        utils.remove_temp_folder(self.output_path + 'temp')
        
        
    
        
    
        
        
    
    
    
    
        
        
        
        