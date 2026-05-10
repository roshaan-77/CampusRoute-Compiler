from pprint import pprint

from phase_common import read_source
from src.lexer import Lexer
from src.parser import Parser


source = read_source("Run syntax analysis only")
tokens = Lexer(source).tokenize()
program = Parser(tokens).parse()
pprint(program)
