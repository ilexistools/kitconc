# Spec: confiabilidade do app Kitconc e dos corpora em arquivos

## Decisão e objetivo

O Kitconc continuará usando o formato atual de workspace e corpus (`info.tab`, arquivos de origem, índices e resultados no filesystem). Esta entrega melhora a criação de corpora, o tratamento de falhas, a responsividade da interface Tkinter e a importação/exportação de ZIP.

Partir do estado presente do diretório de trabalho e preservar as alterações locais não relacionadas a este spec.

## Escopo e critérios de aceite

### 1. Criação de corpus com caminhos e nomes seguros — prioridade alta

**Problema:** `kitconc/kit_app.py::__create_corpus()` monta uma string com nome, origem, idioma e opções para `Kit.do_create()`. `Kit.parse_arg()` separa a string por espaços. Caminhos de origem com espaços, como `F:\Meus Textos`, podem ser divididos em argumentos distintos.

**Implementar:**

- Introduzir uma chamada estruturada para criar o corpus, recebendo `name`, `source`, `language` e `tagged` como valores separados. A GUI deve chamar essa operação sem remontar uma linha de comando. A CLI pode continuar usando `argparse`, mas deve encaminhar os argumentos já interpretados para a mesma operação.
- Normalizar e validar o caminho da pasta de origem antes de criar arquivos do corpus. Validar o nome do corpus contra separadores de caminho, `.` e `..`, e impedir colisão com corpus já existente. Mostrar erro compreensível na GUI.
- Manter o funcionamento de nomes e caminhos válidos já aceitos pelo projeto; não exigir que a pessoa digite aspas na interface.

**Aceite:** a GUI cria um corpus a partir de uma pasta com espaços e caracteres acentuados no caminho; nome inválido ou corpus existente é recusado sem alterar o workspace; a CLI continua criando corpora válidos.

### 2. Falhas de marcação e indexação não produzem corpus aparentemente concluído — prioridade alta

**Problema:** `Corpus.add_texts()` usa `subprocess.call()` para `tagging.py`, `tagged.py` e `indexing.py` sem verificar o código de saída; depois acrescenta `Textfiles` e `Source` a `info.tab` mesmo se o processamento falhar.

**Implementar:**

- Verificar o retorno de cada processo; interromper o fluxo e apresentar a etapa, o comando e a mensagem útil de erro quando uma etapa falhar. Usar o mesmo interpretador da aplicação (`sys.executable`) em todas as chamadas Python, inclusive exportação.
- Só registrar contagem e origem em `info.tab` depois de confirmar a indexação. Contar apenas arquivos efetivamente processados, não entradas arbitrárias retornadas por `os.listdir()`.
- Limpar diretórios temporários em `finally`. Definir tratamento para corpus novo parcialmente criado: remover apenas os artefatos criados pela tentativa malsucedida ou manter estado identificável como incompleto; nunca apagar um corpus anterior. A GUI não deve anunciar sucesso quando houver falha.
- Evitar múltiplas linhas contraditórias de `Textfiles`/`Source` em chamadas repetidas; documentar a semântica de adicionar textos a um corpus existente.

**Aceite:** simular falha em marcação e em indexação; em ambos os casos a operação retorna erro, não grava metadados de sucesso e permite nova tentativa sem corromper corpus existente. Um fluxo bem-sucedido preserva os resultados atuais.

### 3. Acesso ao Tkinter somente pela thread principal — prioridade alta

**Problema:** métodos executados em `threading.Thread`, como `__create_corpus()`, `__exec_import_corpus()` e `__exec_wordlist()`, chamam diretamente `destroy()`, diálogos, Treeview, labels e métodos de atualização da interface.

**Implementar:**

