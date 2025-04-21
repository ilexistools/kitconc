# -*- coding: utf-8 -*-
# Author: jlopes@alumni.usp.br
import os
import pickle

def get_languages():
    languages = ['english','portuguese', 'spanish', 'french', 'japanese', 'chinese']
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
    elif language == 'spanish':
        dict_lang = spanish_language()
    elif language == 'french':
        dict_lang = french_language()
    elif language == 'japanese':
        dict_lang = japanese_language()
    elif language == 'chinese':
        dict_lang = chinese_language()
        
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

def spanish_language():
    items = {
        # barra de menú
        0: "Archivo",
        1: "Recursos",
        2: "Modelos",
        3: "Ayuda",
        # menú Archivo
        4: "Nuevo corpus...",
        5: "Eliminar corpus",
        6: "Importar...",
        7: "Exportar...",
        8: "Espacio de trabajo",
        9: "Eliminar archivo",
        10: "Eliminar todo",
        11: "Salir",
        # menú Recursos
        12: "Agregar script...",
        13: "Eliminar script",
        14: "Textos a UTF-8...",
        # menú Modelos
        15: "Crear modelo...",
        16: "Eliminar modelo...",
        17: "Agregar lista de referencia...",
        18: "Agregar lista de exclusión...",
        # menú Ayuda
        19: "Ayuda...",
        20: "Idioma...",
        21: "Crear acceso directo",
        22: "Acerca de Kitconc...",
        # contenedor corpus
        23: "Corpus",
        24: "Nuevo...",
        25: "Eliminar",
        26: "Espacio de trabajo",
        # Caja de herramientas
        27: "Caja de herramientas",
        28: "Herramientas",
        29: "Textos",
        30: "Lista de palabras",
        31: "Palabras clave",
        32: "WTFrecuencia",
        33: "Frecuencia en archivos",
        34: "KWIC",
        35: "Concordancia",
        36: "Colocados",
        37: "Gráfico de colocados",
        38: "Clusters",
        39: "N-gramas",
        40: "Dispersión",
        41: "Dispersión de palabras clave",
        42: "Nube de palabras",
        43: "Scripts",
        # Archivos de datos
        44: "Archivos de datos",
        45: "Archivos",
        # Opciones de herramienta
        46: "Opciones de herramienta",
        47: "Estado:",
        # __load
        48: "No se puede cargar archivo de idioma de la interfaz.",
        49: "Abrir",
        50: "Renombrar",
        51: "Eliminar",
        52: "Eliminar todo",
        53: "Carpeta de salida...",
        54: "Abrir script",
        55: "Agregar script",
        56: "Eliminar",
        57: "Carpeta de scripts...",
        # __export_corpus
        58: "Exportando...",
        # __exec_export_corpus
        59: "Exportar corpus",
        60: "¡Éxito!\nEl corpus actual ha sido guardado.",
        61: "Exportar corpus",
        62: "¡Atención!\nDebe seleccionar un corpus para continuar.",
        # __import_corpus
        63: "Importando...",
        # __renamedialog
        64: "Renombrar",
        65: "Nombre del archivo:",
        66: "Aceptar",
        67: "Cancelar",
        # __newcorpusdialog
        68: "Nuevo corpus",
        69: "Carpeta fuente",
        70: "Buscar...",
        71: "Nombre",
        72: "Idioma (modelo)",
        73: "Etiquetado",
        74: "Crear",
        75: "Cancelar",
        # __createmodelsdialog
        76: "Crear modelo de idioma",
        77: "Corpus etiquetado (directorio)",
        78: "Buscar...",
        79: "Nombre del modelo (idioma)",
        80: "Crear",
        81: "Cancelar",
        # __deletemodeldialog
        82: "Eliminar modelo",
        83: "Nombre del modelo (idioma)",
        84: "Eliminar",
        85: "Cancelar",
        # __on_create_model
        86: "Creando modelo",
        # __create_model
        87: "Crear modelo",
        88: "¡Modelo creado exitosamente!",
        89: "Crear modelo",
        90: "El directorio fuente no es válido.",
        # __delete_model
        91: "Eliminar modelo",
        92: "¡Modelo eliminado exitosamente!",
        # __add_reference_list
        93: "Agregar lista de referencia",
        94: "¡Éxito!\nLa lista fue guardada.",
        95: "Agregar lista de referencia",
        96: "¡Atención!\nDebe seleccionar un archivo para continuar.",
        # __add_stoplist
        97: "Agregar lista de exclusión",
        98: "¡Éxito!\nLa lista fue guardada.",
        99: "Agregar lista de exclusión",
        100: "¡Atención!\nDebe seleccionar un archivo para continuar.",
        # ... continuar para el resto de elementos siguiendo esta lógica
        # __on_texts2utf8
        101: "Ejecutando Textos a UTF8...",
        # __texts2utf8
        102: "Textos a UTF-8",
        103: "¿Desea ver los textos en la carpeta de destino?",
        # __on_add_script
        104: "Agregar script",
        105: "¡Archivo agregado con éxito!",
        # __on_delete_script
        106: "Eliminar script",
        107: "¿Desea eliminar el script?",
        # __on_download_examples
        108: "Ejecutando descarga...",
        # __rename
        109: "Renombrar",
        110: "Ya existe un archivo con el mismo nombre.",
        # __check_workspace_onload
        111: "Espacio de trabajo",
        112: "No hay espacio de trabajo configurado.\n\n¿Desea configurar uno ahora?",
        # __about
        113: "Desarrollado por José Lopes Moreira Filho",
        114: "Acerca de Kitconc",
        # __delete_datafile
        115: "Eliminar archivo",
        116: "¿Desea eliminar el archivo?",
        # __delete_all_datafiles
        117: "Eliminar archivos",
        118: "¿Desea eliminar todos los archivos?",
        119: "eliminando ... ",
        # __corpus_info
        120: "Textos:",
        121: "Tokens:",
        122: "Tipos:",
        123: "TTR:",
        # __delete_corpus
        124: "Eliminar corpus",
        125: "¿Desea eliminar el",
        126: "Error al eliminar el corpus.",
        # __newcorpus_create
        127: "Creando corpus...",
        # __create_corpus
        128: "¡Atención!",
        129: "Nombre del corpus o carpeta fuente no especificados.",
        # __on_open_excel
        130: "Leyendo archivo...",
        # __on_tool
        # Texts
        131: "Textos",
        # Wordlist
        132: "Ejecutar",
        133: "minúsculas",
        134: "Nombre del archivo:",
        135: "lista_de_palabras",
        # WTFreq
        136: "minúsculas",
        137: "Nombre del archivo:",
        138: "wtfreq",
        # WFreqinfiles
        139: "minúsculas",
        140: "Nombre del archivo:",
        141: "wfreqenarchivos",
        # Keywords
        142: "Medida estadística:",
        143: "usar lista de palabras vacías",
        144: "chi-cuadrado",
        145: "log-verosimilitud",
        146: "Nombre del archivo:",
        147: "palabras_clave",
        # KWIC
        148: "Nodo de búsqueda:",
        149: "Sensible a mayúsculas",
        150: "Expresiones regulares",
        151: "Categoría gramatical (POS):",
        152: "Conjunto de etiquetas:",
        153: "Tamaño del horizonte:",
        154: "palabras",
        155: "caracteres",
        156: "Orden:",
        157: "resaltar",
        158: "Límite:",
        159: "Nombre del archivo:",
        160: "kwic",
        # Concordance
        161: "Nodo de búsqueda:",
        162: "Sensible a mayúsculas",
        163: "Expresiones regulares",
        164: "Categoría gramatical (POS):",
        165: "Conjunto de etiquetas:",
        166: "Límite:",
        167: "Nombre del archivo:",
        168: "concordancia",
        # Collocates
        169: "Nodo de búsqueda:",
        170: "Sensible a mayúsculas",
        171: "Expresiones regulares",
        172: "POS del nodo:",
        173: "Conjunto de etiquetas:",
        174: "POS del colocador:",
        175: "Conjunto de etiquetas:",
        176: "Margen izquierdo:",
        177: "Margen derecho:",
        178: "Nombre del archivo:",
        179: "colocaciones",
        # Collgraph
        180: "Nodo de búsqueda:",
        181: "Sensible a mayúsculas",
        182: "Expresiones regulares",
        183: "POS del nodo:",
        184: "Conjunto de etiquetas:",
        185: "POS del colocador:",
        186: "Conjunto de etiquetas:",
        187: "Margen izquierdo:",
        188: "Margen derecho:",
        # Clusters
        189: "Nodo de búsqueda:",
        190: "minúsculas",
        191: "Categoría gramatical (POS):",
        192: "Conjunto de etiquetas:",
        193: "Tamaño del grupo:",
        194: "Frecuencia mínima:",
        195: "Rango mínimo:",
        196: "Nombre del archivo:",
        197: "grupos",
        # N-grams
        198: "Tamaño del n-grama:",
        199: "minúsculas",
        200: "Categoría gramatical (POS):",
        201: "Conjunto de etiquetas:",
        202: "Frecuencia mínima:",
        203: "Rango mínimo:",
        204: "Nombre del archivo:",
        205: "n-gramas",
        # Dispersion
        206: "Nodo de búsqueda:",
        207: "Sensible a mayúsculas",
        208: "Expresiones regulares",
        209: "Categoría gramatical (POS):",
        210: "Conjunto de etiquetas:",
        211: "Límite:",
        212: "Nombre del archivo:",
        213: "dispersión",
        # Keywords dispersion
        214: "minúsculas",
        215: "Límite:",
        216: "Nombre del archivo:",
        217: "dispersión_palabras_clave",
        # Word clouds
        218: "Tipo de lista de palabras:",
        219: "usar lista de palabras vacías",
        220: "Colores:",
        221: "Límite:",
        222: "permitir vertical",
        223: "Formato de salida:",
        # Scripts
        224: "Argumentos:",
        # Running
        225: "Ejecutando lista de palabras...",
        226: "Ejecutando WTFreq",
        227: "Ejecutando WFreqenarchivos...",
        228: "Ejecutando Palabras Clave...",
        229: "Ejecutando KWIC...",
        230: "Ejecutando Concordancia...",
        231: "Ejecutando Colocaciones...",
        232: "Ejecutando Collgraph...",
        233: "Ejecutando Grupos...",
        234: "Ejecutando N-gramas...",
        235: "Ejecutando Dispersión...",
        236: "Ejecutando Dispersión Palabras Clave...",
        237: "Ejecutando Nubes de Palabras...",
        238: "Ejecutando Scripts...",
        # --choose_language
        239: "Elegir idioma...",
        240: "Idiomas disponibles:",
        241: "Aplicar",
        242: "Cancelar",
        # __aply_selected_language
        243: "Información",
        244: "La aplicación debe reiniciarse para completar los cambios.",
        # some warnings
        245: "KWIC",
        246: "Debe ingresar un nodo de búsqueda para continuar.",
        247: "Concordancia",
        248: "Debe ingresar un nodo de búsqueda para continuar.",
        249: "Colocaciones",
        250: "Debe ingresar un nodo de búsqueda para continuar.",
        251: "Collgraph",
        252: "Debe ingresar un nodo de búsqueda para continuar.",
        253: "Grupos",
        254: "Debe ingresar un nodo de búsqueda para continuar.",
        255: "Dispersión",
        256: "Debe ingresar un nodo de búsqueda para continuar.",
        257: "Medida estadística:"

    }
    print('Cambiando a español...')
    return items

