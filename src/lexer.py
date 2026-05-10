# Tokenizer for the CampusRoute language.

# Converts raw CampusRoute source text into a flat list of Token objects.
# Each token carries its type, value, and source line number.

import re
from dataclasses import dataclass
from typing import List

#  Token types
TT = type("TT", (), {
    # Literals
    "NUMBER":     "NUMBER",
    "STRING":     "STRING",
    "BOOL":       "BOOL",

    # Keywords
    "MAP":        "MAP",
    "MARKER":     "MARKER",
    "LABEL":      "LABEL",
    "ROUTE":      "ROUTE",
    "CIRCLE":     "CIRCLE",
    "RECT":       "RECT",
    "POLYGON":    "POLYGON",
    "LET":        "LET",
    "LAYER":      "LAYER",
    "FOR":        "FOR",
    "IN":         "IN",
    "IF":         "IF",
    "THEN":       "THEN",
    "END":        "END",
    "EXPORT":     "EXPORT",
    "AS":         "AS",
    "AT":         "AT",
    "FROM":       "FROM",
    "TO":         "TO",
    "RADIUS":     "RADIUS",

    # Identifiers
    "IDENT":      "IDENT",

    # Operators & punctuation
    "EQUALS":     "EQUALS",       # =
    "EQ":         "EQ",           # ==
    "NEQ":        "NEQ",          # !=
    "GT":         "GT",           # >
    "LT":         "LT",           # <
    "GTE":        "GTE",          # >=
    "LTE":        "LTE",          # <=
    "LPAREN":     "LPAREN",       # (
    "RPAREN":     "RPAREN",       # )
    "LBRACKET":   "LBRACKET",     # [
    "RBRACKET":   "RBRACKET",     # ]
    "COMMA":      "COMMA",        # ,
    "ARROW":      "ARROW",        # ->

    "EOF":        "EOF",
})

#  Token dataclass
@dataclass
class Token:
    type: str
    value: object
    line: int

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"

#  Keywords table
KEYWORDS = {
    "map":      TT.MAP,
    "marker":   TT.MARKER,
    "label":    TT.LABEL,
    "route":    TT.ROUTE,
    "circle":   TT.CIRCLE,
    "rect":     TT.RECT,
    "polygon":  TT.POLYGON,
    "let":      TT.LET,
    "layer":    TT.LAYER,
    "for":      TT.FOR,
    "in":       TT.IN,
    "if":       TT.IF,
    "then":     TT.THEN,
    "end":      TT.END,
    "export":   TT.EXPORT,
    "as":       TT.AS,
    "at":       TT.AT,
    "from":     TT.FROM,
    "to":       TT.TO,
    "radius":   TT.RADIUS,
    "true":     TT.BOOL,
    "false":    TT.BOOL,
}

#  Lexer
class LexerError(Exception):
    pass


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.tokens: List[Token] = []

    # helpers 

    def peek(self, offset=0) -> str:
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else ""

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
        return ch

    def match(self, expected: str) -> bool:
        if self.pos < len(self.source) and self.source[self.pos] == expected:
            self.pos += 1
            return True
        return False

    def add(self, ttype: str, value=None):
        self.tokens.append(Token(ttype, value, self.line))

    def error(self, msg: str):
        raise LexerError(f"[Lexer Error] Line {self.line}: {msg}")

    #  main tokenize loop 

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self._scan_token()
        self.add(TT.EOF)
        return self.tokens

    def _scan_token(self):
        ch = self.advance()

        # Whitespace
        if ch in " \t\r\n":
            return

        # Comments  (// ... )
        if ch == "/" and self.peek() == "/":
            while self.peek() and self.peek() != "\n":
                self.advance()
            return

        # String literals
        if ch == '"':
            self._string()
            return

        # Numbers with units
        if ch.isdigit() or (ch == "-" and self.peek().isdigit()):
            self._number(ch)
            return

        # Two-char operators
        if ch == "=" and self.match("="):
            self.add(TT.EQ, "=="); return
        if ch == "!" and self.match("="):
            self.add(TT.NEQ, "!="); return
        if ch == ">" and self.match("="):
            self.add(TT.GTE, ">="); return
        if ch == "<" and self.match("="):
            self.add(TT.LTE, "<="); return
        if ch == "-" and self.match(">"):
            self.add(TT.ARROW, "->"); return

        # Single-char operators
        single = {
            "=": TT.EQUALS,
            ">": TT.GT,
            "<": TT.LT,
            "(": TT.LPAREN,
            ")": TT.RPAREN,
            "[": TT.LBRACKET,
            "]": TT.RBRACKET,
            ",": TT.COMMA,
        }
        if ch in single:
            self.add(single[ch], ch)
            return

        # Identifiers and keywords
        if ch.isalpha() or ch == "_" or ch == "#":
            self._ident_or_keyword(ch)
            return

        self.error(f"Unexpected character: {ch!r}")

    #  sub-scanners 

    def _string(self):
        # ""
        start = self.pos
        while self.peek() and self.peek() != '"':
            if self.peek() == "\n":
                self.error("Unterminated string literal")
            self.advance()
        if not self.peek():
            self.error("Unterminated string literal")
        self.advance()  # closing "
        value = self.source[start: self.pos - 1]
        self.add(TT.STRING, value)

    def _number(self, first_ch: str):
        # Numbers with units
        buf = first_ch
        while self.peek().isdigit():
            buf += self.advance()
        if self.peek() == "." and self.source[self.pos + 1:self.pos + 2].isdigit():
            buf += self.advance()  # consume '.'
            while self.peek().isdigit():
                buf += self.advance()
        value = float(buf)

        # Optional unit suffix
        unit = ""
        if self.peek() in ("k", "m"):
            unit_buf = self.advance()
            if unit_buf == "k" and self.peek() == "m":
                unit_buf += self.advance()
            unit = unit_buf

        if unit == "km":
            value = value * 1000

        self.add(TT.NUMBER, value)

    def _ident_or_keyword(self, first_ch: str):
        buf = first_ch
        while self.peek().isalnum() or self.peek() in ("_", "-"):
            buf += self.advance()
        lower = buf.lower()
        if lower in KEYWORDS:
            ttype = KEYWORDS[lower]
            value = True if lower == "true" else (False if lower == "false" else lower)
            self.add(ttype, value)
        else:
            self.add(TT.IDENT, buf)
