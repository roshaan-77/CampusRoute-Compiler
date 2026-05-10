from phase_common import read_source
from src.lexer import Lexer


source = read_source("Run lexical analysis only")
tokens = Lexer(source).tokenize()
for token in tokens:
    print(token)