def french_language():
    items = {
        # barre de menu
        0: "Fichier",
        1: "Ressources",
        2: "Modèles",
        3: "Aide",
        # menu Fichier
        4: "Nouveau corpus...",
        5: "Supprimer corpus",
        6: "Importer...",
        7: "Exporter...",
        8: "Espace de travail",
        9: "Supprimer fichier",
        10: "Tout supprimer",
        11: "Quitter",
        # menu Ressources
        12: "Ajouter script...",
        13: "Supprimer script",
        14: "Textes en UTF-8...",
        # menu Modèles
        15: "Créer modèle...",
        16: "Supprimer modèle...",
        17: "Ajouter liste de référence...",
        18: "Ajouter liste d'exclusion...",
        # menu Aide
        19: "Aide...",
        20: "Langue...",
        21: "Créer raccourci",
        22: "À propos de Kitconc...",
        # conteneur corpus
        23: "Corpus",
        24: "Nouveau...",
        25: "Supprimer",
        26: "Espace de travail",
        # Boîte à outils
        27: "Boîte à outils",
        28: "Outils",
        29: "Textes",
        30: "Liste de mots",
        31: "Mots-clés",
        32: "WTFrequence",
        33: "Fréquence dans fichiers",
        34: "KWIC",
        35: "Concordance",
        36: "Cooccurrences",
        37: "Graphique de cooccurrences",
        38: "Clusters",
        39: "N-grammes",
        40: "Dispersion",
        41: "Dispersion mots-clés",
        42: "Nuage de mots",
        43: "Scripts",
        # Fichiers de données
        44: "Fichiers de données",
        45: "Fichiers",
        # Options des outils
        46: "Options des outils",
        47: "Statut :",
        # __load
        48: "Impossible de charger le fichier de langue de l'interface.",
        49: "Ouvrir",
        50: "Renommer",
        51: "Supprimer",
        52: "Tout supprimer",
        53: "Dossier de sortie...",
        54: "Ouvrir script",
        55: "Ajouter script",
        56: "Supprimer",
        57: "Dossier des scripts...",
        # Autres entrées à continuer dans la même logique si nécessaire...
        # __export_corpus
        58: "Exécution de l'exportation...",
        # __exec_export_corpus
        59: "Exporter le corpus",
        60: "Succès !\nLe corpus actuel a été sauvegardé.",
        61: "Exporter le corpus",
        62: "Attention !\nVous devez sélectionner un corpus pour continuer.",
        # __import_corpus
        63: "Exécution de l'importation...",
        # __renamedialog
        64: "Renommer",
        65: "Nom du fichier :",
        66: "OK",
        67: "Annuler",
        # __newcorpusdialog
        68: "Nouveau corpus",
        69: "Dossier source",
        70: "Parcourir...",
        71: "Nom",
        72: "Langue (modèle)",
        73: "Étiqueté",
        74: "Créer",
        75: "Annuler",
        # __createmodelsdialog
        76: "Créer un modèle linguistique",
        77: "Corpus étiqueté (répertoire)",
        78: "Parcourir...",
        79: "Nom du modèle (langue)",
        80: "Créer",
        81: "Annuler",
        # __deletemodeldialog
        82: "Supprimer le modèle",
        83: "Nom du modèle (langue)",
        84: "Supprimer",
        85: "Annuler",
        # __on_create_model
        86: "Création du modèle",
        # __create_model
        87: "Créer un modèle",
        88: "Le modèle a été créé avec succès !",
        89: "Créer un modèle",
        90: "Le répertoire source n'est pas valide.",
        # __delete_model
        91: "Supprimer le modèle",
        92: "Le modèle a été supprimé avec succès !",
        # __add_reference_list
        93: "Ajouter une liste de référence",
        94: "Succès !\nLa liste a été enregistrée.",
        95: "Ajouter une liste de référence",
        96: "Attention !\nVous devez sélectionner un fichier pour continuer.",
        # __add_stoplist
        97: "Ajouter une stoplist",
        98: "Succès !\nLa liste a été enregistrée.",
        99: "Ajouter une stoplist",
        100: "Attention !\nVous devez sélectionner un fichier pour continuer.",
        # __on_texts2utf8
        101: "Exécution de Textes en UTF8...",
        # __texts2utf8
        102: "Textes en UTF-8",
        103: "Voulez-vous voir les textes dans le dossier de destination ?",
        # __on_add_script
        104: "Ajouter un script",
        105: "Fichier ajouté avec succès !",
        # __on_delete_script
        106: "Supprimer le script",
        107: "Voulez-vous supprimer le script",
        # __on_download_examples
        108: "Téléchargement en cours...",
        # __rename
        109: "Renommer",
        110: "Un fichier portant le même nom existe déjà.",
        # __check_workspace_onload
        111: "Espace de travail",
        112: "Aucun espace de travail défini.\n\nVoulez-vous en définir un maintenant ?",
        # __about
        113: "Développé par José Lopes Moreira Filho",
        114: "À propos de Kitconc",
        # __delete_datafile
        115: "Supprimer le fichier",
        116: "Voulez-vous supprimer le fichier",
        # __delete_all_datafiles
        117: "Supprimer les fichiers",
        118: "Voulez-vous supprimer tous les fichiers ?",
        119: "suppression ...",
        # __corpus_info
        120: "Textes :",
        121: "Tokens :",
        122: "Types :",
        123: "TTR :",
        # __delete_corpus
        124: "Supprimer le corpus",
        125: "Voulez-vous supprimer le",
        126: "Erreur lors de la suppression du corpus.",
        # __newcorpus_create
        127: "Création du corpus...",
        # __create_corpus
        128: "Attention !",
        129: "Aucun nom de corpus ou dossier source.",
        # __on_open_excel
        130: "Lecture du fichier...",
        # __on_tool
        # Texts
        131: "Textes",
        # Wordlist
        132: "Exécuter",
        133: "minuscules",
        134: "Nom du fichier :",
        135: "liste_de_mots",
        # WTFreq
        136: "minuscules",
        137: "Nom du fichier :",
        138: "wtfreq",
        # WFreqinfiles
        139: "minuscules",
        140: "Nom du fichier :",
        141: "wfreqdansfichiers",
        # Keywords
        142: "Mesure statistique :",
        143: "utiliser une stoplist",
        144: "chi-carré",
        145: "vraisemblance logarithmique",
        146: "Nom du fichier :",
        147: "mots_clés",
        # KWIC
        148: "Nœud de recherche :",
        149: "Sensible à la casse",
        150: "Expressions régulières",
        151: "Partie du discours (POS) :",
        152: "Jeu d'étiquettes :",
        153: "Taille de l’horizon :",
        154: "mots",
        155: "caractères",
        156: "Tri :",
        157: "surligner",
        158: "Limite :",
        159: "Nom du fichier :",
        160: "kwic",
        # Concordance
        161: "Nœud de recherche :",
        162: "Sensible à la casse",
        163: "Expressions régulières",
        164: "Partie du discours (POS) :",
        165: "Jeu d'étiquettes :",
        166: "Limite :",
        167: "Nom du fichier :",
        168: "concordance",
        # Collocates
        169: "Nœud de recherche :",
        170: "Sensible à la casse",
        171: "Expressions régulières",
        172: "POS du nœud :",
        173: "Jeu d'étiquettes :",
        174: "POS du colocatif :",
        175: "Jeu d'étiquettes :",
        176: "Étendue gauche :",
        177: "Étendue droite :",
        178: "Nom du fichier :",
        179: "collocations",
        # Collgraph
        180: "Nœud de recherche :",
        181: "Sensible à la casse",
        182: "Expressions régulières",
        183: "POS du nœud :",
        184: "Jeu d'étiquettes :",
        185: "POS du colocatif :",
        186: "Jeu d'étiquettes :",
        187: "Étendue gauche :",
        188: "Étendue droite :",
        # Clusters
        189: "Nœud de recherche :",
        190: "minuscules",
        191: "Partie du discours (POS) :",
        192: "Jeu d'étiquettes :",
        193: "Taille du cluster :",
        194: "Fréquence minimale :",
        195: "Plage minimale :",
        196: "Nom du fichier :",
        197: "clusters",
        # N-grams
        198: "Taille du n-gramme :",
        199: "minuscules",
        200: "Partie du discours (POS) :",
        201: "Jeu d'étiquettes :",
        202: "Fréquence minimale :",
        203: "Plage minimale :",
        204: "Nom du fichier :",
        205: "ngrams",
        # Dispersion
        206: "Nœud de recherche :",
        207: "Sensible à la casse",
        208: "Expressions régulières",
        209: "Partie du discours (POS) :",
        210: "Jeu d'étiquettes :",
        211: "Limite :",
        212: "Nom du fichier :",
        213: "dispersion",
        # Keywords dispersion
        214: "minuscules",
        215: "Limite :",
        216: "Nom du fichier :",
        217: "dispersion_mots_clés",
        # Word clouds
        218: "Type de liste de mots :",
        219: "utiliser une stoplist",
        220: "Couleurs :",
        221: "Limite :",
        222: "autoriser le vertical",
        223: "Format de sortie :",
        # Scripts
        224: "Arguments :",
        # Runnning
        225: "Exécution de la liste de mots...",
        226: "Exécution de WTFreq",
        227: "Exécution de WFreqdansfichiers...",
        228: "Exécution des mots clés...",
        229: "Exécution de KWIC...",
        230: "Exécution de Concordance...",
        231: "Exécution de Collocations...",
        232: "Exécution de Collgraph...",
        233: "Exécution de Clusters...",
        234: "Exécution de N-grammes...",
        235: "Exécution de Dispersion...",
        236: "Exécution de Dispersion mots clés...",
        237: "Exécution des nuages de mots...",
        238: "Exécution de Scripts...",
        # --choose_language
        239: "Choisir la langue...",
        240: "Langues disponibles :",
        241: "Appliquer",
        242: "Annuler",
        # __aply_selected_language
        243: "Information",
        244: "L'application doit redémarrer pour appliquer les modifications.",
        # some warnings
        245: "KWIC",
        246: "Vous devez entrer un nœud de recherche pour continuer.",
        247: "Concordance",
        248: "Vous devez entrer un nœud de recherche pour continuer.",
        249: "Collocations",
        250: "Vous devez entrer un nœud de recherche pour continuer.",
        251: "Collgraph",
        252: "Vous devez entrer un nœud de recherche pour continuer.",
        253: "Clusters",
        254: "Vous devez entrer un nœud de recherche pour continuer.",
        255: "Dispersion",
        256: "Vous devez entrer un nœud de recherche pour continuer.",
        257: "Mesure statistique :"

    }
    print('Passage au français...')
    return items

