# CampusRoute Compiler Project Report

## 1. Project Overview

CampusRoute Compiler is a Compiler Construction project designed to convert a
simple campus-route source file into an interactive HTML map. The project focuses
on the route between FAST NUCES Karachi Main Campus and FAST NUCES Karachi City
Campus. Instead of manually writing long mapping code, the user writes readable
instructions such as where to place markers, how to draw a route, which labels to
show, and what output file should be generated.

The project demonstrates the complete compiler workflow required for evaluation:
lexical analysis, syntax analysis, semantic analysis, intermediate code
generation, optimization, target code generation, and final map generation. The
final HTML output contains a styled information panel showing both campus names,
the approximate straight-line distance, and a color legend for the map.

Team members:

- Roshaan Haider
- Affan Rehman
- Mujtaba Khan
- Moazzam Junaid

## 2. Language Concept

CampusRoute source code is written as simple commands. A user can define the map
center, store coordinates in variables, place markers, draw routes, create
circles, add labels, group items into layers, use loops, apply conditions, and
export the result as an HTML file.

Example source commands:

```text
map center=(24.8586, 67.1672) zoom=11 theme=light
let mainCampus = (24.857468, 67.264638)
let cityCampus = (24.859722, 67.069722)

route "FAST Main Campus to FAST City Campus"
    from mainCampus
    to cityCampus
    color=orange width=3
end

export as "fast_campus_distance.html"
```

In simple words, the project reads these instructions, checks that they are
valid, and generates a browser-based map. This makes the project easy to explain
in viva because the input and output are both visible and meaningful.

## 3. Compiler Phases

### 3.1 Lexical Analysis

The lexical analyzer reads the source file character by character and converts
the text into tokens. For example, the word `map` becomes a `MAP` token, a quoted
campus name becomes a `STRING` token, and a coordinate value becomes a `NUMBER`
token. Lexical errors are reported when an unknown character or invalid string is
found.

Main file: `src/lexer.py`  
Standalone runner: `lexer_phase.py`

### 3.2 Syntax Analysis

The parser receives the token list and checks whether the source follows the
grammar. It builds an Abstract Syntax Tree, which is a structured representation
of the program. If a route is missing `end`, or if a statement starts with an
invalid word, the parser reports a syntax error with line information.

Main file: `src/parser.py`  
Standalone runner: `parser_phase.py`

### 3.3 Semantic Analysis

The semantic analyzer checks the meaning of the program. It verifies that a map
statement exists, export is present, coordinates are in valid ranges, variables
are declared before use, loops use list variables, and values have suitable
types. This phase also maintains a symbol table containing variable names,
values, data types, and scope information.

Main file: `src/semantic.py`  
Standalone runner: `semantic_phase.py`

### 3.4 Intermediate Code Generation

After semantic analysis, the compiler converts the AST into three-address code.
This intermediate code is easier to optimize and explain than direct HTML map
generation. It includes operations such as `MAP`, `ASSIGN`, `MARKER`, `ROUTE`,
`DISTANCE_KM`, and `EXPORT`.

Main file: `src/icg.py`  
Standalone runner: `icg_phase.py`  
Generated file: `output/intermediate.tac`

### 3.5 Code Optimization

The optimizer improves the intermediate code before target generation. Three
optimization techniques are implemented:

- Constant folding: evaluates expressions such as `zoom >= 12` during
  compilation.
- Copy propagation: replaces alias variables with their original variables where
  possible.
- Dead code elimination: removes unreachable code when a condition is known to
  be false.

Main file: `src/optimizer.py`  
Standalone runner: `optimizer_phase.py`  
Generated file: `output/optimized.tac`

### 3.6 Target Code Generation

The target code generator converts optimized TAC into VM-style instructions.
These instructions are low-level compared with the source language and include
commands such as `PUSH_POINT`, `ADD_MARKER`, `ADD_ROUTE`, `CALC_DISTANCE_KM`,
`EXPORT_HTML`, and `HALT`.

Main file: `src/target_codegen.py`  
Standalone runner: `target_phase.py`  
Generated file: `output/target.vm`

## 4. Final Output

The final output is an interactive HTML map generated in the `output` folder.
The map shows:

- FAST NUCES Karachi Main Campus marker
- FAST NUCES Karachi City Campus marker
- Route between both campuses
- Approximate straight-line distance
- Nearby area labels
- Bus stop layer
- Styled information panel and color legend

Final output file:

```text
output/fast_campus_distance.html
```

## 5. How to Run

Open the project folder:

```bash
cd C:\CC_Project
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the complete compiler:

```bash
python main.py fast_campus_route.cr
```

Run individual phases:

```bash
python lexer_phase.py fast_campus_route.cr
python parser_phase.py fast_campus_route.cr
python semantic_phase.py fast_campus_route.cr
python icg_phase.py fast_campus_route.cr
python optimizer_phase.py fast_campus_route.cr
python target_phase.py fast_campus_route.cr
```

Run test cases:

```bash
pytest tests/testcases.py -v
```

## 6. Error Handling

The project includes lexical, syntax, and semantic error handling. Lexical errors
catch invalid characters and unterminated strings. Syntax errors catch invalid
grammar, missing keywords, and incomplete blocks. Semantic errors catch missing
map/export statements, invalid coordinate ranges, undefined variables, wrong loop
variables, invalid opacity, and invalid route width.

Clear error messages help during demo because the evaluator can test both valid
and invalid inputs.

## 7. Conclusion

CampusRoute Compiler is a complete compiler project with all required phases. It
uses a meaningful real-world example, demonstrates independent execution of each
compiler phase, generates intermediate and target code, performs real
optimization, and produces a visible HTML map as the final result. The project is
suitable for viva because the flow is simple to explain: source file, tokens,
AST, semantic checks, TAC, optimized TAC, VM-style target code, and final map.
