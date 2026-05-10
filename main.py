import argparse
import os
import sys

from src.codegen import CodeGenError
from src.compiler import compile_source
from src.lexer import LexerError
from src.parser import ParseError
from src.semantic import SemanticError


def main():
    parser = argparse.ArgumentParser(
        prog="campusroute",
        description="CampusRoute Compiler - compile campus route source files into interactive HTML maps.",
    )
    parser.add_argument("source", help="Path to the CampusRoute source file")
    parser.add_argument(
        "--output-dir",
        default="output",
        metavar="DIR",
        help="Directory to save generated files (default: ./output)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.source):
        print(f"[Error] File not found: {args.source}")
        sys.exit(1)

    with open(args.source, "r", encoding="utf-8") as f:
        source = f.read()

    print(f"\n{'=' * 50}")
    print("  CampusRoute Compiler")
    print(f"  Source : {args.source}")
    print(f"  Output : {args.output_dir}/")
    print(f"{'=' * 50}\n")

    try:
        out_path = compile_source(source, output_dir=args.output_dir)
        print(f"\n{'=' * 50}")
        print("Compilation successful")
        print(f"  Open in browser: {os.path.abspath(out_path)}")
        print(f"{'=' * 50}\n")
    except LexerError as e:
        print(f"\n{e}")
        print("\nFAIL: Compilation failed at Lexer phase.")
        sys.exit(1)
    except ParseError as e:
        print(f"\n{e}")
        print("\nFAIL: Compilation failed at Parser phase.")
        sys.exit(1)
    except SemanticError as e:
        print(f"\n{e}")
        print("\nFAIL: Compilation failed at Semantic Analysis phase.")
        sys.exit(1)
    except CodeGenError as e:
        print(f"\n[Code Gen Error] {e}")
        print("\nFAIL: Compilation failed at Code Generation phase.")
        sys.exit(1)


if __name__ == "__main__":
    main()
