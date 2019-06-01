import os ,sys
try:
    import nltk 
    import pandas
    import xlsxwriter 
    import matplotlib  
    import kitconc 
    print('Kitconc %s' % kitconc.__version__)
except:
    print('Sorry. Something is wrong with your installation.')
