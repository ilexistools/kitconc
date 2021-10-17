# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os
import pickle

def get_languages():
    languages = ['english','portuguese']
    return languages

def set_language(language):
    # set destionation path
    dest = os.path.dirname(os.path.abspath(__file__)) + '/data/gui_lang.pickle'
    # get language dictionary
    dict_lang = None
    if language == 'english':
        dict_lang = english_language()
    elif language == 'portuguese':
        dict_lang = portuguese_language()
    # save dictionary
    if dict_lang != None:
        with open(dest,'wb') as fh:
            pickle.dump(dict_lang,fh)

def set_default_language():
    path = os.path.dirname(os.path.abspath(__file__)) + '/data/gui_lang_default.pickle'
    dest = os.path.dirname(os.path.abspath(__file__)) + '/data/gui_lang.pickle'
    if os.path.exists(dest):
        os.remove(dest)
    if os.path.exists(path):
        with open(path, 'rb') as fh:
            dict_lang = pickle.load(fh)
        with open(dest, 'wb') as fh:
            pickle.dump(dict_lang,fh)


def english_language():
    items = {
        # menubar
        0: "File",
        1: "Resources",
        2: "Models",
        3: "Help",
        # menu File
        4: "New corpus...",
        5: "Delete corpus",
        6: "Import...",
        7: "Export...",
        8: "Workspace",
        9: "Delete file",
        10: "Remove all",
        11: "Exit",
        # menu Resources
        12: "Add script...",
        13: "Delete script",
        14: "Texts to UTF-8...",
        # menu Models
        15: "Create model...",
        16: "Delete model...",
        17: "Add reference list...",
        18: "Add stoplist...",
        # menu Help
        19: "Help...",
        20: "Language...",
        21: "Create shortcut",
        22: "About Kitconc...",
        # corpus container
        23: "Corpus",
        24: "New...",
        25: "Delete",
        26: "Workspace",
        # Toolbox
        27: "Toolbox",
        28: "Tools",
        29: "Texts",
        30: "Wordlist",
        31: "Keywords",
        32: "WTFreq",
        33: "WFreqinfiles",
        34: "KWIC",
        35: "Concordance",
        36: "Collocates",
        37: "Collgraph",
        38: "Clusters",
        39: "N-grams",
        40: "Dispersion",
        41: "Keywords dispersion",
        42: "Word clouds",
        43: "Scripts",
        # Data files
        44: "Data files",
        45: "Files",
        # Tool options
        46: "Tool options",
        47: "Status:",
        # __load
        48: "Cannot load GUI language file.",
        49: "Open",
        50: "Rename",
        51: "Delete",
        52: "Remove all",
        53: "Output folder...",
        54: "Open script",
        55: "Add script",
        56: "Delete",
        57: "Scripts folder...",
        # __export_corpus
        58: "Running Export...",
        # __exec_export_corpus
        59: "Export corpus",
        60: "Success!\nThe current corpus was saved.",
        61: "Export corpus",
        62: "Attention!\nYou need to select a corpus to continue.",
        # __import_corpus
        63: "Running Import...",
        # __renamedialog
        64: "Rename",
        65: "File name:",
        66: "OK",
        67: "Cancel",
        # __newcorpusdialog
        68: "New corpus",
        69: "Source folder",
        70: "Browse...",
        71: "Name",
        72: "Language (model)",
        73: "Tagged",
        74: "Create",
        75: "Cancel",
        # __createmodelsdialog
        76: "Create language model",
        77: "Tagged corpus (directory)",
        78: "Browse...",
        79: "Model name (language)",
        80: "Create",
        81: "Cancel",
        # __deletemodeldialog
        82: "Delete model",
        83: "Model name (language)",
        84: "Delete",
        85: "Cancel",
        # __on_create_model
        86: "Creating model",
        # __create_model
        87: "Create model",
        88: "The model was created successfully!",
        89: "Create model",
        90: "The source directory is not valid.",
        # __delete_model
        91: "Delete model",
        92: "The model was deleted successfully!",
        # __add_reference_list
        93: "Add reference list",
        94: "Success!\nThe list was saved.",
        95: "Add reference list",
        96: "Attention!\nYou need to select a file to continue.",
        # __add_stoplist
        97: "Add stoplist",
        98: "Success!\nThe list was saved.",
        99: "Add stoplist",
        100: "Attention!\nYou need to select a file to continue.",
        # __on_texts2utf8
        101: "Running Texts to UTF8...",
        # __texts2utf8
        102: "Texts to UTF-8",
        103: "Do you want to see the texts in the target folder?",
        # __on_add_script
        104: "Add script",
        105: "File successfully added!",
        # __on_delete_script
        106: "Delete script",
        107: "Do you want to delete the script",
        # __on_download_examples
        108: "Running Downloading...",
        # __rename
        109: "Rename",
        110: "A file with the same name already exists.",
        # __check_workspace_onload
        111: "Workspace",
        112: "No workspace set.\n\nDo you want to set a workspace now?",
        # __about
        113: "Developed by José Lopes Moreira Filho",
        114: "About Kitconc",
        # __delete_datafile
        115: "Delete file",
        116: "Do you want to delete the file",
        # __delete_all_datafiles
        117: "Remove files",
        118: "Do you want to delete all files?",
        119: "removing ... ",
        # __corpus_info
        120: "Texts:",
        121: "Tokens:",
        122: "Types:",
        123: "TTR:",
        # __delete_corpus
        124: "Delete corpus",
        125: "Do you want to delete the",
        126: "Error when deleting corpus.",
        # __newcorpus_create
        127: "Creating corpus...",
        # __create_corpus
        128: "Attention!",
        129: "No corpus name or source folder.",
        # __on_open_excel
        130: "Reading file...",
        # __on_tool
        # Texts
        131: "Texts",
        # Wordlist
        132: "Execute",
        133: "lowercase",
        134: "Filename:",
        135: "wordlist",
        # WTFreq
        136: "lowercase",
        137: "Filename:",
        138: "wtfreq",
        # WFreqinfiles
        139: "lowercase",
        140: "Filename:",
        141: "wfreqinfiles",
        # Keywords
        142: "Statistical measure:",
        143: "use stoplist",
        144: "chi-square",
        145: "log-likelihood",
        146: "Filename:",
        147: "keywords",
        # KWIC
        148: "Search node:",
        149: "Case sensitive",
        150: "Regular expressions",
        151: "Part of speech (POS):",
        152: "Tagset:",
        153: "Horizon size:",
        154: "words",
        155: "chars",
        156: "Sorting:",
        157: "highlight",
        158: "Limit:",
        159: "Filename:",
        160: "kwic",
        # Concordance
        161: "Search node:",
        162: "Case sensitive",
        163: "Regular expressions",
        164: "Part of speech (POS):",
        165: "Tagset:",
        166: "Limit:",
        167: "Filename:",
        168: "concordance",
        # Collocates
        169: "Search node:",
        170: "Case sensitive",
        171: "Regular expressions",
        172: "Node POS:",
        173: "Tagset:",
        174: "Collocate POS:",
        175: "Tagset:",
        176: "Left span:",
        177: "Right span:",
        178: "Filename:",
        179: "collocates",
        # Collgraph
        180: "Search node:",
        181: "Case sensitive",
        182: "Regular expressions",
        183: "Node POS:",
        184: "Tagset:",
        185: "Collocate POS:",
        186: "Tagset:",
        187: "Left span:",
        188: "Right span:",
        # Clusters
        189: "Search node:",
        190: "lowercase",
        191: "Part of speech (POS):",
        192: "Tagset:",
        193: "Cluster size:",
        194: "Min freq:",
        195: "Min range:",
        196: "Filename:",
        197: "clusters",
        # N-grams
        198: "N-gram size:",
        199: "lowercase",
        200: "Part of speech (POS):",
        201: "Tagset:",
        202: "Min freq:",
        203: "Min range:",
        204: "Filename:",
        205: "ngrams",
        # Dispersion
        206: "Search node:",
        207: "Case sensitive",
        208: "Regular expressions",
        209: "Part of speech (POS):",
        210: "Tagset:",
        211: "Limit:",
        212: "Filename:",
        213: "dispersion",
        # Keywords dispersion
        214: "lowercase",
        215: "Limit:",
        216: "Filename:",
        217: "keywords_dispersion",
        # Word clouds
        218: "Wordlist type:",
        219: "use stoplist",
        220: "Colors:",
        221: "Limit:",
        222: "allow vertical",
        223: "Output format:",
        # Scripts
        224: "Args:",
        # Runnning
        225: "Running Wordlist...",
        226: "Running WTFreq",
        227: "Running WFreqinfiles...",
        228: "Running Keywords...",
        229: "Running KWIC...",
        230: "Running Concordance...",
        231: "Running Collocates...",
        232: "Running Collgraph...",
        233: "Running Clusters...",
        234: "Running N-grams...",
        235: "Running Dispersion...",
        236: "Running Keywords dispersion...",
        237: "Running Word clouds...",
        238: "Running Scripts...",
        # --choose_language
        239: "Choose language...",
        240: "Available Languages:",
        241: "Apply",
        242: "Cancel",
        # __aply_selected_language
        243: "Information",
        244: "The application must restart to complete the changes.",
        # some warnings
        245: "KWIC",
        246: "You need to enter a search node to continue.",
        247: "Concordance",
        248: "You need to enter a search node to continue.",
        249: "Collocates",
        250: "You need to enter a search node to continue.",
        251: "Collgraph",
        252: "You need to enter a search node to continue.",
        253: "Clusters",
        254: "You need to enter a search node to continue.",
        255: "Dispersion",
        256: "You need to enter a search node to continue.",
        257: "Statistical measure:"
    }
    print('Changing to english...')
    return items

