import os,sys 
import numpy as np 
import multiprocessing as mp 

def get_files ():
    path = sys.argv[1] + sys.argv[2] + '/data/temp/'
    for filename in os.listdir(path):
        yield filename 

def create_npy_array(filename):
    source_path = sys.argv[1] + sys.argv[2] + '/data/temp/' + filename 
    dest_path = sys.argv[1] + sys.argv[2] + '/data/tagged/' + filename 
    arr=np.loadtxt(source_path, dtype=int, delimiter='\t',encoding='utf-8')
    np.save(dest_path,arr,allow_pickle=False)
    
def create_npy_arrays():
    filenames = get_files()
    p = mp.Pool(mp.cpu_count())
    p.map(create_npy_array,filenames)
    p.close()
    p.join()

if __name__ == '__main__':
    create_npy_arrays()
    
