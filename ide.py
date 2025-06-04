import sys
import os
import json
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTextEdit, QFileSystemModel, QTreeView, QAction,
    QFileDialog, QMessageBox, QSplitter, QSizePolicy, QMenu,
    QDialog, QPushButton, QLabel, QLineEdit, QShortcut, QCheckBox,
    QPlainTextEdit, QFontDialog, QAbstractItemView, QInputDialog,
    QCompleter, QListView, QColorDialog, QGridLayout, QScrollArea
)
from PyQt5.QtGui import (
    QIcon, QFont, QColor, QFontMetrics, QTextCharFormat, QTextCursor,
    QTextDocument, QSyntaxHighlighter, QImage, QPixmap, QTextOption, QKeySequence
)
from PyQt5.QtCore import Qt, QDir, QProcess, QTimer, QThread, pyqtSignal, QUrl, QMimeData, QStringListModel, QSize, QRect

try:
    from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
    from PyQt5.QtMultimediaWidgets import QVideoWidget
    _HAS_MULTIMEDIA = True
except ImportError:
    _HAS_MULTIMEDIA = False

import re
try:
    import jedi
    _HAS_JEDI = True
except ImportError:
    _HAS_JEDI = False
    print("Jedi not found. Auto-completion will be basic.")


# Define syntax highlighting colors for various programming languages and elements.
# These colors are used to provide visual distinction in the code editor.
SYNTAX_COLORS = {
    "comments": "#375e3d",
    "variable": "#c32454",
    "strings": "#cd683d",
    "integer": "#539799",
    "float": "#539799",
    "boolean": "#d65151",
    "function": "#2f6199",
    "import": "#912749",
    "keywords": "#6b3e75",
    "self_keyword": "#d65151",
    "class_name": "#fbb954",
    "decorator": "#912749",
    "html_tag": "#2f6199",
    "html_attribute": "#912749",
    "css_selector": "#6b3e75",
    "css_property": "#c32454",
    "js_keyword": "#6b3e75",
    "js_string": "#cd683d",
    "js_comment": "#375e3d",
    "java_keyword": "#6b3e75",
    "c_cpp_keyword": "#6b3e75",
    "csharp_keyword": "#6b3e75",
    "sql_keyword": "#6b3e75",
    "swift_keyword": "#6b3e75",
    "ruby_keyword": "#6b3e75",
    "go_keyword": "#6b3e75",
    "rust_keyword": "#6b3e75",
    "php_keyword": "#6b3e75",
    "perl_keyword": "#6b3e75",
    "kotlin_keyword": "#6b3e75",
    "react_native_keyword": "#6b3e75",
    "xml_tag": "#2f6199",
    "xml_attribute": "#912749",
    "json_key": "#c32454",
    "json_value_string": "#cd683d",
    "json_value_number": "#539799",
    "markdown_heading": "#2f6199",
    "markdown_bold": "#c32454",
    "markdown_italic": "#cd683d",
    "shell_keyword": "#6b3e75",
    "shell_string": "#cd683d",
    "typescript_keyword": "#6b3e75",
    "vue_keyword": "#2f6199",
    "dart_keyword": "#6b3e75",
    "r_keyword": "#6b3e75",
}

# Define color themes for the IDE, supporting dark and light modes.
# Each theme specifies colors for various UI elements like background, text, selections, etc.
THEMES = {
    "dark": {
        "bg_color": "#282c34", # Background for main window and code editor
        "text_color": "#abb2bf", # Default text color
        "selection_bg": "#3a3f4b", # Background for selected text
        "current_line_bg": "#2e333b", # Background for the current line in editor
        "tab_bg": "#21252b", # Background for inactive tabs
        "tab_text": "#abb2bf", # Text color for inactive tabs
        "tab_selected_bg": "#282c34", # Background for selected tab
        "border_color": "#3e4452", # Border color for various widgets
        "terminal_bg": "#1e1e1e", # Background for terminal
        "terminal_text": "#d4d4d4", # Text color for terminal
        "scrollbar_bg": "#3e4452",
        "scrollbar_handle": "#616a75",
        "scrollbar_handle_hover": "#7b8692",
        "completer_bg": "#21252b",
        "completer_text": "#abb2bf",
        "completer_selection_bg": "#3a3f4b",
        "file_tree_selection_bg": "#007acc", # Blue for file tree selection
        "file_tree_selection_text": "#ffffff", # White text for file tree selection
    },
    "light": {
        "bg_color": "#ffffff",
        "text_color": "#333333",
        "selection_bg": "#c8d8f0",
        "current_line_bg": "#f0f0f0",
        "tab_bg": "#f0f0f0",
        "tab_text": "#333333",
        "tab_selected_bg": "#ffffff",
        "border_color": "#cccccc",
        "terminal_bg": "#f8f8f8",
        "terminal_text": "#333333",
        "scrollbar_bg": "#e0e0e0",
        "scrollbar_handle": "#a0a0a0",
        "scrollbar_handle_hover": "#808080",
        "completer_bg": "#f0f0f0",
        "completer_text": "#333333",
        "completer_selection_bg": "#c8d8f0",
        "file_tree_selection_bg": "#4a90d9", # Blue for file tree selection
        "file_tree_selection_text": "#ffffff", # White text for file tree selection
    }
}

# Configuration file path for saving user preferences
CONFIG_FILE = "kodykoala_config.json"
SESSION_FILE = "kodykoala_session.json" # File for crash recovery

# CustomFileSystemModel extends QFileSystemModel to provide custom icons.
# This is used to display a custom folder icon in the file tree.
class CustomFileSystemModel(QFileSystemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.folder_icon_path = "C:/Users/Aiden shoroz/Desktop/folder.png"
        self.folder_icon = self._load_custom_folder_icon()

    def _load_custom_folder_icon(self):
        if os.path.exists(self.folder_icon_path):
            return QIcon(self.folder_icon_path)
        else:
            print(f"Warning: Custom folder icon not found at {self.folder_icon_path}. Using default icon.")
            return QIcon.fromTheme("folder") # Fallback to default folder icon

    def icon(self, index):
        if self.isDir(index):
            return self.folder_icon # Return custom icon for directories
        return super().icon(index) # For other files, return default icon

# PythonHighlighter provides syntax highlighting for Python code.
# It defines rules for keywords, strings, comments, functions, numbers, etc.
class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        # Keyword format and rules
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["keywords"]))
        keywords = ['False', 'None', 'True', 'and', 'as', 'assert', 'async',
                    'await', 'break', 'class', 'continue', 'def', 'del',
                    'elif', 'else', 'except', 'finally', 'for', 'from',
                    'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal',
                    'not', 'or', 'pass', 'raise', 'return', 'try', 'while',
                    'with', 'yield', 'print', 'input', 'len', 'range', 'list',
                    'dict', 'set', 'tuple', 'str', 'int', 'float', 'bool',
                    'super', 'self', 'abs', 'all', 'any', 'ascii', 'bin',
                    'bytes', 'callable', 'chr', 'classmethod', 'compile', 'complex',
                    'delattr', 'dir', 'divmod', 'enumerate', 'exec', 'filter',
                    'format', 'frozenset', 'getattr', 'globals', 'hasattr', 'hash',
                    'help', 'hex', 'id', 'issubclass', 'iter', 'map', 'max', 'min',
                    'next', 'object', 'oct', 'open', 'ord', 'pow', 'property',
                    'repr', 'reversed', 'round', 'setattr', 'slice', 'sorted',
                    'staticmethod', 'sum', 'type', 'vars', 'zip']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), keywordFormat)
                                       for keyword in keywords])

        # String format and rules (single, double, and triple quotes)
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
        self.highlightingRules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), stringFormat))
        self.highlightingRules.append((re.compile(r'"""[\s\S]*?"""'), stringFormat))
        self.highlightingRules.append((re.compile(r"'''[\s\S]*?'''"), stringFormat))

        # Comment format and rules
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'#[^\n]*'), commentFormat))

        # Function format and rules
        functionFormat = QTextCharFormat()
        functionFormat.setForeground(QColor(SYNTAX_COLORS["function"]))
        self.highlightingRules.append((re.compile(r'\b[A-Za-z_][A-Za-z0-9_]*\s*\('), functionFormat))

        # Number format and rules (integers and floats)
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(SYNTAX_COLORS["integer"]))
        self.highlightingRules.append((re.compile(r'\b[0-9]+(?:\.[0-9]+)?\b'), numberFormat))

        # 'self' keyword format
        selfFormat = QTextCharFormat()
        selfFormat.setForeground(QColor(SYNTAX_COLORS["self_keyword"]))
        self.highlightingRules.append((re.compile(r'\bself\b'), selfFormat))

        # Class name format and rules
        classNameFormat = QTextCharFormat()
        classNameFormat.setForeground(QColor(SYNTAX_COLORS["class_name"]))
        self.highlightingRules.append((re.compile(r'\bclass\s+([A-Z][A-Za-z0-9_]*)\b'), classNameFormat))

        # Decorator format and rules
        decoratorFormat = QTextCharFormat()
        decoratorFormat.setForeground(QColor(SYNTAX_COLORS["decorator"]))
        self.highlightingRules.append((re.compile(r'@\b[A-Za-z_][A-Za-z0-9_]*\b'), decoratorFormat))

    # Applies highlighting rules to a block of text.
    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            if pattern.pattern.startswith(r'\bclass\s+') or pattern.pattern.startswith(r'@'):
                # Special handling for class names and decorators to highlight only the relevant part
                match_iter = pattern.finditer(text)
                for match in match_iter:
                    if match.groups():
                        self.setFormat(match.start(1), len(match.group(1)), format)
                    else:
                        self.setFormat(match.start(), match.end() - match.start(), format)
            else:
                # General highlighting for other patterns
                expression = pattern
                index = expression.search(text)
                while index:
                    self.setFormat(index.start(), index.end() - index.start(), format)
                    index = expression.search(text, index.end())
        self.setCurrentBlockState(0)

# HtmlHighlighter provides syntax highlighting for HTML code.
class HtmlHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        tagFormat = QTextCharFormat()
        tagFormat.setForeground(QColor(SYNTAX_COLORS["html_tag"]))
        self.highlightingRules.append((re.compile(r'</?[a-zA-Z0-9]+[^>]*>'), tagFormat))

        attributeFormat = QTextCharFormat()
        attributeFormat.setForeground(QColor(SYNTAX_COLORS["html_attribute"]))
        self.highlightingRules.append((re.compile(r'\b[a-zA-Z\-]+\s*='), attributeFormat))

        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r'"[^"]*"'), stringFormat))
        self.highlightingRules.append((re.compile(r"'[^']*'"), stringFormat))

        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'<!--.*?-->'), commentFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# CssHighlighter provides syntax highlighting for CSS code.
class CssHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        selectorFormat = QTextCharFormat()
        selectorFormat.setForeground(QColor(SYNTAX_COLORS["css_selector"]))
        self.highlightingRules.append((re.compile(r'[.#]?[a-zA-Z0-9\-]+\s*{'), selectorFormat))
        self.highlightingRules.append((re.compile(r'\b(body|html|div|span|p|a|ul|ol|li|h1|h2|h3|h4|h5|h6)\b'), selectorFormat))

        propertyFormat = QTextCharFormat()
        propertyFormat.setForeground(QColor(SYNTAX_COLORS["css_property"]))
        css_properties = ['align-items', 'background', 'background-color', 'border', 'border-radius',
                          'box-shadow', 'color', 'display', 'flex', 'font-family', 'font-size',
                          'font-weight', 'height', 'justify-content', 'margin', 'margin-bottom',
                          'margin-left', 'margin-right', 'margin-top', 'max-width', 'min-height',
                          'opacity', 'overflow', 'padding', 'padding-bottom', 'padding-left',
                          'padding-right', 'padding-top', 'position', 'text-align', 'text-decoration',
                          'transform', 'transition', 'width', 'z-index', 'top', 'bottom', 'left', 'right']
        self.highlightingRules.extend([(re.compile(r'\b' + prop + r'\b\s*:'), propertyFormat) for prop in css_properties])

        valueFormat = QTextCharFormat()
        valueFormat.setForeground(QColor(SYNTAX_COLORS["function"]))
        self.highlightingRules.append((re.compile(r':\s*[^;}]*'), valueFormat))

        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'/\*.*?\*/'), commentFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# JavaScriptHighlighter provides syntax highlighting for JavaScript code.
class JavaScriptHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["js_keyword"]))
        keywords = ['break', 'case', 'catch', 'class', 'const', 'continue',
                    'debugger', 'default', 'delete', 'do', 'else', 'export',
                    'extends', 'finally', 'for', 'function', 'if', 'import',
                    'in', 'instanceof', 'new', 'return', 'super', 'switch',
                    'this', 'throw', 'typeof', 'var', 'void', 'while',
                    'with', 'yield', 'let', 'static', 'await', 'async', 'of',
                    'console', 'log', 'document', 'window', 'alert', 'confirm',
                    'prompt', 'fetch', 'then', 'catch', 'finally', 'map', 'filter',
                    'reduce', 'forEach', 'setTimeout', 'setInterval', 'clearTimeout',
                    'clearInterval', 'JSON', 'parse', 'stringify', 'Math', 'Date',
                    'Array', 'Object', 'String', 'Number', 'Boolean', 'Promise',
                    'Symbol', 'Proxy', 'Reflect', 'WeakMap', 'WeakSet', 'Set', 'Map']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), keywordFormat)
                                       for keyword in keywords])

        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["js_string"]))
        self.highlightingRules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
        self.highlightingRules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), stringFormat))
        self.highlightingRules.append((re.compile(r'`[^`\\]*(\\.[^`\\]*)*`'), stringFormat))

        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'//[^\n]*'), commentFormat))
        self.highlightingRules.append((re.compile(r'/\*.*?\*/', re.DOTALL), commentFormat))

        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(SYNTAX_COLORS["integer"]))
        self.highlightingRules.append((re.compile(r'\b[0-9]+(?:\.[0-9]+)?\b'), numberFormat))

        functionFormat = QTextCharFormat()
        functionFormat.setForeground(QColor(SYNTAX_COLORS["function"]))
        self.highlightingRules.append((re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*\('), functionFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# JavaHighlighter provides syntax highlighting for Java code.
class JavaHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["java_keyword"]))
        keywords = ['abstract', 'continue', 'for', 'new', 'switch', 'assert', 'default', 'goto',
                    'package', 'synchronized', 'boolean', 'do', 'if', 'private', 'this', 'break',
                    'double', 'implements', 'protected', 'throw', 'byte', 'else', 'import',
                    'public', 'throws', 'case', 'enum', 'instanceof', 'return', 'transient',
                    'catch', 'extends', 'int', 'short', 'try', 'char', 'final', 'interface',
                    'static', 'void', 'class', 'finally', 'long', 'strictfp', 'volatile',
                    'const', 'float', 'native', 'super', 'while', 'null', 'true', 'false',
                    'System', 'out', 'println', 'main', 'String', 'void', 'public', 'private',
                    'protected']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), keywordFormat) for keyword in keywords])
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
        self.highlightingRules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), stringFormat))
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'//[^\n]*'), commentFormat))
        self.highlightingRules.append((re.compile(r'/\*.*?\*/', re.DOTALL), commentFormat))
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(SYNTAX_COLORS["integer"]))
        self.highlightingRules.append((re.compile(r'\b[0-9]+(?:\.[0-9]+)?\b'), numberFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# CppHighlighter provides syntax highlighting for C++ code.
class CppHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["c_cpp_keyword"]))
        keywords = ['alignas', 'alignof', 'and', 'and_eq', 'asm', 'atomic_cancel',
                    'atomic_commit', 'atomic_noexcept', 'auto', 'bitand', 'bitor',
                    'bool', 'break', 'case', 'catch', 'char', 'char8_t', 'char16_t',
                    'char32_t', 'class', 'compl', 'concept', 'const', 'consteval',
                    'constexpr', 'constinit', 'const_cast', 'continue', 'co_await',
                    'co_return', 'co_yield', 'decltype', 'default', 'delete', 'do',
                    'double', 'dynamic_cast', 'else', 'enum', 'explicit', 'export',
                    'extern', 'false', 'float', 'for', 'friend', 'goto', 'if',
                    'inline', 'int', 'long', 'mutable', 'namespace', 'new', 'noexcept',
                    'not', 'not_eq', 'nullptr', 'operator', 'or', 'or_eq', 'private',
                    'protected', 'public', 'reflexpr', 'register', 'reinterpret_cast',
                    'requires', 'return', 'short', 'signed', 'sizeof', 'static',
                    'static_assert', 'static_cast', 'struct', 'switch', 'synchronized',
                    'template', 'this', 'thread_local', 'throw', 'true', 'try',
                    'typedef', 'typeid', 'typename', 'union', 'unsigned', 'using',
                    'virtual', 'void', 'volatile', 'wchar_t', 'while', 'xor', 'xor_eq',
                    'cout', 'cin', 'endl', 'std', 'vector', 'string', 'map', 'set', 'include']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), keywordFormat) for keyword in keywords])
        preprocessorFormat = QTextCharFormat()
        preprocessorFormat.setForeground(QColor(SYNTAX_COLORS["import"]))
        self.highlightingRules.append((re.compile(r'#.*'), preprocessorFormat))
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
        self.highlightingRules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), stringFormat))
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'//[^\n]*'), commentFormat))
        self.highlightingRules.append((re.compile(r'/\*.*?\*/', re.DOTALL), commentFormat))
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(SYNTAX_COLORS["integer"]))
        self.highlightingRules.append((re.compile(r'\b[0-9]+(?:\.[0-9]+)?\b'), numberFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# CSharpHighlighter provides syntax highlighting for C# code.
class CSharpHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["csharp_keyword"]))
        keywords = ['abstract', 'as', 'base', 'bool', 'break', 'byte', 'case', 'catch',
                    'char', 'checked', 'class', 'const', 'continue', 'decimal', 'default',
                    'delegate', 'do', 'double', 'else', 'enum', 'event', 'explicit', 'extern',
                    'false', 'finally', 'fixed', 'float', 'for', 'foreach', 'goto', 'if',
                    'implicit', 'in', 'int', 'interface', 'internal', 'is', 'lock', 'long',
                    'namespace', 'new', 'null', 'object', 'operator', 'out', 'override',
                    'params', 'private', 'protected', 'public', 'readonly', 'ref', 'return',
                    'sbyte', 'sealed', 'short', 'sizeof', 'stackalloc', 'static', 'string',
                    'struct', 'switch', 'this', 'throw', 'true', 'try', 'typeof', 'uint',
                    'ulong', 'unchecked', 'unsafe', 'ushort', 'using', 'virtual', 'void',
                    'volatile', 'while', 'add', 'alias', 'ascending', 'async', 'await',
                    'by', 'descending', 'dynamic', 'from', 'get', 'global', 'group', 'into',
                    'join', 'let', 'nameof', 'on', 'orderby', 'partial', 'remove', 'select',
                    'set', 'value', 'var', 'when', 'where', 'yield', 'Console', 'WriteLine']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), keywordFormat) for keyword in keywords])
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
        self.highlightingRules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), stringFormat))
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'//[^\n]*'), commentFormat))
        self.highlightingRules.append((re.compile(r'/\*.*?\*/', re.DOTALL), commentFormat))
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(SYNTAX_COLORS["integer"]))
        self.highlightingRules.append((re.compile(r'\b[0-9]+(?:\.[0-9]+)?\b'), numberFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# ScssHighlighter provides syntax highlighting for SCSS code.
class ScssHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []
        variableFormat = QTextCharFormat()
        variableFormat.setForeground(QColor(SYNTAX_COLORS["variable"]))
        self.highlightingRules.append((re.compile(r'\$[a-zA-Z0-9_-]+'), variableFormat))

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["keywords"]))
        keywords = ['@import', '@mixin', '@include', '@function', '@return', '@extend', '@if', '@else', '@for', '@each', '@while']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), keywordFormat) for keyword in keywords])

        css_highlighter = CssHighlighter(document)
        self.highlightingRules.extend(css_highlighter.highlightingRules)

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# SqlHighlighter provides syntax highlighting for SQL code.
class SqlHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["sql_keyword"]))
        keywords = ['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'INSERT', 'INTO', 'VALUES',
                    'UPDATE', 'SET', 'DELETE', 'FROM', 'CREATE', 'TABLE', 'ALTER', 'DROP',
                    'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'ON', 'GROUP BY', 'ORDER BY',
                    'HAVING', 'AS', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX',
                    'DATABASE', 'USE', 'PRIMARY KEY', 'FOREIGN KEY', 'NOT NULL', 'UNIQUE',
                    'INDEX', 'VIEW', 'PROCEDURE', 'FUNCTION', 'TRIGGER', 'BEGIN', 'END',
                    'COMMIT', 'ROLLBACK', 'TRUNCATE', 'UNION', 'ALL', 'EXISTS', 'LIKE',
                    'IN', 'IS', 'NULL', 'BETWEEN', 'CASE', 'WHEN', 'THEN', 'END', 'CAST',
                    'CONVERT', 'DATE', 'TIME', 'DATETIME', 'VARCHAR', 'INT', 'TEXT', 'BOOLEAN']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b', re.IGNORECASE), keywordFormat) for keyword in keywords])

        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), stringFormat))

        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'--[^\n]*'), commentFormat))
        self.highlightingRules.append((re.compile(r'/\*.*?\*/', re.DOTALL), commentFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# SwiftHighlighter provides syntax highlighting for Swift code.
class SwiftHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["swift_keyword"]))
        keywords = ['associatedtype', 'class', 'deinit', 'enum', 'extension', 'fileprivate',
                    'func', 'import', 'init', 'inout', 'internal', 'let', 'open', 'operator',
                    'private', 'protocol', 'public', 'static', 'struct', 'subscript', 'typealias',
                    'var', 'break', 'case', 'continue', 'default', 'defer', 'do', 'else',
                    'fallthrough', 'for', 'guard', 'if', 'in', 'repeat', 'return', 'switch',
                    'where', 'while', 'as', 'Any', 'catch', 'false', 'is', 'nil', 'rethrows',
                    'super', 'self', 'Self', 'throw', 'throws', 'true', 'try', 'associativity',
                    'convenience', 'dynamic', 'didSet', 'final', 'get', 'infix', 'indirect',
                    'lazy', 'left', 'mutating', 'nonmutating', 'optional', 'override', 'postfix',
                    'precedence', 'prefix', 'Protocol', 'required', 'right', 'set', 'Type',
                    'unowned', 'weak', 'willSet', 'print']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), keywordFormat) for keyword in keywords])
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'//[^\n]*'), commentFormat))
        self.highlightingRules.append((re.compile(r'/\*.*?\*/', re.DOTALL), commentFormat))
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(SYNTAX_COLORS["integer"]))
        self.highlightingRules.append((re.compile(r'\b[0-9]+(?:\.[0-9]+)?\b'), numberFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# RubyHighlighter provides syntax highlighting for Ruby code.
class RubyHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["ruby_keyword"]))
        keywords = ['BEGIN', 'END', 'alias', 'and', 'begin', 'break', 'case', 'class',
                    'def', 'defined?', 'do', 'else', 'elsif', 'end', 'ensure', 'false',
                    'for', 'if', 'in', 'module', 'next', 'nil', 'not', 'or', 'redo',
                    'rescue', 'retry', 'return', 'self', 'super', 'then', 'true',
                    'undef', 'unless', 'until', 'when', 'while', 'yield', 'puts', 'gets']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), keywordFormat) for keyword in keywords])
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
        self.highlightingRules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), stringFormat))
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'#[^\n]*'), commentFormat))
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(SYNTAX_COLORS["integer"]))
        self.highlightingRules.append((re.compile(r'\b[0-9]+(?:\.[0-9]+)?\b'), numberFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# GoHighlighter provides syntax highlighting for Go code.
class GoHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["go_keyword"]))
        keywords = ['break', 'case', 'chan', 'const', 'continue', 'default', 'defer', 'else',
                    'fallthrough', 'for', 'func', 'go', 'goto', 'if', 'import', 'interface',
                    'map', 'package', 'range', 'return', 'select', 'struct', 'switch', 'type',
                    'var', 'fmt', 'Println', 'main']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), keywordFormat) for keyword in keywords])
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
        self.highlightingRules.append((re.compile(r'`.*?`', re.DOTALL), stringFormat))
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'//[^\n]*'), commentFormat))
        self.highlightingRules.append((re.compile(r'/\*.*?\*/', re.DOTALL), commentFormat))
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(SYNTAX_COLORS["integer"]))
        self.highlightingRules.append((re.compile(r'\b[0-9]+(?:\.[0-9]+)?\b'), numberFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# RustHighlighter provides syntax highlighting for Rust code.
class RustHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["rust_keyword"]))
        keywords = ['as', 'break', 'const', 'continue', 'crate', 'else', 'enum', 'extern',
                    'false', 'fn', 'for', 'if', 'impl', 'in', 'let', 'loop', 'match',
                    'mod', 'move', 'mut', 'pub', 'ref', 'return', 'self', 'Self', 'static',
                    'struct', 'super', 'trait', 'true', 'type', 'unsafe', 'use', 'where',
                    'while', 'async', 'await', 'dyn', 'macro', 'union', 'println']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), keywordFormat) for keyword in keywords])
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'//[^\n]*'), commentFormat))
        self.highlightingRules.append((re.compile(r'/\*.*?\*/', re.DOTALL), commentFormat))
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(SYNTAX_COLORS["integer"]))
        self.highlightingRules.append((re.compile(r'\b[0-9]+(?:\.[0-9]+)?\b'), numberFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# PhpHighlighter provides syntax highlighting for PHP code.
class PhpHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["php_keyword"]))
        keywords = ['__halt_compiler', 'abstract', 'and', 'array', 'as', 'break', 'callable',
                    'case', 'catch', 'class', 'clone', 'const', 'continue', 'declare', 'default',
                    'die', 'do', 'echo', 'else', 'elseif', 'empty', 'enddeclare', 'endfor',
                    'endforeach', 'endif', 'endswitch', 'endwhile', 'eval', 'exit', 'extends',
                    'final', 'finally', 'for', 'foreach', 'function', 'global', 'goto', 'if',
                    'implements', 'include', 'include_once', 'instanceof', 'insteadof', 'interface',
                    'isset', 'list', 'namespace', 'new', 'or', 'print', 'private', 'protected',
                    'public', 'require', 'require_once', 'return', 'static', 'switch', 'throw',
                    'trait', 'try', 'unset', 'use', 'var', 'while', 'xor', 'yield']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b', re.IGNORECASE), keywordFormat) for keyword in keywords])
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
        self.highlightingRules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), stringFormat))
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'//[^\n]*'), commentFormat))
        self.highlightingRules.append((re.compile(r'#[^\n]*'), commentFormat))
        self.highlightingRules.append((re.compile(r'/\*.*?\*/', re.DOTALL), commentFormat))
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(SYNTAX_COLORS["integer"]))
        self.highlightingRules.append((re.compile(r'\b[0-9]+(?:\.[0-9]+)?\b'), numberFormat))
        variableFormat = QTextCharFormat()
        variableFormat.setForeground(QColor(SYNTAX_COLORS["variable"]))
        self.highlightingRules.append((re.compile(r'\$[a-zA-Z_][a-zA-Z0-9_]*'), variableFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# PerlHighlighter provides syntax highlighting for Perl code.
class PerlHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["perl_keyword"]))
        keywords = ['abs', 'accept', 'alarm', 'and', 'atan2', 'bind', 'binmode', 'bless',
                    'break', 'caller', 'chdir', 'chmod', 'chomp', 'chop', 'chown', 'chr',
                    'chroot', 'close', 'closedir', 'connect', 'continue', 'cos', 'crypt',
                    'dbmclose', 'dbmopen', 'defined', 'delete', 'die', 'do', 'dump', 'each',
                    'else', 'elsif', 'endgrent', 'endhostent', 'endnetent', 'endprotoent',
                    'endpwent', 'endservent', 'eof', 'eval', 'exec', 'exists', 'exit',
                    'exp', 'fcntl', 'fileno', 'flock', 'for', 'foreach', 'fork', 'format',
                    'formline', 'getc', 'getgrent', 'getgrgid', 'getgrnam', 'gethostbyaddr',
                    'gethostbyname', 'gethostent', 'getlogin', 'getnetbyaddr', 'getnetbyname',
                    'getnetent', 'getpeername', 'getpgrp', 'getppid', 'getpriority',
                    'getprotobyname', 'getprotobynumber', 'getprotoent', 'getpwent',
                    'getpwnam', 'getpwuid', 'getservbyname', 'getservbyport', 'getservent',
                    'getsockname', 'getsockopt', 'glob', 'gmtime', 'goto', 'grep', 'hex',
                    'if', 'index', 'int', 'ioctl', 'join', 'keys', 'kill', 'last', 'lc',
                    'lcfirst', 'length', 'link', 'listen', 'local', 'localtime', 'log',
                    'lstat', 'map', 'mkdir', 'msgctl', 'msgget', 'msgrcv', 'msgsnd', 'my',
                    'next', 'no', 'oct', 'open', 'opendir', 'or', 'ord', 'our', 'pack',
                    'pipe', 'pop', 'pos', 'print', 'printf', 'prototype', 'push', 'quotemeta',
                    'rand', 'read', 'readdir', 'readlink', 'readpipe', 'recv', 'redo', 'ref',
                    'rename', 'require', 'reset', 'return', 'reverse', 'rewinddir', 'rindex',
                    'rmdir', 'say', 'scalar', 'seek', 'seekdir', 'select', 'semctl', 'semget',
                    'semop', 'send', 'setgrent', 'sethostent', 'setnetent', 'setpgrp',
                    'setpriority', 'setprotoent', 'setpwent', 'setservent', 'setsockopt',
                    'shift', 'shmctl', 'shmget', 'shmread', 'shmwrite', 'shutdown', 'sin',
                    'sleep', 'socket', 'socketpair', 'sort', 'splice', 'split', 'sprintf',
                    'sqrt', 'srand', 'stat', 'state', 'study', 'sub', 'substr', 'symlink',
                    'syscall', 'sysopen', 'sysread', 'sysseek', 'system', 'syswrite', 'tell',
                    'telldir', 'tie', 'tied', 'time', 'times', 'tr', 'truncate', 'uc', 'ucfirst',
                    'umask', 'undef', 'unless', 'unlink', 'unpack', 'unshift', 'untie', 'until',
                    'use', 'utime', 'values', 'vec', 'wait', 'waitpid', 'wantarray', 'warn',
                    'when', 'while', 'write', 'y']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), keywordFormat) for keyword in keywords])
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
        self.highlightingRules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), stringFormat))
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'#[^\n]*'), commentFormat))
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(SYNTAX_COLORS["integer"]))
        self.highlightingRules.append((re.compile(r'\b[0-9]+(?:\.[0-9]+)?\b'), numberFormat))
        variableFormat = QTextCharFormat()
        variableFormat.setForeground(QColor(SYNTAX_COLORS["variable"]))
        self.highlightingRules.append((re.compile(r'[\$\@\%][a-zA-Z_][a-zA-Z0-9_]*'), variableFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# KotlinHighlighter provides syntax highlighting for Kotlin code.
class KotlinHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["kotlin_keyword"]))
        keywords = ['as', 'as?', 'break', 'class', 'continue', 'do', 'else', 'false',
                    'for', 'fun', 'if', 'in', 'interface', 'is', 'null', 'object',
                    'package', 'return', 'super', 'this', 'throw', 'true', 'try',
                    'typealias', 'typeof', 'val', 'var', 'when', 'while', 'by', 'catch',
                    'constructor', 'delegate', 'dynamic', 'field', 'file', 'finally',
                    'get', 'import', 'init', 'param', 'property', 'receiver', 'set',
                    'setparam', 'where', 'actual', 'annotation', 'companion', 'crossinline',
                    'data', 'enum', 'expect', 'external', 'infix', 'inline', 'inner',
                    'internal', 'lateinit', 'noinline', 'open', 'operator', 'out',
                    'override', 'private', 'protected', 'public', 'reified', 'sealed',
                    'suspend', 'tailrec', 'vararg', 'println']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), keywordFormat) for keyword in keywords])
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
        self.highlightingRules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), stringFormat))
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'//[^\n]*'), commentFormat))
        self.highlightingRules.append((re.compile(r'/\*.*?\*/', re.DOTALL), commentFormat))
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(SYNTAX_COLORS["integer"]))
        self.highlightingRules.append((re.compile(r'\b[0-9]+(?:\.[0-9]+)?\b'), numberFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# ReactNativeHighlighter provides syntax highlighting for React Native (JSX/TSX) code.
class ReactNativeHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []
        js_highlighter = JavaScriptHighlighter(document)
        self.highlightingRules.extend(js_highlighter.highlightingRules)

        jsxTagFormat = QTextCharFormat()
        jsxTagFormat.setForeground(QColor(SYNTAX_COLORS["html_tag"]))
        self.highlightingRules.append((re.compile(r'<[A-Za-z][A-Za-z0-9_.]*[^>]*>'), jsxTagFormat))
        self.highlightingRules.append((re.compile(r'</[A-Za-z][A-Za-z0-9_.]*>'), jsxTagFormat))

        jsxAttributeFormat = QTextCharFormat()
        jsxAttributeFormat.setForeground(QColor(SYNTAX_COLORS["html_attribute"]))
        self.highlightingRules.append((re.compile(r'\b[a-zA-Z\-]+\s*='), jsxAttributeFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# XmlHighlighter provides syntax highlighting for XML code.
class XmlHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        tagFormat = QTextCharFormat()
        tagFormat.setForeground(QColor(SYNTAX_COLORS["xml_tag"]))
        self.highlightingRules.append((re.compile(r'</?[a-zA-Z0-9_.:\-]+[^>]*>'), tagFormat))

        attributeFormat = QTextCharFormat()
        attributeFormat.setForeground(QColor(SYNTAX_COLORS["xml_attribute"]))
        self.highlightingRules.append((re.compile(r'\b[a-zA-Z_:\-]+="[^"]*"'), attributeFormat))
        self.highlightingRules.append((re.compile(r'\b[a-zA-Z_:\-]+=\'[^\']*\''), attributeFormat))

        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r'"[^"]*"'), stringFormat))
        self.highlightingRules.append((re.compile(r"'[^']*'"), stringFormat))

        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'<!--.*?-->'), commentFormat))

        doctypeFormat = QTextCharFormat()
        doctypeFormat.setForeground(QColor(SYNTAX_COLORS["import"]))
        self.highlightingRules.append((re.compile(r'<!DOCTYPE[^>]*>'), doctypeFormat))

        cdataFormat = QTextCharFormat()
        cdataFormat.setForeground(QColor(SYNTAX_COLORS["variable"]))
        self.highlightingRules.append((re.compile(r'<!\[CDATA\[.*?\]\]>', re.DOTALL), cdataFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# JsonHighlighter provides syntax highlighting for JSON data.
class JsonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        keyFormat = QTextCharFormat()
        keyFormat.setForeground(QColor(SYNTAX_COLORS["json_key"]))
        self.highlightingRules.append((re.compile(r'"(\w+)":'), keyFormat))

        stringValueFormat = QTextCharFormat()
        stringValueFormat.setForeground(QColor(SYNTAX_COLORS["json_value_string"]))
        self.highlightingRules.append((re.compile(r':\s*"[^"]*"'), stringValueFormat))

        numberValueFormat = QTextCharFormat()
        numberValueFormat.setForeground(QColor(SYNTAX_COLORS["json_value_number"]))
        self.highlightingRules.append((re.compile(r':\s*\b-?\d+(\.\d+)?([eE][+\-]?\d+)?\b'), numberValueFormat))

        booleanNullFormat = QTextCharFormat()
        booleanNullFormat.setForeground(QColor(SYNTAX_COLORS["boolean"]))
        self.highlightingRules.append((re.compile(r'\b(true|false|null)\b'), booleanNullFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                if pattern.pattern == r'"(\w+)":':
                    self.setFormat(index.start(1), len(index.group(1)), format)
                else:
                    self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# MarkdownHighlighter provides syntax highlighting for Markdown text.
class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        headingFormat = QTextCharFormat()
        headingFormat.setForeground(QColor(SYNTAX_COLORS["markdown_heading"]))
        self.highlightingRules.append((re.compile(r'^#+\s.*'), headingFormat))

        boldFormat = QTextCharFormat()
        boldFormat.setForeground(QColor(SYNTAX_COLORS["markdown_bold"]))
        boldFormat.setFontWeight(QFont.Bold)
        self.highlightingRules.append((re.compile(r'\*\*([^\*]+)\*\*'), boldFormat))
        self.highlightingRules.append((re.compile(r'__([^_]+)__'), boldFormat))

        italicFormat = QTextCharFormat()
        italicFormat.setForeground(QColor(SYNTAX_COLORS["markdown_italic"]))
        italicFormat.setFontItalic(True)
        self.highlightingRules.append((re.compile(r'\*([^\*]+)\*'), italicFormat))
        self.highlightingRules.append((re.compile(r'_([^_]+)_'), italicFormat))

        codeBlockFormat = QTextCharFormat()
        codeBlockFormat.setForeground(QColor(SYNTAX_COLORS["variable"]))
        self.highlightingRules.append((re.compile(r'`[^`]+`'), codeBlockFormat))
        self.highlightingRules.append((re.compile(r'```[\s\S]*?```', re.DOTALL), codeBlockFormat))

        linkFormat = QTextCharFormat()
        linkFormat.setForeground(QColor(SYNTAX_COLORS["function"]))
        linkFormat.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        self.highlightingRules.append((re.compile(r'\[([^\]]+)\]\(([^\)]+)\)'), linkFormat))

        listFormat = QTextCharFormat()
        listFormat.setForeground(QColor(SYNTAX_COLORS["keywords"]))
        self.highlightingRules.append((re.compile(r'^\s*[\-\*\+]\s'), listFormat))
        self.highlightingRules.append((re.compile(r'^\s*\d+\.\s'), listFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                if pattern.pattern.startswith(r'\*\*') or pattern.pattern.startswith(r'__') or \
                   pattern.pattern.startswith(r'\*') or pattern.pattern.startswith(r'_') or \
                   pattern.pattern.startswith(r'`') or pattern.pattern.startswith(r'\['):
                    self.setFormat(index.start(1), len(index.group(1)), format)
                else:
                    self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# ShellHighlighter provides syntax highlighting for Shell scripts (Bash).
class ShellHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["shell_keyword"]))
        keywords = ['if', 'then', 'else', 'elif', 'fi', 'case', 'esac', 'for', 'while',
                    'until', 'do', 'done', 'in', 'function', 'select', 'break', 'continue',
                    'return', 'exit', 'export', 'declare', 'local', 'readonly', 'unset',
                    'source', 'test', '[[', ']]', '[', ']', 'cd', 'pwd', 'ls', 'grep',
                    'find', 'awk', 'sed', 'cut', 'sort', 'uniq', 'head', 'tail', 'cat',
                    'echo', 'printf', 'read', 'trap', 'set', 'shopt', 'alias', 'unalias']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), keywordFormat) for keyword in keywords])

        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["shell_string"]))
        self.highlightingRules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
        self.highlightingRules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), stringFormat))

        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'#[^\n]*'), commentFormat))

        variableFormat = QTextCharFormat()
        variableFormat.setForeground(QColor(SYNTAX_COLORS["variable"]))
        self.highlightingRules.append((re.compile(r'\$[a-zA-Z_][a-zA-Z0-9_]*'), variableFormat))
        self.highlightingRules.append((re.compile(r'\$\{[a-zA-Z_][a-zA-Z0-9_]*\}'), variableFormat))

        commandFormat = QTextCharFormat()
        commandFormat.setForeground(QColor(SYNTAX_COLORS["function"]))
        self.highlightingRules.append((re.compile(r'^\s*\b[a-zA-Z_][a-zA-Z0-9_]*\b'), commandFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# TypeScriptHighlighter provides syntax highlighting for TypeScript code.
class TypeScriptHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        js_highlighter = JavaScriptHighlighter(document)
        self.highlightingRules.extend(js_highlighter.highlightingRules)

        tsKeywordFormat = QTextCharFormat()
        tsKeywordFormat.setForeground(QColor(SYNTAX_COLORS["typescript_keyword"]))
        ts_keywords = ['public', 'private', 'protected', 'interface', 'enum', 'abstract',
                       'implements', 'extends', 'static', 'readonly', 'declare', 'type',
                       'module', 'namespace', 'as', 'is', 'infer', 'keyof', 'unique',
                       'never', 'any', 'unknown', 'void', 'boolean', 'number', 'string',
                       'symbol', 'bigint']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), tsKeywordFormat) for keyword in ts_keywords])

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# VueHighlighter provides syntax highlighting for Vue.js single-file components.
class VueHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        # HTML part
        html_highlighter = HtmlHighlighter(document)
        self.highlightingRules.extend(html_highlighter.highlightingRules)

        # CSS part
        css_highlighter = CssHighlighter(document)
        self.highlightingRules.extend(css_highlighter.highlightingRules)

        # JavaScript part
        js_highlighter = JavaScriptHighlighter(document)
        self.highlightingRules.extend(js_highlighter.highlightingRules)

        # Vue specific directives and components
        vueKeywordFormat = QTextCharFormat()
        vueKeywordFormat.setForeground(QColor(SYNTAX_COLORS["vue_keyword"]))
        vue_keywords = ['v-bind', 'v-on', 'v-model', 'v-if', 'v-else', 'v-else-if',
                        'v-for', 'v-show', 'v-text', 'v-html', 'v-pre', 'v-cloak',
                        'v-once', 'slot', 'template', 'script', 'style', 'data',
                        'methods', 'computed', 'watch', 'props', 'components',
                        'mounted', 'created', 'updated', 'destroyed', 'beforeCreate',
                        'beforeMount', 'beforeUpdate', 'beforeDestroy']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), vueKeywordFormat) for keyword in vue_keywords])

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# DartHighlighter provides syntax highlighting for Dart code.
class DartHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["dart_keyword"]))
        keywords = ['abstract', 'as', 'assert', 'async', 'await', 'break', 'case', 'catch',
                    'class', 'const', 'continue', 'covariant', 'default', 'deferred', 'do',
                    'dynamic', 'else', 'enum', 'export', 'extends', 'extension', 'external',
                    'factory', 'false', 'final', 'finally', 'for', 'Function', 'get', 'hide',
                    'if', 'implements', 'import', 'in', 'interface', 'is', 'late', 'library',
                    'mixin', 'new', 'null', 'on', 'operator', 'part', 'required', 'rethrow',
                    'return', 'set', 'show', 'static', 'super', 'switch', 'sync', 'this',
                    'throw', 'true', 'try', 'typedef', 'var', 'void', 'while', 'with', 'yield',
                    'int', 'double', 'String', 'bool', 'List', 'Map', 'Set', 'print']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), keywordFormat) for keyword in keywords])
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
        self.highlightingRules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), stringFormat))
        self.highlightingRules.append((re.compile(r'"""[\s\S]*?"""'), stringFormat))
        self.highlightingRules.append((re.compile(r"'''[\s\S]*?'''"), stringFormat))
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'//[^\n]*'), commentFormat))
        self.highlightingRules.append((re.compile(r'/\*.*?\*/', re.DOTALL), commentFormat))
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(SYNTAX_COLORS["integer"]))
        self.highlightingRules.append((re.compile(r'\b[0-9]+(?:\.[0-9]+)?\b'), numberFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# RHighlighter provides syntax highlighting for R code.
class RHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(SYNTAX_COLORS["r_keyword"]))
        keywords = ['if', 'else', 'repeat', 'while', 'for', 'in', 'next', 'break',
                    'function', 'return', 'switch', 'try', 'tryCatch', 'stop', 'warning',
                    'message', 'library', 'require', 'attach', 'detach', 'source',
                    'data', 'read.csv', 'read.table', 'write.csv', 'write.table',
                    'plot', 'hist', 'boxplot', 'mean', 'median', 'sum', 'min', 'max',
                    'sd', 'var', 'lm', 'glm', 'summary', 'print', 'cat', 'paste',
                    'c', 'list', 'data.frame', 'matrix', 'array', 'factor', 'TRUE',
                    'FALSE', 'NA', 'NULL', 'Inf', 'NaN']
        self.highlightingRules.extend([(re.compile(r'\b' + keyword + r'\b'), keywordFormat) for keyword in keywords])
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(SYNTAX_COLORS["strings"]))
        self.highlightingRules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), stringFormat))
        self.highlightingRules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), stringFormat))
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(SYNTAX_COLORS["comments"]))
        self.highlightingRules.append((re.compile(r'#[^\n]*'), commentFormat))
        numberFormat = QTextCharFormat()
        numberFormat.setForeground(QColor(SYNTAX_COLORS["integer"]))
        self.highlightingRules.append((re.compile(r'\b[0-9]+(?:\.[0-9]+)?\b'), numberFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = expression.search(text)
            while index:
                self.setFormat(index.start(), index.end() - index.start(), format)
                index = expression.search(text, index.end())

# Worker class for running external processes in a separate thread.
# This prevents the UI from freezing during long-running operations.
class Worker(QThread):
    finished = pyqtSignal(str, str)

    def __init__(self, command, tool_name):
        super().__init__()
        self.command = command
        self.tool_name = tool_name

    def run(self):
        try:
            process = QProcess()
            process.start(self.command)
            process.waitForFinished()
            output = process.readAllStandardOutput().data().decode().strip()
            error_output = process.readAllStandardError().data().decode().strip()
            result = output if output else error_output
            self.finished.emit(self.tool_name, result)
        except Exception as e:
            self.finished.emit(self.tool_name, f"Error running {self.tool_name}: {e}")

# CodeEditor is the main text editing widget with syntax highlighting and auto-completion.
class CodeEditor(QTextEdit):
    def __init__(self, parent=None, ide_instance=None):
        super().__init__(parent)
        self.ide_instance = ide_instance # Reference to the IDE instance
        self.setFont(QFont("Inter", 10))
        self.setTabStopWidth(QFontMetrics(self.font()).width(' ' * 4))
        self.setAcceptDrops(True)
        self.highlighter = None
        self.language_detected = False
        self.auto_close_enabled = True # Default, will be updated by IDE
        self.completer_enabled = True # Default, will be updated by IDE
        self.setWordWrapMode(QTextOption.NoWrap) # Disable word wrap for horizontal scrollbar

        # Setup auto-completion
        self.completer = QCompleter(self)
        self.completer.setModel(QStringListModel())
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.insertCompletion)
        self.completer.popup().setWindowOpacity(0.9) # Set opacity for completer popup

        # Connect signals for dynamic behavior
        self.document().contentsChange.connect(self.update_completer_words)
        self.document().contentsChange.connect(self._auto_detect_language_on_type)
        self.document().contentsChanged.connect(self._handle_document_modified)
        self.update_completer_words()

    # Sets the appropriate syntax highlighter based on the file extension.
    def set_highlighter(self, file_extension):
        if self.highlighter:
            self.highlighter.setDocument(None)

        # Map file extensions to their respective highlighter classes
        if file_extension == '.py':
            self.highlighter = PythonHighlighter(self.document())
        elif file_extension == '.html':
            self.highlighter = HtmlHighlighter(self.document())
        elif file_extension == '.css':
            self.highlighter = CssHighlighter(self.document())
        elif file_extension == '.js':
            self.highlighter = JavaScriptHighlighter(self.document())
        elif file_extension == '.java':
            self.highlighter = JavaHighlighter(self.document())
        elif file_extension in ['.cpp', '.cxx', '.cc', '.h', '.hpp']:
            self.highlighter = CppHighlighter(self.document())
        elif file_extension == '.cs':
            self.highlighter = CSharpHighlighter(self.document())
        elif file_extension == '.scss':
            self.highlighter = ScssHighlighter(self.document())
        elif file_extension in ['.sql']:
            self.highlighter = SqlHighlighter(self.document())
        elif file_extension == '.swift':
            self.highlighter = SwiftHighlighter(self.document())
        elif file_extension == '.rb':
            self.highlighter = RubyHighlighter(self.document())
        elif file_extension == '.go':
            self.highlighter = GoHighlighter(self.document())
        elif file_extension == '.rs':
            self.highlighter = RustHighlighter(self.document())
        elif file_extension == '.php':
            self.highlighter = PhpHighlighter(self.document())
        elif file_extension == '.pl':
            self.highlighter = PerlHighlighter(self.document())
        elif file_extension == '.kt':
            self.highlighter = KotlinHighlighter(self.document())
        elif file_extension in ['.jsx', '.tsx']: # Use file_extension here
            self.highlighter = ReactNativeHighlighter(self.document())
        elif file_extension in ['.xml', '.xsd', '.xsl', '.svg']: # Use file_extension here
            self.highlighter = XmlHighlighter(self.document())
        elif file_extension == '.json':
            self.highlighter = JsonHighlighter(self.document())
        elif file_extension == '.md':
            self.highlighter = MarkdownHighlighter(self.document())
        elif file_extension in ['.sh', '.bash']: # Use file_extension here
            self.highlighter = ShellHighlighter(self.document())
        elif file_extension in ['.ts', '.tsx']: # Use file_extension here
            self.highlighter = TypeScriptHighlighter(self.document())
        elif file_extension in ['.vue']: # Use file_extension here
            self.highlighter = VueHighlighter(self.document())
        elif file_extension == '.dart':
            self.highlighter = DartHighlighter(self.document())
        elif file_extension == '.r':
            self.highlighter = RHighlighter(self.document())
        else:
            self.highlighter = None # No highlighter for unknown file types
        
        if self.highlighter:
            self.highlighter.rehighlight()
            self.language_detected = True # Mark language as detected

    # Attempts to auto-detect the language based on the initial text content.
    # This is useful for new, unsaved files.
    def _auto_detect_language_on_type(self):
        if not self.ide_instance:
            return

        file_path = self.ide_instance.tab_paths.get(self) # Get path using widget as key

        # Only auto-detect if the file is new/untitled and language hasn't been detected yet.
        if file_path is not None or self.language_detected:
            return

        text = self.toPlainText().strip().lower()
        detected_ext = None

        # Heuristic rules for language detection
        if text.startswith('<!doctype html>') or text.startswith('<html'):
            detected_ext = '.html'
        elif text.startswith('import ') or text.startswith('package '):
            if re.search(r'\bclass\b|\bpublic static void main\b', text):
                detected_ext = '.java'
            elif re.search(r'\bfun\b|\bval\b|\bvar\b', text):
                detected_ext = '.kt'
            elif re.search(r'\bpackage main\b|\bfunc main\b', text):
                detected_ext = '.go'
            elif re.search(r'\bimport\s+react\b|\bimport\s+\{.*\}\s+from\s+\'react\'', text):
                detected_ext = '.jsx'
            elif re.search(r'\bimport\s+\{.*\}\s+from\s+\'vue\'', text) or re.search(r'<template>|<script>|<style>', self.toPlainText().strip()):
                detected_ext = '.vue'
            elif re.search(r'\bimport\s+\'dart:io\'', text) or re.search(r'\bvoid\s+main\s*\(', text):
                detected_ext = '.dart'
        elif text.startswith('#include') or re.search(r'\b(int|void|char|double|float)\s+main\s*\(', text):
            detected_ext = '.cpp'
        elif text.startswith('using system;') or re.search(r'\bclass\b.*?\bpublic static void main\b', text):
            detected_ext = '.cs'
        elif text.startswith('<?php'):
            detected_ext = '.php'
        elif text.startswith('require ') or text.startswith('use '):
            if re.search(r'\bmy\b|\buse strict\b', text):
                detected_ext = '.pl'
            elif re.search(r'\bdef\b|\bend\b|\bclass\b', text):
                detected_ext = '.rb'
        elif text.startswith('fn ') or text.startswith('mod '):
            detected_ext = '.rs'
        elif text.startswith('@import') or re.search(r'\$[a-zA-Z0-9_-]+', text):
            detected_ext = '.scss'
        elif re.search(r'\b(select|insert|update|delete)\b', text):
            detected_ext = '.sql'
        elif re.search(r'\bfunc\b|\bvar\b|\blet\b', text) and not text.startswith('import '):
            detected_ext = '.swift'
        elif text.startswith('//') or text.startswith('/*'):
            pass # Comments alone are not enough for detection
        elif text.strip().startswith('{') or text.strip().startswith('.'):
            detected_ext = '.css'
        elif re.search(r'\bfunction\b|\bconst\b|\blet\b|\bvar\b', text):
            detected_ext = '.js'
        elif re.search(r'\b(def|class|import)\b', text):
            detected_ext = '.py'
        elif text.startswith('<') and '>' in text:
            detected_ext = '.xml'
        elif text.startswith('{') and '}' in text and ':' in text:
            detected_ext = '.json'
        elif text.startswith('# ') or text.startswith('## ') or text.startswith('- ') or text.startswith('* '):
            detected_ext = '.md'
        elif text.startswith('#!') or text.startswith('echo ') or text.startswith('ls '):
            detected_ext = '.sh'
        elif re.search(r'\b(function|var|let|const)\b', text) and re.search(r'\b(interface|enum|type)\b', text):
            detected_ext = '.ts'
        elif re.search(r'\b(library|require|attach|detach)\b', text) or re.search(r'<-', text):
            detected_ext = '.r'

        # Apply highlighter if a language is detected
        if detected_ext:
            self.set_highlighter(detected_ext)
            # Find the tab widget and index for this editor
            tab_widget = None
            tab_index = -1
            for i in range(self.ide_instance.left_tab_widget.count()):
                if self.ide_instance.left_tab_widget.widget(i) == self:
                    tab_widget = self.ide_instance.left_tab_widget
                    tab_index = i
                    break
            if not tab_widget and not self.ide_instance.right_tab_widget.isHidden():
                for i in range(self.ide_instance.right_tab_widget.count()):
                    if self.ide_instance.right_tab_widget.widget(i) == self:
                        tab_widget = self.ide_instance.right_tab_widget
                        tab_index = i
                        break

            if tab_widget and tab_index != -1 and tab_widget.tabText(tab_index) == "Untitled":
                tab_widget.setTabText(tab_index, f"Untitled ({detected_ext[1:].upper()})")
            self.ide_instance.statusBar().showMessage(f"Language auto-detected as {detected_ext[1:].upper()}", 1500)
            # Disconnect to prevent re-detection on every keystroke after initial detection
            self.document().contentsChange.disconnect(self._auto_detect_language_on_type)

    # Handles document modification to update tab text (e.g., add '*' for unsaved changes).
    def _handle_document_modified(self):
        if not self.ide_instance:
            return

        # Find the tab widget and index for this editor
        tab_widget = None
        tab_index = -1
        for i in range(self.ide_instance.left_tab_widget.count()):
            if self.ide_instance.left_tab_widget.widget(i) == self:
                tab_widget = self.ide_instance.left_tab_widget
                tab_index = i
                break
        if not tab_widget and not self.ide_instance.right_tab_widget.isHidden():
            for i in range(self.ide_instance.right_tab_widget.count()):
                    if self.ide_instance.right_tab_widget.widget(i) == self:
                        tab_widget = self.ide_instance.right_tab_widget
                        tab_index = i
                        break

        if tab_widget and tab_index != -1:
            current_tab_text = tab_widget.tabText(tab_index)
            if self.document().isModified():
                if not current_tab_text.startswith('*'):
                    tab_widget.setTabText(tab_index, '*' + current_tab_text)
            else:
                if current_tab_text.startswith('*'):
                    tab_widget.setTabText(tab_index, current_tab_text[1:])

    # Inserts the selected completion into the text editor.
    def insertCompletion(self, completion):
        if self.completer.widget() != self:
            return
        
        tc = self.textCursor()
        # Get the current word prefix
        tc.select(QTextCursor.WordUnderCursor)
        prefix = tc.selectedText()

        # If the completion starts with the prefix, replace the prefix with the completion
        if completion.startswith(prefix):
            tc.insertText(completion[len(prefix):]) # Insert only the remaining part of the completion
        else:
            # If the completion doesn't start with the prefix, replace the whole word
            tc.insertText(completion)
        
        self.setTextCursor(tc)

    # Returns the word currently under the text cursor.
    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText()

    # Updates the word list for the completer based on the current document content.
    def update_completer_words(self):
        if not self.completer_enabled:
            return

        text = self.toPlainText()
        cursor = self.textCursor()
        cursor_line = cursor.blockNumber() + 1
        cursor_column = cursor.positionInBlock()
        
        if _HAS_JEDI:
            try:
                file_path = self.ide_instance.tab_paths.get(self)
                # jedi.Script expects source and path for constructor. line and column for complete().
                script = jedi.Script(text, path=file_path)
                completions = script.complete(line=cursor_line, column=cursor_column)
                words = sorted(list(set([c.name for c in completions])))
            except Exception as e:
                # Fallback to simple word completion if jedi fails
                print(f"Jedi completion failed: {e}. Falling back to simple word completion.")
                words = sorted(list(set(re.findall(r'\b\w+\b', text))))
        else:
            # Simple word completion
            words = sorted(list(set(re.findall(r'\b\w+\b', text))))
        
        self.completer.model().setStringList(words)

    # Applies the selected theme's stylesheet to the CodeEditor.
    def apply_theme(self, theme_name):
        theme = THEMES[theme_name]
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme["bg_color"]};
                color: {theme["text_color"]};
                selection-background-color: {theme["selection_bg"]};
                border: 1px solid {theme["border_color"]};
                border-radius: 5px;
            }}
            QScrollBar:vertical {{
                border: none;
                background: {theme["scrollbar_bg"]};
                width: 8px; /* Thinner vertical scrollbar */
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {theme["scrollbar_handle"]};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {theme["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                width: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QScrollBar:horizontal {{
                border: none;
                background: {theme["scrollbar_bg"]};
                height: 8px; /* Thinner horizontal scrollbar */
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {theme["scrollbar_handle"]};
                min-width: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {theme["scrollbar_handle_hover"]};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
                height: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
            QCompleter {{
                background-color: {theme["completer_bg"]};
                color: {theme["completer_text"]};
                selection-background-color: {theme["completer_selection_bg"]};
                border: 1px solid {theme["border_color"]};
                border-radius: 5px;
            }}
            QCompleter::item:selected {{
                background-color: {theme["completer_selection_bg"]};
                color: {theme["completer_text"]};
            }}
        """)

    # Handles drag enter events for file dropping.
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    # Handles drop events for files dropped onto the editor.
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            main_window = self.ide_instance # Use the stored IDE instance
            if not isinstance(main_window, IDE):
                super().dropEvent(event)
                return

            # Determine which tab widget the drop occurred on
            target_tab_widget = None
            if main_window.left_tab_widget.geometry().contains(self.mapToGlobal(event.pos())):
                target_tab_widget = main_window.left_tab_widget
            elif not main_window.right_tab_widget.isHidden() and \
                 main_window.right_tab_widget.geometry().contains(self.mapToGlobal(event.pos())):
                target_tab_widget = main_window.right_tab_widget
            
            if not target_tab_widget:
                super().dropEvent(event)
                return

            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    if event.modifiers() & Qt.ShiftModifier:
                        # If Shift is pressed, insert directory path
                        self.insertPlainText(os.path.dirname(file_path))
                        main_window.statusBar().showMessage(f"Inserted directory: {os.path.dirname(file_path)}", 2000)
                    else:
                        # Otherwise, open the file in the appropriate tab widget
                        main_window.open_file(file_path, target_tab_widget=target_tab_widget)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    # Overrides key press events for auto-closing brackets/quotes and completer interaction.
    def keyPressEvent(self, event):
        # If completer is visible, handle specific keys to prevent default behavior
        if self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore()
                return

        # Auto-closing functionality
        if self.auto_close_enabled:
            cursor = self.textCursor()
            if event.text() == '(':
                cursor.insertText('()')
                cursor.movePosition(QTextCursor.PreviousCharacter)
                self.setTextCursor(cursor)
                event.accept()
                return
            elif event.text() == '[':
                cursor.insertText('[]')
                cursor.movePosition(QTextCursor.PreviousCharacter)
                self.setTextCursor(cursor)
                event.accept()
                return
            elif event.text() == '{':
                cursor.insertText('{}')
                cursor.movePosition(QTextCursor.PreviousCharacter)
                self.setTextCursor(cursor)
                event.accept()
                return
            elif event.text() == "'":
                cursor.insertText("''")
                cursor.movePosition(QTextCursor.PreviousCharacter)
                self.setTextCursor(cursor)
                event.accept()
                return
            elif event.text() == '"':
                cursor.insertText('""')
                cursor.movePosition(QTextCursor.PreviousCharacter)
                self.setTextCursor(cursor)
                event.accept()
                return
            elif event.key() == Qt.Key_Backspace and not cursor.hasSelection():
                # If backspace is pressed and there's an auto-closed pair, delete both
                pos = cursor.position()
                if pos > 0:
                    char_before = self.toPlainText()[pos-1]
                    char_after = self.toPlainText()[pos] if pos < len(self.toPlainText()) else ''
                    pairs = {'(': ')', '[': ']', '{': '}', "'": "'", '"': '"'}
                    if char_before in pairs and pairs[char_before] == char_after:
                        cursor.deleteChar() # Delete the character after the cursor
                        super().keyPressEvent(event) # Then delete the character before the cursor
                        event.accept()
                        return
        
        super().keyPressEvent(event) # Call base class method for normal key handling

        # Show completer popup if there are completions and it's not already visible
        if self.completer_enabled:
            prefix = self.textUnderCursor()
            if len(prefix) >= 1:
                self.completer.setCompletionPrefix(prefix)
                cr = self.cursorRect()
                cr.setWidth(self.completer.popup().sizeHint().width())
                self.completer.complete(cr)
            else:
                self.completer.popup().hide() # Hide if prefix is too short

    # Handles wheel events for zooming text with Ctrl + scroll.
    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            font = self.font()
            if event.angleDelta().y() > 0:
                font.setPointSize(font.pointSize() + 1)
            else:
                new_size = font.pointSize() - 1
                if new_size > 0: # Ensure font size doesn't go below 1
                    font.setPointSize(new_size)
            self.setFont(font)
            self.setTabStopWidth(QFontMetrics(self.font()).width(' ' * 4))
            event.accept()
        else:
            super().wheelEvent(event)

# MediaViewer widget for displaying images and playing videos.
class MediaViewer(QWidget):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignCenter)

        self.media_widget = None
        self.player = None

        self._load_media()

    # Loads and displays media (image or video) based on file type.
    def _load_media(self):
        file_ext = os.path.splitext(self.file_path)[1].lower()

        if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']:
            self.media_widget = QLabel(self)
            image = QImage(self.file_path)
            if image.isNull():
                self.media_widget.setText(f"Could not load image: {os.path.basename(self.file_path)}")
                self.media_widget.setAlignment(Qt.AlignCenter)
            else:
                pixmap = QPixmap.fromImage(image)
                # Scale pixmap to fit the label while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.media_widget.setPixmap(scaled_pixmap)
                self.media_widget.setScaledContents(False) # Set to False as we're handling scaling manually
                self.media_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Allow label to expand
                self.media_widget.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(self.media_widget)
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            if _HAS_MULTIMEDIA: # Check if multimedia modules are available
                self.player = QMediaPlayer(self)
                self.video_widget = QVideoWidget(self)
                self.player.setVideoOutput(self.video_widget)
                self.layout.addWidget(self.video_widget)

                # Add video playback controls
                controls_layout = QHBoxLayout()
                self.play_button = QPushButton("Play")
                self.play_button.clicked.connect(self.player.play)
                self.pause_button = QPushButton("Pause")
                self.pause_button.clicked.connect(self.player.pause)
                self.stop_button = QPushButton("Stop")
                self.stop_button.clicked.connect(self.player.stop)

                controls_layout.addWidget(self.play_button)
                controls_layout.addWidget(self.pause_button)
                controls_layout.addWidget(self.stop_button)
                self.layout.addLayout(controls_layout)

                self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.file_path)))
                self.player.play()
            else:
                self.media_widget = QLabel(self)
                self.media_widget.setText(f"Multimedia modules not found. Cannot play video: {os.path.basename(self.file_path)}")
                self.media_widget.setAlignment(Qt.AlignCenter)
                self.layout.addWidget(self.media_widget)
        else:
            self.media_widget = QLabel(self)
            self.media_widget.setText(f"Unsupported file type: {os.path.basename(self.file_path)}")
            self.media_widget.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(self.media_widget)

    def resizeEvent(self, event):
        # Re-scale image when the viewer is resized
        if isinstance(self.media_widget, QLabel) and self.media_widget.pixmap():
            # Only reload and scale if the pixmap is not null and the image was loaded successfully
            original_image = QImage(self.file_path)
            if not original_image.isNull():
                pixmap = QPixmap.fromImage(original_image)
                scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.media_widget.setPixmap(scaled_pixmap)
        super().resizeEvent(event)

# FindDialog provides a dialog for finding text within the active editor.
class FindDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Find")
        self.setMinimumWidth(300)
        self.layout = QVBoxLayout(self)

        self.find_label = QLabel("Find what:")
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Enter text to find...")
        self.layout.addWidget(self.find_label)
        self.layout.addWidget(self.find_input)

        self.case_sensitive_checkbox = QCheckBox("Case sensitive")
        self.layout.addWidget(self.case_sensitive_checkbox)

        self.whole_word_checkbox = QCheckBox("Whole words only")
        self.layout.addWidget(self.whole_word_checkbox)

        self.find_next_button = QPushButton("Find Next")
        self.find_next_button.clicked.connect(self._find_next)
        self.layout.addWidget(self.find_next_button)

        self.find_prev_button = QPushButton("Find Previous")
        self.find_prev_button.clicked.connect(self._find_prev)
        self.layout.addWidget(self.find_prev_button)

        self.editor = None # Reference to the editor to perform find operations on

    def set_editor(self, editor):
        self.editor = editor

    # Determines the find flags based on checkbox states.
    def _get_find_flags(self):
        flags = QTextDocument.FindFlags()
        if self.case_sensitive_checkbox.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.whole_word_checkbox.isChecked():
            flags |= QTextDocument.FindWholeWords
        return flags

    # Finds the next occurrence of the text.
    def _find_next(self):
        if self.editor:
            text_to_find = self.find_input.text()
            if text_to_find:
                # Ensure cursor is at the beginning of the selection for 'find next'
                cursor = self.editor.textCursor()
                if cursor.hasSelection():
                    cursor.setPosition(cursor.selectionEnd())
                    self.editor.setTextCursor(cursor)

                found = self.editor.find(text_to_find, self._get_find_flags())
                if not found:
                    QMessageBox.information(self, "Find", f"'{text_to_find}' not found.")
            else:
                QMessageBox.warning(self, "Find", "Please enter text to find.")

    # Finds the previous occurrence of the text.
    def _find_prev(self):
        if self.editor:
            text_to_find = self.find_input.text()
            if text_to_find:
                # Ensure cursor is at the end of the selection for 'find previous'
                cursor = self.editor.textCursor()
                if cursor.hasSelection():
                    cursor.setPosition(cursor.selectionStart())
                    self.editor.setTextCursor(cursor)

                flags = self._get_find_flags() | QTextDocument.FindBackward
                found = self.editor.find(text_to_find, flags)
                if not found:
                    QMessageBox.information(self, "Find", f"'{text_to_find}' not found.")
            else:
                QMessageBox.warning(self, "Find", "Please enter text to find.")

# SyntaxPaletteDialog allows users to customize syntax highlighting colors.
class SyntaxPaletteDialog(QDialog):
    color_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Syntax Color Palette")
        self.layout = QVBoxLayout(self)
        self.color_buttons = {}

        self._create_color_pickers()

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self._apply_colors)
        self.layout.addWidget(self.apply_button)

    # Creates color picker buttons for each syntax element.
    def _create_color_pickers(self):
        grid_layout = QGridLayout()
        row, col = 0, 0
        max_cols = 2 # Display color pickers in two columns

        for key, color_hex in SYNTAX_COLORS.items():
            h_layout = QHBoxLayout()
            label = QLabel(key.replace('_', ' ').title() + ":")
            color_button = QPushButton()
            color_button.setFixedSize(24, 24)
            color_button.setStyleSheet(f"background-color: {color_hex}; border: 1px solid gray; border-radius: 4px;")
            color_button.clicked.connect(lambda checked, k=key: self._pick_color(k))
            self.color_buttons[key] = color_button
            h_layout.addWidget(label)
            h_layout.addStretch()
            h_layout.addWidget(color_button)
            
            grid_layout.addLayout(h_layout, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        self.layout.addLayout(grid_layout)

    # Opens a color dialog to pick a new color for a syntax element.
    def _pick_color(self, key):
        current_color = QColor(SYNTAX_COLORS[key])
        color = QColorDialog.getColor(current_color, self, "Select Color")
        if color.isValid():
            SYNTAX_COLORS[key] = color.name() # Update the global SYNTAX_COLORS dictionary
            self.color_buttons[key].setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray; border-radius: 4px;")

    # Emits a signal to reapply colors after changes are made.
    def _apply_colors(self):
        self.color_changed.emit()
        self.accept()

# QuickSwitcherDialog allows fast navigation between open tabs.
class QuickSwitcherDialog(QDialog):
    def __init__(self, ide_instance, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Open")
        self.setMinimumSize(400, 300)
        self.ide = ide_instance
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to filter files...")
        self.search_input.textChanged.connect(self._filter_list)
        self.layout.addWidget(self.search_input)

        self.tab_list_view = QListView()
        self.list_model = QStringListModel()
        self.tab_list_view.setModel(self.list_model)
        self.tab_list_view.clicked.connect(self._item_clicked)
        self.tab_list_view.doubleClicked.connect(self._item_double_clicked)
        self.layout.addWidget(self.tab_list_view)

        self._populate_list()
        self.search_input.setFocus()

        # Keyboard navigation for the list
        self.tab_list_view.keyPressEvent = self._handle_list_key_press

    def _populate_list(self):
        self.all_tabs_data = [] # Stores (display_name, file_path, tab_widget_instance, tab_index, widget_instance)
        
        # Collect tabs from left panel
        for i in range(self.ide.left_tab_widget.count()):
            widget = self.ide.left_tab_widget.widget(i)
            file_path = self.ide.tab_paths.get(widget)
            tab_text = self.ide.left_tab_widget.tabText(i)
            display_name = tab_text
            if file_path:
                display_name = f"{os.path.basename(file_path)} - {os.path.dirname(file_path)}"
            self.all_tabs_data.append((display_name, file_path, self.ide.left_tab_widget, i, widget))

        # Collect tabs from right panel (if visible)
        if not self.ide.right_tab_widget.isHidden():
            for i in range(self.ide.right_tab_widget.count()):
                widget = self.ide.right_tab_widget.widget(i)
                file_path = self.ide.tab_paths.get(widget)
                tab_text = self.ide.right_tab_widget.tabText(i)
                display_name = tab_text
                if file_path:
                    display_name = f"{os.path.basename(file_path)} - {os.path.dirname(file_path)} (Right Panel)"
                self.all_tabs_data.append((display_name, file_path, self.ide.right_tab_widget, i, widget))
        
        self.current_filtered_data = list(self.all_tabs_data)
        self.list_model.setStringList([data[0] for data in self.current_filtered_data])
        if self.current_filtered_data:
            self.tab_list_view.setCurrentIndex(self.list_model.index(0))

    def _filter_list(self, text):
        self.current_filtered_data = [
            data for data in self.all_tabs_data if text.lower() in data[0].lower()
        ]
        self.list_model.setStringList([data[0] for data in self.current_filtered_data])
        if self.current_filtered_data:
            self.tab_list_view.setCurrentIndex(self.list_model.index(0))
        else:
            self.tab_list_view.clearSelection()

    def _item_clicked(self, index):
        # Allow single click to highlight, double click to open
        pass

    def _item_double_clicked(self, index):
        self._activate_selected_tab()

    def _handle_list_key_press(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self._activate_selected_tab()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key_Up:
            self.tab_list_view.setCurrentIndex(self.tab_list_view.model().index(max(0, self.tab_list_view.currentIndex().row() - 1)))
        elif event.key() == Qt.Key_Down:
            self.tab_list_view.setCurrentIndex(self.tab_list_view.model().index(min(self.tab_list_view.model().rowCount() - 1, self.tab_list_view.currentIndex().row() + 1)))
        else:
            super(QListView, self.tab_list_view).keyPressEvent(event) # Pass other keys to default handling

    def _activate_selected_tab(self):
        selected_index = self.tab_list_view.currentIndex()
        if selected_index.isValid():
            row = selected_index.row()
            if 0 <= row < len(self.current_filtered_data):
                _, _, tab_widget_instance, tab_index, widget_instance = self.current_filtered_data[row]
                tab_widget_instance.setCurrentIndex(tab_index)
                # Ensure the IDE's active editor is updated
                self.ide._set_active_tab_widget(tab_widget_instance.currentIndex(), tab_widget_instance) 
                self.accept()

# The main IDE window, containing all components and logic.
class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KodyKoala")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowOpacity(1.0) # Ensure window is fully opaque

        self.current_theme = "dark"
        self.current_directory = os.getcwd()
        self.auto_save_enabled = False
        self.auto_save_on_python_format = False # New setting for auto-format on save
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._perform_auto_save)
        self.auto_save_interval = 5 * 60 * 1000 # Auto-save every 5 minutes
        self.auto_close_enabled = True
        self.completer_enabled = True
        self.current_font = QFont("Inter", 10)

        self._load_config() # Load settings on startup

        self.find_dialog = FindDialog(self)

        self._create_actions()
        
        self.toggle_split_view_action = QAction("Toggle Split View", self)
        self.toggle_split_view_action.setCheckable(True)
        self.toggle_split_view_action.setChecked(False)
        self.toggle_split_view_action.setShortcut("Ctrl+Shift+E")
        self.toggle_split_view_action.triggered.connect(self._toggle_split_view)

        self._init_ui()
        self.apply_theme(self.current_theme) # Apply loaded theme
        self._update_edit_actions_state()

        self.zen_mode_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.zen_mode_shortcut.activated.connect(self._toggle_zen_mode)
        self.in_zen_mode = False

        # Apply loaded font to initial editor and terminals
        if self.current_editor:
            self.current_editor.setFont(self.current_font)
            self.current_editor.setTabStopWidth(QFontMetrics(self.current_font).width(' ' * 4))
        self.left_terminal.setFont(self.current_font)
        self.right_terminal.setFont(self.current_font) # Apply to right terminal as well

        # Quick Switcher Shortcut
        self.quick_switcher_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        self.quick_switcher_shortcut.activated.connect(self._show_quick_switcher)

        # Restore session on startup
        self._restore_session()

    # Saves current configuration (theme, font, auto-save, etc.) to a JSON file.
    def _save_config(self):
        config = {
            "theme": self.current_theme,
            "font_family": self.current_font.family(),
            "font_size": self.current_font.pointSize(),
            "auto_save_enabled": self.auto_save_enabled,
            "auto_close_enabled": self.auto_close_enabled,
            "completer_enabled": self.completer_enabled,
            "auto_save_on_python_format": self.auto_save_on_python_format, # Save new setting
            "syntax_colors": SYNTAX_COLORS # Save current syntax colors
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving configuration: {e}")

    # Loads configuration from a JSON file.
    def _load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.current_theme = config.get("theme", "dark")
                self.current_font = QFont(config.get("font_family", "Inter"), config.get("font_size", 10))
                self.auto_save_enabled = config.get("auto_save_enabled", False)
                self.auto_close_enabled = config.get("auto_close_enabled", True)
                self.completer_enabled = config.get("completer_enabled", True)
                self.auto_save_on_python_format = config.get("auto_save_on_python_format", False) # Load new setting
                # Load syntax colors, merging with defaults to handle new keys
                loaded_syntax_colors = config.get("syntax_colors", {})
                for key, value in loaded_syntax_colors.items():
                    if key in SYNTAX_COLORS: # Only update existing keys
                        SYNTAX_COLORS[key] = value
        except Exception as e:
            print(f"Error loading configuration: {e}")
            # Reset to default if loading fails
            self.current_theme = "dark"
            self.current_font = QFont("Inter", 10)
            self.auto_save_enabled = False
            self.auto_close_enabled = True
            self.completer_enabled = True
            self.auto_save_on_python_format = False
            # SYNTAX_COLORS remains default if not loaded successfully

    # Saves the current session state (open files and their content) for crash recovery.
    def _save_session(self):
        session_data = []
        for tab_widget in [self.left_tab_widget, self.right_tab_widget]:
            for i in range(tab_widget.count()):
                widget = tab_widget.widget(i)
                file_path = self.tab_paths.get(widget)
                if isinstance(widget, CodeEditor):
                    session_data.append({
                        "path": file_path,
                        "content": widget.toPlainText(), # Always save content
                        "is_modified": widget.document().isModified(),
                        "panel": "left" if tab_widget == self.left_tab_widget else "right",
                        "tab_index": i # Store tab index to try and restore order
                    })
        try:
            with open(SESSION_FILE, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=4)
        except Exception as e:
            print(f"Error saving session: {e}")

    # Restores the previous session from the session file.
    def _restore_session(self):
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                if not session_data:
                    return # No session data to restore

                reply = QMessageBox.question(self, "Restore Session",
                                             "A previous session was found. Do you want to restore unsaved work?",
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    # Clear initial untitled tab
                    if self.left_tab_widget.count() == 1 and self.tab_paths.get(self.left_tab_widget.widget(0)) is None:
                        self.left_tab_widget.removeTab(0)
                        if self.left_tab_widget.widget(0) in self.tab_paths: # Check before deleting
                            del self.tab_paths[self.left_tab_widget.widget(0)] # Remove from tracking

                    # Sort session data to restore tabs in order
                    session_data.sort(key=lambda x: (x.get("panel", "left"), x.get("tab_index", 0)))

                    for item in session_data:
                        file_path = item.get("path")
                        content = item.get("content")
                        is_modified = item.get("is_modified", False)
                        panel = item.get("panel", "left")

                        target_tab_widget = self.left_tab_widget if panel == "left" else self.right_tab_widget
                        
                        if panel == "right" and self.right_tab_widget.isHidden():
                            self._toggle_split_view() # Ensure right panel is visible

                        editor = CodeEditor(self, self)
                        editor.setText(content if content is not None else "")
                        editor.document().setModified(is_modified)
                        editor.auto_close_enabled = self.auto_close_enabled
                        editor.completer.setCompletionMode(QCompleter.PopupCompletion if self.completer_enabled else QCompleter.Disabled)
                        editor.setFont(self.current_font)
                        editor.setTabStopWidth(QFontMetrics(self.current_font).width(' ' * 4))

                        tab_name = "Untitled"
                        if file_path:
                            tab_name = os.path.basename(file_path)
                            editor.set_highlighter(os.path.splitext(file_path)[1].lower())
                        else:
                            # Try to auto-detect language for restored untitled files
                            editor.language_detected = False # Allow auto-detection
                            editor._auto_detect_language_on_type() # Trigger auto-detection

                        if is_modified:
                            tab_name = '*' + tab_name
                        
                        tab_index = target_tab_widget.addTab(editor, tab_name)
                        target_tab_widget.setCurrentIndex(tab_index)
                        self.tab_paths[editor] = file_path # Store path (or None for untitled)

                        self.statusBar().showMessage(f"Restored: {tab_name}", 2000)
                    
                    # Ensure at least one tab is active
                    if self.left_tab_widget.count() > 0:
                        self.left_tab_widget.setCurrentIndex(0)
                        self._set_active_tab_widget(0, self.left_tab_widget)
                    elif not self.right_tab_widget.isHidden() and self.right_tab_widget.count() > 0:
                        self.right_tab_widget.setCurrentIndex(0)
                        self._set_active_tab_widget(0, self.right_tab_widget)
                    else:
                        self._new_file(target_tab_widget=self.left_tab_widget) # Create new if nothing restored
                    
                    self.statusBar().showMessage("Session restored.", 2000)
                
                # Delete the session file after restoration attempt
                os.remove(SESSION_FILE)
            except Exception as e:
                print(f"Error restoring session: {e}")
                QMessageBox.warning(self, "Session Restore Error", f"Could not restore previous session: {e}")
        
        # If no session file or user declined, ensure at least one tab is open
        if self.left_tab_widget.count() == 0 and (self.right_tab_widget.isHidden() or self.right_tab_widget.count() == 0):
            self._new_file(target_tab_widget=self.left_tab_widget)


    # Overrides close event to save configuration and session before exiting.
    def closeEvent(self, event):
        self._save_config()
        self._save_session() # Save session before closing
        super().closeEvent(event)

    # Updates the enabled/disabled state of various edit actions based on the current editor.
    def _update_edit_actions_state(self):
        can_edit = self.current_editor is not None and isinstance(self.current_editor, CodeEditor)
        self.undo_action.setEnabled(can_edit)
        self.redo_action.setEnabled(can_edit)
        self.cut_action.setEnabled(can_edit)
        self.copy_action.setEnabled(can_edit)
        self.paste_action.setEnabled(can_edit)
        self.select_all_action.setEnabled(can_edit)
        self.find_action.setEnabled(can_edit)
        self.save_file_action.setEnabled(can_edit)
        self.save_as_file_action.setEnabled(can_edit)
        self.syntax_palette_action.setEnabled(True) # Always enabled
        self.toggle_auto_closer_action.setEnabled(True) # Always enabled
        self.toggle_completer_action.setEnabled(True) # Always enabled
        self.select_font_action.setEnabled(True) # Always enabled

        # Actions dependent on Python file type
        is_python_file = False
        if can_edit:
            file_path = self.tab_paths.get(self.current_editor)
            if file_path and isinstance(file_path, str) and file_path.lower().endswith('.py'):
                is_python_file = True

        self.run_script_action.setEnabled(is_python_file)
        self.flake8_action.setEnabled(is_python_file)
        self.black_action.setEnabled(is_python_file)
        self.mypy_action.setEnabled(is_python_file)


    # Initializes the main user interface components.
    def _init_ui(self):
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(3)
        self.setCentralWidget(self.main_splitter)

        # Left panel (file tree and directory selector)
        self.left_panel_container = QWidget()
        self.left_panel_layout = QVBoxLayout(self.left_panel_container)
        self.left_panel_layout.setContentsMargins(5, 5, 5, 5)

        self._create_menu_bar()

        self.dir_selector_layout = QHBoxLayout()
        self.dir_label = QLabel("Current Dir:")
        self.dir_path_display = QLineEdit(self.current_directory)
        self.dir_path_display.setReadOnly(True)
        
        # Replace "Change" button with a clickable icon
        self.change_dir_icon_label = QLabel()
        folder_icon_path = "C:/Users/Aiden shoroz/Desktop/folder.png"
        if os.path.exists(folder_icon_path):
            pixmap = QPixmap(folder_icon_path)
            # Scale icon to a larger fixed size (e.g., 48x48 for more prominence)
            scaled_pixmap = pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.change_dir_icon_label.setPixmap(scaled_pixmap)
        else:
            self.change_dir_icon_label.setText("Change Dir") # Fallback text if icon not found
            print(f"Warning: Custom folder icon for 'Change Dir' button not found at {folder_icon_path}. Using text label.")

        self.change_dir_icon_label.setToolTip("Change Directory")
        self.change_dir_icon_label.setFixedSize(48, 48) # Set fixed size for the label
        self.change_dir_icon_label.mousePressEvent = lambda event: self._change_directory() # Make it clickable

        self.dir_selector_layout.addWidget(self.dir_label)
        self.dir_selector_layout.addWidget(self.dir_path_display)
        self.dir_selector_layout.addWidget(self.change_dir_icon_label)
        self.dir_selector_layout.addStretch() # Push icon to the right

        self.left_panel_layout.addLayout(self.dir_selector_layout)

        # File system tree view
        self.file_model = CustomFileSystemModel() # Use custom model for folder icons
        self.file_model.setRootPath(self.current_directory)
        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        self.file_tree.setRootIndex(self.file_model.index(self.current_directory))
        self.file_tree.setColumnHidden(1, True) # Hide size column
        self.file_tree.setColumnHidden(2, True) # Hide type column
        self.file_tree.setColumnHidden(3, True) # Hide date modified column
        self.file_tree.setHeaderHidden(True) # Hide header
        self.file_tree.doubleClicked.connect(self._on_file_tree_double_clicked)
        
        # Enable drag and drop for the file tree
        self.file_tree.setDragEnabled(True)
        self.file_tree.setAcceptDrops(True)
        self.file_tree.setDropIndicatorShown(True)
        self.file_tree.setDragDropMode(QAbstractItemView.DragDrop)
        self.file_tree.setDragDropOverwriteMode(True)
        
        self.file_tree.viewport().setAcceptDrops(True)
        self.file_tree.setDropIndicatorShown(True)
        self.file_tree.dragEnterEvent = self._file_tree_drag_enter_event
        self.file_tree.dropEvent = self._file_tree_drop_event

        self.left_panel_layout.addWidget(self.file_tree)
        self.main_splitter.addWidget(self.left_panel_container)

        # Right panel (code editors and terminal)
        self.right_panel_container = QWidget()
        self.right_panel_layout = QVBoxLayout(self.right_panel_container)
        self.right_panel_layout.setContentsMargins(5, 5, 5, 5)

        self.code_splitter = QSplitter(Qt.Horizontal)
        self.code_splitter.setHandleWidth(3)
        self.code_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Left tab widget for code editors
        self.left_tab_widget = QTabWidget()
        self.left_tab_widget.setTabsClosable(True)
        self.left_tab_widget.tabCloseRequested.connect(self._close_tab)
        self.left_tab_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.left_tab_widget.customContextMenuRequested.connect(lambda pos: self._show_tab_context_menu(pos, self.left_tab_widget))
        self.left_tab_widget.currentChanged.connect(lambda index: self._set_active_tab_widget(index, self.left_tab_widget))
        # Set tab bar to stretch to fill available space, removing dots
        self.left_tab_widget.tabBar().setElideMode(Qt.ElideNone)
        self.left_tab_widget.tabBar().setUsesScrollButtons(True)
        self.left_tab_widget.tabBar().setExpanding(True)
        self.left_tab_widget.setObjectName("left_tab_widget") # For identification

        # Right tab widget for split view
        self.right_tab_widget = QTabWidget()
        self.right_tab_widget.setTabsClosable(True)
        self.right_tab_widget.tabCloseRequested.connect(self._close_tab)
        self.right_tab_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.right_tab_widget.customContextMenuRequested.connect(lambda pos: self._show_tab_context_menu(pos, self.right_tab_widget))
        self.right_tab_widget.currentChanged.connect(lambda index: self._set_active_tab_widget(index, self.right_tab_widget))
        self.right_tab_widget.hide() # Initially hidden for single view
        # Set tab bar to stretch to fill available space, removing dots
        self.right_tab_widget.tabBar().setElideMode(Qt.ElideNone)
        self.right_tab_widget.tabBar().setUsesScrollButtons(True)
        self.right_tab_widget.tabBar().setExpanding(True)
        self.right_tab_widget.setObjectName("right_tab_widget") # For identification


        self.code_splitter.addWidget(self.left_tab_widget)
        self.code_splitter.addWidget(self.right_tab_widget)
        self.code_splitter.setStretchFactor(0, 1)
        self.code_splitter.setStretchFactor(1, 1)

        self.right_panel_layout.addWidget(self.code_splitter)

        # Terminal splitter (for output)
        self.terminal_splitter = QSplitter(Qt.Horizontal)
        self.terminal_splitter.setHandleWidth(3)
        self.terminal_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.left_terminal = QPlainTextEdit()
        self.left_terminal.setReadOnly(True)
        self.left_terminal.setFont(QFont("Monospace", 9))
        self.left_terminal.setObjectName("left_terminal") # For identification
        self.terminal_splitter.addWidget(self.left_terminal)

        self.right_terminal = QPlainTextEdit()
        self.right_terminal.setReadOnly(True)
        self.right_terminal.setFont(QFont("Monospace", 9))
        self.right_terminal.setObjectName("right_terminal") # For identification
        self.right_terminal.hide() # Initially hidden
        self.terminal_splitter.addWidget(self.right_terminal)

        self.terminal_splitter.setStretchFactor(0, 1)
        self.terminal_splitter.setStretchFactor(1, 1)


        self.right_panel_layout.addWidget(self.terminal_splitter)

        self.main_splitter.addWidget(self.right_panel_container)

        # Set initial sizes for the main splitter panels (folder tree width decreased by 25%)
        # Original ratio was 0.25 for left panel. New ratio is 0.25 * 0.75 = 0.1875
        initial_left_panel_width_ratio = 0.1875
        self.main_splitter.setSizes([int(self.width() * initial_left_panel_width_ratio), int(self.width() * (1 - initial_left_panel_width_ratio))])

        # Set stretch factors for code editor and terminal within the right panel
        self.right_panel_layout.setStretchFactor(self.code_splitter, 7)
        self.right_panel_layout.setStretchFactor(self.terminal_splitter, 3)

        # Dictionary to keep track of open files and their paths: widget_instance -> file_path
        self.tab_paths = {}

        self.current_editor = None # Currently active code editor
        self.active_tab_widget = self.left_tab_widget # Currently active tab widget

        # Create an initial untitled file
        # This will be overridden by session restore if applicable
        if self.left_tab_widget.count() == 0:
            self._new_file(target_tab_widget=self.left_tab_widget)

    # Creates all QActions for menu items and toolbar buttons.
    def _create_actions(self):
        self.new_file_action = QAction(QIcon.fromTheme("document-new"), "New File", self)
        self.new_file_action.setShortcut("Ctrl+N")
        self.new_file_action.triggered.connect(lambda: self._new_file(target_tab_widget=self.active_tab_widget))

        self.open_file_action = QAction(QIcon.fromTheme("document-open"), "Open File", self)
        self.open_file_action.setShortcut("Ctrl+O")
        self.open_file_action.triggered.connect(self._open_file_dialog)

        self.save_file_action = QAction(QIcon.fromTheme("document-save"), "Save File", self)
        self.save_file_action.setShortcut("Ctrl+S")
        self.save_file_action.triggered.connect(self._save_file)

        self.save_as_file_action = QAction(QIcon.fromTheme("document-save-as"), "Save As...", self)
        self.save_as_file_action.setShortcut("Ctrl+Shift+S")
        self.save_as_file_action.triggered.connect(self._save_file_as)

        self.undo_action = QAction(QIcon.fromTheme("edit-undo"), "Undo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(lambda: self.current_editor.undo() if self.current_editor and isinstance(self.current_editor, CodeEditor) else None)

        self.redo_action = QAction(QIcon.fromTheme("edit-redo"), "Redo", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(lambda: self.current_editor.redo() if self.current_editor and isinstance(self.current_editor, CodeEditor) else None)

        self.cut_action = QAction(QIcon.fromTheme("edit-cut"), "Cut", self)
        self.cut_action.setShortcut("Ctrl+X")
        self.cut_action.triggered.connect(lambda: self.current_editor.cut() if self.current_editor and isinstance(self.current_editor, CodeEditor) else None)

        self.copy_action = QAction(QIcon.fromTheme("edit-copy"), "Copy", self)
        self.copy_action.setShortcut("Ctrl+C")
        self.copy_action.triggered.connect(lambda: self.current_editor.copy() if self.current_editor and isinstance(self.current_editor, CodeEditor) else None)

        self.paste_action = QAction(QIcon.fromTheme("edit-paste"), "Paste", self)
        self.paste_action.setShortcut("Ctrl+V")
        self.paste_action.triggered.connect(lambda: self.current_editor.paste() if self.current_editor and isinstance(self.current_editor, CodeEditor) else None)

        self.select_all_action = QAction(QIcon.fromTheme("edit-select-all"), "Select All", self)
        self.select_all_action.setShortcut("Ctrl+A")
        self.select_all_action.triggered.connect(lambda: self.current_editor.selectAll() if self.current_editor and isinstance(self.current_editor, CodeEditor) else None)

        self.run_script_action = QAction(QIcon.fromTheme("media-playback-start"), "Run Script", self)
        self.run_script_action.setShortcut("Ctrl+R")
        self.run_script_action.triggered.connect(self._run_script)

        self.flake8_action = QAction(QIcon.fromTheme("utilities-terminal"), "Run Flake8", self)
        self.flake8_action.triggered.connect(lambda: self._run_external_tool("flake8"))

        self.black_action = QAction(QIcon.fromTheme("format-text-align-left"), "Run Black", self)
        self.black_action.triggered.connect(lambda: self._run_external_tool("black"))

        self.mypy_action = QAction(QIcon.fromTheme("system-run"), "Run MyPy", self)
        self.mypy_action.triggered.connect(lambda: self._run_external_tool("mypy"))

        self.dark_theme_action = QAction("Dark Theme", self)
        self.dark_theme_action.triggered.connect(lambda: self.apply_theme("dark"))

        self.light_theme_action = QAction("Light Theme", self)
        self.light_theme_action.triggered.connect(lambda: self.apply_theme("light"))

        self.find_action = QAction(QIcon.fromTheme("edit-find"), "Find...", self)
        self.find_action.setShortcut("Ctrl+F")
        self.find_action.triggered.connect(self._show_find_dialog)

        self.auto_save_action = QAction("Auto Save", self)
        self.auto_save_action.setCheckable(True)
        self.auto_save_action.setChecked(self.auto_save_enabled)
        self.auto_save_action.triggered.connect(self._toggle_auto_save)

        self.auto_format_on_save_action = QAction("Auto Format Python on Save", self)
        self.auto_format_on_save_action.setCheckable(True)
        self.auto_format_on_save_action.setChecked(self.auto_save_on_python_format)
        self.auto_format_on_save_action.triggered.connect(self._toggle_auto_format_on_save)

        self.zen_mode_action = QAction("Zen Mode", self)
        self.zen_mode_action.setCheckable(True)
        self.zen_mode_action.triggered.connect(self._toggle_zen_mode)

        self.select_font_action = QAction("Select Font...", self)
        self.select_font_action.triggered.connect(self._select_font_dialog)

        self.toggle_terminal_action = QAction("Toggle Terminal", self)
        self.toggle_terminal_action.setCheckable(True)
        self.toggle_terminal_action.setChecked(True)
        self.toggle_terminal_action.triggered.connect(self._toggle_terminal_visibility)

        # Removed self.keybinds_action as requested
        # self.keybinds_action = QAction("Customize Keybinds...", self)
        # self.keybinds_action.triggered.connect(self._show_keybinds_dialog)

        self.syntax_palette_action = QAction("Syntax Palette...", self)
        self.syntax_palette_action.triggered.connect(self._show_syntax_palette_dialog)

        self.toggle_auto_closer_action = QAction("Toggle Auto Closer", self)
        self.toggle_auto_closer_action.setCheckable(True)
        self.toggle_auto_closer_action.setChecked(self.auto_close_enabled)
        self.toggle_auto_closer_action.triggered.connect(self._toggle_auto_closer)

        self.toggle_completer_action = QAction("Toggle Completer", self)
        self.toggle_completer_action.setCheckable(True)
        self.toggle_completer_action.setChecked(self.completer_enabled)
        self.toggle_completer_action.triggered.connect(self._toggle_completer)

    # Creates the application's menu bar with File, Edit, Run, Tools, and View menus.
    def _create_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self.new_file_action)
        file_menu.addAction(self.open_file_action)
        file_menu.addAction(self.save_file_action)
        file_menu.addAction(self.save_as_file_action)
        file_menu.addSeparator()
        file_menu.addAction(QAction("Exit", self, triggered=self.close))

        edit_menu = menu_bar.addMenu("&Edit")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.cut_action)
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.select_all_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.find_action)
        edit_menu.addSeparator()
        # Removed keybinds_action as requested
        # edit_menu.addAction(self.keybinds_action)
        # edit_menu.addSeparator()
        theme_menu = edit_menu.addMenu("Themes")
        theme_menu.addAction(self.dark_theme_action)
        theme_menu.addAction(self.light_theme_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.syntax_palette_action)
        edit_menu.addAction(self.select_font_action)

        run_menu = menu_bar.addMenu("&Run")
        run_menu.addAction(self.run_script_action)

        tools_menu = menu_bar.addMenu("&Tools")
        tools_menu.addAction(self.flake8_action)
        tools_menu.addAction(self.black_action)
        tools_menu.addAction(self.mypy_action)
        tools_menu.addSeparator()
        tools_menu.addAction(self.toggle_auto_closer_action)
        tools_menu.addAction(self.toggle_completer_action)
        tools_menu.addAction(self.auto_save_action)
        tools_menu.addAction(self.auto_format_on_save_action) # New auto-format on save action

        view_menu = menu_bar.addMenu("&View")
        view_menu.addAction(self.zen_mode_action)
        view_menu.addAction(self.toggle_terminal_action)
        view_menu.addSeparator()
        view_menu.addAction(self.toggle_split_view_action)

    # Sets the currently active tab widget and updates the current editor reference.
    def _set_active_tab_widget(self, index, source_tab_widget=None):
        if source_tab_widget is None:
            # This case happens during initial setup or when no signal sender is available.
            # Prioritize the left tab widget if it has tabs
            if self.left_tab_widget.count() > 0:
                self.active_tab_widget = self.left_tab_widget
                self.current_editor = self.left_tab_widget.currentWidget()
            # Otherwise, check the right tab widget if it's visible and has tabs
            elif not self.right_tab_widget.isHidden() and self.right_tab_widget.count() > 0:
                self.active_tab_widget = self.right_tab_widget
                self.current_editor = self.right_tab_widget.currentWidget()
            else:
                # No active tab widget or editor
                self.active_tab_widget = None
                self.current_editor = None
        else:
            # If called by a tab widget's currentChanged signal
            self.active_tab_widget = source_tab_widget
            self.current_editor = source_tab_widget.widget(index)
        
        # Ensure current_editor is a CodeEditor for actions that require it
        if not isinstance(self.current_editor, CodeEditor):
            self.current_editor = None # Set to None if it's a MediaViewer or other non-editable widget

        if self.current_editor and isinstance(self.current_editor, CodeEditor):
            # Update completer mode based on global setting
            self.current_editor.completer.setCompletionMode(QCompleter.PopupCompletion if self.completer_enabled else QCompleter.Disabled)
        
        self._update_edit_actions_state() # Update action states based on new active editor

    # Creates a new untitled file in the specified tab widget.
    def _new_file(self, target_tab_widget):
        editor = CodeEditor(self, self) # Pass self (IDE instance) to CodeEditor
        tab_index = target_tab_widget.addTab(editor, "Untitled")
        target_tab_widget.setCurrentIndex(tab_index)
        self.tab_paths[editor] = None # Mark as unsaved using widget as key
        self.current_editor = editor
        self.active_tab_widget = target_tab_widget # Ensure active_tab_widget is set
        self.apply_theme(self.current_theme) # Apply current theme to new editor
        self._update_edit_actions_state()
        editor.auto_close_enabled = self.auto_close_enabled
        editor.completer.setCompletionMode(QCompleter.PopupCompletion if self.completer_enabled else QCompleter.Disabled)
        editor.setFont(self.current_font) # Apply current font to new editor
        editor.setTabStopWidth(QFontMetrics(self.current_font).width(' ' * 4))

    # Opens a file dialog to select a file to open.
    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", self.current_directory, "All Files (*.*)")
        if file_path:
            self.open_file(file_path, target_tab_widget=self.active_tab_widget)

    # Opens a file, handling different file types (code, image, video).
    # Includes logic for handling large files with warnings.
    def open_file(self, file_path, target_tab_widget):
        # Check if the file is already open
        for widget, path in self.tab_paths.items():
            if path == file_path:
                # Find which tab widget this widget belongs to
                for i in range(self.left_tab_widget.count()):
                    if self.left_tab_widget.widget(i) == widget:
                        self.left_tab_widget.setCurrentIndex(i)
                        self._set_active_tab_widget(i, self.left_tab_widget) # Update active editor
                        self.statusBar().showMessage(f"File already open: {os.path.basename(file_path)}", 2000)
                        return
                if not self.right_tab_widget.isHidden():
                    for i in range(self.right_tab_widget.count()):
                        if self.right_tab_widget.widget(i) == widget:
                            self.right_tab_widget.setCurrentIndex(i)
                            self._set_active_tab_widget(i, self.right_tab_widget) # Update active editor
                            self.statusBar().showMessage(f"File already open: {os.path.basename(file_path)}", 2000)
                            return


        file_ext = os.path.splitext(file_path)[1].lower()
        new_widget_instance = None

        try:
            file_size = os.path.getsize(file_path)
            # Warn for very large files (e.g., > 500 MB)
            if file_size > 500 * 1024 * 1024:
                reply = QMessageBox.question(self, "Very Large File Warning",
                                             f"The file '{os.path.basename(file_path)}' is extremely large ({file_size / (1024*1024):.2f} MB). "
                                             "Opening it directly might cause significant performance issues or crashes. "
                                             "Consider using a specialized large file viewer for this file. Do you want to proceed anyway?",
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            # Warn for large files (e.g., > 50 MB)
            elif file_size > 50 * 1024 * 1024:
                 reply = QMessageBox.question(self, "Large File Warning",
                                             f"The file '{os.path.basename(file_path)}' is large ({file_size / (1024*1024):.2f} MB). "
                                             "Opening it directly might cause performance issues. Do you want to proceed?",
                                             QMessageBox.Yes | QMessageBox.No)
                 if reply == QMessageBox.No:
                    return

            # Handle different file types
            if file_ext in ['.py', '.txt', '.md', '.json', '.html', '.css', '.js',
                            '.java', '.cpp', '.cxx', '.cc', '.h', '.hpp', '.cs',
                            '.scss', '.sql', '.swift', '.rb', '.go', '.rs', '.php',
                            '.pl', '.kt', '.jsx', '.tsx', '.xml', '.xsd', '.xsl', '.svg',
                            '.sh', '.bash', '.ts', '.vue', '.dart', '.r']:
                # Open as a code editor
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                editor = CodeEditor(self, self) # Pass self (IDE instance)
                editor.setText(content)
                editor.document().setModified(False)
                editor.set_highlighter(file_ext)
                editor.auto_close_enabled = self.auto_close_enabled
                editor.completer.setCompletionMode(QCompleter.PopupCompletion if self.completer_enabled else QCompleter.Disabled)
                editor.setFont(self.current_font) # Apply current font
                editor.setTabStopWidth(QFontMetrics(self.current_font).width(' ' * 4))
                new_widget_instance = editor
            elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']:
                # Open as an image viewer
                new_widget_instance = MediaViewer(file_path, self)
            elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                # Open as a video player if multimedia modules are available
                if _HAS_MULTIMEDIA:
                    new_widget_instance = MediaViewer(file_path, self)
                else:
                    new_widget_instance = QLabel(f"Multimedia modules not found. Cannot play video: {os.path.basename(file_path)}")
                    new_widget_instance.setAlignment(Qt.AlignCenter)
            else:
                # For unsupported types, try to open as plain text with a warning
                QMessageBox.warning(self, "Unsupported File Type",
                                    f"Opening files of type '{file_ext}' is not fully supported in the editor. "
                                    "Attempting to open as plain text if possible, otherwise it will show a viewer.")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                editor = CodeEditor(self, self) # Pass self (IDE instance)
                editor.setText(content)
                editor.document().setModified(False)
                editor.setFont(self.current_font) # Apply current font
                editor.setTabStopWidth(QFontMetrics(self.current_font).width(' ' * 4))
                new_widget_instance = editor
        except Exception as e:
            QMessageBox.critical(self, "Error Opening File", f"Could not open file '{os.path.basename(file_path)}': {e}")
            return

        if new_widget_instance:
            tab_name = os.path.basename(file_path)
            tab_index = target_tab_widget.addTab(new_widget_instance, tab_name)
            target_tab_widget.setCurrentIndex(tab_index)

            self.tab_paths[new_widget_instance] = file_path # Store using widget as key
            
            # Update current_editor and active_tab_widget
            self._set_active_tab_widget(tab_index, target_tab_widget) 

            self.apply_theme(self.current_theme)
            self._update_edit_actions_state()
            self.statusBar().showMessage(f"Opened: {os.path.basename(file_path)}", 2000)
        else:
            QMessageBox.critical(self, "Error", f"Could not create viewer for file: {file_path}")

    # Saves the content of the current active editor to its associated file path.
    def _save_file(self):
        if not self.current_editor or not isinstance(self.current_editor, CodeEditor):
            QMessageBox.information(self, "Save", "Only code editor files can be saved.")
            return

        file_path = self.tab_paths.get(self.current_editor)

        if file_path is None:
            # If the file is untitled, prompt for "Save As"
            self._save_file_as()
        else:
            try:
                # If auto-format on save is enabled for Python files
                if self.auto_save_on_python_format and file_path.lower().endswith('.py'):
                    # Temporarily save to a temp file, run black, then read back
                    temp_file_path = file_path + ".temp_format"
                    with open(temp_file_path, 'w', encoding='utf-8') as f:
                        f.write(self.current_editor.toPlainText())
                    
                    process = QProcess()
                    process.start(f"black \"{temp_file_path}\"")
                    process.waitForFinished()
                    
                    if process.exitCode() == 0:
                        with open(temp_file_path, 'r', encoding='utf-8') as f:
                            formatted_content = f.read()
                        self.current_editor.setText(formatted_content)
                        self.statusBar().showMessage(f"Auto-formatted and saved: {os.path.basename(file_path)}", 2000)
                    else:
                        self.statusBar().showMessage(f"Black formatting failed for {os.path.basename(file_path)}", 2000)
                        # Fallback to saving original content if formatting fails
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(self.current_editor.toPlainText())
                    os.remove(temp_file_path) # Clean up temp file
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(self.current_editor.toPlainText())
                    self.statusBar().showMessage(f"Saved: {os.path.basename(file_path)}", 2000)

                self.current_editor.document().setModified(False)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file: {e}")

    # Saves the content of the current active editor to a new file path chosen by the user.
    def _save_file_as(self):
        if not self.current_editor or not isinstance(self.current_editor, CodeEditor):
            QMessageBox.information(self, "Save As", "Only code editor files can be saved.")
            return

        # Define file filters for various programming languages and common file types
        file_filters = (
            "Python Files (*.py);;"
            "Java Files (*.java);;"
            "HTML Files (*.html);;"
            "JavaScript Files (*.js);;"
            "C++ Files (*.cpp *.cxx *.cc *.h *.hpp);;"
            "C# Files (*.cs);;"
            "CSS Files (*.css);;"
            "SCSS Files (*.scss);;"
            "SQL Files (*.sql);;"
            "Swift Files (*.swift);;"
            "Ruby Files (*.rb);;"
            "Go Files (*.go);;"
            "Rust Files (*.rs);;"
            "PHP Files (*.php);;"
            "Perl Files (*.pl);;"
            "Kotlin Files (*.kt);;"
            "React Native Files (*.jsx *.tsx);;"
            "XML Files (*.xml *.xsd *.xsl *.svg);;"
            "JSON Files (*.json);;"
            "Markdown Files (*.md);;"
            "Shell Script Files (*.sh *.bash);;"
            "TypeScript Files (*.ts *.tsx);;"
            "Vue Files (*.vue);;"
            "Dart Files (*.dart);;"
            "R Files (*.r);;"
            "Text Files (*.txt);;"
            "All Files (*.*)"
        )
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File As", self.current_directory, file_filters)
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.current_editor.toPlainText())
                self.current_editor.document().setModified(False)

                # Update tab_paths: remove old entry if it exists, add new one
                old_file_path = self.tab_paths.get(self.current_editor)
                if old_file_path:
                    del self.tab_paths[self.current_editor]
                
                self.tab_paths[self.current_editor] = file_path
                
                # Find the index of the current editor in its tab widget
                tab_index = self.active_tab_widget.indexOf(self.current_editor)
                if tab_index != -1:
                    self.active_tab_widget.setTabText(tab_index, os.path.basename(file_path))
                
                file_ext = os.path.splitext(file_path)[1].lower()
                self.current_editor.set_highlighter(file_ext) # Apply new highlighter based on extension

                self.statusBar().showMessage(f"Saved as: {os.path.basename(file_path)}", 2000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file: {e}")

    # Closes a tab, prompting to save unsaved changes if necessary.
    def _close_tab(self, index):
        sender_tab_widget = self.sender()
        if not isinstance(sender_tab_widget, QTabWidget):
            return

        widget_to_close = sender_tab_widget.widget(index)
        file_path = self.tab_paths.get(widget_to_close)

        # Prompt to save if the document has unsaved changes
        if isinstance(widget_to_close, CodeEditor) and widget_to_close.document().isModified():
            reply = QMessageBox.question(self, "Save Changes?",
                                         f"Do you want to save changes to {sender_tab_widget.tabText(index)}?",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if reply == QMessageBox.Save:
                # Temporarily set the current editor and active tab widget to the one being closed
                # to ensure correct saving context
                temp_current_editor = self.current_editor
                temp_active_tab_widget = self.active_tab_widget
                self.current_editor = widget_to_close
                self.active_tab_widget = sender_tab_widget
                self._save_file()
                # Restore original active editor and tab widget
                self.current_editor = temp_current_editor
                self.active_tab_widget = temp_active_tab_widget
            elif reply == QMessageBox.Cancel:
                return # Do not close the tab if cancelled
        
        # Stop media playback if closing a media viewer
        if isinstance(widget_to_close, MediaViewer) and widget_to_close.player and \
           widget_to_close.player.state() != QMediaPlayer.StoppedState:
            widget_to_close.player.stop()

        # Remove the file from tracking dictionaries
        if widget_to_close in self.tab_paths:
            del self.tab_paths[widget_to_close]

        sender_tab_widget.removeTab(index)

        # If all tabs are closed in a widget, create a new untitled file
        if sender_tab_widget.count() == 0:
            self._new_file(target_tab_widget=sender_tab_widget)

        # Update the active editor and actions based on the new current tab
        self._set_active_tab_widget(sender_tab_widget.currentIndex(), sender_tab_widget)

    # Handles double-clicking on a file or folder in the file tree.
    def _on_file_tree_double_clicked(self, index):
        file_path = self.file_model.filePath(index)
        if os.path.isfile(file_path):
            self.open_file(file_path, target_tab_widget=self.active_tab_widget)

    # Handles drag enter events for the file tree.
    def _file_tree_drag_enter_event(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    # Handles drop events for files dropped onto the file tree.
    # Allows copying files into directories within the tree.
    def _file_tree_drop_event(self, event):
        if event.mimeData().hasUrls():
            target_index = self.file_tree.indexAt(event.pos())
            target_path = self.file_model.filePath(target_index)

            if os.path.isdir(target_path):
                dest_dir = target_path
            else:
                dest_dir = os.path.dirname(target_path)
            
            if not os.path.exists(dest_dir):
                QMessageBox.warning(self, "Invalid Drop Location", f"Target directory does not exist: {dest_dir}")
                event.ignore()
                return

            for url in event.mimeData().urls():
                src_path = url.toLocalFile()
                if os.path.isfile(src_path):
                    try:
                        file_name = os.path.basename(src_path)
                        dest_path = os.path.join(dest_dir, file_name)
                        
                        if os.path.exists(dest_path):
                            reply = QMessageBox.question(self, "Overwrite File?",
                                                         f"File '{file_name}' already exists in '{dest_path}'. Overwrite?",
                                                         QMessageBox.Yes | QMessageBox.No)
                            if reply == QMessageBox.No:
                                continue

                        shutil.copy2(src_path, dest_path) # Copy the file
                        self.statusBar().showMessage(f"Copied: {file_name} to {dest_dir}", 2000)
                    except Exception as e:
                        QMessageBox.critical(self, "File Copy Error", f"Could not copy {os.path.basename(src_path)}: {e}")
            
            # Refresh the file tree view after copy operation
            self.file_model.setRootPath(self.current_directory)
            self.file_tree.setRootIndex(self.file_model.index(self.current_directory))
            event.acceptProposedAction()
        else:
            event.ignore()

    # Allows the user to change the current working directory of the file tree.
    def _change_directory(self):
        new_dir = QFileDialog.getExistingDirectory(self, "Select Directory", self.current_directory)
        if new_dir:
            self.current_directory = new_dir
            self.file_model.setRootPath(self.current_directory)
            self.file_tree.setRootIndex(self.file_model.index(self.current_directory))
            self.dir_path_display.setText(self.current_directory)
            self.statusBar().showMessage(f"Changed directory to: {self.current_directory}", 2000)

    # Runs the currently active Python script or prompts the user to select one.
    def _run_script(self):
        python_files_open = []
        # Collect all open Python files from both tab widgets
        for widget, file_path in self.tab_paths.items():
            if isinstance(widget, CodeEditor) and file_path and file_path.lower().endswith('.py'):
                # Find which tab widget this widget belongs to
                tab_text = ""
                for i in range(self.left_tab_widget.count()):
                    if self.left_tab_widget.widget(i) == widget:
                        tab_text = self.left_tab_widget.tabText(i)
                        break
                if not tab_text and not self.right_tab_widget.isHidden():
                    for i in range(self.right_tab_widget.count()):
                        if self.right_tab_widget.widget(i) == widget:
                            tab_text = self.right_tab_widget.tabText(i) + " (Right Panel)"
                            break
                if tab_text:
                    python_files_open.append((file_path, tab_text, widget))

        if not python_files_open:
            self.get_active_terminal().append("No Python file open to run.")
            return

        file_to_run_path = None
        editor_for_run = None

        if len(python_files_open) == 1:
            file_to_run_path = python_files_open[0][0]
            editor_for_run = python_files_open[0][2]
        else:
            # If multiple Python files are open, let the user choose
            items = [f"{name}" for path, name, widget in python_files_open]
            item, ok = QInputDialog.getItem(self, "Run Script", "Select a Python file to run:", items, 0, False)
            if ok and item:
                for path, name, widget in python_files_open:
                    if name == item:
                        file_to_run_path = path
                        editor_for_run = widget
                        break
            else:
                self.get_active_terminal().append("Script run cancelled by user.")
                return

        # Prompt to save if the selected file has unsaved changes
        if editor_for_run and editor_for_run.document().isModified():
            reply = QMessageBox.question(self, "Run Unsaved File",
                                         f"The file '{os.path.basename(file_to_run_path)}' has unsaved changes. Save it before running?",
                                         QMessageBox.Save | QMessageBox.Cancel)
            if reply == QMessageBox.Save:
                # Temporarily switch context to save the specific file
                temp_current_editor = self.current_editor
                temp_active_tab_widget = self.active_tab_widget
                self.current_editor = editor_for_run
                
                # Find the tab widget that contains this editor
                found_tab_widget = None
                for i in range(self.left_tab_widget.count()):
                    if self.left_tab_widget.widget(i) == editor_for_run:
                        found_tab_widget = self.left_tab_widget
                        break
                if not found_tab_widget and not self.right_tab_widget.isHidden():
                    for i in range(self.right_tab_widget.count()):
                        if self.right_tab_widget.widget(i) == editor_for_run:
                            found_tab_widget = self.right_tab_widget
                            break
                
                if found_tab_widget:
                    self.active_tab_widget = found_tab_widget
                    self._save_file()
                else:
                    QMessageBox.warning(self, "Save Error", "Could not determine context to save the selected file.")
                    self.get_active_terminal().append("Script run cancelled due to save error.")
                    return

                self.current_editor = temp_current_editor
                self.active_tab_widget = temp_active_tab_widget
            elif reply == QMessageBox.Cancel:
                self.get_active_terminal().append("Script run cancelled.")
                return

        # Validate the file path before running
        if file_to_run_path is None or not os.path.exists(file_to_run_path) or not file_to_run_path.lower().endswith('.py'):
            self.get_active_terminal().append("Cannot run: selected file is not a valid Python script or does not exist.")
            return

        target_terminal = self.get_terminal_for_editor(editor_for_run)
        target_terminal.clear()
        target_terminal.appendPlainText(f"--- Running: {os.path.basename(file_to_run_path)} ---")
        self.statusBar().showMessage(f"Running {os.path.basename(file_to_run_path)}...", 0)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(lambda: self._handle_stdout(target_terminal))
        self.process.readyReadStandardError.connect(lambda: self._handle_stderr(target_terminal))
        self.process.finished.connect(lambda exit_code, exit_status: self._script_finished(exit_code, exit_status, target_terminal))

        self.process.setWorkingDirectory(os.path.dirname(file_to_run_path))
        self.process.start("python", [os.path.basename(file_to_run_path)])

    # Handles standard output from an external process.
    def _handle_stdout(self, terminal_widget):
        data = self.process.readAllStandardOutput().data().decode()
        terminal_widget.appendPlainText(data.strip())

    # Handles standard error from an external process.
    def _handle_stderr(self, terminal_widget):
        data = self.process.readAllStandardError().data().decode()
        terminal_widget.appendHtml(f"<span style='color: red;'>{data.strip()}</span>")

    # Called when an external script finishes execution.
    def _script_finished(self, exit_code, exit_status, terminal_widget):
        terminal_widget.appendPlainText(f"--- Script finished with exit code: {exit_code} ---")
        self.statusBar().clearMessage()

    # Runs external Python development tools (Flake8, Black, MyPy) on the current file.
    def _run_external_tool(self, tool_name):
        if not self.current_editor or not isinstance(self.current_editor, CodeEditor):
            self.get_active_terminal().append(f"No Python file open in active editor to run {tool_name}.")
            return

        file_path = self.tab_paths.get(self.current_editor)

        if file_path is None or not os.path.exists(file_path) or not file_path.lower().endswith('.py'):
            self.get_active_terminal().append(f"Please save the current file as a .py file before running {tool_name}.")
            return

        self._save_file() # Ensure the file is saved before running the tool

        target_terminal = self.get_terminal_for_editor(self.current_editor)
        target_terminal.clear()
        target_terminal.appendPlainText(f"--- Running {tool_name} on {os.path.basename(file_path)} ---")
        self.statusBar().showMessage(f"Running {tool_name}...", 0)

        command = ""
        if tool_name == "flake8":
            command = f"flake8 \"{file_path}\""
        elif tool_name == "black":
            command = f"black \"{file_path}\""
        elif tool_name == "mypy":
            command = f"mypy \"{file_path}\""
        else:
            target_terminal.appendPlainText(f"Unknown tool: {tool_name}")
            self.statusBar().clearMessage()
            return

        # Run the tool in a separate worker thread
        self.worker = Worker(command, tool_name)
        self.worker.finished.connect(lambda tn, output: self._tool_finished(tn, output, target_terminal))
        self.worker.start()

    # Called when an external tool finishes execution.
    def _tool_finished(self, tool_name, output, terminal_widget):
        terminal_widget.appendPlainText(f"--- {tool_name} Output ---")
        if output:
            terminal_widget.appendPlainText(output)
        else:
            terminal_widget.appendPlainText(f"{tool_name} found no issues." if tool_name != "black" else f"{tool_name} finished.")
        self.statusBar().clearMessage()
        if tool_name == "black":
            # If Black was run, reload the file content as it might have been formatted
            file_path = self.tab_paths.get(self.current_editor)
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.current_editor.setText(content)
                    self.current_editor.document().setModified(False)
                    self.statusBar().showMessage(f"File formatted by Black: {os.path.basename(file_path)}", 2000)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not reload file after Black: {e}")

    # Displays a context menu when a tab is right-clicked.
    def _show_tab_context_menu(self, pos, source_tab_widget):
        index = source_tab_widget.tabBar().tabAt(pos)
        if index == -1:
            return

        menu = QMenu(self)

        close_action = QAction("Close", self)
        close_action.triggered.connect(lambda: self._close_tab(index))
        menu.addAction(close_action)

        rename_action = QAction("Rename...", self)
        rename_action.triggered.connect(lambda: self._rename_file(index, source_tab_widget))
        widget_at_index = source_tab_widget.widget(index)
        file_path = self.tab_paths.get(widget_at_index)
        rename_action.setEnabled(file_path is not None) # Only enable rename for saved files
        menu.addAction(rename_action)

        # Add actions to move tabs between left and right panels
        if source_tab_widget == self.left_tab_widget:
            move_action = QAction("Move to Right Panel", self)
            move_action.triggered.connect(lambda: self._move_tab(index, source_tab_widget, self.right_tab_widget))
            move_action.setEnabled(not self.right_tab_widget.isHidden()) # Only enable if right panel is visible
            menu.addAction(move_action)
        elif source_tab_widget == self.right_tab_widget:
            move_action = QAction("Move to Left Panel", self)
            move_action.triggered.connect(lambda: self._move_tab(index, source_tab_widget, self.left_tab_widget))
            menu.addAction(move_action)
        
        menu.addSeparator()
        cancel_action = QAction("Cancel", self)
        menu.addAction(cancel_action)

        menu.exec_(source_tab_widget.mapToGlobal(pos))

    # Renames the file associated with a tab.
    def _rename_file(self, index, source_tab_widget):
        widget_to_rename = source_tab_widget.widget(index)
        old_file_path = self.tab_paths.get(widget_to_rename)
        if not old_file_path:
            QMessageBox.warning(self, "Rename File", "Cannot rename unsaved (Untitled) file.")
            return

        old_file_name = os.path.basename(old_file_path)
        new_file_name, ok = QInputDialog.getText(self, "Rename File", "Enter new file name:",
                                                 QLineEdit.Normal, old_file_name)
        if ok and new_file_name and new_file_name != old_file_name:
            new_file_path = os.path.join(os.path.dirname(old_file_path), new_file_name)
            if os.path.exists(new_file_path):
                QMessageBox.warning(self, "Rename File", f"A file named '{new_file_name}' already exists.")
                return
            try:
                os.rename(old_file_path, new_file_path) # Rename the file on disk
                
                # Update tracking dictionaries
                del self.tab_paths[widget_to_rename]
                self.tab_paths[widget_to_rename] = new_file_path
                source_tab_widget.setTabText(index, os.path.basename(new_file_path))
                
                file_ext = os.path.splitext(new_file_path)[1].lower()
                if isinstance(widget_to_rename, CodeEditor):
                    widget_to_rename.set_highlighter(file_ext) # Update highlighter for new extension

                self.statusBar().showMessage(f"Renamed '{old_file_name}' to '{new_file_name}'", 2000)
                # Refresh file tree view to reflect the rename
                self.file_model.setRootPath(self.current_directory)
                self.file_tree.setRootIndex(self.file_model.index(self.current_directory))

            except Exception as e:
                QMessageBox.critical(self, "Rename Error", f"Could not rename file: {e}")

    # Moves a tab from one tab widget to another (e.g., between left and right panels).
    def _move_tab(self, index, source_tab_widget, target_tab_widget):
        widget_to_move = source_tab_widget.widget(index)
        tab_name = source_tab_widget.tabText(index)
        # file_path is already associated with widget_to_move in self.tab_paths

        # Remove tab from source
        source_tab_widget.removeTab(index)
        
        # Add tab to target widget
        new_index = target_tab_widget.addTab(widget_to_move, tab_name)
        target_tab_widget.setCurrentIndex(new_index)
        # No need to update self.tab_paths here, as the key (widget_to_move) remains the same

        # If source widget becomes empty, create a new untitled file
        if source_tab_widget.count() == 0:
            self._new_file(target_tab_widget=source_tab_widget)

        self.statusBar().showMessage(f"Moved '{tab_name}' to {'right' if target_tab_widget == self.right_tab_widget else 'left'} panel.", 2000)
        # Ensure active editor is correctly set after move
        self._set_active_tab_widget(target_tab_widget.currentIndex(), target_tab_widget)

    # Toggles the split view (showing/hiding the right code editor panel).
    def _toggle_split_view(self):
        is_split = self.right_tab_widget.isVisible()
        
        if is_split:
            # If currently in split view, move all tabs from right to left panel
            while self.right_tab_widget.count() > 0:
                widget_to_move = self.right_tab_widget.widget(0)
                tab_name = self.right_tab_widget.tabText(0)
                # file_path is already associated with widget_to_move in self.tab_paths

                self.right_tab_widget.removeTab(0)
                # No need to delete from self.tab_paths, as widget_to_move is just changing parent
                
                new_index = self.left_tab_widget.addTab(widget_to_move, tab_name)
                # No need to add to self.tab_paths, as widget_to_move is already a key

            self.right_tab_widget.hide()
            self.right_terminal.hide() # Hide right terminal too
            self.code_splitter.setSizes([self.code_splitter.width(), 0]) # Expand left panel
            self.terminal_splitter.setSizes([self.terminal_splitter.width(), 0]) # Expand left terminal
        else:
            # If not in split view, show right panel and distribute space
            self.right_tab_widget.show()
            self.right_terminal.show() # Show right terminal
            self.code_splitter.setSizes([int(self.code_splitter.width() * 0.5), int(self.code_splitter.width() * 0.5)])
            self.terminal_splitter.setSizes([int(self.terminal_splitter.width() * 0.5), int(self.terminal_splitter.width() * 0.5)])
            if self.right_tab_widget.count() == 0:
                self._new_file(target_tab_widget=self.right_tab_widget) # Create new file if right panel is empty

        # Ensure left panel always has at least one tab
        if self.left_tab_widget.count() == 0:
            self._new_file(target_tab_widget=self.left_tab_widget)

        self.statusBar().showMessage(f"Split view: {'On' if not is_split else 'Off'}", 2000)
        # Re-set active tab widget to ensure correct context
        if self.active_tab_widget.count() > 0:
            self._set_active_tab_widget(self.active_tab_widget.currentIndex(), self.active_tab_widget)
        else:
            # If active_tab_widget became empty, default to left_tab_widget
            self.active_tab_widget = self.left_tab_widget
            self.current_editor = self.left_tab_widget.currentWidget()
            self._update_edit_actions_state()

    # Toggles Zen Mode, which hides UI elements for a distraction-free editing experience.
    def _toggle_zen_mode(self):
        self.in_zen_mode = not self.in_zen_mode
        if self.in_zen_mode:
            self.menuBar().hide()
            self.statusBar().hide()
            self.left_panel_container.hide()
            self.terminal_splitter.hide()
            self.toggle_terminal_action.setChecked(False) # Uncheck terminal toggle
            self.main_splitter.setSizes([0, self.width()]) # Expand editor to full width
            self.right_panel_layout.setStretchFactor(self.code_splitter, 1) # Give all vertical space to code editor
            self.statusBar().showMessage("Zen Mode: ON (Press Esc to exit)", 0)
        else:
            self.menuBar().show()
            self.statusBar().show()
            self.left_panel_container.show()
            if self.toggle_terminal_action.isChecked(): # Restore terminal visibility if it was on
                self.terminal_splitter.show()
            # Restore original splitter sizes based on current window width
            initial_left_panel_width_ratio = 0.1875
            self.main_splitter.setSizes([int(self.width() * initial_left_panel_width_ratio), int(self.width() * (1 - initial_left_panel_width_ratio))])
            self.right_panel_layout.setStretchFactor(self.code_splitter, 7)
            self.right_panel_layout.setStretchFactor(self.terminal_splitter, 3)
            self.statusBar().showMessage("Zen Mode: OFF", 2000)
        self.zen_mode_action.setChecked(self.in_zen_mode) # Update menu action checkbox

    # Displays a dialog showing current keybinds.
    # Removed as requested
    # def _show_keybinds_dialog(self):
    #     keybinds = {
    #         "New File": self.new_file_action.shortcut().toString() if self.new_file_action.shortcut() else "None",
    #         "Open File": self.open_file_action.shortcut().toString() if self.open_file_action.shortcut() else "None",
    #         "Save File": self.save_file_action.shortcut().toString() if self.save_file_action.shortcut() else "None",
    #         "Save As": self.save_as_file_action.shortcut().toString() if self.save_as_file_action.shortcut() else "None",
    #         "Undo": self.undo_action.shortcut().toString() if self.undo_action.shortcut() else "None",
    #         "Redo": self.redo_action.shortcut().toString() if self.redo_action.shortcut() else "None",
    #         "Cut": self.cut_action.shortcut().toString() if self.cut_action.shortcut() else "None",
    #         "Copy": self.copy_action.shortcut().toString() if self.copy_action.shortcut() else "None",
    #         "Paste": self.paste_action.shortcut().toString() if self.paste_action.shortcut() else "None",
    #         "Select All": self.select_all_action.shortcut().toString() if self.select_all_action.shortcut() else "None",
    #         "Run Script": self.run_script_action.shortcut().toString() if self.run_script_action.shortcut() else "None",
    #         "Find": self.find_action.shortcut().toString() if self.find_action.shortcut() else "None",
    #         "Zen Mode": self.zen_mode_shortcut.keySequence().toString() if self.zen_mode_shortcut.keySequence() else "None",
    #         "Toggle Terminal": self.toggle_terminal_action.shortcut().toString() if self.toggle_terminal_action.shortcut() else "None",
    #         "Toggle Split View": self.toggle_split_view_action.shortcut().toString() if self.toggle_split_view_action.shortcut() else "None",
    #         "Toggle Auto Closer": self.toggle_auto_closer_action.shortcut().toString() if self.toggle_auto_closer_action.shortcut() else "None",
    #         "Toggle Completer": self.toggle_completer_action.shortcut().toString() if self.toggle_completer_action.shortcut() else "None",
    #         "Quick Open": self.quick_switcher_shortcut.keySequence().toString() if self.quick_switcher_shortcut.keySequence() else "None",
    #     }
    #     dialog = KeybindsDialog(keybinds, self)
    #     dialog.exec_()

    # Displays a dialog for customizing syntax highlighting colors.
    def _show_syntax_palette_dialog(self):
        dialog = SyntaxPaletteDialog(self)
        dialog.color_changed.connect(self._reapply_syntax_highlighting) # Reapply highlighting after color changes
        dialog.exec_()

    # Reapplies syntax highlighting to all open code editors.
    def _reapply_syntax_highlighting(self):
        for widget, file_path in self.tab_paths.items():
            if isinstance(widget, CodeEditor):
                if file_path:
                    file_ext = os.path.splitext(file_path)[1].lower()
                    widget.set_highlighter(file_ext)
                else:
                    # If file is untitled, re-detect language based on content
                    widget.language_detected = False
                    widget._auto_detect_language_on_type()
        self.statusBar().showMessage("Syntax colors applied.", 2000)

    # Toggles the auto-closing bracket/quote feature.
    def _toggle_auto_closer(self):
        self.auto_close_enabled = self.toggle_auto_closer_action.isChecked()
        # Apply setting to all existing and new code editors
        for widget in self.tab_paths.keys(): # Iterate through widgets in tab_paths
            if isinstance(widget, CodeEditor):
                widget.auto_close_enabled = self.auto_close_enabled
        # Also apply to current editor if it's not yet in tab_paths (e.g., new untitled)
        if self.current_editor and isinstance(self.current_editor, CodeEditor) and self.current_editor not in self.tab_paths:
            self.current_editor.auto_close_enabled = self.auto_close_enabled
        self.statusBar().showMessage(f"Auto Closer: {'Enabled' if self.auto_close_enabled else 'Disabled'}", 2000)

    # Toggles the auto-completion feature.
    def _toggle_completer(self):
        self.completer_enabled = self.toggle_completer_action.isChecked()
        # Apply setting to all existing and new code editors
        for widget in self.tab_paths.keys(): # Iterate through widgets in tab_paths
            if isinstance(widget, CodeEditor):
                widget.completer.setCompletionMode(QCompleter.PopupCompletion if self.completer_enabled else QCompleter.Disabled)
        # Also apply to current editor if it's not yet in tab_paths (e.g., new untitled)
        if self.current_editor and isinstance(self.current_editor, CodeEditor) and self.current_editor not in self.tab_paths:
            self.current_editor.completer.setCompletionMode(QCompleter.PopupCompletion if self.completer_enabled else QCompleter.Disabled)
        self.statusBar().showMessage(f"Completer: {'Enabled' if self.completer_enabled else 'Disabled'}", 2000)

    # Displays the find dialog for searching text in the current editor.
    def _show_find_dialog(self):
        if self.current_editor and isinstance(self.current_editor, CodeEditor):
            self.find_dialog.set_editor(self.current_editor)
            self.find_dialog.exec_()
        else:
            QMessageBox.information(self, "Find", "No active code editor to search in.")

    # Toggles the auto-save feature.
    def _toggle_auto_save(self):
        self.auto_save_enabled = self.auto_save_action.isChecked()
        if self.auto_save_enabled:
            self.auto_save_timer.start(self.auto_save_interval)
            self.statusBar().showMessage(f"Auto Save: ON (every {self.auto_save_interval / 1000 / 60} minutes)", 2000)
        else:
            self.auto_save_timer.stop()
            self.statusBar().showMessage("Auto Save: OFF", 2000)

    # Toggles the auto-format on save feature for Python files.
    def _toggle_auto_format_on_save(self):
        self.auto_save_on_python_format = self.auto_format_on_save_action.isChecked()
        self.statusBar().showMessage(f"Auto Format Python on Save: {'Enabled' if self.auto_save_on_python_format else 'Disabled'}", 2000)

    # Performs an auto-save operation for the current modified file.
    def _perform_auto_save(self):
        # Iterate through all open code editors in both tab widgets
        all_code_editors = []
        for i in range(self.left_tab_widget.count()):
            widget = self.left_tab_widget.widget(i)
            if isinstance(widget, CodeEditor):
                all_code_editors.append(widget)
        if not self.right_tab_widget.isHidden():
            for i in range(self.right_tab_widget.count()):
                widget = self.right_tab_widget.widget(i)
                if isinstance(widget, CodeEditor):
                    all_code_editors.append(widget)

        saved_count = 0
        for editor in all_code_editors:
            if editor.document().isModified():
                file_path = self.tab_paths.get(editor)
                try:
                    if file_path: # If it's a saved file
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(editor.toPlainText())
                        editor.document().setModified(False)
                        self.statusBar().showMessage(f"Auto-saved: {os.path.basename(file_path)}", 1000)
                        saved_count += 1
                    else: # If it's an untitled file, save to session file
                        # Content will be saved to session file on closeEvent,
                        # but we can mark it as "pseudo-saved" to avoid repeated popups
                        # This part is implicitly handled by _save_session on close.
                        # For now, just show a message for untitled files.
                        self.statusBar().showMessage(f"Auto-save: Untitled file modified. Will be recovered on restart.", 1000)

                except Exception as e:
                    print(f"Auto-save failed for {file_path if file_path else 'untitled file'}: {e}")
        
        if saved_count > 0:
            self.statusBar().showMessage(f"Auto-saved {saved_count} file(s).", 1000)


    # Displays a font selection dialog and applies the chosen font to all editors and the terminal.
    def _select_font_dialog(self):
        font, ok = QFontDialog.getFont(self.current_font, self)
        if ok:
            self.current_font = font # Update the stored current font
            for widget in self.tab_paths.keys(): # Iterate through widgets in tab_paths
                if isinstance(widget, CodeEditor):
                    widget.setFont(self.current_font)
                    widget.setTabStopWidth(QFontMetrics(self.current_font).width(' ' * 4))
            # Also apply to current editor if it's not yet in tab_paths (e.g., new untitled)
            if self.current_editor and isinstance(self.current_editor, CodeEditor) and self.current_editor not in self.tab_paths:
                self.current_editor.setFont(self.current_font)
                self.current_editor.setTabStopWidth(QFontMetrics(self.current_font).width(' ' * 4))
            self.left_terminal.setFont(self.current_font)
            self.right_terminal.setFont(self.current_font) # Apply to right terminal
            self.statusBar().showMessage(f"Font changed to: {self.current_font.family()}, {self.current_font.pointSize()}pt", 2000)

    # Toggles the visibility of the terminal panel.
    def _toggle_terminal_visibility(self):
        is_visible = self.terminal_splitter.isVisible()
        self.terminal_splitter.setVisible(not is_visible)
        self.toggle_terminal_action.setChecked(not is_visible)
        self.statusBar().showMessage(f"Terminal: {'Visible' if not is_visible else 'Hidden'}", 2000)

        # Adjust splitter stretch factors based on terminal visibility
        if not is_visible:
            self.right_panel_layout.setStretchFactor(self.code_splitter, 7)
            self.right_panel_layout.setStretchFactor(self.terminal_splitter, 3)
            # Ensure right terminal visibility matches right tab widget
            if not self.right_tab_widget.isHidden():
                self.right_terminal.show()
        else:
            self.right_panel_layout.setStretchFactor(self.code_splitter, 1)
            self.right_panel_layout.setStretchFactor(self.terminal_splitter, 0)
            self.right_terminal.hide() # Hide right terminal if main terminal is hidden

    # Returns the active terminal widget based on the active code editor panel.
    def get_active_terminal(self):
        if self.active_tab_widget == self.left_tab_widget:
            return self.left_terminal
        elif self.active_tab_widget == self.right_tab_widget and not self.right_tab_widget.isHidden():
            return self.right_terminal
        return self.left_terminal # Fallback

    # Returns the specific terminal associated with a given editor widget.
    def get_terminal_for_editor(self, editor_widget):
        # Determine which tab widget the editor belongs to
        for i in range(self.left_tab_widget.count()):
            if self.left_tab_widget.widget(i) == editor_widget:
                return self.left_terminal
        for i in range(self.right_tab_widget.count()):
            if self.right_tab_widget.widget(i) == editor_widget:
                return self.right_terminal
        return self.left_terminal # Fallback if editor not found or not a code editor

    # Displays the Quick Switcher dialog.
    def _show_quick_switcher(self):
        dialog = QuickSwitcherDialog(self, self)
        dialog.exec_()

    # Applies the selected theme to the entire IDE.
    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        theme = THEMES[theme_name]

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme["bg_color"]};
                color: {theme["text_color"]};
            }}
            QTabWidget::pane {{
                border: 1px solid {theme["border_color"]};
                border-radius: 5px;
            }}
            QTabBar::tab {{
                background: {theme["tab_bg"]};
                color: {theme["tab_text"]};
                border: 1px solid {theme["border_color"]};
                border-bottom-color: {theme["border_color"]};
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 5px 10px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {theme["tab_selected_bg"]};
                color: {theme["text_color"]};
                border-bottom-color: {theme["tab_selected_bg"]};
            }}
            QTabBar::tab:hover {{
                background: {theme["current_line_bg"]};
            }}
            QSplitter::handle {{
                background-color: {theme["border_color"]};
                width: 3px;
                height: 3px;
            }}
            QTreeView {{
                background-color: {theme["bg_color"]};
                color: {theme["text_color"]};
                border: 1px solid {theme["border_color"]};
                border-radius: 5px;
            }}
            QTreeView::item:selected {{
                background-color: {theme["file_tree_selection_bg"]}; /* Blue highlight for selected items */
                color: {theme["file_tree_selection_text"]}; /* White text for file tree selection */
                border-radius: 3px; /* Rounded corners for selected item */
                padding: 2px; /* Add some padding */
            }}
            QTreeView::branch:selected {{
                background-color: {theme["file_tree_selection_bg"]}; /* Ensure branch also highlights blue */
            }}
            QPlainTextEdit {{ /* Terminal */
                background-color: {theme["terminal_bg"]};
                color: {theme["terminal_text"]};
                border: 1px solid {theme["border_color"]};
                border-radius: 5px;
            }}
            QLineEdit {{
                background-color: {theme["terminal_bg"]};
                color: {theme["terminal_text"]};
                border: 1px solid {theme["border_color"]};
                padding: 2px;
                border-radius: 3px;
            }}
            QPushButton {{
                background-color: {theme["current_line_bg"]};
                color: {theme["text_color"]};
                border: 1px solid {theme["border_color"]};
                border-radius: 5px;
                padding: 3px 8px;
            }}
            QPushButton:hover {{
                background-color: {theme["selection_bg"]};
            }}
            QMenu {{
                background-color: {theme["bg_color"]};
                color: {theme["text_color"]};
                border: 1px solid {theme["border_color"]};
            }}
            QMenu::item:selected {{
                background-color: {theme["selection_bg"]};
            }}
            QDialog {{
                background-color: {theme["bg_color"]};
                color: {theme["text_color"]};
                border-radius: 5px;
            }}
            QLabel {{
                color: {theme["text_color"]};
            }}
            QCheckBox {{
                color: {theme["text_color"]};
            }}
            QCompleter {{
                border: 1px solid {theme["border_color"]};
                border-radius: 4px;
                background-color: {theme["completer_bg"]};
                color: {theme["completer_text"]};
                selection-background-color: {theme["completer_selection_bg"]};
            }}
            QCompleter::item:selected {{
                background-color: {theme["completer_selection_bg"]};
                color: {theme["completer_text"]};
            }}
            QuickSwitcherDialog {{
                background-color: {theme["bg_color"]};
                color: {theme["text_color"]};
                border: 1px solid {theme["border_color"]};
                border-radius: 5px;
            }}
            QuickSwitcherDialog QLineEdit {{
                background-color: {theme["terminal_bg"]};
                color: {theme["terminal_text"]};
                border: 1px solid {theme["border_color"]};
                padding: 5px;
                border-radius: 3px;
            }}
            QuickSwitcherDialog QListView {{
                background-color: {theme["bg_color"]};
                color: {theme["text_color"]};
                border: 1px solid {theme["border_color"]};
                border-radius: 5px;
            }}
            QuickSwitcherDialog QListView::item:selected {{
                background-color: {theme["file_tree_selection_bg"]};
                color: {theme["file_tree_selection_text"]};
            }}
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ide = IDE()
    ide.show()
    sys.exit(app.exec_())
