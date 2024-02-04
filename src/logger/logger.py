import logging
import inspect
import os
import pprint
from datetime import datetime
from .color import *
# https://pygments.org/docs/styles/#ansiterminalstyle
from pygments import highlight
from pygments.style import Style, ansicolors
from pygments.styles import get_all_styles, get_style_by_name
from pygments.token import Token
from pygments.formatters import Terminal256Formatter
from pygments.lexers import PythonLexer

"""
print(list(get_all_styles()))
print(list(get_style_by_name('emacs')))
material
autumn
arduino
dracula
"""


def pprint_color(obj) -> None:
    """Pretty-print in color."""
    print(highlight(pprint.pformat(obj, indent=1, depth=4), PythonLexer(),
          Terminal256Formatter(style=get_style_by_name('dracula'))), end="")


class Logger(logging.Logger):
    format_string = f"%(message)s"

    def inspector(self):
        return inspect.stack()[2].filename, inspect.stack()[2].lineno

    def __init__(self, name):
        super().__init__(name)
        formatter = logging.Formatter(
            self.format_string, datefmt='%m/%d/%Y %H:%M:%S')
        shandler = logging.StreamHandler()
        shandler.setFormatter(formatter)
        shandler.setLevel(logging.NOTSET)
        self.handler = shandler
        self.handlers.append(shandler)

    def debug(self, msg, *args, **kwargs):
        time = datetime.now().strftime('%d-%m-%Y %H:%M:%S.%f')[:-3]
        fileName, lineno = self.inspector()
        colored_message = f"{fg.BLUE}[DEBUG]{fg.RESET} {time} {style.DIM}{fileName}#{lineno}{style.RESET_ALL}\n{style.DIM}{msg}{style.RESET_ALL}"
        super().debug(colored_message, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        time = datetime.now().strftime('%d-%m-%Y %H:%M:%S.%f')[:-3]
        fileName, lineno = self.inspector()
        colored_message = f"{time} {fg.GREEN}[INFO] {msg}{fg.RESET} {style.DIM}{fileName}#{lineno}{style.RESET_ALL}"
        super().info(colored_message, *args, **kwargs)

    def json(self, msg, *args, **kwargs):
        time = datetime.now().strftime('%d-%m-%Y %H:%M:%S.%f')[:-3]
        fileName, lineno = self.inspector()
        super().info(
            f"{fg.BLUE}[JSON]{fg.RESET} {time} {style.DIM}{fileName}#{lineno}{style.RESET_ALL}")
        pprint_color(msg)

    def warning(self, msg, *args, **kwargs):
        time = datetime.now().strftime('%d-%m-%Y %H:%M:%S.%f')[:-3]
        fileName, lineno = self.inspector()
        colored_message = f"{fg.YELLOW}[WARN]{fg.RESET} {time} {style.DIM}{fileName}#{lineno}{style.RESET_ALL}\n       {fg.YELLOW}{msg}{fg.RESET}"
        super().warning(colored_message, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        time = datetime.now().strftime('%d-%m-%Y %H:%M:%S.%f')[:-3]
        fileName, lineno = self.inspector()
        colored_message = f"{fg.RED}[ERROR]{fg.RESET} {time} {style.DIM}{fileName}#{lineno}{style.RESET_ALL}\n        {fg.RED}{msg}{fg.RESET}"
        super().error(colored_message, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        time = datetime.now().strftime('%d-%m-%Y %H:%M:%S.%f')[:-3]
        with open(os.path.join(os.path.dirname(__file__), 'critical.msg')) as f:
            critical_message = f.read()
        colored_message = f"{time} {fg.RED}{style.BRIGHT}{critical_message} {style.RESET_ALL}\n{fg.RED}{msg}{fg.RESET}"
        super().critical(colored_message, *args, **kwargs)
