# Using Kitconc from Python

Use this when writing scripts or notebooks instead of calling tools one by one.

## The agent tools in-process

`KitconcTools` exposes exactly the MCP/CLI tools as Python methods returning the same JSON-ready
dicts:

```python
from kitconc.agent.actions import KitconcActions
from kitconc.agent.tools import KitconcTools

tools = KitconcTools(KitconcActions("kitconc_workspace"))
print(tools.workspace_info())
qa = tools.corpus_qa("ads")
out = tools.recipe_run("glossary-candidates", {"corpus": "ads", "export_path": "glossary.xlsx"})
kw = tools.analyze_keywords("ads", effect=["log-ratio"], p_value="p<0.01", limit=0)
top = tools.result_filter(kw["result_id"], where="FREQUENCY >= 5", sort_by="KEYNESS", keep=20)
frame = tools.results.get(top["result_id"]).frame      # pandas DataFrame
```

## The classic corpus API

```python
from kitconc.kit_corpus import Corpus

corpus = Corpus("kitconc_workspace", "ads", "english")
corpus.add_texts("kitconc_corpora/ads", verbose=True)        # create once

wl = corpus.wordlist(stoplist="default", dispersion=True)
kw = corpus.keywords(ref_corpus="reference", effect=["log-ratio"], p_value="p<0.01")
kwic = corpus.kwic("teach*", wildcards=True, sample=50, seed=1)
coll = corpus.collocates("skills", measure="log-dice", min_freq=3)
clusters = corpus.clusters("skills", size=3, position="left")
ngrams = corpus.ngrams(size=3, pos="NN IN NN")
frames = corpus.pframes(size=4, slots=1)
disp = corpus.dispersion("salary"); print(disp.stats)
print(kw.df.head(10)); kw.save_excel(corpus.output_path + "keywords.xlsx")
```

Every result has a pandas `df`. spaCy-tagged corpora:

```python
from kitconc.kit_spacy import create_corpus
create_corpus("kitconc_workspace", "ads_spacy", "kitconc_corpora/ads", "english", "en_core_web_sm")
```

Other languages without a built-in tagger: `Corpus(workspace, name, "no-tagging")`.
