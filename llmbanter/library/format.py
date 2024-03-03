import ast

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import PythonLexer
from rich.text import Text


class RichTerminalFormatter:
    def is_python_code(self, text: str) -> bool:
        try:
            ast.parse(text)
            return True
        except SyntaxError:
            return False

    def format_response(self, text: str, default_color: str) -> str:
        if self.is_python_code(text):
            # TODO: extract any ```python ... ``` code blocks and format them
            text_code = highlight(text, PythonLexer(), TerminalFormatter())
            return str(Text.from_ansi(text_code))  # Prep for rich text printing
        return f"[{default_color}]{text}[/{default_color}]"
