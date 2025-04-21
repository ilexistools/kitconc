# -*- coding: utf-8 -*-
# Author: jlopes@alumni.usp.br
import os,sys 
from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import PIL.Image
import PIL.ImageTk
import kitconc 
from kitconc.kit_corpus import Corpus 
from kitconc import version 
from kitconc.kit_cmd import Kit 
from kitconc.core import Config
import threading
import subprocess
import pickle
import platform
from kitconc import kit_app_language
from ttkbootstrap import Window
import ttkbootstrap as tkb
from ttkbootstrap import Style
from ttkbootstrap.widgets import Radiobutton


class KitApp(Window):

    def __init__(self):
        super().__init__(themename="flatly")  # ou outro tema 
        self.__platform = sys.platform
        self.__load()
    
    def __load(self):
        """This function loads window's config using tkbootstrap"""

        # platform
        self.__platform = sys.platform

        # get python implementation
        self.implementation = platform.python_implementation()

        # get current dir
        self.__cwd = os.getcwd()

        # get script path
        self.__path = os.path.dirname(os.path.abspath(__file__))

        # check shortcut in Windows
        try:
            if self.__platform in ('win32', 'win64'):
                self.state('zoomed')
                bat_path = os.path.join(self.__cwd, 'kitconc.bat')
                if os.path.exists(bat_path):
                    os.remove(bat_path)
            else:
                self.attributes('-zoomed', True)  # Para macOS/Linux (pode variar por WM)
        except Exception as e:
            print(e)

        # load GUI language
        try:
            with open(os.path.join(self.__path, 'data/gui_lang.pickle'), 'rb') as fh:
                self.__gui_lang = pickle.load(fh)
            
        except Exception as e:
            print(e)
            kit_app_language.set_default_language()

        # set window config
        self.title('Kitconc ' + version.__version__)
        window_height = 720
        window_width = 1280
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        self.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        self.resizable(True, True)

        # ensure the window ID is created
        self.update_idletasks()
        import ctypes

        if sys.platform.startswith('win'):
            # On Windows: clear the WS_MAXIMIZEBOX bit via Win32 API
            GWL_STYLE      = -16
            WS_MAXIMIZEBOX = 0x00010000
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
            style &= ~WS_MAXIMIZEBOX
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)

        else:
            # On X11/Linux: hint to the WM that this is a "dialog"
            try:
                self.attributes('-type', 'dialog')
            except ttk.TclError:
                pass

        # load icons
        try:
            self.__load_icons()
            self.update_idletasks()
        except Exception as e:
            print(e)
            

        # set python icon for window
        try:
            self.tk.call('wm', 'iconphoto', self._w, self.icon_python)
        except Exception as e:
            print(e)

        # create kit object and set workspace
        self.kit = Kit()
        self.kit.corpus_in_use = None

        # add widgets to window
        self.__add_widgets()
        self.__check_workspace_onload()
        self.__load_corpora()

        # add popup menu
        self.popup_menu = Menu(self, tearoff=0)
        self.popup_menu.add_command(label=self.__gui_lang[49], command=self.__on_open_excel)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label=self.__gui_lang[50], command=self.__renamedialog)
        self.popup_menu.add_command(label=self.__gui_lang[51], command=self.__delete_datafile)
        self.popup_menu.add_command(label=self.__gui_lang[52], command=self.__delete_all_datafiles)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label=self.__gui_lang[53], command=self.__open_output_folder)

        # add popup dropdown menu on right click for files treeview
        self.frm_trv_files.bind('<Button-3>', self.__popup)

        # add popup menu to tools
        self.popup_menu_tools = Menu(self, tearoff=0)
        #self.popup_menu_tools.add_command(label=self.__gui_lang[54], command=self.__on_open_script)
        self.popup_menu_tools.add_separator()
        #self.popup_menu_tools.add_command(label=self.__gui_lang[55], command=self.__on_add_script)
        #self.popup_menu_tools.add_command(label=self.__gui_lang[56], command=self.__on_delete_script)
        self.popup_menu_tools.add_separator()
        #self.popup_menu_tools.add_command(label=self.__gui_lang[57], command=self.__open_scripts_folder)

        # add popup dropdown menu on right click for tools treeview
        #self.frm_trv_tools.bind('<Button-3>', self.__popup_tools)

        
    def __add_widgets(self):
        """Adiciona widgets responsivos com seleção de ferramenta via Combobox."""

        # Toolbar no topo
        toolbar = ttk.Frame(self, padding=5)
        toolbar.pack(side="top", fill="x")

        for title, items in [
            (self.__gui_lang[0], [
                (self.__gui_lang[4], self.__newcorpusdialog),
                (self.__gui_lang[5], self.__delete_corpus),
                None,
                (self.__gui_lang[6], self.__import_corpus),
                (self.__gui_lang[7], self.__export_corpus),
                None,
                (self.__gui_lang[8], self.__set_workspace),
                None,
                (self.__gui_lang[9], self.__delete_datafile),
                (self.__gui_lang[10], self.__delete_all_datafiles),
                None,
                (self.__gui_lang[11], self.quit),
            ]),
            (self.__gui_lang[1], [
                #(self.__gui_lang[12], self.__on_add_script),
                #(self.__gui_lang[13], self.__on_delete_script),
                None,
                (self.__gui_lang[14], self.__on_texts2utf8),
            ]),
            (self.__gui_lang[2], [
                (self.__gui_lang[15], self.__createmodelsdialog),
                (self.__gui_lang[16], self.__on_delete_model),
                None,
                (self.__gui_lang[17], self.__add_reference_list),
                (self.__gui_lang[18], self.__add_stoplist),
            ]),
            (self.__gui_lang[3], [
                (self.__gui_lang[19], self.__show_help),
                (self.__gui_lang[20], self.__choose_language),
                (self.__gui_lang[21], self.__create_shortcut),
                (self.__gui_lang[22], self.__about),
            ]),
        ]:
            mb = ttk.Menubutton(toolbar, text=title)
            menu = Menu(mb, tearoff=0)
            for item in items:
                if item is None:
                    menu.add_separator()
                else:
                    menu.add_command(label=item[0], command=item[1])
            mb["menu"] = menu
            mb.pack(side="left", padx=5)

        # Frame principal
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Seleção de corpus
        self.frm_lbl_corpora = ttk.LabelFrame(main_frame, text=self.__gui_lang[23])
        self.frm_lbl_corpora.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)

        frm_top = ttk.Frame(self.frm_lbl_corpora)
        frm_top.pack(fill="x", padx=5, pady=5)

        self.frm_cmb_corpora = ttk.Combobox(frm_top, state='readonly')
        self.frm_cmb_corpora.pack(side="left", padx=5)
        self.__load_corpora()
        self.frm_cmb_corpora.bind("<<ComboboxSelected>>", lambda e: self.__oncorpusselected())

        self.frm_lbl_info = ttk.Label(frm_top, text='')
        self.frm_lbl_info.pack(side="left", padx=10)

        frm_btns = ttk.Frame(self.frm_lbl_corpora)
        frm_btns.pack(fill="x", padx=5, pady=5)

        """
        self.frm_btn_newcorpus = ttk.Button(frm_btns, text=self.__gui_lang[24], command=self.__newcorpusdialog, bootstyle="primary")
        self.frm_btn_newcorpus.pack(side="left", padx=5)
        self.frm_btn_deletecorpus = ttk.Button(frm_btns, text=self.__gui_lang[25], command=self.__delete_corpus, bootstyle="danger")
        self.frm_btn_deletecorpus.pack(side="left", padx=5)
        self.frm_btn_workspace = ttk.Button(frm_btns, text=self.__gui_lang[26], command=self.__set_workspace, bootstyle="info")
        self.frm_btn_workspace.pack(side="left", padx=5)
        """
        
         # Tools – Solid Buttons com destaque no selecionado
        tools_frame = ttk.LabelFrame(main_frame, text=self.__gui_lang[46] if hasattr(self, '__gui_lang') else 'Tools')
        tools_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))

        # set Texts as default
        self.selected_tool = self.__gui_lang[29]

        tools = [
            (self.__gui_lang[29], self.__gui_lang[29]),   # Texts
            (self.__gui_lang[30], self.__gui_lang[30]),
            (self.__gui_lang[31], self.__gui_lang[31]),
            (self.__gui_lang[32], self.__gui_lang[32]),
            (self.__gui_lang[33], self.__gui_lang[33]),
            (self.__gui_lang[34], self.__gui_lang[34]),
            (self.__gui_lang[35], self.__gui_lang[35]),
            (self.__gui_lang[36], self.__gui_lang[36]),
            (self.__gui_lang[37], self.__gui_lang[37]),
            (self.__gui_lang[38], self.__gui_lang[38]),
            (self.__gui_lang[39], self.__gui_lang[39]),
            (self.__gui_lang[40], self.__gui_lang[40]),
            #(self.__gui_lang[41], self.__gui_lang[41]),
        ]
        tools = [t for t in tools if t]

        # variável de seleção e mapeamentos
        self.tool_var = StringVar(value=tools[0][1])
        self._tool_map = {display: value for display, value in tools}
        self._tool_buttons = {}

        # container para os botões
        frm_tools = ttk.Frame(tools_frame)
        frm_tools.pack(fill="x", padx=5, pady=5)

        # criação dos botões
        for display, value in tools:
            btn = ttk.Button(
                frm_tools,
                text=display,
                bootstyle="primary",
                command=lambda v=value: self._on_tool_button(v)
            )
            btn.pack(side="left", padx=3, pady=2)
            self._tool_buttons[value] = btn

        # destaca o inicial
        self._highlight_selected_tool()


        # define proporções das colunas
        main_frame.grid_rowconfigure(2, weight=1)
        for col in range(2): main_frame.grid_columnconfigure(col, weight=1)

        # Coluna 1: Opções
        self.frm_lbl_options = ttk.LabelFrame(main_frame, text=self.__gui_lang[46])
        self.frm_lbl_options.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        # Coluna 2: Arquivos
        self.frm_lbl_files = ttk.LabelFrame(main_frame, text=self.__gui_lang[44])
        self.frm_lbl_files.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)

        files_container = ttk.Frame(self.frm_lbl_files)
        files_container.pack(fill="both", expand=True, padx=5, pady=5)
        files_container.columnconfigure(0, weight=1)
        files_container.rowconfigure(0, weight=1)

        self.frm_trv_files = ttk.Treeview(files_container, selectmode='browse')
        self.frm_trv_files.grid(row=0, column=0, sticky="nsew")
        self.frm_scroll_files = ttk.Scrollbar(files_container, orient="vertical", command=self.frm_trv_files.yview)
        self.frm_scroll_files.grid(row=0, column=1, sticky="ns")
        self.frm_trv_files.configure(yscrollcommand=self.frm_scroll_files.set)
        self.frm_trv_files.heading("#0", text=self.__gui_lang[45])
        self.frm_trv_files.bind("<Double-1>", lambda e: self.__on_open_excel())

        # Rodapé
        bottom_status = ttk.Frame(self)
        bottom_status.pack(side="bottom", fill="x", padx=10, pady=5)
        self.frm_lbl_status = ttk.Label(bottom_status, text=self.__gui_lang[47] + ' ')
        self.frm_lbl_status.pack(side="left")
        self.frm_pgb = ttk.Progressbar(bottom_status, mode='determinate', maximum=100)
        self.frm_pgb.pack(side="left", fill="x", expand=True, padx=10)


    def _on_tool_button(self, value):
        """Callback único para todos os botões de ferramenta."""
        self.tool_var.set(value)
        self.__on_tool_selected(value)
        self._highlight_selected_tool()

    def _highlight_selected_tool(self):
        """Atualiza o estilo de cada botão, destacando o selecionado."""
        selected = self.tool_var.get()
        for v, btn in self._tool_buttons.items():
            if v == selected:
                btn.configure(bootstyle="success")
            else:
                btn.configure(bootstyle="primary")
            



    def __on_tool_selected(self, value):
        self.selected_tool = value
        # Aqui você pode chamar self.__on_tool() ou outras lógicas
        print(f"Ferramenta selecionada: {value}")
        self.__on_tool()  # se quiser manter compatibilidade com lógica antiga





        
   
    
    # export corpus
    def __export_corpus(self):
        if self.implementation == 'CPython':
            def callback():
                self.__show_progress(self.__gui_lang[58])
                t = threading.Thread (target=self.__exec_export_corpus)
                t.start()
            self.after_idle(callback)
        else:
            self.__exec_export_corpus()
    
    def __exec_export_corpus(self):
        if self.kit.corpus_in_use != None:
            source_folder = filedialog.askdirectory()
            if len(source_folder)!= 0:
                self.kit.do_export_corpus(source_folder)
                messagebox.showinfo(self.__gui_lang[59], self.__gui_lang[60])
        else:
            messagebox.showwarning(self.__gui_lang[61], self.__gui_lang[62])
        self.__hide_progress()
    
    
    # import corpus
    def __import_corpus(self):
        if self.implementation == 'CPython':
            def callback():
                self.__show_progress(self.__gui_lang[63])
                t = threading.Thread (target=self.__exec_import_corpus)
                t.start()
            self.after_idle(callback)
        else:
            target=self.__exec_import_corpus()

    def __exec_import_corpus(self):
        filename = filedialog.askopenfilename()
        if len(filename)!= 0:
            self.kit.do_import_corpus(filename)
            self.__load_corpora()
        self.__hide_progress()
    
    # rename dialog
    def __renamedialog(self):
        def callback():
            # window
            self.top = Toplevel()
            self.top.title(self.__gui_lang[64])
            window_height = 100
            window_width = 280
            screen_width = self.top.winfo_screenwidth()
            screen_height = self.top.winfo_screenheight()
            x_cordinate = int((screen_width/2) - (window_width/2))
            y_cordinate = int((screen_height/2) - (window_height/2))
            self.top.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))
            self.top.resizable(False, False)
            self.top.tk.call('wm', 'iconphoto', self.top._w, self.icon_python)
            self.top.focus()
            self.top.update_idletasks()
            # widgets
            lbl_filename = ttk.Label(self.top,text=self.__gui_lang[65])
            lbl_filename.place(x=5,y=5)
            self.newname = StringVar()
            txt_filename = ttk.Entry(self.top,textvariable=self.newname)
            txt_filename.place(x=5,y=25,width=150)
            btn_ok = ttk.Button(self.top,text=self.__gui_lang[66],width=10,command=self.__rename)
            btn_ok.place(x=5,y=60)
            btn_cancel = ttk.Button(self.top,text=self.__gui_lang[67],width=10,command=self.__rename_cancel)
            btn_cancel.place(x=105,y=60)
            # set focus
            i = self.frm_trv_files.selection()[0]
            filename = self.frm_trv_files.item(i,'text').strip()
            if len(filename)!=0:
                self.newname.set(filename)
            txt_filename.focus()
        self.after_idle(callback)
    
    # get languages 
    def __get_languages(self):
        I = 11
        E = 7
        files = os.listdir(self.__path + '/data/')
        self.__languages=[]
        d = dict()
        for filename in files:
            if filename.endswith('_model.pickle'):
                try:
                    language = filename[:-13]
                    if language not in d:
                        d[language]=None
                except:
                    pass 
            elif filename.startswith('pos_tagger_'):
                try:
                    size = len(filename)
                    m = size - (I+E)
                    language = filename[I:(I+m)]
                    if language not in d:
                        d[language]=None
                except:
                    pass
        for k in d:
            if k != 'language':
                self.__languages.append(k)
        # add a no-tagging model for raw texts
        self.__languages.append('no-tagging')

    # new corpus dialog
    def __newcorpusdialog(self):
        # obtém idiomas
        self.__get_languages()

        # cria janela
        self.top = Toplevel(self.master)
        self.top.title(self.__gui_lang[68])
        # desabilita maximize/redimensionamento
        self.top.resizable(False, False)
        self.top.tk.call('wm', 'iconphoto', self.top._w, self.icon_python)

        # layout básico
        self.top.columnconfigure(0, weight=1)
        self.top.rowconfigure(0, weight=1)
        main = ttk.Frame(self.top, padding=10)
        main.grid(sticky='nsew')
        for i in range(3):
            main.columnconfigure(i, weight=1)
        for j in range(5):
            main.rowconfigure(j, weight=0)
        main.rowconfigure(1, weight=1)

        # --- widgets linha 0-4 ---
        ttk.Label(main, text=self.__gui_lang[69])\
            .grid(row=0, column=0, sticky='w')
        self.source = StringVar()
        ttk.Entry(main, textvariable=self.source, state='readonly')\
            .grid(row=1, column=0, columnspan=2, sticky='ew', padx=(0,5))
        ttk.Button(main, text=self.__gui_lang[70],
                command=self.__newcorpus_browse)\
            .grid(row=1, column=2, sticky='e')

        ttk.Label(main, text=self.__gui_lang[71])\
            .grid(row=2, column=0, sticky='w', pady=(10,0))
        ttk.Label(main, text=self.__gui_lang[72])\
            .grid(row=2, column=1, columnspan=2,
                sticky='w', pady=(10,0))

        self.corpusname = StringVar()
        ttk.Entry(main, textvariable=self.corpusname)\
            .grid(row=3, column=0, sticky='ew', padx=(0,5))

        self.cmb_newcorpus_language = ttk.Combobox(
            main,
            state='readonly',
            values=self.__languages
        )
        self.cmb_newcorpus_language.grid(
            row=3, column=1, columnspan=2, sticky='ew'
        )
        self.cmb_newcorpus_language.current(0)

        self.chk_tagged = ttk.Checkbutton(
            main, text=self.__gui_lang[73]
        )
        self.chk_tagged.state(['!alternate','!disabled'])
        self.chk_tagged.grid(
            row=4, column=0, sticky='w', pady=(10,0)
        )

        ttk.Button(main, text=self.__gui_lang[74],
                command=self.__newcorpus_create)\
            .grid(row=4, column=1, sticky='e',
                padx=(5,5), pady=(10,0))
        ttk.Button(main, text=self.__gui_lang[75],
                command=self.__newcorpus_cancel)\
            .grid(row=4, column=2, sticky='w',
                pady=(10,0))

        # foco inicial
        main.focus_set()

        # força layout para poder medir
        self.top.update_idletasks()
        natural_w = self.top.winfo_width()
        natural_h = self.top.winfo_height()

        # centraliza na tela
        screen_w = self.top.winfo_screenwidth()
        screen_h = self.top.winfo_screenheight()
        x = (screen_w - natural_w) // 2
        y = (screen_h - natural_h) // 2
        self.top.geometry(f"{natural_w}x{natural_h}+{x}+{y}")

        # limita tamanho ao natural
        self.top.maxsize(natural_w, natural_h)

        # torna modal
        self.top.wait_visibility()
        self.top.grab_set()








    
    
    # create models dialog
    def __createmodelsdialog(self):
        # cria janela
        self.top = Toplevel(self.master)
        self.top.title(self.__gui_lang[76])
        # permite apenas redimensionar em largura
        self.top.resizable(False, False)
        self.top.tk.call('wm', 'iconphoto', self.top._w, self.icon_python)

        # layout básico e responsivo
        self.top.columnconfigure(0, weight=1)
        self.top.rowconfigure(0, weight=1)
        main = ttk.Frame(self.top, padding=10)
        main.grid(sticky='nsew')
        # coluna 1 expande; colunas 0 e 2 fixas
        for col in (0, 1, 2):
            main.columnconfigure(col, weight=(1 if col == 1 else 0))
        # três linhas de widgets
        for row in range(3):
            main.rowconfigure(row, weight=0)

        # --- widgets ---

        # Fonte (com botão de busca)
        ttk.Label(main, text=self.__gui_lang[77])\
            .grid(row=0, column=0, sticky='w',  padx=(0,5), pady=(0,5))
        self.source = StringVar()
        ttk.Entry(main, textvariable=self.source, state='readonly')\
            .grid(row=0, column=1, sticky='ew', padx=(0,5), pady=(0,5))
        ttk.Button(main, text=self.__gui_lang[78],
                command=self.__newcorpus_browse)\
            .grid(row=0, column=2, sticky='e', padx=(5,0), pady=(0,5))

        # Nome do modelo / linguagem
        ttk.Label(main, text=self.__gui_lang[79])\
            .grid(row=1, column=0, sticky='w',  padx=(0,5), pady=(0,5))
        self.language = StringVar()
        ttk.Entry(main, textvariable=self.language)\
            .grid(row=1, column=1, columnspan=2, sticky='ew',
                padx=(0,5), pady=(0,5))

        # Botões de ação
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=2, column=0, columnspan=3,
                    sticky='e', pady=(10,0))
        btn_frame.columnconfigure(0, weight=1)
        ttk.Button(btn_frame, text=self.__gui_lang[80],
                command=self.__on_create_model)\
            .grid(row=0, column=1, padx=(5,0))
        ttk.Button(btn_frame, text=self.__gui_lang[81],
                command=self.__create_model_cancel)\
            .grid(row=0, column=2, padx=(5,0))

        # foco inicial
        self.language_entry = main.nametowidget(main.grid_slaves(row=1, column=1)[0])
        self.language_entry.focus_set()

        # força layout e calcula tamanho natural
        self.top.update_idletasks()
        w = self.top.winfo_width()
        h = self.top.winfo_height()
        sw = self.top.winfo_screenwidth()
        sh = self.top.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2

        # aplica tamanho e centraliza
        self.top.geometry(f"{w}x{h}+{x}+{y}")
        # opcional: evita que altura seja alterada
        self.top.minsize(w, h)

        # torna modal
        self.top.wait_visibility()
        self.top.grab_set()
        self.master.wait_window(self.top)


    
    # create delete model dialog
    def __deletemodeldialog(self):
        def callback():
            # recarrega lista de modelos
            self.__languages = []
            self.__get_languages()

            # cria janela oculta e modal
            self.top = Toplevel(self.master)
            #self.top.withdraw()
            self.top.transient(self.master)
            self.top.title(self.__gui_lang[82])
            self.top.resizable(False, False)
            self.top.tk.call('wm', 'iconphoto', self.top._w, self.icon_python)

            # container principal
            main = ttk.Frame(self.top, padding=10)
            main.grid(sticky='nsew')
            # colunas: label fixa, combobox expansível
            main.columnconfigure(0, weight=0)
            main.columnconfigure(1, weight=1)
            # duas linhas: uma para widgets, outra para botões
            main.rowconfigure(0, weight=0)
            main.rowconfigure(1, weight=0)

            # --- widgets ---
            # Label de instrução
            ttk.Label(main, text=self.__gui_lang[83]) \
                .grid(row=0, column=0, sticky='w', padx=(0,5), pady=(0,5))
            # Combobox de modelos
            self.cmb_language_model = ttk.Combobox(
                main,
                state='readonly',
                values=self.__languages
            )
            self.cmb_language_model.grid(row=0, column=1, sticky='ew', pady=(0,5))
            self.cmb_language_model.current(0)

            # Botões
            btn_frame = ttk.Frame(main)
            btn_frame.grid(row=1, column=0, columnspan=2,
                        sticky='e', pady=(10,0))
            btn_frame.columnconfigure(0, weight=1)
            ttk.Button(btn_frame, text=self.__gui_lang[84],
                    command=self.__delete_model) \
                .grid(row=0, column=1, padx=(5,0))
            ttk.Button(btn_frame, text=self.__gui_lang[85],
                    command=self.__delete_model_cancel) \
                .grid(row=0, column=2, padx=(5,0))

            # foco inicial
            self.cmb_language_model.focus_set()

            # calcula tamanho natural e centraliza
            self.top.update_idletasks()
            w = self.top.winfo_width()
            h = self.top.winfo_height()
            sw = self.top.winfo_screenwidth()
            sh = self.top.winfo_screenheight()
            x = (sw - w) // 2
            y = (sh - h) // 2
            self.top.geometry(f"{w}x{h}+{x}+{y}")

            # mostra e torna modal
            self.top.deiconify()
            self.top.grab_set()
            self.master.wait_window(self.top)

        self.after_idle(callback)

    
    # create model 
    def __on_create_model(self):
        def callback():
            self.__show_progress(self.__gui_lang[86])
            t = threading.Thread (target=self.__create_model)
            t.start()
        self.top.after_idle(callback)
        
    def __create_model(self):
        source_folder = str(self.source.get()).strip()
        language = str(self.language.get()).strip().replace(' ','_')
        language = language.replace('model','mdl')
        self.top.destroy()
        if os.path.exists(source_folder):
            models = kitconc.kit_models.Models()
            models.nltk_create_model(source_folder,language,show_progress=True)
            messagebox.showinfo(self.__gui_lang[87], self.__gui_lang[88])
        else:
            messagebox.showwarning(self.__gui_lang[89], self.__gui_lang[90])
        self.focus()
        self.__hide_progress()
    
    def __on_delete_model(self):
        self.__deletemodeldialog()
    
    def __delete_model(self):
        language_model = str(self.cmb_language_model.get()).strip()
        # pos tagger
        path = self.__path + '/data/pos_tagger_' + language_model + '.pickle'
        if os.path.exists(path):
            os.remove(path)
        # word tokenizer
        path = self.__path + '/data/word_tokenizer_' + language_model + '.pickle'
        if os.path.exists(path):
            os.remove(path)
        # sent tokenizer
        path = self.__path + '/data/sent_tokenizer_' + language_model + '.pickle'
        if os.path.exists(path):
            os.remove(path)
        # reflist
        path = self.__path + '/data/reflist_' + language_model + '.tab'
        if os.path.exists(path):
            os.remove(path)
        # stoplist
        path = self.__path + '/data/stoplist_' + language_model + '.tab'
        if os.path.exists(path):
            os.remove(path)
        self.top.destroy()
        messagebox.showinfo(self.__gui_lang[91], self.__gui_lang[92])
        self.focus()
        
            
    
    def __delete_model_cancel(self):
        def callback():
            self.top.destroy()
            self.focus()
        self.top.after_idle(callback)
        
        
    
    def __create_model_cancel(self):
        def callback():
            self.top.destroy()
            self.focus()
        self.top.after_idle(callback)
                
    # add reference list
    def __add_reference_list(self):
        if self.kit.corpus_in_use != None:
            filename  = filedialog.askopenfilename(filetypes = (("Text Documents","*.txt"),("Text Documents","*.tab")))
            if len(filename)!= 0:
                if os.path.exists(filename):
                    config = Config()
                    with open(filename,'r',encoding='utf-8') as fh:
                        content = fh.read()
                    config.add_reflist(content, self.kit.language)
                    messagebox.showinfo(self.__gui_lang[93], self.__gui_lang[94])
            else:
                messagebox.showwarning(self.__gui_lang[95], self.__gui_lang[96])
        self.__hide_progress()
    
    # add stoplist list
    def __add_stoplist(self):
        if self.kit.corpus_in_use != None:
            filename  = filedialog.askopenfilename(filetypes = (("Text Documents","*.txt"),("Text Documents","*.tab")))
            if len(filename)!= 0:
                if os.path.exists(filename):
                    config = Config()
                    with open(filename,'r',encoding='utf-8') as fh:
                        content = fh.read()
                    config.add_stoplist(content, self.kit.language)
                    messagebox.showinfo(self.__gui_lang[97], self.__gui_lang[98])
            else:
                messagebox.showwarning(self.__gui_lang[99], self.__gui_lang[100])
        self.__hide_progress()
        
        
        
    # load icons
    def __load_icons (self):
        """loads icons: python, tool, excel and script"""
        self.icon_python = self.__load_icon('python')
        self.icon_script = self.__load_icon('script')
        self.icon_tool = self.__load_icon('tool')
        self.icon_excel = self.__load_icon('excel')
        self.icon_text = self.__load_icon('text')
        
    def __load_icon(self,filename):
        """Loads a png image from file and converts to use in tkinter"""
        try:
            if os.path.exists(self.__path + '/' + filename + '.png'):
                im = PIL.Image.open(self.__path + '/' + filename + '.png')
                return PIL.ImageTk.PhotoImage(im)
            elif os.path.exists(self.__path + '/data/images/' + filename + '.png'):
                im = PIL.Image.open(self.__path + '/data/images/' + filename  + '.png')
                return PIL.ImageTk.PhotoImage(im)
        except Exception as e:
            print(e) 
            
    # show progress
    def __show_progress(self,s):
        if self.implementation == 'CPython':
            self.frm_lbl_status['text']= 'Status: ' + s
            self.frm_pgb['mode'] = 'indeterminate'
            self.frm_pgb.start()
            if self.__platform == 'win32' or self.__platform == 'win64':
                try:
                    self.config(cursor='wait')
                except Exception as e:
                    print(e)
            self.update()
        else:
            self.frm_lbl_status['text'] = 'Status: ' + s
            self.frm_pgb['mode'] = 'indeterminate'
            self.frm_pgb.start()


    # hide progress
    def __hide_progress(self):
        if self.implementation == 'CPython':
            self.frm_lbl_status['text']='Status:'
            self.frm_pgb['mode'] = 'determinate'
            self.frm_pgb.stop()
            self.config(cursor='')
            self.update()
        else:
            self.frm_lbl_status['text'] = 'Status:'
            self.frm_pgb['mode'] = 'determinate'
            self.frm_pgb.stop()



    # help
    def __show_help(self):
        def callback():
            try:
                import webbrowser
                url = "https://github.com/ilexistools/kitconc"
                webbrowser.open(url,new=2)
            except Exception as e:
                    print(e)
        self.after_idle(callback)
    
    # text2utf8
    
    def __on_texts2utf8(self):
        def callback():
            self.__show_progress(self.__gui_lang[101])
            t = threading.Thread (target=self.__texts2utf8)
            t.start()
        self.after_idle(callback)
    
    def __texts2utf8(self):
        try:
            source_folder = filedialog.askdirectory()
            if len(source_folder)!= 0:
                dest_folder = source_folder + '/utf8'
                if os.path.exists(dest_folder)==False:
                    os.mkdir(dest_folder)
                self.kit.do_text2utf8('"' + source_folder + '" "' + dest_folder + '"' )
                flag = messagebox.askyesno(self.__gui_lang[102], self.__gui_lang[103])
                if flag == True:
                    self.__open_folder(dest_folder)
        except Exception as e:
            print(e)
        self.__hide_progress()
     
    
    # add script
    def __on_add_script(self):
        def callback():
            import shutil
            filename = filedialog.askopenfilename(title='Select file',filetypes = (("python script","*.py"),("all files","*.*")))
            if len(filename.strip())!=0:
                if os.path.exists(filename)==True:
                    name= os.path.basename(filename)
                    shutil.copy(filename, self.__path + '/data/scripts/' + name)
                    self.__load_tools()
                    messagebox.showinfo(self.__gui_lang[104], self.__gui_lang[105])
        self.after_idle(callback)
    
    # delete script
    def __on_delete_script(self):
        def callback():
            filename = ''
            if len(self.frm_trv_tools.selection())!= 0:
                i = self.frm_trv_tools.selection()[0]
                filename = self.frm_trv_tools.item(i,'text').strip()
            if len(filename)!=0 and self.frm_trv_tools.parent(filename)=='Scripts':
                s=messagebox.askyesno(self.__gui_lang[106], self.__gui_lang[107] + ' "' + filename +'"?')
                if s == True:
                    try:
                        os.remove(self.__path + '/data/scripts/' + filename + '.py')
                    except:
                        pass
            self.focus()
            self.__load_tools()
        self.after_idle(callback)
        
    
    # download examples
    def __on_download_examples(self):
        def callback():
            self.__show_progress(self.__gui_lang[108])
            t = threading.Thread (target=self.__download_examples)
            t.start()
        self.top.after_idle(callback)
    
    def __download_examples(self):
        filename = filedialog.askdirectory()
        if len(filename.strip())!=0:
            self.kit.do_examples(' --dest_path "' + filename + '"')
            self.__hide_progress()
    
    def __popup(self,event):
        if len(self.frm_trv_files.get_children())!=0:
            self.popup_menu.post(event.x_root,event.y_root)
    
    def __popup_tools(self,event):
        if len(self.frm_trv_tools.get_children())!=0:
            i = self.frm_trv_tools.selection()[0]
            tool = self.frm_trv_tools.item(i,'text').strip()
            if tool == 'Scripts' or len(self.script_name)!= 0:
                self.popup_menu_tools.post(event.x_root,event.y_root)
    
    def __open_output_folder(self):
        try:
            filename = self.frm_trv_files.item(0,'text').strip() + '.xlsx'
            output_path = self.kit.workspace +  self.kit.corpus_in_use + '/output/' 
            if self.__platform == 'win32' or self.__platform == 'win64':
                subprocess.Popen(r'explorer /select,"%s"' % os.path.normpath(output_path + filename))
            elif self.__platform == 'linux' or self.__platform == 'linux2':
                subprocess.Popen(["xdg-open", output_path])
            elif self.__platform == 'darwin':
                subprocess.Popen(["open", output_path])
            else:
                subprocess.Popen(["xdg-open", output_path])
        except Exception as e:
            print(e) 
    
    def __open_scripts_folder(self):
        try:
            if len(self.script_name)!=0:
                scripts_path = self.__path + '/data/scripts/' 
                if self.__platform == 'win32' or self.__platform == 'win64':
                    subprocess.Popen(r'explorer /select,"%s"' % os.path.normpath(scripts_path + self.script_name + '.py'))
                elif self.__platform == 'linux' or self.__platform == 'linux2':
                    subprocess.Popen(["xdg-open", scripts_path])
                elif self.__platform == 'darwin':
                    subprocess.Popen(["open", scripts_path])
                else:
                    subprocess.Popen(["xdg-open", scripts_path])
        except Exception as e:
            print(e)
    
    def __open_folder(self,folder_path):
        try:
            if os.path.exists(folder_path)==True:
                if self.__platform == 'win32' or self.__platform == 'win64':
                    subprocess.Popen(r'explorer /select,"%s"' % os.path.normpath(folder_path))
                elif self.__platform == 'linux' or self.__platform == 'linux2':
                    subprocess.Popen(["xdg-open", folder_path])
                elif self.__platform == 'darwin':
                    subprocess.Popen(["open", folder_path])
                else:
                    subprocess.Popen(["xdg-open", folder_path])
        except Exception as e:
            print(e) 
            
    
    def __rename(self):
        i = self.frm_trv_files.selection()[0]
        filename = self.frm_trv_files.item(i,'text').strip()
        if len(filename) != 0:
            new_name = self.newname.get().strip().replace(' ','_')
            if len(new_name) != 0:
                output_path = self.kit.workspace +  self.kit.corpus_in_use + '/output/'
                if os.path.exists(output_path  + filename + '.xlsx'):
                    if os.path.exists(output_path  + new_name + '.xlsx')==True:
                        messagebox.showwarning(self.__gui_lang[109], self.__gui_lang[110])
                    else:
                        os.rename(output_path  + filename + '.xlsx',output_path  + new_name + '.xlsx')
                        self.__load_datafiles()
                        self.__rename_cancel()
    
    def __rename_cancel(self):
        def callback():
                self.top.destroy()
                self.focus()
        self.top.after_idle(callback)
                
        
        
    def __check_workspace_onload(self):
        if os.path.exists(self.__path + '/kitconc.tmp'):
            self.kit.load_workspace()
        elif os.path.exists('kitconc.tmp'):
            self.kit.load_workspace()
        else:
            s = messagebox.askyesno(self.__gui_lang[111], self.__gui_lang[112])
            if s ==True:
                self.__set_workspace()
    
    def __set_workspace(self):
        filename = filedialog.askdirectory()
        if len(filename) != 0:
            if os.path.isdir(filename):
                self.kit.do_workspace(filename) 
                self.__load_corpora()
            else:
                self.__check_workspace_onload()
        
    def __about(self):
        def callback():
            info=[]
            info.append('Kitconc ' + version.__version__)
            info.append(self.__gui_lang[113])
            info.append('jlopes@alumni.usp.br')
            messagebox.showinfo(self.__gui_lang[114], '\n'.join(info))
        self.after_idle(callback)
    
    def __create_shortcut(self):
        def callback():
            filename = filedialog.askdirectory()
            if os.path.isdir(filename):
                if self.__platform == 'win32' or self.__platform == 'win64':
                    # create kitconc.bat for desktop
                    s = []
                    # the script uses vb to create a link in the desktop
                    script = ("""@echo off
                    set SCRIPT="%TEMP%\%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"
                    echo Set oWS = WScript.CreateObject("WScript.Shell") >> %SCRIPT%
                    echo sLinkFile = "%USERPROFILE%\Desktop\Kitconc.lnk" >> %SCRIPT%
                    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
                    echo oLink.TargetPath = "<target_path>" >> %SCRIPT%
                    echo oLink.IconLocation = "<icon>" >> %SCRIPT%
                    echo oLink.Save >> %SCRIPT%
                    cscript /nologo %SCRIPT%
                    del %SCRIPT%""")
                    script = script.replace('<target_path>',self.__path + '/kitconc.bat')
                    script = script.replace('<icon>',self.__path + '/data/images/python3.ico')
                    s.append(script)
                    s.append('start python ' + self.__path + '/kit_app.py')
                    with open (filename + '/kitconc.bat','w',encoding='utf-8') as fh:
                        fh.write('\n'.join(s))
                    # create kitconc.bat for kitconc
                    s = []
                    s.append("@echo off")
                    s.append('start python ' + self.__path + '/kit_app.py')
                    with open (self.__path + '/kitconc.bat','w',encoding='utf-8') as fh:
                        fh.write('\n'.join(s))
                else:
                    s = []
                    s.append('#!/bin/bash')
                    s.append('python ' + self.__path + '/kit_app.py')
                    with open (filename + '/kitconc.sh','w',encoding='utf-8') as fh:
                        fh.write('\n'.join(s))
        self.after_idle(callback)
        
    
    def __load_corpora(self):
        try:
            corpora = []
            for filename in os.listdir(self.kit.workspace):
                if os.path.isdir(self.kit.workspace + '/' + filename):
                    if os.path.exists(self.kit.workspace + '/' + filename + '/info.tab'):
                        corpora.append(filename)
            self.frm_cmb_corpora['values'] = corpora 
        except:
            pass 
    
    def __load_datafiles(self):
        if self.kit.corpus_in_use != None:
            for i in self.frm_trv_files.get_children():
                self.frm_trv_files.delete(i)
            
            if os.path.exists(self.kit.workspace +'/' + self.kit.corpus_in_use + '/output'):
                files = os.listdir(self.kit.workspace +'/' + self.kit.corpus_in_use + '/output')
                i = 0
                for filename in files:
                    if filename.endswith('.xlsx') or filename.endswith('.xls'):
                        if filename.startswith('~')==False:
                            self.frm_trv_files.insert('','end',str(i),text=filename.replace('.xlsx',''),image=self.icon_excel)
                            i+=1
                            
    def __delete_datafile(self):
        def callback():
            if self.kit.corpus_in_use != None:
                filename = ''
                if len(self.frm_trv_files.selection())!= 0:
                    i = self.frm_trv_files.selection()[0]
                    filename = self.frm_trv_files.item(i,'text').strip()
                if len(filename)!=0:
                    s=messagebox.askyesno(self.__gui_lang[115], self.__gui_lang[116] + ' "' + filename +'"?')
                    if s == True:
                        try:
                            os.remove(self.kit.workspace + self.kit.corpus_in_use + '/output/' + filename + '.xlsx')
                        except:
                            pass
                self.focus()
                self.__load_datafiles()
        self.after_idle(callback)
    
    def __delete_all_datafiles(self):
        def callback():
            try:
                if self.kit.corpus_in_use != None:
                    if messagebox.askyesno(self.__gui_lang[117], self.__gui_lang[118]):
                        output_path = self.kit.workspace + self.kit.corpus_in_use + '/output/'
                        files = os.listdir(output_path)
                        if len(files) != 0:
                            for filename in files:
                                os.remove(output_path + filename)
                                print(self.__gui_lang[119] + filename)
                        self.__load_datafiles()
            except Exception as e:
                print(e)
        self.after_idle(callback)
    
    def __oncorpusselected(self):
        def callback():
            corpusname = self.frm_cmb_corpora.get()
            self.kit.do_use(corpusname)
            self.frm_lbl_info['text'] = self.__corpus_info()
            self.__load_datafiles()
            tags = {}
            try:
                with open(os.path.join(self.kit.workspace, self.kit.corpus_in_use,'data/idx/tags.pickle'),'rb') as fh:
                    tags = pickle.load(fh)
                self.tagset = list(tags.values())
            except (FileNotFoundError, EOFError, pickle.UnpicklingError):
                # no tags yet, just use empty
                self.tagset = []
            if self.frm_lbl_options != None:
                if len(self.frm_lbl_options.winfo_children())!=0:
                    for widget in self.frm_lbl_options.winfo_children():
                        widget.destroy()
                    self.frm_lbl_options.update()
            self.__on_tool()
        self.after_idle(callback)
    
    def __corpus_info(self):
        import locale
        locale.setlocale(locale.LC_ALL, '')
        corpus_info = []
        if os.path.exists(self.kit.workspace +'/' + self.kit.corpus_in_use + '/info.tab'):
            with open (self.kit.workspace +'/' + self.kit.corpus_in_use + '/info.tab','r', encoding='utf-8') as fh:
                for line in fh:
                    if len(line.strip())!=0:
                        fields = line.strip().split('\t')
                        if len(fields) >= 2:
                            if fields[0].startswith('Textfiles'):
                                corpus_info.append(self.__gui_lang[120] + ' %s' % locale.format_string("%d", int(fields[1]), grouping=True) )
                            elif fields[0].startswith('Tokens'):
                                corpus_info.append(self.__gui_lang[121] + ' %s' % locale.format_string("%d", int(fields[1]), grouping=True)  )
                            elif fields[0].startswith('Types'):
                                corpus_info.append(self.__gui_lang[122] + ' %s' % locale.format_string("%d", int(fields[1]), grouping=True) )
                            elif fields[0].startswith('Type/token'):
                                corpus_info.append(self.__gui_lang[123] + ' %s' % round(float(fields[1]),2) )
                            elif fields[0].startswith('Source:'):
                                self.textfiles_path = fields[1]
        return ' - '.join(corpus_info) + '     '
                        
                    
    def __corpus_exists(self,corpus_name):
        flag = False
        if self.kit.workspace is not None:
            if os.path.exists(self.kit.workspace + '/' + corpus_name + '/info.tab'):
                flag = True
        return flag 
    
    def __delete_corpus(self):
        def callback():
            if len(self.frm_cmb_corpora.get())!=0:
                s=messagebox.askyesno(self.__gui_lang[124], self.__gui_lang[125] + ' "' + self.frm_cmb_corpora.get() +'" corpus?')
                if s == True:
                    try:
                        corpus_name = self.frm_cmb_corpora.get()
                        if self.__corpus_exists(corpus_name):
                            import shutil
                            shutil.rmtree(self.kit.workspace + corpus_name)
                            self.frm_cmb_corpora.set('')
                            # clear corpus selection
                            self.kit.corpus_in_use = None
                            # clear tool selection
                            if len(self.frm_lbl_options.winfo_children()) != 0:
                                for widget in self.frm_lbl_options.winfo_children():
                                    widget.destroy()
                                self.frm_lbl_options.update()
                            # clear files in the box
                            for item in self.frm_trv_files.get_children():
                                self.frm_trv_files.delete(item)
                            self.frm_trv_files.update()

                            # clear corpus info
                            self.frm_lbl_info['text']=''
                    except:
                        print(self.__gui_lang[126])
            self.focus()
            self.__load_corpora()
            self.__load_datafiles()
        self.after_idle(callback)
    
    def __newcorpus_browse(self):
        def callback():
            filename = filedialog.askdirectory()
            self.source.set( filename)
            self.top.focus()
        self.top.after_idle(callback)
        
    def __newcorpus_create(self):
        if self.implementation == 'CPython':
            def callback():
                self.__show_progress(self.__gui_lang[127])
                t = threading.Thread(target=self.__create_corpus)
                t.start()
            self.top.after_idle(callback)
        else:
            def callback():
                self.__show_progress(self.__gui_lang[127])
                t = threading.Thread(target=self.__create_corpus)
                t.start()
                self.top.destroy()
                self.focus()
            self.top.after_idle(callback)
    
    def __create_corpus(self):
        if len(self.corpusname.get().strip()) != 0 and len(self.source.get().strip()) != 0:
            # capturando do atributo, não mais de self.top.children
            language = self.cmb_newcorpus_language.get()
            tagged = 'True' if self.chk_tagged.instate(['selected']) else 'False'
            self.top.destroy()
            self.kit.do_create(
                f"{self.corpusname.get()} {self.source.get()} {language} --tagged {tagged}"
            )
            self.__load_corpora()
            self.focus()
            self.__hide_progress()
        else:
            messagebox.showwarning(self.__gui_lang[128], self.__gui_lang[129])
            self.top.focus()

        
    def __newcorpus_cancel(self):
        def callback():
            self.top.destroy()
            self.focus()
        self.top.after_idle(callback)
    
    def __on_open_excel(self):
        def callback():
            self.__show_progress(self.__gui_lang[130])
            t = threading.Thread (target=self.__open_excel)
            t.start()
        self.after_idle(callback)
        
    def __open_excel(self):
        if len(self.frm_trv_files.selection())!= 0:
            i = self.frm_trv_files.selection()[0]
            filename = self.frm_trv_files.item(i,'text')
            self.kit.do_open(filename)
        self.__hide_progress()
    
    # open text
    
    def __on_open_text(self):
        def callback():
            self.__show_progress(self.__gui_lang[130])
            t = threading.Thread (target=self.__open_text)
            t.start()
        self.after_idle(callback)
    
    def __open_text(self):
        if len(self.trv_texts.selection())!= 0:
            i = self.trv_texts.selection()[0]
            filename = self.trv_texts.item(i,'text')
            filename = self.textfiles_path + '/' + filename.strip() 
            try:
                if len(filename) != 0:
                    if self.__platform == 'win32' or self.__platform == 'win64':
                        os.system('notepad.exe ' + filename)
                    elif self.__platform == 'linux' or self.__platform == 'linux2':
                        subprocess.Popen(['gedit', filename])
                    elif self.__platform == 'darwin':
                        subprocess.Popen(["open", filename])
                    else:
                        subprocess.Popen(["xdg-open", filename])
            except Exception as e:
                print(e)
                
        self.__hide_progress()
    
    # open script
    def __on_open_script(self):
        def callback():
            self.__show_progress(self.__gui_lang[130])
            t = threading.Thread (target=self.__open_script)
            t.start()
        self.after_idle(callback)
        
    def __open_script(self):
        try:
            if len(self.script_name) != 0:
                filename = self.__path + '/data/scripts/' + self.script_name + '.py'
                if self.__platform == 'win32' or self.__platform == 'win64':
                    os.system('notepad.exe ' + filename)
                elif self.__platform == 'linux' or self.__platform == 'linux2':
                    subprocess.Popen(['gedit', filename])
                elif self.__platform == 'darwin':
                    subprocess.Popen(["open", filename])
                else:
                    subprocess.Popen(["xdg-open", filename])
        except Exception as e:
            print(e) 
        self.__hide_progress()
    
    def __rename_file(self,default_name):
        output_path = self.kit.workspace +  self.kit.corpus_in_use + '/output/'
        filename = self.filename.get()
        if len(filename.strip()) == 0:
            filename = default_name
        else:
            filename = filename.strip().replace(' ','_')
        if os.path.exists(output_path  + default_name + '.xlsx'):
            try:
                os.rename(output_path  + default_name + '.xlsx',output_path  + filename + '.xlsx')
            except:
                os.remove(output_path  + filename + '.xlsx')
                os.rename(output_path + default_name + '.xlsx', output_path + filename + '.xlsx')
        self.filename.set(filename)


        
    
    
    def __on_tool(self):
        def callback():
            self.script_name = ''
            
            if self.selected_tool != None:
                tool = self.selected_tool
                if len(self.frm_lbl_options.winfo_children())!=0:
                    for widget in self.frm_lbl_options.winfo_children():
                        widget.destroy()
                    self.frm_lbl_options.update()
            else:
                tool = ''
            
            # Texts
            if tool == self.__gui_lang[29] and self.kit.corpus_in_use != None:
                container = ttk.Frame(self.frm_lbl_options)
                container.pack(fill="both", expand=True, padx=5, pady=5)

                # Scrollbar + Treeview layout
                self.trv_texts = ttk.Treeview(container, selectmode='browse')
                self.trv_texts.heading("#0", text=self.__gui_lang[131])

                self.scroll_texts = ttk.Scrollbar(container, orient="vertical", command=self.trv_texts.yview)
                self.trv_texts.configure(yscrollcommand=self.scroll_texts.set)

                # Layout: Treeview à esquerda, Scrollbar à direita
                self.trv_texts.pack(side="left", fill="both", expand=True)
                self.scroll_texts.pack(side="right", fill="y")

                self.trv_texts.bind("<Double-1>", lambda event: self.__on_open_text())

                # Carregar textos do corpus
                corpus = Corpus(self.kit.workspace, self.kit.corpus_in_use)
                filenames = corpus.textfiles()
                for filename in filenames:
                    self.trv_texts.insert('', 'end', filename, text=' ' + filename, image=self.icon_text)

                    
            # Wordlist
            elif tool == self.__gui_lang[30] and self.kit.corpus_in_use != None:
                container = ttk.Frame(self.frm_lbl_options)
                container.pack(fill="both", expand=True, padx=5, pady=5)

                self.chk_lowercase = ttk.Checkbutton(container, text=self.__gui_lang[133])
                self.chk_lowercase.state(['selected'])
                self.chk_lowercase.pack(anchor="w", pady=(0, 5))

                self.lbl_filename = ttk.Label(container, text=self.__gui_lang[134])
                self.lbl_filename.pack(anchor="w")

                self.filename = StringVar(value=self.__gui_lang[135])
                self.txt_filename = ttk.Entry(container, textvariable=self.filename)
                self.txt_filename.pack(fill="x", pady=(0, 5))

                self.btn_execute = ttk.Button(container, text=self.__gui_lang[132], command=self.__on_wordlist)
                self.btn_execute.pack(anchor="w", pady=(10, 0))

            # Keywords
            elif tool == self.__gui_lang[31] and self.kit.corpus_in_use != None:
                container = ttk.Frame(self.frm_lbl_options)
                container.pack(fill="both", expand=True, padx=5, pady=5)

                # Stoplist checkbox
                self.chk_stoplist = ttk.Checkbutton(container, text=self.__gui_lang[143])
                self.chk_stoplist.state(['!selected', '!alternate', '!disabled'])  # garante estado normal
                self.chk_stoplist.pack(anchor="w", pady=(0, 5))

                # Label + Radiobuttons para medida estatística
                self.lbl_measure = ttk.Label(container, text=self.__gui_lang[142])
                self.lbl_measure.pack(anchor="w")

                self.rdo_stat1 = ttk.Radiobutton(container, text=self.__gui_lang[144], value=1)
                self.rdo_stat1.pack(anchor="w", pady=(0, 2))

                self.rdo_stat2 = ttk.Radiobutton(container, text=self.__gui_lang[145], value=2)
                self.rdo_stat2.state(['selected', '!alternate', '!disabled'])
                self.rdo_stat2.pack(anchor="w", pady=(0, 10))

                # Label + Entry para nome de arquivo
                self.lbl_filename = ttk.Label(container, text=self.__gui_lang[146])
                self.lbl_filename.pack(anchor="w")

                self.filename = StringVar()
                self.filename.set(self.__gui_lang[147])
                self.txt_filename = ttk.Entry(container, textvariable=self.filename)
                self.txt_filename.pack(fill="x", padx=(0, 10), pady=(0, 10))

                # Botão de execução
                self.btn_execute = ttk.Button(container, text=self.__gui_lang[132], command=self.__on_keywords)
                self.btn_execute.pack(anchor="w", pady=10)


            # WTFreq
            elif tool == self.__gui_lang[32] and self.kit.corpus_in_use != None:
                container = ttk.Frame(self.frm_lbl_options)
                container.pack(fill="both", expand=True, padx=5, pady=5)

                # Checkbutton lowercase
                self.chk_lowercase = ttk.Checkbutton(container, text=self.__gui_lang[136])
                self.chk_lowercase.state(['selected', '!alternate', '!disabled'])
                self.chk_lowercase.pack(anchor="w", pady=(0, 10))

                # Label + Entry do nome do arquivo
                file_frame = ttk.Frame(container)
                file_frame.pack(fill="x", pady=(0, 10))
                self.lbl_filename = ttk.Label(file_frame, text=self.__gui_lang[137])
                self.lbl_filename.pack(anchor="w")
                self.filename = StringVar()
                self.filename.set(self.__gui_lang[138])
                self.txt_filename = ttk.Entry(file_frame, textvariable=self.filename)
                self.txt_filename.pack(fill="x")

                # Botão Executar
                self.btn_execute = ttk.Button(container, text=self.__gui_lang[132], command=self.__on_wtfreq)
                self.btn_execute.pack(anchor="w", pady=(10, 0))


            # WFreqinfiles
            elif tool == self.__gui_lang[33] and self.kit.corpus_in_use != None:
                container = ttk.Frame(self.frm_lbl_options)
                container.pack(fill="both", expand=True, padx=5, pady=5)

                # Checkbutton lowercase
                self.chk_lowercase = ttk.Checkbutton(container, text=self.__gui_lang[139])
                self.chk_lowercase.state(['selected', '!alternate', '!disabled'])
                self.chk_lowercase.pack(anchor="w", pady=(0, 10))

                # Label + Entry do nome do arquivo
                file_frame = ttk.Frame(container)
                file_frame.pack(fill="x", pady=(0, 10))
                self.lbl_filename = ttk.Label(file_frame, text=self.__gui_lang[140])
                self.lbl_filename.pack(anchor="w")
                self.filename = StringVar()
                self.filename.set(self.__gui_lang[141])
                self.txt_filename = ttk.Entry(file_frame, textvariable=self.filename)
                self.txt_filename.pack(fill="x")

                # Botão Executar
                self.btn_execute = ttk.Button(container, text=self.__gui_lang[132], command=self.__on_wfreqinfiles)
                self.btn_execute.pack(anchor="w", pady=(10, 0))


            # KWIC
            elif tool == self.__gui_lang[34] and self.kit.corpus_in_use is not None:
                # configura colunas para grid (até 3 para os grupos)
                for col in range(3):
                    self.frm_lbl_options.columnconfigure(col, weight=1)

                # Row 0: Label Search Node
                self.lbl_searchnode = ttk.Label(
                    self.frm_lbl_options, text=self.__gui_lang[148]
                )
                self.lbl_searchnode.grid(row=0, column=0,
                                        columnspan=3,
                                        sticky='w', padx=5, pady=2)

                # Row 1: Entry Search Node
                self.searchnode = StringVar()
                self.txt_searchnode = ttk.Entry(
                    self.frm_lbl_options, textvariable=self.searchnode
                )
                self.txt_searchnode.grid(row=1, column=0,
                                        columnspan=3,
                                        sticky='ew', padx=5, pady=2)
                self.txt_searchnode.focus()

                # Row 2: Checkbutton Case
                self.chk_case = ttk.Checkbutton(
                    self.frm_lbl_options, text=self.__gui_lang[149]
                )
                self.chk_case.state(['!selected', '!alternate', '!disabled'])
                self.chk_case.grid(row=2, column=0,
                                sticky='w', padx=5, pady=2)

                # Row 3: Checkbutton RegExp
                self.chk_regexp = ttk.Checkbutton(
                    self.frm_lbl_options, text=self.__gui_lang[150]
                )
                self.chk_regexp.state(['!selected', '!alternate', '!disabled'])
                self.chk_regexp.grid(row=3, column=0,
                                    sticky='w', padx=5, pady=2)

                # Row 4: Label POS
                self.lbl_pos = ttk.Label(
                    self.frm_lbl_options, text=self.__gui_lang[151]
                )
                self.lbl_pos.grid(row=4, column=0,
                                sticky='w', padx=5, pady=2)

                # Row 5: Entry Node Position
                self.nodepos = StringVar()
                self.txt_nodepos = ttk.Entry(
                    self.frm_lbl_options, textvariable=self.nodepos
                )
                self.txt_nodepos.grid(row=5, column=0,
                                    sticky='ew', padx=5, pady=2)

                # Row 6: Label Tags
                self.lbl_tags = ttk.Label(
                    self.frm_lbl_options, text=self.__gui_lang[152]
                )
                self.lbl_tags.grid(row=6, column=0,
                                sticky='w', padx=5, pady=2)

                # Row 7: Combobox Tags
                tagset = ['---'] + self.tagset
                self.cmb_tags_kwic = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=tagset
                )
                self.cmb_tags_kwic.current(0)
                self.cmb_tags_kwic.bind(
                    "<<ComboboxSelected>>", self.__add_tag_kwic
                )
                self.cmb_tags_kwic.grid(row=7, column=0,
                                        sticky='ew', padx=5, pady=2)

                # Row 8: Label Horizon Size
                self.lbl_horizon = ttk.Label(
                    self.frm_lbl_options, text=self.__gui_lang[153]
                )
                self.lbl_horizon.grid(row=8, column=0,
                                    sticky='w', padx=5, pady=2)

                # Row 9: Horizon and Width combos on the same line
                self.cmb_horizon = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=[5, 10, 15, 20, 25]
                )
                self.cmb_horizon.current(1)
                self.cmb_horizon.grid(row=9, column=0,
                                    sticky='ew', padx=5, pady=2)

                self.cmb_width = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=list(range(45, 105, 5))
                )
                self.cmb_width.current(1)
                self.cmb_width.grid(row=9, column=1,
                                    sticky='ew', padx=5, pady=2)

                # Row 10: Label Sorting
                self.lbl_sort = ttk.Label(
                    self.frm_lbl_options, text=self.__gui_lang[156]
                )
                self.lbl_sort.grid(row=10, column=0,
                                sticky='w', padx=5, pady=2)

                # Row 11: Three sort combos on the same line
                hor = ['L5', 'L4', 'L3', 'L2', 'L1', '-', 'R1', 'R2', 'R3', 'R4', 'R5']
                self.cmb_sort1 = ttk.Combobox(
                    self.frm_lbl_options, state='readonly', values=hor
                )
                self.cmb_sort1.current(5)
                self.cmb_sort1.grid(row=11, column=0,
                                    sticky='ew', padx=5, pady=2)

                self.cmb_sort2 = ttk.Combobox(
                    self.frm_lbl_options, state='readonly', values=hor
                )
                self.cmb_sort2.current(5)
                self.cmb_sort2.grid(row=11, column=1,
                                    sticky='ew', padx=5, pady=2)

                self.cmb_sort3 = ttk.Combobox(
                    self.frm_lbl_options, state='readonly', values=hor
                )
                self.cmb_sort3.current(5)
                self.cmb_sort3.grid(row=11, column=2,
                                    sticky='ew', padx=5, pady=2)

                # Row 12: Checkbutton Highlight
                self.chk_highlight = ttk.Checkbutton(
                    self.frm_lbl_options, text=self.__gui_lang[157]
                )
                self.chk_highlight.state(['selected', '!alternate', '!disabled'])
                self.chk_highlight.grid(row=12, column=0,
                                        sticky='w', padx=5, pady=2)

                # Row 13: Label Limit
                self.lbl_limit = ttk.Label(
                    self.frm_lbl_options, text=self.__gui_lang[158]
                )
                self.lbl_limit.grid(row=13, column=0,
                                    sticky='w', padx=5, pady=2)

                # Row 14: Entry Limit
                self.limit = StringVar(value='0')
                self.txt_limit = ttk.Entry(
                    self.frm_lbl_options, textvariable=self.limit
                )
                self.txt_limit.grid(row=14, column=0,
                                    sticky='ew', padx=5, pady=2)

                # Row 15: Label Filename
                self.lbl_filename = ttk.Label(
                    self.frm_lbl_options, text=self.__gui_lang[159]
                )
                self.lbl_filename.grid(row=15, column=0,
                                    sticky='w', padx=5, pady=2)

                # Row 16: Entry Filename
                self.filename = StringVar(value=self.__gui_lang[160])
                self.txt_filename = ttk.Entry(
                    self.frm_lbl_options, textvariable=self.filename
                )
                self.txt_filename.grid(row=16, column=0,
                                    sticky='ew', padx=5, pady=2)

                # Row 17: Button Execute
                self.btn_execute = ttk.Button(
                    self.frm_lbl_options,
                    text=self.__gui_lang[132],
                    command=self.__on_kwic
                )
                self.btn_execute.grid(row=17, column=0,
                                    sticky='w', padx=5, pady=10)


            
            # Concordance
            elif tool == self.__gui_lang[35] and self.kit.corpus_in_use is not None:
                # configurações de colunas
                self.frm_lbl_options.columnconfigure(0, weight=1)
                self.frm_lbl_options.columnconfigure(1, weight=1)

                # Linha 0: label de busca
                self.lbl_searchnode = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[161]
                )
                self.lbl_searchnode.grid(
                    row=0, column=0,
                    columnspan=2,
                    sticky='w',
                    padx=5, pady=2
                )

                # Linha 1: entry de busca
                self.searchnode = StringVar()
                self.txt_searchnode = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.searchnode
                )
                self.txt_searchnode.grid(
                    row=1, column=0,
                    columnspan=2,
                    sticky='ew',
                    padx=5, pady=2
                )
                self.txt_searchnode.focus()

                # Linha 2: checkbox Case sensitive
                self.chk_case = ttk.Checkbutton(
                    self.frm_lbl_options,
                    text=self.__gui_lang[162]
                )
                self.chk_case.grid(
                    row=2, column=0,
                    sticky='w',
                    padx=5, pady=2
                )

                # Linha 3: checkbox RegExp
                self.chk_regexp = ttk.Checkbutton(
                    self.frm_lbl_options,
                    text=self.__gui_lang[163]
                )
                self.chk_regexp.grid(
                    row=3, column=0,
                    sticky='w',
                    padx=5, pady=2
                )

                # Linha 4: label Posição
                self.lbl_pos = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[164]
                )
                self.lbl_pos.grid(
                    row=4, column=0,
                    sticky='w',
                    padx=5, pady=2
                )

                # Linha 5: entry Posição
                self.nodepos = StringVar()
                self.txt_nodepos = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.nodepos
                )
                self.txt_nodepos.grid(
                    row=5, column=0,
                    sticky='ew',
                    padx=5, pady=2
                )

                # Linha 6: label Tags
                self.lbl_tags = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[165]
                )
                self.lbl_tags.grid(
                    row=6, column=0,
                    sticky='w',
                    padx=5, pady=2
                )

                # Linha 7: combobox Tags
                tagset = ['---'] + self.tagset
                self.cmb_tags_conc = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=tagset
                )
                self.cmb_tags_conc.current(0)
                self.cmb_tags_conc.bind(
                    "<<ComboboxSelected>>",
                    self.__add_tag_conc
                )
                self.cmb_tags_conc.grid(
                    row=7, column=0,
                    sticky='ew',
                    padx=5, pady=2
                )

                # Linha 8: label Limite
                self.lbl_limit = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[166]
                )
                self.lbl_limit.grid(
                    row=8, column=0,
                    sticky='w',
                    padx=5, pady=2
                )

                # Linha 9: entry Limite
                self.limit = StringVar(value='0')
                self.txt_limit = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.limit
                )
                self.txt_limit.grid(
                    row=9, column=0,
                    sticky='ew',
                    padx=5, pady=2
                )

                # Linha 10: label Nome do arquivo
                self.lbl_filename = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[167]
                )
                self.lbl_filename.grid(
                    row=10, column=0,
                    sticky='w',
                    padx=5, pady=2
                )

                # Linha 11: entry Nome do arquivo
                self.filename = StringVar(value=self.__gui_lang[168])
                self.txt_filename = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.filename
                )
                self.txt_filename.grid(
                    row=11, column=0,
                    sticky='ew',
                    padx=5, pady=2
                )

                # Linha 12: botão Execute alinhado à esquerda
                self.btn_execute = ttk.Button(
                    self.frm_lbl_options,
                    text=self.__gui_lang[132],
                    command=self.__on_concordance
                )
                self.btn_execute.grid(
                    row=12, column=0,
                    sticky='w',
                    padx=5, pady=10
                )


            # Collocates
            elif tool == self.__gui_lang[36] and self.kit.corpus_in_use is not None:
                # permite que as colunas cresçam
                self.frm_lbl_options.columnconfigure(0, weight=1)
                self.frm_lbl_options.columnconfigure(1, weight=1)

                # Row 0: Label Search Node
                self.lbl_searchnode = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[169]
                )
                self.lbl_searchnode.grid(
                    row=0, column=0,
                    columnspan=2,
                    sticky='w', padx=5, pady=2
                )

                # Row 1: Entry Search Node
                self.searchnode = StringVar()
                self.txt_searchnode = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.searchnode
                )
                self.txt_searchnode.grid(
                    row=1, column=0,
                    columnspan=2,
                    sticky='ew', padx=5, pady=2
                )
                self.txt_searchnode.focus()

                # Row 2: Checkbutton Case
                self.chk_case = ttk.Checkbutton(
                    self.frm_lbl_options,
                    text=self.__gui_lang[170]
                )
                self.chk_case.grid(
                    row=2, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 3: Checkbutton RegExp
                self.chk_regexp = ttk.Checkbutton(
                    self.frm_lbl_options,
                    text=self.__gui_lang[171]
                )
                self.chk_regexp.grid(
                    row=3, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 4: Label POS
                self.lbl_pos = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[172]
                )
                self.lbl_pos.grid(
                    row=4, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 5: Entry Node Position
                self.nodepos = StringVar()
                self.txt_nodepos = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.nodepos
                )
                self.txt_nodepos.grid(
                    row=5, column=0,
                    sticky='ew', padx=5, pady=2
                )

                # Row 6: Label Tagset 1
                self.lbl_tags = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[173]
                )
                self.lbl_tags.grid(
                    row=6, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 7: Combobox Tagset 1
                tagset = ['---'] + self.tagset
                self.cmb_tags_coll1 = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=tagset
                )
                self.cmb_tags_coll1.grid(
                    row=7, column=0,
                    sticky='ew', padx=5, pady=2
                )
                self.cmb_tags_coll1.current(0)
                self.cmb_tags_coll1.bind(
                    '<<ComboboxSelected>>', self.__add_tag_coll1
                )

                # Row 8: Label Collocation Position
                self.lbl_collpos = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[174]
                )
                self.lbl_collpos.grid(
                    row=8, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 9: Entry Collocation Position
                self.collpos = StringVar()
                self.txt_collpos = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.collpos
                )
                self.txt_collpos.grid(
                    row=9, column=0,
                    sticky='ew', padx=5, pady=2
                )

                # Row 10: Label Tagset 2
                self.lbl_tags2 = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[175]
                )
                self.lbl_tags2.grid(
                    row=10, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 11: Combobox Tagset 2
                self.cmb_tags_coll2 = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=tagset
                )
                self.cmb_tags_coll2.grid(
                    row=11, column=0,
                    sticky='ew', padx=5, pady=2
                )
                self.cmb_tags_coll2.current(0)
                self.cmb_tags_coll2.bind(
                    '<<ComboboxSelected>>', self.__add_tag_coll2
                )

                # Row 12: Label Left Span
                self.lbl_leftspan = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[176]
                )
                self.lbl_leftspan.grid(
                    row=12, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 13: Combobox Left Span
                self.cmb_leftspan = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=[0,1,2,3,4,5]
                )
                self.cmb_leftspan.grid(
                    row=13, column=0,
                    sticky='ew', padx=5, pady=2
                )
                self.cmb_leftspan.current(5)

                # Row 14: Label Right Span
                self.lbl_rightspan = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[177]
                )
                self.lbl_rightspan.grid(
                    row=14, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 15: Combobox Right Span
                self.cmb_rightspan = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=[0,1,2,3,4,5]
                )
                self.cmb_rightspan.grid(
                    row=15, column=0,
                    sticky='ew', padx=5, pady=2
                )
                self.cmb_rightspan.current(5)

                # Row 16: Label Measure
                self.lbl_measure = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[257]
                )
                self.lbl_measure.grid(
                    row=16, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 17: Combobox Measure
                self.cmb_measure = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=['MI','T-score']
                )
                self.cmb_measure.grid(
                    row=17, column=0,
                    sticky='ew', padx=5, pady=2
                )
                self.cmb_measure.current(1)

                # Row 18: Label Filename
                self.lbl_filename = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[178]
                )
                self.lbl_filename.grid(
                    row=18, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 19: Entry Filename
                self.filename = StringVar(value=self.__gui_lang[179])
                self.txt_filename = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.filename
                )
                self.txt_filename.grid(
                    row=19, column=0,
                    sticky='ew', padx=5, pady=2
                )

                # Row 20: Button Execute aligned left
                self.btn_execute = ttk.Button(
                    self.frm_lbl_options,
                    text=self.__gui_lang[132],
                    command=self.__on_collocates
                )
                self.btn_execute.grid(
                    row=20, column=0,
                    sticky='w', padx=5, pady=10
                )


            # Collgraph
            elif tool == self.__gui_lang[37] and self.kit.corpus_in_use is not None:
                # permita redimensionamento das duas colunas
                self.frm_lbl_options.columnconfigure(0, weight=1)
                self.frm_lbl_options.columnconfigure(1, weight=1)

                # Row 0: Label Search Node
                self.lbl_searchnode = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[180]
                )
                self.lbl_searchnode.grid(
                    row=0, column=0,
                    columnspan=2,
                    sticky='w', padx=5, pady=2
                )

                # Row 1: Entry Search Node
                self.searchnode = StringVar()
                self.txt_searchnode = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.searchnode
                )
                self.txt_searchnode.grid(
                    row=1, column=0,
                    columnspan=2,
                    sticky='ew', padx=5, pady=2
                )
                self.txt_searchnode.focus()

                # Row 2: Checkbutton Case
                self.chk_case = ttk.Checkbutton(
                    self.frm_lbl_options,
                    text=self.__gui_lang[181]
                )
                self.chk_case.grid(
                    row=2, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 3: Checkbutton Regexp
                self.chk_regexp = ttk.Checkbutton(
                    self.frm_lbl_options,
                    text=self.__gui_lang[182]
                )
                self.chk_regexp.grid(
                    row=3, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 4: Label POS
                self.lbl_pos = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[183]
                )
                self.lbl_pos.grid(
                    row=4, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 5: Entry POS
                self.nodepos = StringVar()
                self.txt_nodepos = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.nodepos
                )
                self.txt_nodepos.grid(
                    row=5, column=0,
                    sticky='ew', padx=5, pady=2
                )

                # Row 6: Label Tagset 1
                self.lbl_tags = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[184]
                )
                self.lbl_tags.grid(
                    row=6, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 7: Combobox Tagset 1
                tagset = ['---'] + self.tagset
                self.cmb_tags_cg1 = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=tagset
                )
                self.cmb_tags_cg1.grid(
                    row=7, column=0,
                    sticky='ew', padx=5, pady=2
                )
                self.cmb_tags_cg1.current(0)
                self.cmb_tags_cg1.bind(
                    "<<ComboboxSelected>>", self.__add_tag_cg1
                )

                # Row 8: Label Collocation Position
                self.lbl_collpos = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[185]
                )
                self.lbl_collpos.grid(
                    row=8, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 9: Entry Collocation Position
                self.collpos = StringVar()
                self.txt_collpos = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.collpos
                )
                self.txt_collpos.grid(
                    row=9, column=0,
                    sticky='ew', padx=5, pady=2
                )

                # Row 10: Label Tagset 2
                self.lbl_tags2 = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[186]
                )
                self.lbl_tags2.grid(
                    row=10, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 11: Combobox Tagset 2
                self.cmb_tags_cg2 = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=tagset
                )
                self.cmb_tags_cg2.grid(
                    row=11, column=0,
                    sticky='ew', padx=5, pady=2
                )
                self.cmb_tags_cg2.current(0)
                self.cmb_tags_cg2.bind(
                    "<<ComboboxSelected>>", self.__add_tag_cg2
                )

                # Row 12: Label Left Span
                self.lbl_leftspan = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[187]
                )
                self.lbl_leftspan.grid(
                    row=12, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 13: Combobox Left Span
                self.cmb_leftspan = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=[0,1,2,3,4,5]
                )
                self.cmb_leftspan.grid(
                    row=13, column=0,
                    sticky='ew', padx=5, pady=2
                )
                self.cmb_leftspan.current(5)

                # Row 14: Label Right Span
                self.lbl_rightspan = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[188]
                )
                self.lbl_rightspan.grid(
                    row=14, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 15: Combobox Right Span
                self.cmb_rightspan = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=[0,1,2,3,4,5]
                )
                self.cmb_rightspan.grid(
                    row=15, column=0,
                    sticky='ew', padx=5, pady=2
                )
                self.cmb_rightspan.current(5)

                # Row 16: Label Measure
                self.lbl_measure = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[257]
                )
                self.lbl_measure.grid(
                    row=16, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 17: Combobox Measure
                self.cmb_measure = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=['MI', 'T-score']
                )
                self.cmb_measure.grid(
                    row=17, column=0,
                    sticky='ew', padx=5, pady=2
                )
                self.cmb_measure.current(1)

                # Row 18: Button Execute aligned left
                self.btn_execute = ttk.Button(
                    self.frm_lbl_options,
                    text=self.__gui_lang[132],
                    command=self.__on_collgraph
                )
                self.btn_execute.grid(
                    row=18, column=0,
                    sticky='w', padx=5, pady=10
                )


            
            # Clusters
            elif tool == self.__gui_lang[38] and self.kit.corpus_in_use is not None:
                # habilita responsividade das colunas
                self.frm_lbl_options.columnconfigure(0, weight=1)
                self.frm_lbl_options.columnconfigure(1, weight=1)

                # Row 0: Label Search Node
                self.lbl_searchnode = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[189]
                )
                self.lbl_searchnode.grid(
                    row=0, column=0,
                    columnspan=2,
                    sticky='w', padx=5, pady=2
                )

                # Row 1: Entry Search Node
                self.searchnode = StringVar()
                self.txt_searchnode = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.searchnode
                )
                self.txt_searchnode.grid(
                    row=1, column=0,
                    columnspan=2,
                    sticky='ew', padx=5, pady=2
                )
                self.txt_searchnode.focus()

                # Row 2: Checkbutton Lowercase Case
                self.chk_case = ttk.Checkbutton(
                    self.frm_lbl_options,
                    text=self.__gui_lang[190]
                )
                self.chk_case.grid(
                    row=2, column=0,
                    columnspan=2,
                    sticky='w', padx=5, pady=2
                )

                # Row 3: Label POS
                self.lbl_pos = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[191]
                )
                self.lbl_pos.grid(
                    row=3, column=0,
                    columnspan=2,
                    sticky='w', padx=5, pady=2
                )

                # Row 4: Entry POS
                self.nodepos = StringVar()
                self.txt_nodepos = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.nodepos
                )
                self.txt_nodepos.grid(
                    row=4, column=0,
                    columnspan=2,
                    sticky='ew', padx=5, pady=2
                )

                # Row 5: Label Tagset
                self.lbl_tags = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[192]
                )
                self.lbl_tags.grid(
                    row=5, column=0,
                    columnspan=2,
                    sticky='w', padx=5, pady=2
                )

                # Row 6: Combobox Tagset
                tagset = ['---'] + self.tagset
                self.cmb_tags_clusters = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=tagset
                )
                self.cmb_tags_clusters.grid(
                    row=6, column=0,
                    columnspan=2,
                    sticky='ew', padx=5, pady=2
                )
                self.cmb_tags_clusters.current(0)
                self.cmb_tags_clusters.bind(
                    '<<ComboboxSelected>>', self.__add_tag_clusters
                )

                # Row 7: Label Size
                self.lbl_size = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[193]
                )
                self.lbl_size.grid(
                    row=7, column=0,
                    columnspan=2,
                    sticky='w', padx=5, pady=2
                )

                # Row 8: Combobox Size
                self.cmb_size = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=[1,2,3,4,5]
                )
                self.cmb_size.grid(
                    row=8, column=0,
                    columnspan=2,
                    sticky='w', padx=5, pady=2
                )
                self.cmb_size.current(2)

                # Row 9: Label Min Freq
                self.lbl_minfreq = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[194]
                )
                self.lbl_minfreq.grid(
                    row=9, column=0,
                    columnspan=2,
                    sticky='w', padx=5, pady=2
                )

                # Row 10: Entry Min Freq
                self.minfreq = StringVar(value='1')
                self.txt_minfreq = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.minfreq
                )
                self.txt_minfreq.grid(
                    row=10, column=0,
                    columnspan=2,
                    sticky='w', padx=5, pady=2
                )

                # Row 11: Label Min Range
                self.lbl_minrange = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[195]
                )
                self.lbl_minrange.grid(
                    row=11, column=0,
                    columnspan=2,
                    sticky='w', padx=5, pady=2
                )

                # Row 12: Entry Min Range
                self.minrange = StringVar(value='1')
                self.txt_minrange = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.minrange
                )
                self.txt_minrange.grid(
                    row=12, column=0,
                    columnspan=2,
                    sticky='w', padx=5, pady=2
                )

                # Row 13: Label Filename
                self.lbl_filename = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[196]
                )
                self.lbl_filename.grid(
                    row=13, column=0,
                    columnspan=2,
                    sticky='w', padx=5, pady=2
                )

                # Row 14: Entry Filename
                self.filename = StringVar(value=self.__gui_lang[197])
                self.txt_filename = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.filename
                )
                self.txt_filename.grid(
                    row=14, column=0,
                    columnspan=2,
                    sticky='ew', padx=5, pady=2
                )

                # Row 15: Button Execute aligned left
                self.btn_execute = ttk.Button(
                    self.frm_lbl_options,
                    text=self.__gui_lang[132],
                    command=self.__on_clusters
                )
                self.btn_execute.grid(
                    row=15, column=0,
                    sticky='w', padx=5, pady=10
                )


            # N‑grams
            elif tool == self.__gui_lang[39] and self.kit.corpus_in_use is not None:
                # configure columns
                self.frm_lbl_options.columnconfigure(0, weight=1)
                self.frm_lbl_options.columnconfigure(1, weight=1)

                # Row 0: Label Size
                self.lbl_size = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[198]
                )
                self.lbl_size.grid(
                    row=0, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 1: Combobox Size
                self.cmb_size = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=[1,2,3,4,5]
                )
                self.cmb_size.grid(
                    row=1, column=0,
                    sticky='ew', padx=5, pady=2
                )
                self.cmb_size.current(2)

                # Row 2: Checkbutton Case
                self.chk_case = ttk.Checkbutton(
                    self.frm_lbl_options,
                    text=self.__gui_lang[199]
                )
                self.chk_case.grid(
                    row=2, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 3: Label POS
                self.lbl_pos = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[200]
                )
                self.lbl_pos.grid(
                    row=3, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 4: Entry POS
                self.nodepos = StringVar()
                self.txt_nodepos = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.nodepos
                )
                self.txt_nodepos.grid(
                    row=4, column=0,
                    sticky='ew', padx=5, pady=2
                )

                # Row 5: Label Tagset
                self.lbl_tags = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[201]
                )
                self.lbl_tags.grid(
                    row=5, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 6: Combobox Tagset
                tagset = ['---'] + self.tagset
                self.cmb_tags_ng = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=tagset
                )
                self.cmb_tags_ng.grid(
                    row=6, column=0,
                    sticky='ew', padx=5, pady=2
                )
                self.cmb_tags_ng.current(0)
                self.cmb_tags_ng.bind(
                    '<<ComboboxSelected>>', self.__add_tag_ng
                )

                # Row 7: Label Min Freq
                self.lbl_minfreq = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[202]
                )
                self.lbl_minfreq.grid(
                    row=7, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 8: Entry Min Freq
                self.minfreq = StringVar(value='1')
                self.txt_minfreq = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.minfreq
                )
                self.txt_minfreq.grid(
                    row=8, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 9: Label Min Range
                self.lbl_minrange = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[203]
                )
                self.lbl_minrange.grid(
                    row=9, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 10: Entry Min Range
                self.minrange = StringVar(value='1')
                self.txt_minrange = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.minrange
                )
                self.txt_minrange.grid(
                    row=10, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 11: Label Filename
                self.lbl_filename = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[204]
                )
                self.lbl_filename.grid(
                    row=11, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 12: Entry Filename
                self.filename = StringVar(value=self.__gui_lang[205])
                self.txt_filename = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.filename
                )
                self.txt_filename.grid(
                    row=12, column=0,
                    columnspan=2,
                    sticky='ew', padx=5, pady=2
                )

                # Row 13: Button Execute aligned left
                self.btn_execute = ttk.Button(
                    self.frm_lbl_options,
                    text=self.__gui_lang[132],
                    command=self.__on_ngrams
                )
                self.btn_execute.grid(
                    row=13, column=0,
                    sticky='w', padx=5, pady=10
                )

            # Dispersion
            elif tool == self.__gui_lang[40] and self.kit.corpus_in_use is not None:
                # configure columns
                self.frm_lbl_options.columnconfigure(0, weight=1)
                self.frm_lbl_options.columnconfigure(1, weight=1)

                # Row 0: Label Search Node
                self.lbl_searchnode = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[206]
                )
                self.lbl_searchnode.grid(
                    row=0, column=0,
                    columnspan=2,
                    sticky='w', padx=5, pady=2
                )

                # Row 1: Entry Search Node
                self.searchnode = StringVar()
                self.txt_searchnode = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.searchnode
                )
                self.txt_searchnode.grid(
                    row=1, column=0,
                    columnspan=2,
                    sticky='ew', padx=5, pady=2
                )
                self.txt_searchnode.focus()

                # Row 2: Checkbutton Case
                self.chk_case = ttk.Checkbutton(
                    self.frm_lbl_options,
                    text=self.__gui_lang[207]
                )
                self.chk_case.grid(
                    row=2, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 3: Checkbutton RegExp
                self.chk_regexp = ttk.Checkbutton(
                    self.frm_lbl_options,
                    text=self.__gui_lang[208]
                )
                self.chk_regexp.grid(
                    row=3, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 4: Label POS
                self.lbl_pos = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[209]
                )
                self.lbl_pos.grid(
                    row=4, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 5: Entry POS
                self.nodepos = StringVar()
                self.txt_nodepos = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.nodepos
                )
                self.txt_nodepos.grid(
                    row=5, column=0,
                    sticky='ew', padx=5, pady=2
                )

                # Row 6: Label Tagset
                self.lbl_tags = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[210]
                )
                self.lbl_tags.grid(
                    row=6, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 7: Combobox Tagset
                tagset = ['---'] + self.tagset
                self.cmb_tags_disp = ttk.Combobox(
                    self.frm_lbl_options,
                    state='readonly',
                    values=tagset
                )
                self.cmb_tags_disp.grid(
                    row=7, column=0,
                    sticky='ew', padx=5, pady=2
                )
                self.cmb_tags_disp.current(0)
                self.cmb_tags_disp.bind(
                    '<<ComboboxSelected>>', self.__add_tag_disp
                )

                # Row 8: Label Limit
                self.lbl_limit = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[211]
                )
                self.lbl_limit.grid(
                    row=8, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 9: Entry Limit
                self.limit = StringVar(value='0')
                self.txt_limit = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.limit
                )
                self.txt_limit.grid(
                    row=9, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 10: Label Filename
                self.lbl_filename = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[212]
                )
                self.lbl_filename.grid(
                    row=10, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 11: Entry Filename
                self.filename = StringVar(value=self.__gui_lang[213])
                self.txt_filename = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.filename
                )
                self.txt_filename.grid(
                    row=11, column=0,
                    sticky='ew', padx=5, pady=2
                )

                # Row 12: Button Execute aligned left
                self.btn_execute = ttk.Button(
                    self.frm_lbl_options,
                    text=self.__gui_lang[132],
                    command=self.__on_dispersion
                )
                self.btn_execute.grid(
                    row=12, column=0,
                    sticky='w', padx=5, pady=10
                )

            # Keywords dispersion
            elif tool == self.__gui_lang[41] and self.kit.corpus_in_use is not None:
                # configure column
                self.frm_lbl_options.columnconfigure(0, weight=1)

                # Row 0: Checkbutton Lowercase
                self.chk_lowercase = ttk.Checkbutton(
                    self.frm_lbl_options,
                    text=self.__gui_lang[214]
                )
                self.chk_lowercase.grid(
                    row=0, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 1: Label Limit
                self.lbl_limit = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[215]
                )
                self.lbl_limit.grid(
                    row=1, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 2: Entry Limit
                self.limit = StringVar(value='25')
                self.txt_limit = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.limit
                )
                self.txt_limit.grid(
                    row=2, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 3: Label Filename
                self.lbl_filename = ttk.Label(
                    self.frm_lbl_options,
                    text=self.__gui_lang[216]
                )
                self.lbl_filename.grid(
                    row=3, column=0,
                    sticky='w', padx=5, pady=2
                )

                # Row 4: Entry Filename
                self.filename = StringVar(value=self.__gui_lang[217])
                self.txt_filename = ttk.Entry(
                    self.frm_lbl_options,
                    textvariable=self.filename
                )
                self.txt_filename.grid(
                    row=4, column=0,
                    sticky='ew', padx=5, pady=2
                )

                # Row 5: Button Execute aligned left
                self.btn_execute = ttk.Button(
                    self.frm_lbl_options,
                    text=self.__gui_lang[132],
                    command=self.__on_keywordsdispersion
                )
                self.btn_execute.grid(
                    row=5, column=0,
                    sticky='w', padx=5, pady=10
                )


            # Word clouds
            elif tool == self.__gui_lang[42] and self.kit.corpus_in_use != None:
                self.frm_lbl_options.columnconfigure(0, weight=1)
                self.frm_lbl_options.columnconfigure(1, weight=1)

                self.lbl_list = ttk.Label(self.frm_lbl_options, text=self.__gui_lang[218])
                self.lbl_list.grid(row=0, column=0, sticky="w", padx=5, pady=2)
                self.cmb_wordlist = ttk.Combobox(self.frm_lbl_options, state="readonly", values=['frequency','keyness','range'])
                self.cmb_wordlist.grid(row=1, column=0, sticky="w", padx=5, pady=2)
                self.cmb_wordlist.current(0)

                self.chk_stoplist = ttk.Checkbutton(self.frm_lbl_options, text=self.__gui_lang[219])
                self.chk_stoplist.grid(row=0, column=1, sticky="w", padx=5, pady=2)

                self.lbl_colors = ttk.Label(self.frm_lbl_options, text=self.__gui_lang[220])
                self.lbl_colors.grid(row=2, column=0, sticky="w", padx=5, pady=2)
                self.cmb_theme = ttk.Combobox(self.frm_lbl_options, state="readonly", values=['grayish','jet','random','fixed'])
                self.cmb_theme.grid(row=3, column=0, sticky="w", padx=5, pady=2)
                self.cmb_theme.current(3)

                self.lbl_limit = ttk.Label(self.frm_lbl_options, text=self.__gui_lang[221])
                self.lbl_limit.grid(row=2, column=1, sticky="w", padx=5, pady=2)
                self.limit = StringVar(value="400")
                self.cmb_limit = ttk.Combobox(self.frm_lbl_options, values=['5','10','15','20','25','50','100','150','200','250','300','350','400'])
                self.cmb_limit.grid(row=3, column=1, sticky="w", padx=5, pady=2)
                self.cmb_limit.current(8)

                self.chk_vertical = ttk.Checkbutton(self.frm_lbl_options, text=self.__gui_lang[222])
                self.chk_vertical.grid(row=4, column=0, sticky="w", padx=5, pady=2)

                self.lbl_format = ttk.Label(self.frm_lbl_options, text=self.__gui_lang[223])
                self.lbl_format.grid(row=5, column=0, sticky="w", padx=5, pady=2)
                self.cmb_format = ttk.Combobox(self.frm_lbl_options, state="readonly", values=['plot','image'])
                self.cmb_format.grid(row=6, column=0, sticky="w", padx=5, pady=2)
                self.cmb_format.current(0)

                self.btn_execute = ttk.Button(self.frm_lbl_options, text=self.__gui_lang[132], command=self.__on_wordclouds)
                self.btn_execute.grid(row=7, column=0, columnspan=2, pady=10)

                
            
            # Scripts
            elif tool == self.__gui_lang[43] and self.kit.corpus_in_use != None:
                # responsividade da coluna única
                self.frm_lbl_options.columnconfigure(0, weight=1)

                # Label de argumentos
                self.lbl_args = ttk.Label(self.frm_lbl_options, text=self.__gui_lang[224])
                self.lbl_args.grid(row=0, column=0, sticky="w", padx=5, pady=(5,2))

                # Entry de argumentos
                self.script_args = StringVar()
                self.txt_args = ttk.Entry(self.frm_lbl_options, textvariable=self.script_args)
                self.txt_args.grid(row=1, column=0, sticky="ew", padx=5, pady=(0,5))
                self.txt_args.focus()

                # Leitura do texto de ajuda (se existir)
                help_text = ""
                try:
                    path = os.path.join(self.__path, "data", "scripts", f"{self.script_name}.py")
                    with open(path, "r", encoding="utf-8") as fh:
                        for line in fh:
                            if line.lower().startswith('""" help:') or line.lower().startswith('"""help:'):
                                help_text = line.strip().strip('"""').strip()
                                break
                except Exception as e:
                    print(e)

                # Label de ajuda
                self.lbl_help = ttk.Label(self.frm_lbl_options, text=help_text, wraplength=250)
                self.lbl_help.grid(row=2, column=0, sticky="w", padx=5, pady=(0,10))

                # Botão Executar
                self.btn_execute = ttk.Button(self.frm_lbl_options, text=self.__gui_lang[132], command=self.__on_scripts)
                self.btn_execute.grid(row=3, column=0, sticky="w", padx=5, pady=(0,5))

             
        self.after_idle(callback)

    # add tag from tagset

    def __add_tag_kwic(self,event):
        tag = str(self.nodepos.get() + ' ' + self.cmb_tags_kwic.get() ).strip()
        self.nodepos.set(tag)
        self.cmb_tags_kwic.current(0)

    def __add_tag_conc(self,event):
        tag = str(self.nodepos.get() + ' ' + self.cmb_tags_conc.get() ).strip()
        self.nodepos.set(tag)
        self.cmb_tags_conc.current(0)

    def __add_tag_coll1(self,event):
        tag = str(self.nodepos.get() + ' ' + self.cmb_tags_coll1.get() ).strip()
        self.nodepos.set(tag)
        self.cmb_tags_coll1.current(0)

    def __add_tag_coll2(self,event):
        tag = str(self.collpos.get() + ' ' + self.cmb_tags_coll2.get() ).strip()
        self.collpos.set(tag)
        self.cmb_tags_coll2.current(0)

    def __add_tag_cg1(self,event):
        tag = str(self.nodepos.get() + ' ' + self.cmb_tags_cg1.get() ).strip()
        self.nodepos.set(tag)
        self.cmb_tags_cg1.current(0)

    def __add_tag_cg2(self,event):
        tag = str(self.collpos.get() + ' ' + self.cmb_tags_cg2.get() ).strip()
        self.collpos.set(tag)
        self.cmb_tags_cg2.current(0)

    def __add_tag_clusters(self,event):
        tag = str(self.nodepos.get() + ' ' + self.cmb_tags_clusters.get() ).strip()
        self.nodepos.set(tag)
        self.cmb_tags_clusters.current(0)

    def __add_tag_ng(self,event):
        tag = str(self.nodepos.get() + ' ' + self.cmb_tags_ng.get() ).strip()
        self.nodepos.set(tag)
        self.cmb_tags_ng.current(0)

    def __add_tag_disp(self,event):
        tag = str(self.nodepos.get() + ' ' + self.cmb_tags_disp.get() ).strip()
        self.nodepos.set(tag)
        self.cmb_tags_disp.current(0)


    
    # wordlist
    def __on_wordlist(self):
        def callback():
            self.__show_progress(self.__gui_lang[225])
            t = threading.Thread (target=self.__exec_wordlist)
            t.start()
        self.after_idle(callback) 
    
    def __exec_wordlist(self):
        lowercase = 'n'
        if self.chk_lowercase.instate(['selected']):
            lowercase='y'
        self.kit.do_wordlist('--lowercase ' + lowercase)
        # rename 
        #self.__rename_file(self.__gui_lang[135])
        self.__rename_file('wordlist')
        self.__load_datafiles()
        self.__hide_progress()
        self.frm_lbl_info['text'] = self.__corpus_info() # update corpus info on screen
    
    # wtfreq
    def __on_wtfreq(self):
        def callback():
            self.__show_progress(self.__gui_lang[226])
            t = threading.Thread (target=self.__exec_wtfreq)
            t.start()
        self.after_idle(callback) 
    
    def __exec_wtfreq(self):
        lowercase = 'n'
        if self.chk_lowercase.instate(['selected']):
            lowercase='y'
        self.kit.do_wtfreq('--lowercase ' + lowercase)
        # rename 
        self.__rename_file('wtfreq')
        self.__load_datafiles()
        self.__hide_progress()
    
    # wfreqinfiles
    def __on_wfreqinfiles(self):
        def callback():
            self.__show_progress(self.__gui_lang[227])
            t = threading.Thread (target=self.__exec_wfreqinfiles)
            t.start()
        self.after_idle(callback) 
    
    def __exec_wfreqinfiles(self):
        lowercase = 'n'
        if self.chk_lowercase.instate(['selected']):
            lowercase='y'
        self.kit.do_wfreqinfiles('--lowercase ' + lowercase)
        # rename 
        self.__rename_file('wfreqinfiles')
        self.__load_datafiles()
        self.__hide_progress()
        
        
    # keywords
    def __on_keywords(self):
        def callback():
            self.__show_progress(self.__gui_lang[228])
            t = threading.Thread (target=self.__exec_keywords)
            t.start()
        self.after_idle(callback) 
    
    def __exec_keywords(self):
        stoplist = 'n'
        if self.chk_stoplist.instate(['selected']):
            stoplist='y'
        measure = 'log-likelihodd'
        if self.rdo_stat1.instate(['selected']):
            measure = 'chi-square'
        self.kit.do_keywords('--stoplist ' + stoplist + ' --measure ' + measure )
        # rename 
        self.__rename_file('keywords')
        self.__load_datafiles()
        self.__hide_progress()
    
    # kwic
    def __on_kwic(self):
        def callback():
            self.__show_progress(self.__gui_lang[229])
            t = threading.Thread (target=self.__exec_kwic)
            t.start()
        self.after_idle(callback) 
    
    def __exec_kwic(self):
        # node
        node = '"' +  self.searchnode.get() + '"'
        # case
        case = ' --case n '
        if self.chk_case.instate(['selected']):
            case=' --case y '
        # regex
        regexp = ' --regexp n '
        if self.chk_regexp.instate(['selected']):
            regexp=' --regexp y '
        # pos
        if len(self.nodepos.get())!=0:
            pos = ' --pos "' + self.nodepos.get() + '"'
        else:
            pos = ''
        # horizon
        horizon = self.cmb_horizon.get()
        if len(horizon)!= 0:
            horizon = ' --horizon ' + horizon 
        else:
            horizon = ''
        width = self.cmb_width.get()
        if len(width)!=0:
            width = ' --width ' + width
        else:
            width = ''
        # sort
        cs = []
        sort1 = self.cmb_sort1.get()
        if sort1 != '-':
            cs.append(sort1) 
            sort1 = ' --sort1 ' + sort1 
        else:
            sort1 = ''
        sort2 = self.cmb_sort2.get()
        if sort2 != '-':
            cs.append(sort2)
            sort2 = ' --sort2 ' + sort2 
        else:
            sort2 = ''
        sort3 = self.cmb_sort3.get()
        if sort3 != '-':
            cs.append(sort3)
            sort3 = ' --sort3 ' + sort3 
        else:
            sort3 = ''
        # highlight
        can_highlight = False
        if self.chk_highlight.instate(['selected']):
            can_highlight=True
        highlight=''
        if len(cs)!=0 and can_highlight == True:
            highlight = ' --highlight "' + ' '.join(cs) + '"'
        # limit
        limit = self.txt_limit.get()
        if len(limit) != 0  and limit != '0':
            limit = ' --limit ' + limit
        else:
            limit = ''
        
        # exec
        if len(self.searchnode.get().strip()) !=0:
            if len(node)!=0:
                self.kit.do_kwic(node  +  case + regexp + pos + horizon + width + sort1 + sort2 + sort3 + highlight + limit)
                # rename 
                self.__rename_file('kwic')
        else:
            messagebox.showwarning(self.__gui_lang[245], self.__gui_lang[246])
            self.txt_searchnode.focus()            
        # update window
        self.__load_datafiles()
        self.__hide_progress()
    
    # concordance
    def __on_concordance(self):
        def callback():
            self.__show_progress(self.__gui_lang[230])
            t = threading.Thread (target=self.__exec_concordance)
            t.start()
        self.after_idle(callback) 
    
    def __exec_concordance(self):
        # node
        node = '"' +  self.searchnode.get() + '"'
        # case
        case = ' --case n '
        if self.chk_case.instate(['selected']):
            case=' --case y '
        # regex
        regexp = ' --regexp n '
        if self.chk_regexp.instate(['selected']):
            regexp=' --regexp y '
        # pos
        if len(self.nodepos.get())!=0:
            pos = ' --pos "' + self.nodepos.get() + '"'
        else:
            pos = ''
        
        # limit
        limit = self.txt_limit.get()
        if len(limit) != 0  and limit != '0':
            limit = ' --limit ' + limit
        else:
            limit = ''
        
        # exec
        if len(self.searchnode.get().strip()) != 0:
            if len(node)!=0:
                self.kit.do_concordance(node  +  case + regexp + pos + limit)
                # rename 
                self.__rename_file('concordance')
        else:
            messagebox.showwarning(self.__gui_lang[247], self.__gui_lang[248])
            self.txt_searchnode.focus()
        # update window
        self.__load_datafiles()
        self.__hide_progress()
    
    # collocates
    def __on_collocates(self):
        def callback():
            self.__show_progress(self.__gui_lang[231])
            t = threading.Thread (target=self.__exec_collocates)
            t.start()
        self.after_idle(callback) 
    
    def __exec_collocates(self):
        # node
        node = '"' +  self.searchnode.get() + '"'
        # case
        case = ' --case n '
        if self.chk_case.instate(['selected']):
            case=' --case y '
        # regex
        regexp = ' --regexp n '
        if self.chk_regexp.instate(['selected']):
            regexp=' --regexp y '
        # pos
        if len(self.nodepos.get())!=0:
            pos = ' --pos "' + self.nodepos.get() + '"'
        else:
            pos = ''
        
        # coll pos
        if len(self.collpos.get())!=0:
            collpos = ' --coll_pos "' + self.collpos.get() + '"'
        else:
            collpos = ''
        
        left_span = ' --left_span ' +  self.cmb_leftspan.get()
        right_span = ' --right_span ' +  self.cmb_rightspan.get()

        # measure
        if self.cmb_measure.get() == 'MI':
            measure = ' --measure "mutual information"'
        else:
            measure = ' --measure t-score'


        # exec
        if len(self.searchnode.get().strip())!=0:
            if len(node)!=0:
                self.kit.do_collocates (node  +  case + regexp + pos + collpos + left_span + right_span + measure )
                # rename 
                self.__rename_file('collocates')
        else:
            messagebox.showwarning(self.__gui_lang[249], self.__gui_lang[250])
            self.txt_searchnode.focus()
            
        # update window
        self.__load_datafiles()
        self.__hide_progress()
    
    # collgraph
    def __on_collgraph(self):
        def callback():
            self.__show_progress(self.__gui_lang[232])
            self.__exec_collgraph()
            #t = threading.Thread (target=self.__exec_collgraph)
            #t.start()
        self.after_idle(callback) 
    
    def __exec_collgraph(self):
        # node
        node = '"' +  self.searchnode.get() + '"'
        # case
        case = ' --case n '
        if self.chk_case.instate(['selected']):
            case=' --case y '
        # regex
        regexp = ' --regexp n '
        if self.chk_regexp.instate(['selected']):
            regexp=' --regexp y '
        # pos
        if len(self.nodepos.get())!=0:
            pos = ' --pos "' + self.nodepos.get() + '"'
        else:
            pos = ''
        
        # coll pos
        if len(self.collpos.get())!=0:
            collpos = ' --coll_pos "' + self.collpos.get() + '"'
        else:
            collpos = ''
        
        left_span = ' --left_span ' +  self.cmb_leftspan.get()
        right_span = ' --right_span ' +  self.cmb_rightspan.get()

        # measure
        if self.cmb_measure.get() == 'MI':
            measure = ' --measure "mutual information"'
        else:
            measure = ' --measure t-score'
        
        # exec
        if len(self.searchnode.get())!=0:
            if len(node)!=0:
                self.kit.do_collgraph(node  +  case + regexp + pos + collpos + left_span + right_span + measure )
        else:
            messagebox.showwarning(self.__gui_lang[251], self.__gui_lang[252])
            self.txt_searchnode.focus()
           
        # update window
        self.__load_datafiles()
        self.__hide_progress()
    
    # clusters
    def __on_clusters(self):
        def callback():
            self.__show_progress(self.__gui_lang[233])
            t = threading.Thread (target=self.__exec_clusters)
            t.start()
        self.after_idle(callback) 
    
    def __exec_clusters(self):
        # node
        node = '"' +  self.searchnode.get() + '"'
        # case
        case = ' --lowercase n '
        if self.chk_case.instate(['selected']):
            case=' --lowercase y '
        # pos
        if len(self.nodepos.get())!=0:
            pos = ' --pos "' + self.nodepos.get() + '"'
        else:
            pos = ''
        # size
        size = ' --size ' +  self.cmb_size.get()
        # minfreq
        minfreq = ' --minfreq ' + self.minfreq.get()
        # minrange 
        minrange = ' --minrange ' + self.minrange.get()
        # exec
        if len(self.searchnode.get().strip())!=0:
            if len(node)!=0:
                self.kit.do_clusters (node + case + pos + size + minfreq + minrange)
                # rename 
                self.__rename_file('clusters')
        else:
            messagebox.showwarning(self.__gui_lang[253], self.__gui_lang[254])
            self.txt_searchnode.focus()
        # update window
        self.__load_datafiles()
        self.__hide_progress()
    
    # ngrams
    def __on_ngrams(self):
        def callback():
            self.__show_progress(self.__gui_lang[234])
            t = threading.Thread (target=self.__exec_ngrams)
            t.start()
        self.after_idle(callback) 
    
    def __exec_ngrams(self):
        # size
        size = self.cmb_size.get()
        # case
        case = ' --lowercase n '
        if self.chk_case.instate(['selected']):
            case=' --lowercase y '
        # pos
        if len(self.nodepos.get())!=0:
            pos = ' --pos "' + self.nodepos.get() + '"'
        else:
            pos = ''
        # minfreq
        minfreq = ' --minfreq ' + self.minfreq.get()
        # minrange 
        minrange = ' --minrange ' + self.minrange.get()
        # exec
        self.kit.do_ngrams (size + case + pos +  minfreq + minrange)
        # rename 
        self.__rename_file('ngrams')
        # update window
        self.__load_datafiles()
        self.__hide_progress()
    
    # dispersion
    def __on_dispersion(self):
        def callback():
            self.__show_progress(self.__gui_lang[235])
            t = threading.Thread (target=self.__exec_dispersion)
            t.start()
        self.after_idle(callback) 
    
    def __exec_dispersion(self):
        # node
        node = '"' +  self.searchnode.get() + '"'
        # case
        case = ' --case n '
        if self.chk_case.instate(['selected']):
            case=' --case y '
        # regex
        regexp = ' --regexp n '
        if self.chk_regexp.instate(['selected']):
            regexp=' --regexp y '
        # pos
        if len(self.nodepos.get())!=0:
            pos = ' --pos "' + self.nodepos.get() + '"'
        else:
            pos = ''
        
        # limit
        limit = self.txt_limit.get()
        if len(limit) != 0  and limit != '0':
            limit = ' --limit ' + limit
        else:
            limit = ''
        # exec
        if len(self.searchnode.get())!=0:
            if len(node)!=0:
                self.kit.do_dispersion(node  +  case + regexp + pos + limit)
                # rename 
                self.__rename_file('dispersion')
        else:
            messagebox.showwarning(self.__gui_lang[255], self.__gui_lang[256])
            self.txt_searchnode.focus()
            
        # update window
        self.__load_datafiles()
        self.__hide_progress()
    
    # keywords dispersion
    def __on_keywordsdispersion(self):
        def callback():
            self.__show_progress(self.__gui_lang[236])
            t = threading.Thread (target=self.__exec_keywordsdispersion)
            t.start()
        self.after_idle(callback) 
    
    def __exec_keywordsdispersion(self):
        lowercase = 'n'
        if self.chk_lowercase.instate(['selected']):
            lowercase='y'
        # limit
        limit = self.txt_limit.get()
        if len(limit) != 0  and limit != '0':
            limit = ' --limit ' + limit
        else:
            limit = ''
        self.kit.do_keywords_dispersion(' --lowercase ' + lowercase + limit)
        
        # rename 
        self.__rename_file('keywords_dispersion')
        # update window
        self.__load_datafiles()
        self.__hide_progress()
    
    # word clouds
    def __on_wordclouds(self):
        def callback():
            self.__show_progress(self.__gui_lang[237])
            #t = threading.Thread (target=self.__exec_wordclouds)
            #t.start()
            self.__exec_wordclouds()
        self.after_idle(callback) 
    
    def __exec_wordclouds(self):
        # stoplist
        stoplist = 'n'
        if self.chk_stoplist.instate(['selected']):
            stoplist = 'y'
        # vertical
        vertical = 'n'
        if self.chk_vertical.instate(['selected']):
            vertical = 'y'
        # theme 
        theme_name  = self.cmb_theme.get()
        if theme_name == 'grayish':
            theme = 2
        elif theme_name == 'jet':
            theme = 1
        elif theme_name == 'random':
            theme= 0
        elif theme_name == 'fixed':
            theme = 3
        else:
            theme = 2
        # limit
        try:
            limit = int(self.cmb_limit.get())
        except:
            limit = 200
        # format 
        rformat = self.cmb_format.get()
        # wordlist 
        wordlist_type = self.cmb_wordlist.get()
        # do it 
        args = '--wordlist %s --theme %s --vertical %s --stoplist %s --limit %s --format %s' % (wordlist_type,theme,vertical,stoplist,limit,rformat)
        self.kit.do_wordcloud(args)
        # update window
        self.__load_datafiles()
        self.__hide_progress()
            
     
    
    
    # scripts
    def __on_scripts(self):
        def callback():
            self.__show_progress(self.__gui_lang[238])
            t = threading.Thread (target=self.__exec_scripts)
            t.start()
        self.after_idle(callback)
    
    def __exec_scripts(self):
        args = ''
        if len(self.script_args.get().strip())!=0:
            args = self.script_args.get().strip()
        os.system('python ' +  self.__path + '/data/scripts/' + self.script_name  + '.py ' + self.kit.workspace + ' ' + self.kit.corpus_in_use + ' ' + args)
        # update window
        self.__load_datafiles()
        self.__hide_progress()

    #  choose gui language
    def __choose_language(self):
        def callback():
            # --- cria janela oculta e modal ---
            self.top = Toplevel(self.master)
            #self.top.withdraw()
            self.top.transient(self.master)
            self.top.title(self.__gui_lang[239])
            # permite redimensionar largura apenas
            self.top.resizable(False, False)
            self.top.tk.call('wm', 'iconphoto', self.top._w, self.icon_python)

            # --- layout responsivo com grid ---
            # container principal
            main = ttk.Frame(self.top, padding=10)
            main.grid(sticky='nsew')
            # colunas: 0 fixa para label, 1 expansível para combobox
            main.columnconfigure(0, weight=0)
            main.columnconfigure(1, weight=1)
            # três linhas de widgets
            for r in range(3):
                main.rowconfigure(r, weight=0)

            # --- widgets ---
            # Label de instrução
            ttk.Label(main, text=self.__gui_lang[240]) \
                .grid(row=0, column=0, sticky='w', padx=(0,5), pady=(0,5))
            # Combobox de idiomas
            self.cmb_language = ttk.Combobox(
                main,
                state='readonly',
                values=kit_app_language.get_languages()
            )
            self.cmb_language.grid(row=0, column=1, sticky='ew', pady=(0,5))
            self.cmb_language.current(0)

            # Botões
            btn_frame = ttk.Frame(main)
            btn_frame.grid(row=1, column=0, columnspan=2,
                        sticky='e', pady=(10,0))
            # espaço flexível antes dos botões
            btn_frame.columnconfigure(0, weight=1)
            ttk.Button(btn_frame, text=self.__gui_lang[241],
                    command=self.__apply_selected_language) \
                .grid(row=0, column=1, padx=(5,0))
            ttk.Button(btn_frame, text=self.__gui_lang[242],
                    command=self.__cancel_choose_language) \
                .grid(row=0, column=2, padx=(5,0))

            # --- foco inicial ---
            self.cmb_language.focus_set()

            # --- calcula tamanho natural e centraliza ---
            self.top.update_idletasks()
            w = self.top.winfo_width()
            h = self.top.winfo_height()
            sw = self.top.winfo_screenwidth()
            sh = self.top.winfo_screenheight()
            x = (sw - w) // 2
            y = (sh - h) // 2
            self.top.geometry(f"{w}x{h}+{x}+{y}")

            # --- exibe e torna modal ---
            self.top.deiconify()
            self.top.grab_set()
            self.master.wait_window(self.top)

        self.after_idle(callback)


    def __apply_selected_language(self):
        def callback():
            language = self.cmb_language.get()
            kit_app_language.set_language(language)
            self.top.destroy()
            self.focus()
            messagebox.showinfo(self.__gui_lang[243], self.__gui_lang[244])
        self.top.after_idle(callback)


    def __cancel_choose_language(self):
        def callback():
            self.top.destroy()
            self.focus()
        self.top.after_idle(callback)

    """ run """
    def run(self):
        self.mainloop()


