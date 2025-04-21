# -*- coding: utf-8 -*-
# Author: jlopes@alumni.usp.br
from kitconc.kit_corpus import Corpus 
from kitconc.kit_models import Models 


def create_corpus(workspace, corpus_name,texts_folder, language='english', spacy_model='en_core_web_trf', show_progress=True):
    corpus = Corpus(workspace,corpus_name,language)
    corpus.add_texts(texts_folder, language_model=Models().spacy_model(spacy_model),show_progress=show_progress)

