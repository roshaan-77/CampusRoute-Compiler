from phase_common import read_source
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer


source = read_source("Run semantic analysis only")
tokens = Lexer(source).tokenize()
program = Parser(tokens).parse()
analyzer = SemanticAnalyzer()
analyzer.analyse(program)

print("Semantic analysis successful.")
print("\nSymbol Table")
for name, value in analyzer.symbol_table.items():
    data_type = analyzer.type_table.get(name, "unknown")
    scope = analyzer.scope_table.get(name, "global")
    print(f"{name}: value={value}, type={data_type}, scope={scope}")

if analyzer.warnings:
    print("\nWarnings")
    for warning in analyzer.warnings:
        print(warning)
