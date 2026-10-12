# -*- coding: utf-8 -*-
# Author: jlopes@alumni.usp.br
import os
import sys
import math
import time
import string
import pickle
from pathlib import Path
from typing import Any, Optional


def read_text_detected(file_path):
    """Read UTF-8 text when possible and detect common legacy encodings."""
    raw = Path(file_path).read_bytes()
    if not raw:
        return ""
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass

    try:
        import chardet

        encoding = chardet.detect(raw).get("encoding")
    except Exception:
        encoding = None
    if encoding:
        try:
            return raw.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            pass
    return raw.decode("cp1252", errors="replace")

def __progress(count, total, suffix=''):
        bar_len = 30
        filled_len = int(round(bar_len * count / float(total)))
        percents = round(100.0 * count / float(total), 1)
        bar = '=' * filled_len + '-' * (bar_len - filled_len)
        sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
        try:
            sys.stdout.flush()
        except OSError:
            pass
        
def keywords_reference(filename):
    def readlines(filename):
        i = 0
        with open(filename,'r',encoding='utf-8') as fh:
            for line in fh:
                if len(line.strip())!=0:
                    if i != 0:
                        fields = line.strip().split('\t')
                        if len(fields) >=4:
                            yield (fields[1],fields[2])
                    i+=1
    tokens = 0
    reflist = {}
    freqlist = readlines(filename)
    for item in freqlist:
        tokens+= int(item[1])
        if item[0] not in reflist:
            reflist[item[0]]=int(item[1])
    return (reflist,tokens) 
        

def load_reference_wordlist(filename):
        reflist = {}
        i = 0
        with open(filename,'r','utf-8') as fh:
            for line in fh:
                if len(line.strip())!=0:
                    if i != 0:
                        fields = line.strip().split('\t')
                        if len(fields) >=4:
                            if fields[1] not in reflist:
                                reflist[fields[1]]=int(fields[2])
                    i+=1
        return reflist

def sent2conll2000(sent):
    s = []
    for token in sent:
        s.append(token[0] + ' ' + token[1] + ' O')
    return '\n'.join(s)   

    
def chi_square(freq_stdc,freq_refc,tk_stdc,tk_refc):
    try:
        a = freq_stdc 
        b = freq_refc 
        c = tk_stdc - a 
        d = tk_refc - b 
        N = a + b + c + d
        chi = N * (a*d-b*c)** 2/((a+b)*(c+d)*(a+c)*(b+d))
        chi = round(chi,2) 
    except Exception as e:
        print(f"Error on chi_squqre: {e}")
        chi = 0.0
    return chi 

def observed_expected(ab,a,b,N, h=1):
    O = ab / float(N)
    E = (a / float(N)) * (b / float(N))
    E =  E * h
    OE = O/E
    return OE 

def mutual_information(ab,a,b,N, h=1):
    O = ab / float(N)
    E = (a / float(N)) * (b / float(N))
    E =  E * h
    OE = O/E
    I = math.log(OE,2)
    I = round(I,2)
    return I 

def tscore(ab,a,b,N, h=1):
    O = ab / float(N)
    E = (a / float(N)) * (b / float(N))
    E =  E * h
    T = (O-E) / (math.sqrt(ab)/float(N))
    T = round(T,2)
    return T

def ll(freq_stdc,freq_refc,tk_stdc,tk_refc):
    """Calculates the log-likelihood value"""
    try:
        O = float(freq_stdc+freq_refc)
        N1 = float(tk_stdc)
        N2 = float(tk_refc)
        E1 = N1*O/(N1+N2) 
        E2 = N2*O/(N1+N2)
        if freq_stdc < 1 or E1 < 1:
            v1 = 0
        else:
            v1 = math.log(freq_stdc/E1)
        if freq_refc < 1 or E2 < 1:
            v2 = 0
        else:
            v2 = math.log(freq_refc/E2)
        LL = round(2 * ((freq_stdc * v1)+(freq_refc * v2)),2)
        Norm_stdc = freq_stdc/float(tk_stdc)
        Norm_refc = freq_refc/float(tk_refc)
        if Norm_stdc == 0:
            Norm_stdc = 0.5 / float(tk_stdc)
        if Norm_refc == 0:
            Norm_refc = 0.5 / float(tk_refc)
        if Norm_stdc < Norm_refc:
            LL = - LL
    except Exception as e:
        print(f"Error on ll: {e}")
        LL = 0.0
    return LL


def logRatio(freq_stdc,freq_refc,tk_stdc,tk_refc):
    Norm_stdc = freq_stdc/float(tk_stdc)
    Norm_refc = freq_refc/float(tk_refc)
    if Norm_stdc == 0:
        Norm_stdc = 0.5 / float(tk_stdc)
    if Norm_refc == 0:
        Norm_refc = 0.5 / float(tk_refc)
    lr = math.log2((Norm_stdc/Norm_refc))
    return lr

