# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import sys 
from kitconc.kit_corpus import Corpus 
print('Hello!')
print('')
print("""This is an example on how to create a custom scripts.
\nHere is how arguments are received: 
""")
print('Arg 1 - Workspace: %s' % sys.argv[1])
print('Arg 2 - Corpus: %s' % sys.argv[2])
if len(sys.argv)>3:
    for i in range(3,len(sys.argv)):
        print('Arg %s: %s' % (i,sys.argv[i]))
print('\nHere is how to use the Corpus object:')
corpus = Corpus(sys.argv[1],sys.argv[2])
print('\nTokens:  %s' % corpus.tokens_count())