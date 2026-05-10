# compiler
# Chains: Lexer,Parser,Semantic Analyser,Code Generator
# + error reporting

from src.lexer    import Lexer,             LexerError
from src.parser   import Parser,            ParseError
from src.semantic import SemanticAnalyzer,  SemanticError
from src.icg      import IntermediateCodeGenerator, ICGError
from src.optimizer import Optimizer
from src.target_codegen import TargetCodeGenerator
from src.codegen  import CodeGenerator,     CodeGenError

# Full compilation pipeline.
# Parameters: raw source code string
# Returns: Path to the generated HTML file.
# Raises:  LexerError / ParseError / SemanticError / CodeGenError on failure.

def compile_source(source: str, output_dir: str = "output") -> str:
    #  Phase 1: Lexing 
    print("[Lexer]    Tokenizing source...")
    lexer  = Lexer(source)
    tokens = lexer.tokenize()
    print(f"[Lexer]    {len(tokens) - 1} tokens produced")

    #  Phase 2: Parsing 
    print("[Parser]   Building AST...")
    parser  = Parser(tokens)
    program = parser.parse()
    node_count = _count_nodes(program)
    print(f"[Parser]   AST built — {node_count} nodes")

    #  Phase 3: Semantic Analysis 
    print("[Semantic] Analysing...")
    analyser = SemanticAnalyzer()
    analyser.analyse(program)
    if analyser.warnings:
        for w in analyser.warnings:
            print(f"             {w}")
    print("[Semantic] No errors found")

    #  Phase 4: Intermediate Code Generation
    print("[ICG]      Generating three-address code...")
    icg = IntermediateCodeGenerator()
    tac = icg.generate(program)
    print(f"[ICG]      {len(tac)} TAC instructions produced")

    #  Phase 5: Code Optimization
    print("[Optimize] Applying constant folding, copy propagation, and dead code elimination...")
    optimizer = Optimizer()
    optimized_tac = optimizer.optimize(tac)
    for change in optimizer.changes:
        print(f"           {change}")
    print(f"[Optimize] {len(optimized_tac)} optimized TAC instructions")

    #  Phase 6: Target Code Generation
    print("[Target]   Generating VM-style target code...")
    target = TargetCodeGenerator()
    target_code = target.generate(optimized_tac)
    print(f"[Target]   {len(target_code)} target instructions produced")

    #  Final project output: HTML map
    print("[Codegen]  Generating final HTML map...")
    gen      = CodeGenerator(output_dir=output_dir)
    out_path = gen.generate(program)
    print(f"[Codegen]  Map saved to {out_path}")

    _write_phase_outputs(output_dir, icg, tac, optimized_tac, optimizer, target, target_code)

    return out_path

#  Utility: count AST nodes recursively
def _count_nodes(node) -> int:
    count = 1
    for attr in ("statements", "body", "then_body"):
        children = getattr(node, attr, None)
        if isinstance(children, list):
            for child in children:
                count += _count_nodes(child)
    return count


def _write_phase_outputs(output_dir, icg, tac, optimized_tac, optimizer, target, target_code):
    import os

    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "intermediate.tac"), "w", encoding="utf-8") as f:
        f.write(icg.format(tac) + "\n")
    with open(os.path.join(output_dir, "optimized.tac"), "w", encoding="utf-8") as f:
        f.write(icg.format(optimized_tac) + "\n\nOptimization Report\n")
        f.write(optimizer.format_report() + "\n")
    with open(os.path.join(output_dir, "target.vm"), "w", encoding="utf-8") as f:
        f.write(target.format(target_code) + "\n")
