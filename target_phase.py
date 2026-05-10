from phase_common import read_source
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.icg import IntermediateCodeGenerator
from src.optimizer import Optimizer
from src.target_codegen import TargetCodeGenerator


source = read_source("Run target code generation only")
tokens = Lexer(source).tokenize()
program = Parser(tokens).parse()
SemanticAnalyzer().analyse(program)

icg = IntermediateCodeGenerator()
tac = icg.generate(program)
optimized = Optimizer().optimize(tac)
target = TargetCodeGenerator()
print(target.format(target.generate(optimized)))
