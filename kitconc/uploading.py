# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os, sys 
import subprocess
import sqlite3



class UploadingProcess(object):
    
    def __init__(self):
        # get args
        self.kit_path = sys.argv[1]
        self.workspace =  sys.argv[2]
        self.corpus_name =  sys.argv[3]
        self.language =  sys.argv[4]
        self.encoding =  sys.argv[5]
        self.source_folder =  sys.argv[6]
        self.tagging =  eval(sys.argv[7])
        self.show_progress =  eval(sys.argv[8])
    
    def execute(self):
        db_path_file = self.workspace + self.corpus_name + '/data/indexes.db'
        data_path_searches = self.workspace + self.corpus_name + '/data/searches.tab'
        data_path_words = self.workspace + self.corpus_name + '/data/words.tab'
        data_path_tags = self.workspace + self.corpus_name + '/data/tags.tab' 
        data_path_textfiles = self.workspace + self.corpus_name + '/data/textfiles.tab'
        if os.path.exists(db_path_file):
            if os.path.exists(data_path_searches):
                subprocess.call(["sqlite3", db_path_file , ".mode tab", ".import " + data_path_searches + " searches" ])
                os.remove(data_path_searches)
            if os.path.exists(data_path_words):
                subprocess.call(["sqlite3", db_path_file , ".mode tab", ".import " + data_path_words + " words" ])
                os.remove(data_path_words)
            if os.path.exists(data_path_tags):
                subprocess.call(["sqlite3", db_path_file , ".mode tab", ".import " + data_path_tags + " tags" ])
                os.remove(data_path_tags)
            if os.path.exists(data_path_textfiles):
                subprocess.call(["sqlite3", db_path_file , ".mode tab", ".import " + data_path_textfiles + " textfiles" ])
                os.remove(data_path_textfiles)
            conn = sqlite3.connect(db_path_file,isolation_level=None) 
            cursor = conn.cursor()
            cursor.execute('begin')
            cursor.execute("""
            CREATE INDEX idx_word ON searches (word_id);
            """)
            cursor.execute("""
            CREATE INDEX idx_tag ON searches (tag_id);
            """)
            conn.commit()
            conn.close()
                
if __name__ == '__main__':
    step3 = UploadingProcess()
    step3.execute()
    