def _safe_load_pickle(path: str | Path, base_dir: Optional[str | Path] = None) -> Any:
    """Loads a pickle file with optional path validation.

    If base_dir is provided, verifies that the resolved path is inside it
    to prevent path-traversal attacks.
    """
    resolved = Path(path).resolve()
    if base_dir is not None:
        base = Path(base_dir).resolve()
        if not str(resolved).startswith(str(base)):
            raise ValueError(f"Path traversal detected: {path!r} is outside {base_dir!r}")
    with open(resolved, 'rb') as fh:
        return pickle.load(fh)


def dump(obj: Any, filename: str) -> None:
    with open(filename, 'wb') as fh:
        pickle.dump(obj, fh)


def load(filename: str, base_dir: Optional[str] = None) -> Any:
    """Loads a pickle file. Pass base_dir to restrict loading to that directory."""
    return _safe_load_pickle(filename, base_dir=base_dir)


_SKIP_FILES = {'.DS_Store', 'desktop.ini', 'Thumbs.db'}

_TEXT_BOMS = (b'\xef\xbb\xbf', b'\xff\xfe', b'\xfe\xff')


def is_probably_text(path: str, sniff_bytes: int = 8192) -> bool:
    """Returns False for binary files (NUL bytes without a UTF-16/32 BOM), e.g. databases or images."""
    with open(path, 'rb') as fh:
        head = fh.read(sniff_bytes)
    if head.startswith(_TEXT_BOMS):
        return True
    return b'\x00' not in head


def list_source_files(source_folder: str) -> tuple:
    """Splits the files of a source folder into ``(accepted, skipped)`` file names.

    Accepted files are plain-text files and documents with a converter in ``SOURCE_CONVERTERS``.
    Skipped files are system files (``_SKIP_FILES``) and binary files such as SQLite databases.
    """
    accepted, skipped = [], []
    for name in sorted(os.listdir(source_folder)):
        path = os.path.join(source_folder, name)
        if not os.path.isfile(path):
            continue
        if name in _SKIP_FILES:
            skipped.append(name)
        elif os.path.splitext(name)[1].lower() in SOURCE_CONVERTERS or is_probably_text(path):
            accepted.append(name)
        else:
            skipped.append(name)
    return accepted, skipped


INFO_TAB_KEYS = ('workspace', 'corpus name', 'language', 'encoding', 'Textfiles', 'Source',
                 'Tokens', 'Types', 'Type/token')


def parse_info_tab(path: str) -> list:
    """Reads an ``info.tab`` file as an ordered list of ``(key, value)`` pairs.

    Keys keep their original case, without the trailing colon. Lines merged by older versions
    (e.g. ``encoding:\\tutf-8Textfiles:\\t98``) are split at the known keys.
    """
    import re

    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    keys = '|'.join(re.escape(k) for k in INFO_TAB_KEYS)
    content = re.sub(r'(?<=[^\n\t])(?=(?:%s):\t)' % keys, '\n', content)
    pairs = []
    for line in content.splitlines():
        line = line.strip()
        if '\t' not in line:
            continue
        key, value = line.split('\t', 1)
        pairs.append((key.rstrip(':').strip(), value.strip()))
    return pairs


def write_info_tab(path: str, pairs) -> None:
    """Writes ``(key, value)`` pairs to an ``info.tab`` file, one ``key:\\tvalue`` per line."""
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(''.join('%s:\t%s\n' % (key, value) for key, value in pairs))


def _pdf_to_text(pdf_path: str) -> str:
    """Extracts plain text from a PDF file.

    Strategy:
    1. Try direct text extraction via pypdf (fast, works for digital PDFs).
    2. If no text is found, fall back to OCR using pdf2image + pytesseract
       (handles scanned image PDFs).

    Raises ImportError if required libraries are not installed.
    """
    try:
        import pypdf
    except ImportError:
        raise ImportError(
            "pypdf is required to read PDF files. Run: uv sync"
        )

    # --- Step 1: direct text extraction ---
    text_parts = []
    with open(pdf_path, 'rb') as fh:
        reader = pypdf.PdfReader(fh)
        for page in reader.pages:
            text_parts.append(page.extract_text() or '')
    text = '\n'.join(text_parts).strip()

    if text:
        return text

    # --- Step 2: OCR fallback for scanned PDFs ---
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        raise ImportError(
            "This PDF appears to be a scanned image. OCR support requires:\n"
            "  uv add pdf2image pytesseract\n"
            "and Tesseract installed on the system (brew install tesseract)."
        )

    images = convert_from_path(pdf_path)
    ocr_parts = [pytesseract.image_to_string(img) for img in images]
    text = '\n'.join(ocr_parts).strip()

    if not text:
        raise ValueError(
            f"Could not extract text from '{pdf_path}' (tried direct extraction and OCR). "
            "The file may be corrupted or contain only non-text content."
        )
    return text


