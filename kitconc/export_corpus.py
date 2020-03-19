# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os,sys
import zipfile

def export(workspace,corpus_name,dest_folder):
    if not workspace.endswith('/'):
        workspace +='/'
    with open(workspace + corpus_name + '/output/read_me.txt','w',encoding='utf-8') as fh:
        fh.write('This is the output folder.')
    fh = zipfile.ZipFile(dest_folder +  '/' + corpus_name + '.zip', 'w', zipfile.ZIP_DEFLATED)
    path = workspace + corpus_name 
    length = len(path)
    for root, dirs, files in os.walk(path):
        folder = corpus_name + '/' + root[length:] 
        for file in files:
            if file.endswith('.xlsx')==False:
                fh.write(os.path.join(root, file),os.path.join(folder, file))
    fh.close()
    if os.path.exists(workspace + corpus_name + '/output/read_me.txt'):
        os.remove(workspace + corpus_name + '/output/read_me.txt')

if __name__ == '__main__':
    workspace = sys.argv[1]
    corpus_name = sys.argv[2]
    dest_folder = sys.argv[3]
    export(workspace,corpus_name,dest_folder)
