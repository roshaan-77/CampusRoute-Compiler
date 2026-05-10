from phase_common import read_source
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.icg import IntermediateCodeGenerator


source = read_source("Run intermediate code generation only")
tokens = Lexer(source).tokenize()
program = Parser(tokens).parse()
SemanticAnalyzer().analyse(program)

icg = IntermediateCodeGenerator()
tac = icg.generate(program)
print(icg.format(tac))