class _MarkupText:
    """Collects the visible text of HTML/XML markup (stdlib only)."""

    BLOCK_TAGS = {'p', 'div', 'br', 'li', 'tr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                  'title', 'section', 'article', 'blockquote', 'pre', 'td', 'th', 'dt', 'dd'}
    SKIP_TAGS = {'script', 'style', 'head'}

    @classmethod
    def extract(cls, markup: str, xml: bool = False) -> str:
        from html.parser import HTMLParser
        import html as html_mod
        import re as re_mod

        if xml:
            # XML: keep every text node, separate elements by line breaks
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(markup)
                parts = [t.strip() for t in root.itertext() if t and t.strip()]
                return '\n'.join(parts)
            except Exception:
                pass

        class Parser(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.parts = []
                self.skip = 0

            def handle_starttag(self, tag, attrs):
                if tag in cls.SKIP_TAGS:
                    self.skip += 1
                elif tag in cls.BLOCK_TAGS:
                    self.parts.append('\n')

            def handle_endtag(self, tag):
                if tag in cls.SKIP_TAGS and self.skip:
                    self.skip -= 1
                elif tag in cls.BLOCK_TAGS:
                    self.parts.append('\n')

            def handle_data(self, data):
                if not self.skip:
                    self.parts.append(data)

        parser = Parser()
        parser.feed(markup)
        parser.close()
        text = html_mod.unescape(''.join(parser.parts))
        text = re_mod.sub(r'[ \t\r\f\v]+', ' ', text)
        text = re_mod.sub(r'\n\s*\n+', '\n', text)
        return text.strip()


def _docx_to_text(path: str) -> str:
    """Extracts paragraphs from a .docx file (WordprocessingML) without dependencies."""
    import zipfile
    import xml.etree.ElementTree as ET
    ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    with zipfile.ZipFile(path) as zf:
        xml_bytes = zf.read('word/document.xml')
    root = ET.fromstring(xml_bytes)
    paragraphs = []
    for p in root.iter(ns + 'p'):
        chunks = []
        for node in p.iter():
            if node.tag == ns + 't' and node.text:
                chunks.append(node.text)
            elif node.tag == ns + 'tab':
                chunks.append('\t')
            elif node.tag in (ns + 'br', ns + 'cr'):
                chunks.append('\n')
        paragraphs.append(''.join(chunks))
    return '\n'.join(p for p in paragraphs if p.strip())


def _odt_to_text(path: str) -> str:
    """Extracts paragraphs from an OpenDocument text (.odt) file."""
    import zipfile
    import xml.etree.ElementTree as ET
    ns_text = '{urn:oasis:names:tc:opendocument:xmlns:text:1.0}'
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read('content.xml'))
    paragraphs = []
    for node in root.iter():
        if node.tag in (ns_text + 'p', ns_text + 'h'):
            paragraphs.append(''.join(node.itertext()))
    return '\n'.join(p for p in paragraphs if p.strip())


def _epub_to_text(path: str) -> str:
    """Extracts the text of an EPUB following its reading order (spine)."""
    import posixpath
    import zipfile
    import xml.etree.ElementTree as ET
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        documents = []
        try:
            container = ET.fromstring(zf.read('META-INF/container.xml'))
            rootfile = next(el for el in container.iter() if el.tag.endswith('rootfile')).get('full-path')
            opf = ET.fromstring(zf.read(rootfile))
            base = posixpath.dirname(rootfile)
            manifest = {}
            for el in opf.iter():
                if el.tag.endswith('item') and el.get('id') and el.get('href'):
                    manifest[el.get('id')] = posixpath.normpath(posixpath.join(base, el.get('href')))
            for el in opf.iter():
                if el.tag.endswith('itemref') and el.get('idref') in manifest:
                    documents.append(manifest[el.get('idref')])
        except Exception:
            documents = []
        if not documents:
            documents = sorted(n for n in names if n.lower().endswith(('.xhtml', '.html', '.htm')))
        texts = []
        for name in documents:
            if name in names:
                markup = zf.read(name).decode('utf-8', errors='replace')
                texts.append(_MarkupText.extract(markup))
    return '\n'.join(t for t in texts if t.strip())


def _markup_file_to_text(path: str, xml: bool = False) -> str:
    return _MarkupText.extract(read_text_detected(path), xml=xml)


# Converters for non-plain-text source files (extension → function returning text)
SOURCE_CONVERTERS = {
    '.pdf': _pdf_to_text,
    '.docx': _docx_to_text,
    '.odt': _odt_to_text,
    '.epub': _epub_to_text,
    '.html': _markup_file_to_text,
    '.htm': _markup_file_to_text,
    '.xhtml': _markup_file_to_text,
    '.xml': lambda path: _markup_file_to_text(path, xml=True),
}


def convert_to_text(path: str) -> Optional[str]:
    """Returns the plain text of a supported document, or None for plain-text files."""
    ext = os.path.splitext(path)[1].lower()
    converter = SOURCE_CONVERTERS.get(ext)
    return converter(path) if converter else None


def prepare_source_folder(source_folder: str) -> tuple:
    """Ensures source_folder is ready for corpus ingestion.

    If the folder contains PDF, Word (.docx), OpenDocument (.odt), EPUB,
    HTML/XHTML or XML files, creates a temporary directory where each one is
    converted to a plain-text .txt file (other files are copied as-is).
    Binary files (see ``list_source_files``) are left out; when there are any,
    the temporary directory holds only the accepted files.
    Returns ``(effective_folder, temp_folder_or_None)``.

    The caller is responsible for deleting ``temp_folder`` (when not None)
    after processing.
    """
    import shutil
    import tempfile

    if not source_folder.endswith('/'):
        source_folder = source_folder + '/'

    all_files, skipped = list_source_files(source_folder)
    skipped = [f for f in skipped if f not in _SKIP_FILES]
    convert_files = [f for f in all_files if os.path.splitext(f)[1].lower() in SOURCE_CONVERTERS]

    if not convert_files and not skipped:
        return source_folder, None

    # At least one document to convert — build a temp copy of the folder
    temp_dir = tempfile.mkdtemp()
    try:
        taken = {f for f in all_files if f not in convert_files}
        for filename in all_files:
            src = os.path.join(source_folder, filename)
            if filename in convert_files:
                text = convert_to_text(src)
                if not text or not text.strip():
                    raise ValueError(f"Could not extract text from '{src}'.")
                txt_name = os.path.splitext(filename)[0] + '.txt'  # replace extension → .txt
                if txt_name in taken:
                    txt_name = filename + '.txt'
                taken.add(txt_name)
                with open(os.path.join(temp_dir, txt_name), 'w', encoding='utf-8') as fh:
                    fh.write(text)
            else:
                shutil.copy2(src, os.path.join(temp_dir, filename))
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

    return temp_dir + '/', temp_dir


def file2utf8(source_file,target_file,source_encoding='mbcs'):
    import codecs
    BLOCKSIZE = 1048576 # or some other, desired size in bytes
    with codecs.open(source_file, "r", source_encoding,errors="surrogateescape") as sourceFile:
        with codecs.open(target_file, "w", "utf-8") as targetFile:
            while True:
                contents = ''.join(filter(lambda x: x in string.printable, sourceFile.read(BLOCKSIZE)))
                if not contents:
                    break
                targetFile.write(contents)
                

def file2utf8b(source_file,target_file,source_encoding='mbcs'):
    import codecs 
    with open(source_file,'rb') as fh1:
        with codecs.open(target_file,'w','utf-8') as fh2:
            while True:
                contents = fh1.read()
                if not contents:
                    break
                fh2.write(contents.decode(source_encoding))

def files2utf8(source_folder,target_folder,source_encoding='mbcs',verbose=False):
    # time start
    if verbose == True:
        print('Running...')
        t0 = time.time()
    if source_folder.endswith('/')==False:
        source_folder = source_folder + '/'
    if target_folder.endswith('/') == False:
        target_folder = target_folder + '/'
    if os.path.exists(target_folder)==False:
        os.mkdir(target_folder)
    files = os.listdir(source_folder)
    i = 0
    total = len(files)
    for filename in files:
        i+=1
        if os.path.isfile(source_folder + filename)==True:
            source_encoding = encoding_get(source_folder + filename)
            if source_encoding != 'utf-8':
                file2utf8b(source_folder + filename,target_folder + filename,source_encoding)
            else:
                with open (source_folder + filename,'r', encoding='utf-8') as fh:
                    content = fh.read()
                with open(target_folder + filename,'w', encoding='utf-8') as fh:
                    fh.write(content)
            if verbose == True:
                __progress(i, total, '')
    # time end
    if verbose == True:
        t1 = time.time()
        total_time = round(t1 - t0,2) 
        print('')
        print('Total time: %s seconds' % total_time) 

def encoding_get(filename):
    try:
        import chardet
        with open (filename,'rb') as fh:
            dados = b''.join([l for l in fh])
            return chardet.detect(dados)['encoding']
    except Exception as e:
        print(f"Error on encoding_get: {e}")

    



