from kitconc.kit_spacy import create_corpus

# Creates a corpus with spaCy POS

create_corpus('kitconc_workspace',      # workspade
              'job_ads',                # corpus name            
              'kitconc_corpora/ads',    # texts folder
              'english',                # language
              'en_core_web_trf',        # spaCy model
              show_progress=True)

