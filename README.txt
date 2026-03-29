**Kitconc 3.2.0**
===========

Kitconc is a package for Corpus Linguistics and text analysis with Python.
It contains, among other things, tools for creating:

* Corpora;
* Frequency wordlists;
* Keywords (Log-Likelihood, Chi-Square, TF-IDF);
* Concordance lines;
* Collocates;
* N-gram lists;
* Dispersion plots;
* Excel data files;
* Semantic search with sentence embeddings.

The package is built on top of platforms and packages for scientific research:
numpy, pandas, NLTK, XlsxWriter and matplotlib.

Requirements
============

Kitconc requires Python 3.10 or later, along with:

numpy>=1.26.4,<2.0.0
pandas>=2.2.0,<3.0.0
matplotlib>=3.7.0,<4.0.0
xlsxwriter>=3.2.3,<4.0.0
ttkbootstrap>=1.12.0,<2.0.0
pillow>=11.2.0,<12.0.0
requests>=2.31.0,<3.0.0
nltk>=3.9.1,<4.0.0
chardet>=5.2.0,<6.0.0
pypdf>=4.0.0,<7.0.0
cryptography>=3.1,<47.0.0
mcp>=1.0.0,<2.0.0

Installation
============

pip install kitconc

Kitconc App (graphical interface)
=================================

kitconc-app

Agent Layer (internal actions)
==============================

Kitconc now includes an internal action layer for agent/tool orchestration:

* kitconc.agent.actions.KitconcActions
* Full parity with shell commands from kit_cmd.py (do_*)
* Typed schemas in kitconc.agent.schemas
* Contract documentation in kitconc/agent/CONTRACT.md

Basic usage:

from kitconc.agent import KitconcActions
actions = KitconcActions("kitconc_workspace")
actions.create("ads", "kitconc_corpora/ads", "english")
actions.use("ads")
rows = actions.keywords(limit=10)

MCP Server (for agent integrations)
===================================

kitconc-mcp --transport stdio

or:

kitconc-mcp --transport sse --host 127.0.0.1 --port 8001

If you installed only with pip install kitconc and need MCP runtime:

pip install mcp

What's new in 3.2.0
====================

* Tkinter launcher command -- start GUI with kitconc-app
* Agent action layer -- kitconc.agent.actions.KitconcActions with command parity from kit_cmd.py
* Typed schemas -- available in kitconc.agent.schemas
* MCP server entrypoint -- run with kitconc-mcp
* Progress flag rename -- use verbose=True (replacing show_progress=True)

What's new in 3.1.0
====================

* TF-IDF keywords -- third keyword extraction method alongside Log-Likelihood and Chi-Square
* Keyword filters -- ignore numbers, ignore words with strange characters, minimum word length
* PDF support -- add PDF files directly to a corpus
* Embeddings module -- semantic search with sentence-transformers and SQLite vector storage
* Dialog improvements -- dialog boxes now center correctly in fullscreen and large-window mode

Language resources
==================

Kitconc comes with built-in language resources for Portuguese and English corpora.
It also provides functions for adding your own language resources.

Usage example
=============

See how easy it is to use Kitconc:

`https://ilexis.net.br/kitconc <https://ilexis.net.br/kitconc>`_
