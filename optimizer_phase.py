from phase_common import read_source
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.icg import IntermediateCodeGenerator
from src.optimizer import Optimizer


source = read_source("Run optimization phase only")
tokens = Lexer(source).tokenize()
program = Parser(tokens).parse()
SemanticAnalyzer().analyse(program)

icg = IntermediateCodeGenerator()
tac = icg.generate(program)
optimizer = Optimizer()
optimized = optimizer.optimize(tac)

print(icg.format(optimized))
print("\nOptimization Report")
print(optimizer.format_report())