def japanese_language():
    items = {
        # メニューバー
        0: "ファイル",
        1: "リソース",
        2: "モデル",
        3: "ヘルプ",
        # ファイルメニュー
        4: "新しいコーパス...",
        5: "コーパスを削除",
        6: "インポート...",
        7: "エクスポート...",
        8: "ワークスペース",
        9: "ファイルを削除",
        10: "すべて削除",
        11: "終了",
        # リソースメニュー
        12: "スクリプトを追加...",
        13: "スクリプトを削除",
        14: "テキストをUTF-8に...",
        # モデルメニュー
        15: "モデルを作成...",
        16: "モデルを削除...",
        17: "参照リストを追加...",
        18: "ストップリストを追加...",
        # ヘルプメニュー
        19: "ヘルプ...",
        20: "言語...",
        21: "ショートカットを作成",
        22: "Kitconcについて...",
        # コーパスコンテナ
        23: "コーパス",
        24: "新規...",
        25: "削除",
        26: "ワークスペース",
        # ツールボックス
        27: "ツールボックス",
        28: "ツール",
        29: "テキスト",
        30: "単語リスト",
        31: "キーワード",
        32: "単語テキスト頻度",
        33: "ファイル内単語頻度",
        34: "KWIC",
        35: "コンコーダンス",
        36: "コロケーション",
        37: "コロケーショングラフ",
        38: "クラスター",
        39: "Nグラム",
        40: "分散",
        41: "キーワード分散",
        42: "ワードクラウド",
        43: "スクリプト",
        # データファイル
        44: "データファイル",
        45: "ファイル",
        # ツールオプション
        46: "ツールオプション",
        47: "状態：",
        # __load
        48: "GUI言語ファイルを読み込めません。",
        49: "開く",
        50: "名前変更",
        51: "削除",
        52: "すべて削除",
        53: "出力フォルダ...",
        54: "スクリプトを開く",
        55: "スクリプトを追加",
        56: "削除",
        57: "スクリプトフォルダ...",
        # 必要に応じて他の項目も同様のロジックで追加...
        # __export_corpus
    58: "エクスポートを実行中...",
    # __exec_export_corpus
    59: "コーパスをエクスポート",
    60: "成功しました！\n現在のコーパスが保存されました。",
    61: "コーパスをエクスポート",
    62: "注意！\n続行するにはコーパスを選択する必要があります。",
    # __import_corpus
    63: "インポートを実行中...",
    # __renamedialog
    64: "名前を変更",
    65: "ファイル名：",
    66: "OK",
    67: "キャンセル",
    # __newcorpusdialog
    68: "新しいコーパス",
    69: "ソースフォルダ",
    70: "参照...",
    71: "名前",
    72: "言語（モデル）",
    73: "品詞タグ付き",
    74: "作成",
    75: "キャンセル",
    # __createmodelsdialog
    76: "言語モデルを作成",
    77: "タグ付きコーパス（ディレクトリ）",
    78: "参照...",
    79: "モデル名（言語）",
    80: "作成",
    81: "キャンセル",
    # __deletemodeldialog
    82: "モデルを削除",
    83: "モデル名（言語）",
    84: "削除",
    85: "キャンセル",
    # __on_create_model
    86: "モデルを作成中",
    # __create_model
    87: "モデルを作成",
    88: "モデルが正常に作成されました！",
    89: "モデルを作成",
    90: "ソースディレクトリが無効です。",
    # __delete_model
    91: "モデルを削除",
    92: "モデルが正常に削除されました！",
    # __add_reference_list
    93: "参照リストを追加",
    94: "成功しました！\nリストが保存されました。",
    95: "参照リストを追加",
    96: "注意！\n続行するにはファイルを選択してください。",
    # __add_stoplist
    97: "ストップリストを追加",
    98: "成功しました！\nリストが保存されました。",
    99: "ストップリストを追加",
    100: "注意！\n続行するにはファイルを選択してください。",
    # __on_texts2utf8
    101: "テキストをUTF8に変換中...",
    # __texts2utf8
    102: "テキストをUTF-8に変換",
    103: "出力フォルダでテキストを表示しますか？",
    # __on_add_script
    104: "スクリプトを追加",
    105: "ファイルが正常に追加されました！",
    # __on_delete_script
    106: "スクリプトを削除",
    107: "スクリプトを削除しますか？",
    # __on_download_examples
    108: "ダウンロードを実行中...",
    # __rename
    109: "名前を変更",
    110: "同じ名前のファイルがすでに存在します。",
    # __check_workspace_onload
    111: "ワークスペース",
    112: "ワークスペースが設定されていません。\n\n今すぐ設定しますか？",
    # __about
    113: "José Lopes Moreira Filho によって開発されました",
    114: "Kitconc について",
    # __delete_datafile
    115: "ファイルを削除",
    116: "ファイルを削除しますか？",
    # __delete_all_datafiles
    117: "ファイルを削除",
    118: "すべてのファイルを削除しますか？",
    119: "削除中 ... ",
    # __corpus_info
    120: "テキスト：",
    121: "トークン：",
    122: "タイプ：",
    123: "TTR：",
    # __delete_corpus
    124: "コーパスを削除",
    125: "削除しますか：",
    126: "コーパスの削除中にエラーが発生しました。",
    # __newcorpus_create
    127: "コーパスを作成中...",
    # __create_corpus
    128: "注意！",
    129: "コーパス名またはソースフォルダが指定されていません。",
    # __on_open_excel
    130: "ファイルを読み込み中...",
    # __on_tool
    # Texts
    131: "テキスト",
    # Wordlist
    132: "実行",
    133: "小文字",
    134: "ファイル名：",
    135: "ワードリスト",
    # WTFreq
    136: "小文字",
    137: "ファイル名：",
    138: "wtfreq",
    # WFreqinfiles
    139: "小文字",
    140: "ファイル名：",
    141: "wfreqinfiles",
    # Keywords
    142: "統計指標：",
    143: "ストップリストを使用",
    144: "カイ二乗",
    145: "対数尤度",
    146: "ファイル名：",
    147: "キーワード",
    # KWIC
    148: "検索ノード：",
    149: "大文字小文字を区別する",
    150: "正規表現",
    151: "品詞（POS）：",
    152: "タグセット：",
    153: "範囲サイズ：",
    154: "語",
    155: "文字",
    156: "ソート：",
    157: "ハイライト",
    158: "上限：",
    159: "ファイル名：",
    160: "kwic",
    # Concordance
    161: "検索ノード：",
    162: "大文字小文字を区別する",
    163: "正規表現",
    164: "品詞（POS）：",
    165: "タグセット：",
    166: "上限：",
    167: "ファイル名：",
    168: "コンコーダンス",
    # Collocates
    169: "検索ノード：",
    170: "大文字小文字を区別する",
    171: "正規表現",
    172: "ノードのPOS：",
    173: "タグセット：",
    174: "共起語のPOS：",
    175: "タグセット：",
    176: "左スパン：",
    177: "右スパン：",
    178: "ファイル名：",
    179: "共起語",
    # Collgraph
    180: "検索ノード：",
    181: "大文字小文字を区別する",
    182: "正規表現",
    183: "ノードのPOS：",
    184: "タグセット：",
    185: "共起語のPOS：",
    186: "タグセット：",
    187: "左スパン：",
    188: "右スパン：",
    # Clusters
    189: "検索ノード：",
    190: "小文字",
    191: "品詞（POS）：",
    192: "タグセット：",
    193: "クラスターサイズ：",
    194: "最小頻度：",
    195: "最小範囲：",
    196: "ファイル名：",
    197: "クラスタ",
    # N-grams
    198: "Nグラムのサイズ：",
    199: "小文字",
    200: "品詞（POS）：",
    201: "タグセット：",
    202: "最小頻度：",
    203: "最小範囲：",
    204: "ファイル名：",
    205: "nグラム",
    # Dispersion
    206: "検索ノード：",
    207: "大文字小文字を区別する",
    208: "正規表現",
    209: "品詞（POS）：",
    210: "タグセット：",
    211: "上限：",
    212: "ファイル名：",
    213: "分散",
    # Keywords dispersion
    214: "小文字",
    215: "上限：",
    216: "ファイル名：",
    217: "キーワード分散",
    # Word clouds
    218: "ワードリストの種類：",
    219: "ストップリストを使用",
    220: "色：",
    221: "上限：",
    222: "縦配置を許可",
    223: "出力形式：",
    # Scripts
    224: "引数：",
    # Running
    225: "ワードリストを実行中...",
    226: "WTFreqを実行中",
    227: "WFreqinfilesを実行中...",
    228: "キーワードを実行中...",
    229: "KWICを実行中...",
    230: "コンコーダンスを実行中...",
    231: "共起語を実行中...",
    232: "Collgraphを実行中...",
    233: "クラスタを実行中...",
    234: "Nグラムを実行中...",
    235: "分散を実行中...",
    236: "キーワード分散を実行中...",
    237: "ワードクラウドを実行中...",
    238: "スクリプトを実行中...",
    # --choose_language
    239: "言語を選択...",
    240: "利用可能な言語：",
    241: "適用",
    242: "キャンセル",
    # __aply_selected_language
    243: "情報",
    244: "変更を反映するにはアプリケーションを再起動する必要があります。",
    # some warnings
    245: "KWIC",
    246: "続行するには検索ノードを入力してください。",
    247: "コンコーダンス",
    248: "続行するには検索ノードを入力してください。",
    249: "共起語",
    250: "続行するには検索ノードを入力してください。",
    251: "Collgraph",
    252: "続行するには検索ノードを入力してください。",
    253: "クラスタ",
    254: "続行するには検索ノードを入力してください。",
    255: "分散",
    256: "続行するには検索ノードを入力してください。",
    257: "統計指標："

    }
    print('日本語に変更中...')
    return items

