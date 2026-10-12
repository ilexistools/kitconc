# AntConc: pesquisa de funcionalidades e comparação com o Kitconc

Data da pesquisa: 2026-10-11. Versão do AntConc analisada: **4.4.2**, com manual de 20/07/2026. Versão do Kitconc analisada: **3.5.1**.

Fontes:

- [Página oficial do AntConc](https://www.laurenceanthony.net/software/antconc/)
- [Manual (help.pdf) 4.4.2](https://www.laurenceanthony.net/software/antconc/releases/AntConc442/docs/help.pdf)
- [Histórico de versões 4.4.2](https://mail.laurenceanthony.net/software/antconc/releases/AntConc442/docs/version_history.pdf)
- [Notas da versão 4.4.0](https://laurenceanthony.net/software/antconc/releases/AntConc440/docs/release_notes_4.4.0.html)
- [Grupo de discussão do AntConc](https://groups.google.com/g/antconc)

---

## Parte 1: o AntConc

### 1.1 Visão geral

- Freeware de Laurence Anthony (Universidade Waseda), com licença para uso não comercial.
- Roda em Windows (instalador ou portátil), macOS (Apple Silicon) e Linux (Flatpak). A série 3.5.9 continua disponível.
- Desde a 4.0.0 é escrito em **Python + Qt**, empacotado com PyInstaller. Antes era em Perl.
- Corpora e resultados ficam em bancos **SQLite**. O usuário pode editar as tabelas, criar índices e exportar ou importar dados de outras ferramentas.
- Desde a 4.4.1 aceita corpora **multimodais**: texto ligado a imagem, áudio, vídeo ou YouTube.

### 1.2 As 10 ferramentas

| # | Ferramenta | O que faz | Opções principais |
|---|---|---|---|
| 1 | **KWIC** | Linhas de concordância (esquerda, termo, direita) | Words/Case/Regex/Full Regex; contexto ajustável; ordenação por 3 chaves (1L…/C/1R…/File/ID) por valor ou frequência; **KPF** (frequência de padrão), com opção de recolher grupos e agrupar padrões únicos; paginação; **amostra aleatória**; Delete e Shift+Delete filtram linhas; clique duplo abre o File View; esconder o termo buscado (exercícios de lacuna); mídia ligada e galeria de imagens |
| 2 | **Plot** | Gráfico em "código de barras" da posição das ocorrências em cada arquivo | Colunas FileID, caminho, tokens, frequência, frequência normalizada e dispersão; **D de Juilland**, Range, desvio padrão e desvio padrão normalizado; tamanho do *bin*; **overlay** de uma segunda busca em outra cor; mostrar arquivos sem ocorrências; barras normalizadas ou proporcionais; zoom; copiar imagem |
| 3 | **File View** | Texto completo com as ocorrências destacadas | Navegar entre ocorrências (Ctrl+F e Ctrl+Shift+F); estatísticas do arquivo; clique duplo envia ao KWIC |
| 4 | **Cluster** | Sequências contíguas em volta do termo | Tamanho do cluster; frequência e *range* mínimos; posição do termo à esquerda, à direita ou nas duas; ordenar por Type, TypeEnd, Freq ou Range |
| 5 | **N-Gram** | Todos os n-gramas do corpus | Tamanho; **Open Slots** (p-frames) com razão type/token e **entropia** por slot; visualizador de variantes; frequência e *range* mínimos |
| 6 | **Collocate** | Colocados dentro de uma janela de *x*L até *y*R | FreqLR, FreqL, FreqR e Range; **likelihood**: LL de 4 ou de 2 termos, com limiar p<0,05 ou p<0,01 e Bonferroni; **efeito**: MI, MI², MI³, Dice, LogDice, LogRatio, T-score, Z-score, com corte top-N |
| 7 | **Word** | Lista de frequência | Rank, Freq, Range, valores normalizados; listas por Type, Type+POS, Type+[POS], Type+Headword, Headword ou Headword+[Type] |
| 8 | **Keyword** | Corpus-alvo contra **corpus de referência escolhido pelo usuário** | Fonte da comparação: Word, Cluster, N-Gram ou Collocate; **palavras-chave negativas**; χ² (com e sem Yates), LL, **Text Dispersion Keyness**; efeito: Dice, LogDice, LogRatio, MI, T, Z, RRF, DRF |
| 9 | **Wordcloud** | Nuvem de palavras a partir de texto livre ou da tabela de qualquer ferramenta | Máscaras; layouts Spiral, Distance Transform ou Square; temas de cor; escala log ou potência; exporta PNG |
| 10 | **ChatAI** | LLM com os resultados das ferramentas como contexto | OpenAI, Gemini ou Claude na nuvem; Llamafile ou LM Studio locais; temperatura, max tokens, streaming, histórico de prompts |

### 1.3 Busca, comum a todas as ferramentas

- **Simples:** `language`, `corpus analysis`.
- **Coringas:** `teach*`, `*ing`, `student|pupil`, `[student,pupil]`, `help_[?]` (a palavra seguida de um item que não é palavra).
- **Regex por token:** `colou?r`, `data.* driven`.
- **Full Regex** no texto inteiro: `\b(\w+)\s+\1\b`. Exige que o corpus tenha sido criado com o texto completo armazenado.
- **Advanced Search:**
  - Lista de consultas.
  - **Context Search**: termos exigidos ou proibidos numa janela, combinados com AND ou OR.
  - **SQL Search** sobre tabelas de metadados: `["genres", "genre = 'academic'", "doc_id"]`.
- **AI Search:** converte linguagem natural em termos de busca.
- **Filtro global de metadados**, para trabalhar com subcorpora.

### 1.4 Gestão de corpora

- **Corpus Library:**
  - Repositório online com corpora prontos: BASE, BAWE, família Brown/LOB de 1931 a 2021, AmE06/BE06, Elsevier OA, entre outros.
  - Papéis Target/Ref, com troca rápida.
  - Importa e exporta a biblioteca em .zip.
  - Atualiza bancos de versões antigas, com backup.
- **Corpus Builder (Files):**
  - **Formatos:** txt, srt, sub, csv, tsv, html, xhtml, xml, doc, docx, pdf, epub.
  - **Indexadores:** palavra simples, palavra+POS+headword, etiquetas no estilo Biber.
  - **Definição de token:** classes Unicode, caracteres definidos pelo usuário ou regex, com área de teste.
  - Ignora cabeçalho, rodapé e tags.
  - Um texto por arquivo ou **um texto por linha**.
  - **Tabelas de metadados** CSV/TSV ligadas pelo `doc_id`.
  - **Lista de lemas** no formato `headword<TAB>forma1<TAB>forma2`.
  - Mídia ligada pelo nome base do arquivo; SRT com alinhamento temporal; transcrição com **Whisper**.
- **Corpus Builder (Word Lists):** corpus feito apenas de uma lista de frequências, usado como referência em palavras-chave.
- **AI Model Manager:** modelos locais `.gguf` e modelos Whisper `.bin`.

### 1.5 Configurações e exportação

- **Configurações globais:**
  - Stoplist/allowlist e filtro de pontuação, aplicados em Cluster, N-Gram, Collocate, Word, Keyword e Wordcloud.
  - Direção do texto: da esquerda para a direita, ou da direita para a esquerda (árabe).
  - Multiplicador da frequência normalizada e casas decimais.
  - Mostrar ou ignorar erros de codificação.
- **Exportação:**
  - Resultados em texto/TSV ou imagem.
  - **Tabelas do banco da aba em ZIP**.
  - Configurações em `.ini`, com restauração da sessão.

### 1.6 Fórmulas estatísticas (notação de Evert, 2004)

- **Efeito:**
  - Dice = 2O₁₁/(R₁+C₁)
  - LogDice = 14 + log₂ Dice
  - LogRatio = log₂(R₂O₁₁ / R₁O₂₁)
  - MI = log₂(O₁₁/E₁₁)
  - MI² = log₂(O₁₁²/E₁₁)
  - MI³ = log₂(O₁₁³/E₁₁)
  - MS = min(O₁₁/R₁, O₁₁/C₁)
  - Mu = O₁₁/E₁₁
  - RRF = R₂O₁₁/R₁O₂₁
  - DRF = O₁₁/R₁ − O₂₁/R₂
  - z = (O₁₁−E₁₁)/√E₁₁
  - T-score: o manual traz √O₁₂ no denominador. A forma usual é (O₁₁−E₁₁)/√O₁₁, então provavelmente é um erro de digitação.
  - Em LogRatio e RRF, se O₂₁ = 0, usa-se 0,5.
- **Significância:**
  - χ² de 4 termos, com e sem Yates.
  - Log-Likelihood de 4 termos e de 2 termos.
  - Text Dispersion (4 e 2 termos): as mesmas fórmulas do LL, aplicadas aos valores de *range* em vez de frequência.

### 1.7 Linha do tempo da série 4.x

| Versão | Novidades |
|---|---|
| 4.0.0 | Reescrita em Python/SQLite, Corpus Manager, paginação, KPF, Plot em tabela com overlay, Cluster e N-Gram separados |
| 4.1.0 | Repositório online de corpora, Wordcloud, Context Search com AND/OR, restauração de sessão |
| 4.2.0 | Listas por Type/POS/Headword, Row Processor, Simple Word List, troca entre alvo e referência |
| 4.2.4 | LogDice, LogRatio, DRF |
| 4.3.0 | ChatAI, leitura de .doc, .xhtml e .epub |
| 4.4.0 | Full Regex, AI Search em todas as ferramentas, filtro global de metadados, nova stoplist/allowlist, AI Model Manager |
| 4.4.1 | Corpora multimodais, SRT, Whisper |
| 4.4.2 | Atualização de bancos antigos, inicialização mais rápida |

---

## Parte 2: comparação com o Kitconc (após a implementação)

As Partes 2 e 3 foram atualizadas depois de implementar as lacunas. Todas as opções novas são parâmetros opcionais: chamadas existentes continuam devolvendo exatamente os mesmos resultados. Isso foi verificado comparando 90 saídas da API antes e depois das mudanças.

Legenda: ✅ equivalente · 🟡 parcial · ❌ ausente · ➕ só o Kitconc tem

### 2.1 Ferramentas

| AntConc | Kitconc | Status | Observações |
|---|---|---|---|
| KWIC | `kwic()`, `Kwic.sort()`, `Kwic.kpf()`, `Kwic.hide_node()` | ✅ | Coringas, Context Search (AND/OR/exclusão), amostra aleatória, KPF, ordenação em 3 níveis, esconder o termo. Frase de até 4 palavras |
| — | `concordance()` | ➕ | Concordância por frase (aceita coringas e amostra) |
| Busca com filtro de POS | parâmetro `pos` | ➕ | |
| Plot | `dispersion()` | ✅ | 5 seções por arquivo e `stats` (range, SD, CV, D de Juilland, DP, DP normalizado). Sem overlay gráfico |
| — | `dispersion_measures()`, `keywords_dispersion()` | ➕ | Dispersão de várias palavras de uma vez |
| File View | `fileview()` | ✅ | Texto do arquivo com as ocorrências marcadas, contagem de tokens/types/hits |
| Cluster | `clusters(size=…, position=…)` | ✅ | Qualquer tamanho; termo à esquerda, à direita ou em qualquer posição |
| N-Gram | `ngrams(search=…)`, `pframes()` | ✅ | Open slots com variantes, TTR e entropia |
| Collocate | `collocates(measure=…, extra_measures=…)` | ✅ | T, MI, MI2, MI3, LL (4 e 2 termos), χ², Dice, LogDice, LogRatio, z, MS, Mu; `min_freq`. Sem *range* por colocado |
| Word | `wordlist(search=…, dispersion=True)`, `lemmalist()` | ✅ | Filtro por consulta, RANGE/D/DP, lista por lema (formato kitconc ou AntConc) |
| Keyword | `keywords(ref_corpus=…, effect=…, polarity=…, p_value=…)` | 🟡 | Corpus de referência do usuário, 11 medidas de efeito, palavras-chave negativas, limiares de p com Bonferroni, Text Dispersion Keyness. Ainda só compara palavras (não clusters, n-gramas ou colocados) |
| Wordcloud | `wordcloud()` | ✅ | A partir de qualquer tabela, dicionário ou texto; PNG |
| ChatAI / AI Search | Servidor MCP + `KitconcActions` | 🟡/➕ | Todas as funções novas também viraram ferramentas MCP |
| — | Busca semântica com embeddings | ➕ | |

### 2.2 Busca

| Recurso do AntConc | Kitconc | Status |
|---|---|---|
| Words / Case | `case_sensitive` | ✅ |
| Regex por token | `regexp=True` | ✅ Usa `re.match`, que ancora só no início do token (para casar o token inteiro, termine o padrão com `$`). Com `wildcards=True` os padrões são ancorados nas duas pontas |
| Coringas (`*`, `?`, `+`, `\|`, `[a,b]`) | `wildcards=True` | ✅ |
| Full Regex no texto | — | ❌ |
| Lista de consultas | — | ❌ (use `a\|b\|c` com coringas) |
| Context Search (AND/OR) | `context=…` | ✅ |
| Metadados / SQL / subcorpora | — | ❌ |

### 2.3 Corpora e infraestrutura

| Recurso do AntConc | Kitconc | Status |
|---|---|---|
| Formatos de entrada | txt, pdf, docx, odt, epub, html/htm/xhtml, xml | ✅ (falta csv com uma linha por texto e srt) |
| Etiquetagem POS | Taggers embutidos (inglês e português), spaCy, treino de modelo | ➕ |
| Lemas | `lemmalist()` com lista embutida (inglês) ou arquivo do usuário | ✅ |
| Corpus de referência do usuário | `ref_corpus=` | ✅ |
| Stoplist / allowlist | `stoplist`/`allowlist` em wordlist, keywords, collocates, clusters, n-gramas e p-frames | ✅ |
| Definição de token, ignorar cabeçalho e tags | — | ❌ |
| Corpus a partir de lista de frequências | — | ❌ |
| Exportação | `.tab`, Excel formatado, MCP (tab/tsv/xlsx), PNG | ✅➕ |
| Interfaces | GUI Tkinter, CLI, API Python, MCP, Docker | ➕ |
| Multimodal e Whisper | — | ❌ |

---

## Parte 3: o que foi implementado e o que ficou de fora

### Implementado

1. Palavras-chave com corpus de referência do usuário, medidas de efeito, palavras-chave negativas, p-valor/Bonferroni, LL de 2 termos, χ² com Yates e Text Dispersion Keyness.
2. Colocados com 13 medidas e colunas extras.
3. Medidas de dispersão (D de Juilland, DP, DP normalizado, SD, CV, range).
4. Coringas `* ? + | [a,b]`.
5. Cluster de qualquer tamanho e posição do termo.
6. P-frames com variantes, TTR e entropia.
7. Lista por lema.
8. Context Search.
9. Stoplist/allowlist nas principais ferramentas.
10. KWIC com amostra aleatória, KPF e opção de esconder o termo.
11. Leitura de docx, odt, epub, html e xml.
12. Nuvem de palavras.
13. Visualizador de arquivo (`fileview()`).
14. Novos comandos da CLI e ferramentas MCP correspondentes (paridade 36/36).
15. Correções: `wordlist(lowercase=False)`, `dispersion()` sem ocorrências e TF-IDF ignorado pela CLI/GUI.

### Não implementado

- **Metadados, SQL e subcorpora:** exigiriam um esquema novo de metadados no workspace em arquivos.
- **Full Regex no texto inteiro:** o índice guarda tokens, não o texto original.
- **Definição de token, ignorar cabeçalho e tags e corpus a partir de lista de frequências:** dependem do pipeline de criação de corpus.
- **Corpora multimodais e Whisper:** fora do escopo do pacote.
- **Palavras-chave de clusters, n-gramas e colocados.**
- **Interface gráfica:** as opções novas estão na API, na CLI e no MCP. A GUI ganhou apenas a correção do TF-IDF; seus formulários não foram alterados.

### Diferenciais do Kitconc mantidos

Filtro por POS, etiquetagem embutida para português, concordância por frase, TF-IDF, colocados comparados e grafos, combolist, Excel formatado, busca semântica, MCP, CLI e API Python.
