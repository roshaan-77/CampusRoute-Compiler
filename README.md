# CampusRoute Compiler

CampusRoute Compiler is a Compiler Construction project that converts simple
campus-map instructions into an interactive HTML map. The current demo shows the
route and approximate straight-line distance between FAST NUCES Karachi Main
Campus and FAST NUCES Karachi City Campus.

## Team Members

- Roshaan Haider
- Affan Rehman
- Mujtaba Khan
- Moazzam Junaid

## Project Idea

The user writes a small source file containing simple map commands such as map
center, campus markers, route, labels, layers, loops, and export instruction.
The compiler reads that file, checks it phase by phase, generates intermediate
code, optimizes it, creates target VM-style code, and finally produces an HTML
map.

## Complete Run Steps

Open terminal in the project folder:

```bash
cd C:\CC_Project
```

Install required packages:

```bash
pip install -r requirements.txt
```

Run the complete compiler:

```bash
python main.py fast_campus_route.cr
```

Open the generated map:

```text
output\fast_campus_distance.html
```

Run automated tests:

```bash
pytest tests/testcases.py -v
```

## Run Each Phase Separately

Lexical analysis:

```bash
python lexer_phase.py fast_campus_route.cr
```

Syntax analysis:

```bash
python parser_phase.py fast_campus_route.cr
```

Semantic analysis:

```bash
python semantic_phase.py fast_campus_route.cr
```

Intermediate code generation:

```bash
python icg_phase.py fast_campus_route.cr
```

Optimization:

```bash
python optimizer_phase.py fast_campus_route.cr
```

Target code generation:

```bash
python target_phase.py fast_campus_route.cr
```

## Output Files

After running the complete compiler, these files are created in `output/`:

| File | Meaning |
|---|---|
| `fast_campus_distance.html` | Final interactive map with route, campuses, distance panel, and legend |
| `intermediate.tac` | Three-address intermediate code |
| `optimized.tac` | Optimized intermediate code plus optimization report |
| `target.vm` | VM-style target code instructions |

## Important Files

| File / Folder | Importance |
|---|---|
| `fast_campus_route.cr` | Main input program for the FAST campus route demo |
| `main.py` | Runs the complete compiler pipeline |
| `lexer_phase.py` | Runs only lexical analysis |
| `parser_phase.py` | Runs only syntax analysis |
| `semantic_phase.py` | Runs only semantic analysis and prints symbol table |
| `icg_phase.py` | Runs only intermediate code generation |
| `optimizer_phase.py` | Runs only code optimization |
| `target_phase.py` | Runs only target code generation |
| `src/lexer.py` | Breaks source code into tokens |
| `src/parser.py` | Builds the Abstract Syntax Tree |
| `src/semantic.py` | Checks variables, types, scope, coordinates, and errors |
| `src/icg.py` | Generates TAC intermediate code |
| `src/optimizer.py` | Applies constant folding, copy propagation, and dead code elimination |
| `src/target_codegen.py` | Generates VM-style target instructions |
| `src/codegen.py` | Generates the final styled HTML map |
| `tests/testcases.py` | Automated test cases |
| `Documentation/CampusRoute_Project_Report.md` | 3-4 page project report |

## Compiler Phases

```text
Source file
   -> Lexical Analysis
   -> Syntax Analysis
   -> Semantic Analysis
   -> Intermediate Code Generation
   -> Code Optimization
   -> Target Code Generation
   -> Final HTML Map
```

## Grammar Summary

```text
program     -> statement*
statement   -> map | marker | label | route | circle | rect | polygon
             | let | layer | for | if | export
map         -> map center=coord zoom=number theme=identifier
marker      -> marker string at coord_or_var attributes
route       -> route string from coord_or_var to coord_or_var attributes end
let         -> let identifier = value
layer       -> layer string statement* end
for         -> for identifier in identifier statement* end
if          -> if value comparison value then statement* end
export      -> export as string
coord       -> (number, number)
```