- Separar o trabalho pesado das ações de interface. Capturar valores dos widgets na thread principal antes de iniciar o worker; o worker recebe valores simples e devolve resultado ou erro.
- Agendar toda atualização de widgets e abertura de diálogos na thread principal usando um mecanismo seguro de entrega de resultados, por exemplo uma fila consultada com `after()`.
- Encerrar sempre o indicador de progresso, tanto em sucesso quanto em erro. Impedir execução concorrente duplicada da mesma operação pela GUI.
- Aplicar o padrão às operações de criação, importação/exportação e análises acionadas em background, evitando uma correção apenas pontual em `wordlist`.

**Aceite:** tarefas demoradas mantêm a janela responsiva; sucesso e falha atualizam a interface sem chamadas Tkinter vindas do worker; o indicador de progresso não fica preso após exceção ou cancelamento.

### 4. Importação e exportação de ZIP previsíveis — prioridade média

**Problema:** os pontos de importação em `kitconc/kit_corpus.py` e `kitconc/kit_cmd.py` extraem ZIP diretamente no workspace. Não há verificação prévia de estrutura, colisão com corpora existentes nem limites de tamanho. Erros podem ser apenas impressos, sem chegar à GUI.

**Implementar:**

- Centralizar a importação em uma rotina compartilhada por GUI, CLI e `Corpora`. Validar os membros antes da extração: caminho relativo contido no destino, nomes aceitáveis, um único diretório raiz de corpus, `info.tab` presente, sem links especiais e sem entradas que sobrescrevam um corpus existente. Definir limite configurável de tamanho total descompactado.
- Extrair primeiro em diretório temporário dentro do workspace, validar o corpus extraído e só então movê-lo para a posição final. Em erro, remover o temporário e preservar o workspace anterior.
- Para importação por URL, aplicar timeout, verificar status HTTP e limitar o tamanho baixado antes de abrir o ZIP. Propagar erros para quem chamou, permitindo mensagem útil na interface.
- Na exportação, verificar que o processo terminou com sucesso e fechar o ZIP de forma segura. Não deixar artefatos temporários no corpus quando a exportação falhar.

**Aceite:** ZIP válido importa e aparece na lista; ZIP inválido, acima do limite ou com nome de corpus já existente é rejeitado sem sobrescrever dados; falha de download ou exportação é apresentada como erro, não como sucesso.

### 5. Verificação dos fluxos de usuário — prioridade média

- Acrescentar testes de integração focados em criação de corpus com caminhos contendo espaços, falha de subprocesso, atualização de `info.tab`, importação/exportação de ZIP e colisão de nomes.
- Manter os testes unitários existentes de análises; usar fixtures pequenas e temporárias. Para o comportamento de threads, isolar a entrega de resultados da GUI e testar essa lógica sem depender de uma janela visível quando possível.
- Rodar a suíte Python existente e registrar resultados. Inspecionar manualmente a GUI para pelo menos: criação bem-sucedida, erro de criação, importação válida, importação rejeitada e análise concluída.

## Compatibilidade e limites

- Preservar o layout legado dos corpora e a leitura de corpora já criados. Não converter nem apagar dados existentes.
- Manter `kitconc-app` como entrada da interface gráfica e os comandos da CLI que já fazem criação, importação e exportação.
- Não alterar as fórmulas das análises linguísticas nesta entrega; o foco é confiabilidade do fluxo de entrada, execução e interface.

## Entrega esperada

1. Código com as cinco melhorias acima, em incrementos revisáveis.
2. README e `CHANGES.txt` atualizados para criação de corpora, mensagens de falha, ZIP e eventuais limites configuráveis.
3. Resumo dos arquivos alterados, comportamento antes/depois, resultados das verificações e limitações restantes.

## Arquivos principais

- `kitconc/kit_app.py`: interface Tkinter e workers.
- `kitconc/kit_cmd.py`: CLI e interpretação de argumentos.
- `kitconc/kit_corpus.py`: criação, processamento, importação e exportação.
- `kitconc/export_corpus.py`: geração de ZIP.
- `tests/`: verificações existentes e novos casos de regressão.