def portuguese_language():
    items = {
        # menubar
        0: "Arquivo",
        1: "Recursos",
        2: "Modelos",
        3: "Ajuda",
        # menu File
        4: "Novo corpus...",
        5: "Excluir corpus",
        6: "Importar...",
        7: "Exportar...",
        8: "Pasta de trabalho",
        9: "Excluir arquivo",
        10: "Remover tudo",
        11: "Sair",
        # menu Resources
        12: "Adicionar script...",
        13: "Excluir script",
        14: "Textos para UTF-8...",
        # menu Models
        15: "Criar modelo...",
        16: "Excluir modelo...",
        17: "Adicionar lista de referência...",
        18: "Adicionar lista de exclusão...",
        # menu Help
        19: "Ajuda...",
        20: "Língua...",
        21: "Criar atalho",
        22: "Sobre o Kitconc...",
        # corpus container
        23: "Corpus",
        24: "Novo...",
        25: "Excluir",
        26: "Pasta de trabalho...",
        # Toolbox
        27: "Caixa de ferramentas",
        28: "Ferramentas",
        29: "Textos",
        30: "Lista de palavras",
        31: "Palavras-chave",
        32: "Palavras/etiquetas",
        33: "Frequência em arquivos",
        34: "KWIC",
        35: "Concordância",
        36: "Colocados",
        37: "Gráfico de colocados",
        38: "Pacotes",
        39: "N-gramas",
        40: "Dispersão",
        41: "Disperão de palavras-chave",
        42: "Nuvem de palavras",
        43: "Scripts",
        # Data files
        44: "Resultados",
        45: "Arquivos",
        # Tool options
        46: "Opções da ferramenta",
        47: "Progresso:",
        # __load
        48: "Não foi possível carregar o arquivo de língua da Interface.",
        49: "Abrir",
        50: "Renomear",
        51: "Excluir",
        52: "Remover tudo",
        53: "Pasta de resultados...",
        54: "Abrir script",
        55: "Adicionar script",
        56: "Excluir",
        57: "Pasta de scripts...",
        # __export_corpus
        58: "Processando...",
        # __exec_export_corpus
        59: "Exportar corpus",
        60: "Sucesso!\nO corpus atual foi salvo.",
        61: "Exportar corpus",
        62: "Atenção!\nÉ necessário selecionar um corpus para continuar.",
        # __import_corpus
        63: "Processando...",
        # __renamedialog
        64: "Renomear",
        65: "Nome do arquivo:",
        66: "OK",
        67: "Cancelar",
        # __newcorpusdialog
        68: "Novo corpus",
        69: "Pasta fonte",
        70: "Procurar...",
        71: "Nome",
        72: "Língua (modelo)",
        73: "Etiquetado",
        74: "Criar",
        75: "Cancelar",
        # __createmodelsdialog
        76: "Criar modelo",
        77: "Corpus etiquetado (diretório)",
        78: "Procurar...",
        79: "Nome do modelo (língua)",
        80: "Criar",
        81: "Cancelar",
        # __deletemodeldialog
        82: "Excluir modelo",
        83: "Nome do modelo (língua)",
        84: "Excluir",
        85: "Cancelar",
        # __on_create_model
        86: "Criando modelo",
        # __create_model
        87: "Criar modelo",
        88: "O modelo foi criado com sucesso!",
        89: "Criar modelo",
        90: "O diretório fonte não é válido.",
        # __delete_model
        91: "Excluir modelo",
        92: "O modelo foi excluído com sucesso!",
        # __add_reference_list
        93: "Adicionar lista de referência",
        94: "Sucesso!\nA lista foi salva.",
        95: "Adicionar lista de referência",
        96: "Atenção!\nÉ preciso selecionar um arquivo para continuar.",
        # __add_stoplist
        97: "Adicionar lista de exclusão",
        98: "Sucesso!\nA lista foi salva.",
        99: "Adicionar lista de exclusão",
        100: "Atenção!\nÉ preciso selecionar um arquivo para continuar.",
        # __on_texts2utf8
        101: "Processando...",
        # __texts2utf8
        102: "Textos para UTF-8",
        103: "Você deseja visualizar os textos na pasta de destino?",
        # __on_add_script
        104: "Adicionar script",
        105: "Arquivo adicionado com sucesso!",
        # __on_delete_script
        106: "Excluir script",
        107: "Deseja excluir o script",
        # __on_download_examples
        108: "Processando...",
        # __rename
        109: "Renomear",
        110: "Um arquivo com o mesmo nome já existe.",
        # __check_workspace_onload
        111: "Pasta de trabalho",
        112: "Nenhuma pasta de trabalho definida.\n\nDeseja definir uma agora?",
        # __about
        113: "Desenvolvido por José Lopes Moreira Filho",
        114: "Sobre o Kitconc",
        # __delete_datafile
        115: "Excluir arquivo",
        116: "Você deseja excluir o arquivo?",
        # __delete_all_datafiles
        117: "Excluir arquivos",
        118: "Você deseja excluir todos os arquivos?",
        119: "removendo ... ",
        # __corpus_info
        120: "Textos:",
        121: "Itens:",
        122: "Formas:",
        123: "RFI:",
        # __delete_corpus
        124: "Excluir corpus",
        125: "Você deseja excluir o",
        126: "Erro ao excluir corpus.",
        # __newcorpus_create
        127: "Criando o corpus...",
        # __create_corpus
        128: "Atenção!",
        129: "Nenhum nome de corpus ou pasta fonte.",
        # __on_open_excel
        130: "Lendo arquivo...",
        # __on_tool
        # Texts
        131: "Textos",
        # Wordlist
        132: "Executar",
        133: "minúsculas",
        134: "Arquivo:",
        135: "lista_de_palavras",
        # WTFreq
        136: "minúsculas",
        137: "Arquivo:",
        138: "palavras_etiquetas",
        # WFreqinfiles
        139: "minúsculas",
        140: "Arquivo:",
        141: "frequencia_em_arquivos",
        # Keywords
        142: "Medida estatística:",
        143: "usar lista de exclusão",
        144: "qui-quadrado",
        145: "log-likelihood",
        146: "Arquivo:",
        147: "palavras_chave",
        # KWIC
        148: "Nódulo:",
        149: "Maiúsculas/minúsculas",
        150: "Expressões regulares",
        151: "Etiquetas (POS):",
        152: "Etiquetas:",
        153: "Horizonte:",
        154: "palavras",
        155: "caracteres",
        156: "Classificar:",
        157: "Realçar classificação",
        158: "Limite:",
        159: "Arquivo:",
        160: "kwic",
        # Concordance
        161: "Nódulo:",
        162: "Maiúsculas/minúsculas",
        163: "Expressões regulares",
        164: "Etiquetas (POS):",
        165: "Etiquetas:",
        166: "Limite:",
        167: "Arquivo:",
        168: "concordancia",
        # Collocates
        169: "Nódulo:",
        170: "Maiúsculas/minúsculas",
        171: "Expressões regulares",
        172: "Nódulo (etiq.):",
        173: "Etiquetas:",
        174: "Colocado (etiq.):",
        175: "Etiquetas:",
        176: "Esquerda:",
        177: "Direita:",
        178: "Arquivo:",
        179: "colocados",
        # Collgraph
        180: "Nódulo:",
        181: "Maiúsculas/minúsculas",
        182: "Expressões regulares",
        183: "Nódulo (etiq.):",
        184: "Etiquetas:",
        185: "Colocado (etq.):",
        186: "Etiquetas:",
        187: "Esquerda:",
        188: "Direita:",
        # Clusters
        189: "Nódulo:",
        190: "minúscula",
        191: "Etiquetas (POS):",
        192: "Etiquetas:",
        193: "Tamanho do pacote:",
        194: "Freq. mínima:",
        195: "Alcance mínimo:",
        196: "Arquivo:",
        197: "pacotes",
        # N-grams
        198: "N-grama (tamanho): ",
        199: "minúscula",
        200: "Etiquetas (POS):",
        201: "Etiquetas:",
        202: "Freq. mínima.:",
        203: "Alcance mínimo:",
        204: "Arquivo:",
        205: "ngramas",
        # Dispersion
        206: "Nódulo:",
        207: "Maiúsculas/minúsculas",
        208: "Expressões regulares",
        209: "Etiquetas (POS):",
        210: "Etiquetas:",
        211: "Limite:",
        212: "Arquivo:",
        213: "dispersao",
        # Keywords dispersion
        214: "minúscula",
        215: "Limite:",
        216: "Arquivo:",
        217: "dispersao_pchave",
        # Word clouds
        218: "Tipo de lista:",
        219: "lista de exclusão",
        220: "Cores:",
        221: "Limite:",
        222: "permitir vertical",
        223: "Formato:",
        # Scripts
        224: "Argumentos:",
        # Runnning
        225: "Processando...",
        226: "Processando...",
        227: "Processando...",
        228: "Processando...",
        229: "Processando...",
        230: "Processando...",
        231: "Processando...",
        232: "Processando...",
        233: "Processando...",
        234: "Processando...",
        235: "Processando...",
        236: "Processando...",
        237: "Processando...",
        238: "Processando...",
        # --choose_language
        239: "Selecionar língua...",
        240: "Línguas disponíveis:",
        241: "Aplicar",
        242: "Cancelar",
        # __aply_selected_language
        243: "Infomação",
        244: "O programa deve ser reiniciado para exibir as alterações.",
        # some warnings
        245: "KWIC",
        246: "É preciso inserir um nódulo para continuar.",
        247: "Concordância",
        248: "É preciso inserir um nódulo para continuar.",
        249: "Colocados",
        250: "É preciso inserir um nódulo para continuar.",
        251: "Gráfico de colocados",
        252: "É preciso inserir um nódulo para continuar.",
        253: "Pacotes",
        254: "É preciso inserir um nódulo para continuar.",
        255: "Dispersão",
        256: "É preciso inserir um nódulo para continuar.",
        257: "Medida estatística:"
    }
    print('Changing to portuguese...')
    return items