def chinese_language():
    items = {
        # 菜单栏
        0: "文件",
        1: "资源",
        2: "模型",
        3: "帮助",
        # 文件菜单
        4: "新建语料库...",
        5: "删除语料库",
        6: "导入...",
        7: "导出...",
        8: "工作空间",
        9: "删除文件",
        10: "全部删除",
        11: "退出",
        # 资源菜单
        12: "添加脚本...",
        13: "删除脚本",
        14: "文本转UTF-8...",
        # 模型菜单
        15: "创建模型...",
        16: "删除模型...",
        17: "添加参考列表...",
        18: "添加停用词表...",
        # 帮助菜单
        19: "帮助...",
        20: "语言...",
        21: "创建快捷方式",
        22: "关于Kitconc...",
        # 语料库容器
        23: "语料库",
        24: "新建...",
        25: "删除",
        26: "工作空间",
        # 工具箱
        27: "工具箱",
        28: "工具",
        29: "文本",
        30: "词汇表",
        31: "关键词",
        32: "单词文本频率",
        33: "文件中词频",
        34: "KWIC",
        35: "语境索引",
        36: "搭配",
        37: "搭配图",
        38: "词簇",
        39: "N-gram",
        40: "分布",
        41: "关键词分布",
        42: "词云",
        43: "脚本",
        # 数据文件
        44: "数据文件",
        45: "文件",
        # 工具选项
        46: "工具选项",
        47: "状态：",
        # __load
        48: "无法加载GUI语言文件。",
        49: "打开",
        50: "重命名",
        51: "删除",
        52: "全部删除",
        53: "输出文件夹...",
        54: "打开脚本",
        55: "添加脚本",
        56: "删除",
        57: "脚本文件夹...",
        # 如需更多元素请继续添加...
        # __export_corpus
    58: "正在导出...",
    # __exec_export_corpus
    59: "导出语料库",
    60: "成功！\n当前语料库已保存。",
    61: "导出语料库",
    62: "注意！\n请先选择一个语料库以继续。",
    # __import_corpus
    63: "正在导入...",
    # __renamedialog
    64: "重命名",
    65: "文件名：",
    66: "确定",
    67: "取消",
    # __newcorpusdialog
    68: "新建语料库",
    69: "源文件夹",
    70: "浏览...",
    71: "名称",
    72: "语言（模型）",
    73: "已标注",
    74: "创建",
    75: "取消",
    # __createmodelsdialog
    76: "创建语言模型",
    77: "已标注语料库（目录）",
    78: "浏览...",
    79: "模型名称（语言）",
    80: "创建",
    81: "取消",
    # __deletemodeldialog
    82: "删除模型",
    83: "模型名称（语言）",
    84: "删除",
    85: "取消",
    # __on_create_model
    86: "正在创建模型",
    # __create_model
    87: "创建模型",
    88: "模型创建成功！",
    89: "创建模型",
    90: "源目录无效。",
    # __delete_model
    91: "删除模型",
    92: "模型删除成功！",
    # __add_reference_list
    93: "添加参考列表",
    94: "成功！\n列表已保存。",
    95: "添加参考列表",
    96: "注意！\n请先选择一个文件以继续。",
    # __add_stoplist
    97: "添加停用词表",
    98: "成功！\n列表已保存。",
    99: "添加停用词表",
    100: "注意！\n请先选择一个文件以继续。",
    # __on_texts2utf8
    101: "正在转换文本为UTF-8...",
    # __texts2utf8
    102: "转换文本为UTF-8",
    103: "是否查看目标文件夹中的文本？",
    # __on_add_script
    104: "添加脚本",
    105: "文件添加成功！",
    # __on_delete_script
    106: "删除脚本",
    107: "是否删除该脚本？",
    # __on_download_examples
    108: "正在下载示例...",
    # __rename
    109: "重命名",
    110: "已存在同名文件。",
    # __check_workspace_onload
    111: "工作区",
    112: "未设置工作区。\n\n是否现在设置？",
    # __about
    113: "由 José Lopes Moreira Filho 开发",
    114: "关于 Kitconc",
    # __delete_datafile
    115: "删除文件",
    116: "是否删除该文件？",
    # __delete_all_datafiles
    117: "删除所有文件",
    118: "是否删除所有文件？",
    119: "正在删除 ... ",
    # __corpus_info
    120: "文本：",
    121: "词元（Token）：",
    122: "类型（Type）：",
    123: "TTR（类型-词元比）：",
    # __delete_corpus
    124: "删除语料库",
    125: "是否删除该",
    126: "删除语料库时出错。",
    # __newcorpus_create
    127: "正在创建语料库...",
    # __create_corpus
    128: "注意！",
    129: "语料库名称或源文件夹未指定。",
    # __on_open_excel
    130: "正在读取文件...",
    # __on_tool
    # Texts
    131: "文本",
    # Wordlist
    132: "执行",
    133: "小写",
    134: "文件名：",
    135: "词表",
    # WTFreq
    136: "小写",
    137: "文件名：",
    138: "wtfreq",
    # WFreqinfiles
    139: "小写",
    140: "文件名：",
    141: "wfreqinfiles",
    # Keywords
    142: "统计方法：",
    143: "使用停用词表",
    144: "卡方检验",
    145: "对数似然比",
    146: "文件名：",
    147: "关键词",
    # KWIC
    148: "搜索词：",
    149: "区分大小写",
    150: "正则表达式",
    151: "词性（POS）：",
    152: "标签集：",
    153: "窗口大小：",
    154: "词",
    155: "字符",
    156: "排序方式：",
    157: "高亮显示",
    158: "限制：",
    159: "文件名：",
    160: "kwic",
    # Concordance
    161: "搜索词：",
    162: "区分大小写",
    163: "正则表达式",
    164: "词性（POS）：",
    165: "标签集：",
    166: "限制：",
    167: "文件名：",
    168: "索引表",
    # Collocates
    169: "搜索词：",
    170: "区分大小写",
    171: "正则表达式",
    172: "节点词性（POS）：",
    173: "标签集：",
    174: "搭配词词性（POS）：",
    175: "标签集：",
    176: "左跨度：",
    177: "右跨度：",
    178: "文件名：",
    179: "搭配词",
    # Collgraph
    180: "搜索词：",
    181: "区分大小写",
    182: "正则表达式",
    183: "节点词性：",
    184: "标签集：",
    185: "搭配词词性：",
    186: "标签集：",
    187: "左跨度：",
    188: "右跨度：",
    # Clusters
    189: "搜索词：",
    190: "小写",
    191: "词性（POS）：",
    192: "标签集：",
    193: "词块大小：",
    194: "最小频率：",
    195: "最小覆盖范围：",
    196: "文件名：",
    197: "词块",
    # N-grams
    198: "N-gram 大小：",
    199: "小写",
    200: "词性（POS）：",
    201: "标签集：",
    202: "最小频率：",
    203: "最小覆盖范围：",
    204: "文件名：",
    205: "n-gram",
    # Dispersion
    206: "搜索词：",
    207: "区分大小写",
    208: "正则表达式",
    209: "词性（POS）：",
    210: "标签集：",
    211: "限制：",
    212: "文件名：",
    213: "分布",
    # Keywords dispersion
    214: "小写",
    215: "限制：",
    216: "文件名：",
    217: "关键词分布",
    # Word clouds
    218: "词表类型：",
    219: "使用停用词表",
    220: "颜色：",
    221: "限制：",
    222: "允许垂直显示",
    223: "输出格式：",
    # Scripts
    224: "参数：",
    # Running
    225: "正在执行词表...",
    226: "正在执行 WTFreq",
    227: "正在执行 WFreqinfiles...",
    228: "正在执行关键词...",
    229: "正在执行 KWIC...",
    230: "正在执行索引表...",
    231: "正在执行搭配词...",
    232: "正在执行 Collgraph...",
    233: "正在执行词块...",
    234: "正在执行 n-gram...",
    235: "正在执行分布...",
    236: "正在执行关键词分布...",
    237: "正在执行词云...",
    238: "正在执行脚本...",
    # --choose_language
    239: "选择语言...",
    240: "可用语言：",
    241: "应用",
    242: "取消",
    # __aply_selected_language
    243: "提示",
    244: "应用必须重新启动以完成更改。",
    # some warnings
    245: "KWIC",
    246: "请先输入搜索词。",
    247: "索引表",
    248: "请先输入搜索词。",
    249: "搭配词",
    250: "请先输入搜索词。",
    251: "Collgraph",
    252: "请先输入搜索词。",
    253: "词块",
    254: "请先输入搜索词。",
    255: "分布",
    256: "请先输入搜索词。",
    257: "统计方法："

    }
    print('切换至中文...')
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




